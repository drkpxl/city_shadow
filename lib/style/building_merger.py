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

        for b in cluster:
            coords = b["coords"]
            area = self.geometry.calculate_polygon_area(coords)
            total_area += area
            weighted_height += b["height"] * area
            all_coords.extend(coords)

        avg_height = (
            weighted_height / total_area if total_area > 0 else cluster[0]["height"]
        )
        hull_coords = self.style_manager.artistic_effects.create_artistic_hull(
            all_coords
        )

        return {
            "coords": hull_coords,
            "height": avg_height,
            "is_cluster": True,
            "size": len(cluster),
        }
