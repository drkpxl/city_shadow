"""
Geometry utilities for Shadow City Generator.

This module provides geometric calculations and transformations needed for
processing GeoJSON features and generating 3D models, including coordinate
transformation, area calculations, and polygon operations.
"""

from math import sqrt, sin, cos, pi, atan2, radians
from typing import List, Tuple, Dict, Any, Callable, Optional, Union
from dataclasses import dataclass

from .logging_manager import LoggingManager


@dataclass
class BoundingBox:
    """Container for geographic bounding box coordinates."""

    min_lon: float
    max_lon: float
    min_lat: float
    max_lat: float

    def get_center(self) -> Tuple[float, float]:
        """Calculate the center point of the bounding box."""
        return ((self.min_lon + self.max_lon) / 2, (self.min_lat + self.max_lat) / 2)


class GeometryUtils:
    """
    Utility class for geometric calculations and transformations.

    Provides methods for:
    - Coordinate transformation
    - Area calculations
    - Polygon operations
    - Distance calculations
    - Point and line operations
    """

    EARTH_RADIUS = 6371000.0  # Earth radius in meters

    def __init__(self, debug: bool = False):
        """
        Initialize geometry utilities.

        Args:
            debug: Enable debug logging
        """
        self.logger = LoggingManager(debug=debug, module_name="geometry")

    def create_coordinate_transformer(
        self, features: List[Dict[str, Any]], size: float
    ) -> Callable[[float, float], List[float]]:
        """
        Create a function that transforms geographic coordinates to model space.

        Args:
            features: List of GeoJSON features
            size: Target size in millimeters for the output model

        Returns:
            Function that transforms (lon, lat) to [x, y] in model space

        Raises:
            ValueError: If no valid coordinates are found in features
        """
        all_coords: List[Tuple[float, float]] = []
        for feature in features:
            coords = self.extract_coordinates(feature)
            all_coords.extend(coords)

        if not all_coords:
            self.logger.warning("No coordinates found in features")
            return lambda lon, lat: [size / 2, size / 2]

        # Calculate bounds
        bbox = self._calculate_bounding_box(all_coords)
        self.logger.debug(f"Bounding box: {bbox}")

        def transform(lon: float, lat: float) -> List[float]:
            """Transform geographic coordinates to model coordinates."""
            x = (
                (lon - bbox.min_lon) / (bbox.max_lon - bbox.min_lon)
                if (bbox.max_lon != bbox.min_lon)
                else 0.5
            )
            y = (
                (lat - bbox.min_lat) / (bbox.max_lat - bbox.min_lat)
                if (bbox.max_lat != bbox.min_lat)
                else 0.5
            )
            return [x * size, y * size]

        return transform

    def extract_coordinates(self, feature: Dict[str, Any]) -> List[Tuple[float, float]]:
        """
        Extract coordinates from a GeoJSON feature.

        Args:
            feature: GeoJSON feature dictionary

        Returns:
            List of (longitude, latitude) tuples

        Raises:
            ValueError: If feature geometry is invalid
        """
        try:
            geometry = feature["geometry"]
            coords: List[Tuple[float, float]] = []

            if geometry["type"] == "Point":
                coords = [tuple(geometry["coordinates"])]
            elif geometry["type"] == "LineString":
                coords = [tuple(coord) for coord in geometry["coordinates"]]
            elif geometry["type"] == "Polygon":
                coords = [tuple(coord) for coord in geometry["coordinates"][0]]
            elif geometry["type"] == "MultiPolygon":
                # Get the largest polygon by number of points
                largest = max(geometry["coordinates"], key=lambda p: len(p[0]))
                coords = [tuple(coord) for coord in largest[0]]

            return coords

        except (KeyError, IndexError, TypeError) as e:
            self.logger.error(f"Invalid feature geometry: {str(e)}")
            raise ValueError(f"Invalid feature geometry: {str(e)}")

    def calculate_centroid(self, points: List[List[float]]) -> List[float]:
        """
        Calculate the centroid of a set of points.

        Args:
            points: List of [x, y] coordinates

        Returns:
            [x, y] coordinates of the centroid

        Raises:
            ValueError: If points list is empty
        """
        if not points:
            raise ValueError("Cannot calculate centroid of empty point set")

        x = sum(p[0] for p in points) / len(points)
        y = sum(p[1] for p in points) / len(points)
        return [x, y]

    def calculate_distance(self, p1: List[float], p2: List[float]) -> float:
        """
        Calculate Euclidean distance between two points.

        Args:
            p1: First point [x, y]
            p2: Second point [x, y]

        Returns:
            Distance between points

        Raises:
            ValueError: If points have invalid coordinates
        """
        try:
            return sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)
        except (IndexError, TypeError) as e:
            raise ValueError(f"Invalid point coordinates: {str(e)}")

    def calculate_polygon_area(self, points: List[List[float]]) -> float:
        """
        Calculate area of a polygon using the shoelace formula.

        Args:
            points: List of [x, y] coordinates forming the polygon

        Returns:
            Area of the polygon

        Raises:
            ValueError: If polygon has fewer than 3 points
        """
        if len(points) < 3:
            raise ValueError("Polygon must have at least 3 points")

        area = 0.0
        j = len(points) - 1
        for i in range(len(points)):
            area += (points[j][0] + points[i][0]) * (points[j][1] - points[i][1])
            j = i
        return abs(area) / 2.0

    def generate_polygon_points(self, points: List[List[float]]) -> Optional[str]:
        """
        Generate polygon points string for OpenSCAD.

        Args:
            points: List of [x, y] coordinates forming the polygon

        Returns:
            String of points formatted for OpenSCAD polygon(),
            or None if points are invalid
        """
        if len(points) < 3:
            self.logger.debug("Not enough points for polygon")
            return None

        if points[0] != points[-1]:
            points = points + [points[0]]

        return ", ".join(f"[{p[0]:.3f}, {p[1]:.3f}]" for p in points)

    def generate_buffered_polygon(
        self, points: List[List[float]], width: float
    ) -> Optional[str]:
        """
        Generate buffered polygon for linear features.

        Args:
            points: List of [x, y] coordinates forming the line
            width: Width of the buffer in model units

        Returns:
            String of points formatted for OpenSCAD polygon(),
            or None if points are invalid
        """
        if len(points) < 2:
            self.logger.debug("Not enough points for buffered polygon")
            return None

        left_side = []
        right_side = []

        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            length = sqrt(dx * dx + dy * dy)

            if length < 0.001:
                continue

            nx = -dy / length * width / 2
            ny = dx / length * width / 2

            left_side.append([p1[0] + nx, p1[1] + ny])
            right_side.append([p1[0] - nx, p1[1] - ny])

            if i == len(points) - 2:  # Last segment
                left_side.append([p2[0] + nx, p2[1] + ny])
                right_side.append([p2[0] - nx, p2[1] - ny])

        if len(left_side) < 2:
            return None

        polygon_points = left_side + list(reversed(right_side))
        return ", ".join(f"[{p[0]:.3f}, {p[1]:.3f}]" for p in polygon_points)

    def approximate_polygon_area_m2(self, coords: List[Tuple[float, float]]) -> float:
        """
        Approximate the area of a lat/lon polygon in square meters.

        Uses a simple projection around the center point of the polygon.

        Args:
            coords: List of (longitude, latitude) coordinates

        Returns:
            Approximate area in square meters

        Raises:
            ValueError: If polygon has fewer than 3 points
        """
        if len(coords) < 3:
            raise ValueError("Polygon must have at least 3 points")

        # Calculate center for projection
        lons, lats = zip(*coords)
        lon_center = sum(lons) / len(lons)
        lat_center = sum(lats) / len(lats)

        # Convert each coordinate to x, y relative to center
        xy_points = []
        for lon, lat in coords:
            x = radians(lon - lon_center) * self.EARTH_RADIUS * cos(radians(lat_center))
            y = radians(lat - lat_center) * self.EARTH_RADIUS
            xy_points.append((x, y))

        # Calculate area using shoelace formula
        area = 0.0
        n = len(xy_points)
        for i in range(n):
            j = (i + 1) % n
            area += xy_points[i][0] * xy_points[j][1]
            area -= xy_points[j][0] * xy_points[i][1]

        return abs(area) / 2.0

    def _calculate_bounding_box(self, coords: List[Tuple[float, float]]) -> BoundingBox:
        """
        Calculate the bounding box for a set of coordinates.

        Args:
            coords: List of (longitude, latitude) tuples

        Returns:
            BoundingBox object

        Raises:
            ValueError: If coordinates list is empty
        """
        if not coords:
            raise ValueError("Cannot calculate bounding box of empty coordinate set")

        lons, lats = zip(*coords)
        return BoundingBox(
            min_lon=min(lons), max_lon=max(lons), min_lat=min(lats), max_lat=max(lats)
        )
