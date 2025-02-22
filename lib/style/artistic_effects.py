# lib/style/artistic_effects.py
from math import sin, cos, pi, atan2


class ArtisticEffects:
    def __init__(self, style_manager):
        self.style_manager = style_manager

    def create_artistic_hull(self, points):
        """Create artistic hull from points based on style settings."""
        if len(points) < 3:
            return points

        from ..geometry import GeometryUtils

        geometry = GeometryUtils()

        center = geometry.calculate_centroid(points)
        sorted_points = self._sort_points_by_angle(points, center)
        hull = self._generate_hull_points(sorted_points, geometry)

        return self._add_artistic_variation(hull)

    def _sort_points_by_angle(self, points, center):
        """Sort points by angle around center."""
        return sorted(points, key=lambda p: atan2(p[1] - center[1], p[0] - center[0]))

    def _generate_hull_points(self, sorted_points, geometry):
        """Generate hull points with optional detail points."""
        hull = []
        detail_level = self.style_manager.style["detail_level"]
        cluster_size = self.style_manager.style["cluster_size"]

        for i in range(len(sorted_points)):
            p1 = sorted_points[i]
            p2 = sorted_points[(i + 1) % len(sorted_points)]
            hull.append(p1)

            if detail_level > 0.5:
                self._add_detail_points(
                    hull, p1, p2, detail_level, cluster_size, geometry
                )

        return hull

    def _add_detail_points(self, hull, p1, p2, detail_level, cluster_size, geometry):
        """Add intermediate detail points between two points."""
        dist = geometry.calculate_distance(p1, p2)
        if dist > cluster_size:
            num_points = int(detail_level * dist / cluster_size)
            for j in range(num_points):
                t = (j + 1) / (num_points + 1)
                mx = p1[0] + t * (p2[0] - p1[0])
                my = p1[1] + t * (p2[1] - p1[1])
                offset = self.style_manager.style["height_variance"] * sin(t * pi)
                hull.append([mx + offset, my - offset])

    def _add_artistic_variation(self, coords):
        """Add style-specific variations to coordinates."""
        varied = []
        variance = self.style_manager.style["height_variance"]
        style = self.style_manager.style["artistic_style"]

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
