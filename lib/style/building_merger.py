# lib/style/building_merger.py
from shapely.geometry import LineString
from ..geometry import GeometryUtils


class BuildingMerger:
    def __init__(self, style_manager):
        self.style_manager = style_manager
        self.geometry = GeometryUtils()

    def merge_buildings(self, buildings, barrier_union=None):
        """Choose and execute merging strategy."""
        if self.style_manager.style["artistic_style"] == "block-combine":
            return self._merge_by_blocks(buildings)
        else:
            return self._merge_by_distance(buildings, barrier_union)

    def _merge_by_blocks(self, buildings):
        """Merge buildings by block."""
        from .block_combiner import BlockCombiner  # Local import

        block_combiner = BlockCombiner(self.style_manager)
        return block_combiner.combine_buildings_by_block(
            self.style_manager.current_features
        )

    def _merge_by_distance(self, buildings, barrier_union):
        """Merge buildings based on distance."""
        merge_dist = self.style_manager.style["merge_distance"]
        if merge_dist <= 0:
            return buildings

        indexed_buildings = self._index_buildings(buildings)
        visited = set()
        clusters = []

        for i, centroidA, bldgA in indexed_buildings:
            if i in visited:
                continue

            cluster = self._build_cluster(
                i, indexed_buildings, visited, barrier_union, merge_dist
            )
            merged = self._merge_cluster(cluster)
            clusters.append(merged)

        return clusters

    def _index_buildings(self, buildings):
        """Create indexed building list with centroids."""
        return [
            (idx, self.geometry.calculate_centroid(bldg["coords"]), bldg)
            for idx, bldg in enumerate(buildings)
        ]

    def _build_cluster(
        self, start_idx, indexed_buildings, visited, barrier_union, merge_dist
    ):
        """Build a cluster of buildings starting from given index."""
        stack = [start_idx]
        cluster = []
        visited.add(start_idx)

        while stack:
            current_idx = stack.pop()
            _, current_centroid, current_bldg = indexed_buildings[current_idx]
            cluster.append(current_bldg)

            for j, centroidB, bldgB in indexed_buildings:
                if j not in visited:
                    dist = self.geometry.calculate_distance(current_centroid, centroidB)
                    if dist < merge_dist:
                        if not self._is_blocked(
                            current_centroid, centroidB, barrier_union
                        ):
                            visited.add(j)
                            stack.append(j)

        return cluster

    def _is_blocked(self, ptA, ptB, barrier_union):
        """Check if line between points is blocked by barrier."""
        if barrier_union is None:
            return False
        line = LineString([ptA, ptB])
        return line.intersects(barrier_union)

    def _merge_cluster(self, cluster):
        """Merge a cluster of buildings into one shape."""
        if len(cluster) == 1:
            return cluster[0]

        total_area = 0.0
        weighted_height = 0.0
        all_coords = []
        roof_styles = []

        for b in cluster:
            coords = b["coords"]
            area = self.geometry.calculate_polygon_area(coords)
            total_area += area
            weighted_height += b["height"] * area
            all_coords.extend(coords)
            if "roof_style" in b:
                roof_styles.append(b["roof_style"])

        avg_height = (
            weighted_height / total_area if total_area > 0 else cluster[0]["height"]
        )
        hull_coords = self.style_manager.artistic_effects.create_artistic_hull(
            all_coords
        )

        # Determine roof style for merged cluster
        # Use the most common style, or pick a random one if they're all different
        if roof_styles:
            from collections import Counter
            style_counts = Counter(roof_styles)
            most_common = style_counts.most_common(1)[0][0]
            roof_style = most_common
            # Use the same params as the first building with this style
            for b in cluster:
                if b.get("roof_style") == roof_style and "roof_params" in b:
                    roof_params = b["roof_params"]
                    break
            else:
                # Generate new params if needed
                import random
                if roof_style == 'pitched':
                    roof_params = {'height_factor': random.uniform(0.2, 0.4)}
                elif roof_style == 'tiered':
                    roof_params = {'levels': random.randint(2, 4)}
                elif roof_style == 'flat':
                    roof_params = {'border': random.uniform(0.8, 1.2)}
                elif roof_style == 'sawtooth':
                    roof_params = {'angle': random.randint(25, 35)}
                elif roof_style == 'modern':
                    roof_params = {'setback': random.uniform(1.8, 2.2)}
                elif roof_style == 'stepped':
                    roof_params = {'levels': random.randint(2, 4)}
                else:
                    roof_params = {}
        else:
            # If no roof styles in cluster, check if we have a list of allowed styles
            available_styles = self.style_manager.style.get('roof_styles', None)
            if available_styles and isinstance(available_styles, list):
                import random
                roof_style = random.choice(available_styles)
                # Generate params for the selected style
                if roof_style == 'pitched':
                    roof_params = {'height_factor': random.uniform(0.2, 0.4)}
                elif roof_style == 'tiered':
                    roof_params = {'levels': random.randint(2, 4)}
                elif roof_style == 'flat':
                    roof_params = {'border': random.uniform(0.8, 1.2)}
                elif roof_style == 'sawtooth':
                    roof_params = {'angle': random.randint(25, 35)}
                elif roof_style == 'modern':
                    roof_params = {'setback': random.uniform(1.8, 2.2)}
                elif roof_style == 'stepped':
                    roof_params = {'levels': random.randint(2, 4)}
                else:
                    roof_params = {}
            else:
                roof_style = None
                roof_params = None

        result = {
            "coords": hull_coords,
            "height": avg_height,
            "is_cluster": True,
            "size": len(cluster),
        }
        
        if roof_style:
            result["roof_style"] = roof_style
            result["roof_params"] = roof_params
            
        return result
