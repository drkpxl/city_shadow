# lib/style_manager.py
from math import log10, sin, cos, pi, atan2
from shapely.geometry import LineString
from .geometry import GeometryUtils
from .style.block_combiner import BlockCombiner


class StyleManager:
    def __init__(self, style_settings=None):
        self.geometry = GeometryUtils()
        self.block_combiner = BlockCombiner(self)
        self.current_features = {}

        # Default style settings
        self.style = {
            "merge_distance": 2.0,
            "cluster_size": 3.0,
            "height_variance": 0.2,
            "detail_level": 1.0,
            "artistic_style": "modern",
            "min_building_area": 600.0,
        }

        # Override defaults with provided settings
        if style_settings:
            self.style.update(style_settings)

    def get_default_layer_specs(self):
        """Get default layer specifications for roads, water, buildings, etc."""
        return {
            "water": {
                "depth": 3,
            },
            "roads": {
                "depth": 0.6,
                "width": 2.0,
            },
            "railways": {
                "depth": 0.2,
                "width": 1.5,
            },
            "buildings": {"min_height": 2, "max_height": 5},
            "base": {
                "height": 5,
            },
            "parks": {
                "start_offset": 0,  # Height offset above the base for parks
                "thickness": 0.5      # Extrusion thickness for parks
            },
        }

    def scale_building_height(self, properties):
        """
        Given a building's OSM properties, produce a scaled building height (in mm).
        Uses a simple log scaling approach to map real-world height to a small range.
        """
        default_height = 4.0

        height_m = None
        if "height" in properties:
            try:
                height_m = float(properties["height"].split()[0])
            except (ValueError, IndexError):
                pass
        elif "building:levels" in properties:
            try:
                levels = float(properties["building:levels"])
                height_m = levels * 3  # assume 3m per level
            except ValueError:
                pass

        if height_m is None:
            height_m = default_height

        layer_specs = self.get_default_layer_specs()
        min_height = layer_specs["buildings"]["min_height"]
        max_height = layer_specs["buildings"]["max_height"]

        # Log scaling from 1..100 meters -> min_height..max_height in mm
        log_min = log10(1.0)
        log_max = log10(101.0)
        log_height = log10(height_m + 1.0)  # +1 to avoid log(0)
        scaled = (log_height - log_min) / (log_max - log_min)
        final_height = min_height + scaled * (max_height - min_height)
        return round(final_height, 2)

    def merge_nearby_buildings(self, buildings, barrier_union=None):
        """Choose merging strategy based on style."""
        if self.style["artistic_style"] == "block-combine":
            return self.block_combiner.combine_buildings_by_block(self.current_features)
        else:
            return self._merge_buildings_by_distance(buildings, barrier_union)

    def _merge_buildings_by_distance(self, buildings, barrier_union=None):
        """Original distance-based merging logic"""
        merge_dist = self.style["merge_distance"]
        if merge_dist <= 0:
            return buildings

        indexed_buildings = []
        for idx, bldg in enumerate(buildings):
            ctd = self.geometry.calculate_centroid(bldg["coords"])
            indexed_buildings.append((idx, ctd, bldg))

        visited = set()
        clusters = []

        for i, centroidA, bldgA in indexed_buildings:
            if i in visited:
                continue

            stack = [i]
            cluster_bldgs = []
            visited.add(i)

            while stack:
                current_idx = stack.pop()
                _, current_centroid, current_bldg = indexed_buildings[current_idx]
                cluster_bldgs.append(current_bldg)

                for j, centroidB, bldgB in indexed_buildings:
                    if j in visited:
                        continue
                    dist = self.geometry.calculate_distance(current_centroid, centroidB)
                    if dist < merge_dist:
                        if not self._is_blocked_by_barrier(
                            current_centroid, centroidB, barrier_union
                        ):
                            visited.add(j)
                            stack.append(j)

            merged = self._merge_building_cluster(cluster_bldgs)
            clusters.append(merged)

        return clusters

    def _is_blocked_by_barrier(self, ptA, ptB, barrier_union):
        """Return True if the line from ptA to ptB intersects the barrier_union"""
        if barrier_union is None:
            return False
        line = LineString([ptA, ptB])
        return line.intersects(barrier_union)

    def _merge_building_cluster(self, cluster):
        """Merge building polygons in 'cluster' into one shape"""
        if len(cluster) == 1:
            return cluster[0]

        total_area = 0.0
        weighted_height = 0.0
        all_coords = []

        for b in cluster:
            coords = b["coords"]
            area = self.geometry.calculate_polygon_area(coords)
            total_area += area
            weighted_height += b["height"] * area
            all_coords.extend(coords)

        avg_height = (
            weighted_height / total_area if total_area > 0 else cluster[0]["height"]
        )
        hull_coords = self._create_artistic_hull(all_coords)

        return {
            "coords": hull_coords,
            "height": avg_height,
            "is_cluster": True,
            "size": len(cluster),
        }

    def _add_artistic_variation(self, coords):
        """Add small coordinate perturbations for artistic effect"""
        varied = []
        variance = self.style["height_variance"]
        style = self.style["artistic_style"]

        if style == "modern":
            for i, (x, y) in enumerate(coords):
                offset = variance * sin(i * pi / len(coords))
                varied.append([x + offset, y + offset])
        elif style == "classic":
            for i, (x, y) in enumerate(coords):
                angle = 2.0 * pi * i / len(coords)
                offset_x = variance * cos(angle)
                offset_y = variance * sin(angle)
                varied.append([x + offset_x, y + offset_y])
        else:  # minimal or block-combine
            varied = coords

        return varied

    def _create_artistic_hull(self, points):
        """Sort points by angle around centroid and optionally add detail"""
        if len(points) < 3:
            return points

        center = self.geometry.calculate_centroid(points)
        sorted_points = sorted(
            points, key=lambda p: atan2(p[1] - center[1], p[0] - center[0])
        )
        hull = []
        detail_level = self.style["detail_level"]

        for i in range(len(sorted_points)):
            p1 = sorted_points[i]
            p2 = sorted_points[(i + 1) % len(sorted_points)]
            hull.append(p1)

            if detail_level > 0.5:
                dist = self.geometry.calculate_distance(p1, p2)
                if dist > self.style["cluster_size"]:
                    num_points = int(detail_level * dist / self.style["cluster_size"])
                    for j in range(num_points):
                        t = (j + 1) / (num_points + 1)
                        mx = p1[0] + t * (p2[0] - p1[0])
                        my = p1[1] + t * (p2[1] - p1[1])
                        offset = self.style["height_variance"] * sin(t * pi)
                        hull.append([mx + offset, my - offset])

        hull = self._add_artistic_variation(hull)
        return hull

    def set_current_features(self, features):
        """Store current features for block-combine style to use"""
        self.current_features = features
