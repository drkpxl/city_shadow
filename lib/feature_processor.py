"""
GeoJSON feature processing for Shadow City Generator.

This module handles the processing and enhancement of GeoJSON features,
including coordinate transformation, feature filtering, and categorization
of different urban elements (buildings, roads, water features, etc.).
"""

from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass

from .geometry import GeometryUtils
from .style_manager import StyleManager
from .logging_manager import LoggingManager


@dataclass
class ProcessedFeatures:
    """Container for processed GeoJSON features by category."""

    water: List[Dict[str, Any]]
    roads: List[Dict[str, Any]]
    railways: List[Dict[str, Any]]
    buildings: List[Dict[str, Any]]

    def __init__(self):
        """Initialize empty feature lists."""
        self.water = []
        self.roads = []
        self.railways = []
        self.buildings = []

    def get_counts(self) -> Dict[str, int]:
        """Return count of features by category."""
        return {
            "water": len(self.water),
            "roads": len(self.roads),
            "railways": len(self.railways),
            "buildings": len(self.buildings),
        }


class FeatureProcessor:
    """
    Processes and enhances GeoJSON features for 3D model generation.

    This class handles:
    - Feature extraction and categorization
    - Coordinate transformation
    - Feature filtering based on size/type
    - Building height calculations
    """

    def __init__(self, style_manager: StyleManager, debug: bool = False):
        """
        Initialize the feature processor.

        Args:
            style_manager: StyleManager instance for processing configuration
            debug: Enable debug logging
        """
        self.style_manager = style_manager
        self.geometry = GeometryUtils()
        self.logger = LoggingManager(debug=debug, module_name="feature_processor")

    def process_features(
        self, geojson_data: Dict[str, Any], size: float
    ) -> ProcessedFeatures:
        """
        Process and enhance GeoJSON features.

        Args:
            geojson_data: Input GeoJSON data dictionary
            size: Target size in millimeters for the output model

        Returns:
            ProcessedFeatures object containing categorized features

        Raises:
            ValueError: If geojson_data is invalid or empty
        """
        if not geojson_data.get("features"):
            raise ValueError("No features found in GeoJSON data")

        self.logger.debug(f"Processing {len(geojson_data['features'])} features")

        # Create coordinate transformer
        transform = self.geometry.create_coordinate_transformer(
            geojson_data["features"], size
        )

        # Initialize container for processed features
        features = ProcessedFeatures()

        # Process each feature
        for feature in geojson_data["features"]:
            self._process_single_feature(feature, features, transform)

        # Log feature counts
        counts = features.get_counts()
        self.logger.debug("Processed feature counts:")
        for category, count in counts.items():
            self.logger.debug(f"  {category}: {count}")

        # Apply building merging/clustering
        features.buildings = self.style_manager.merge_nearby_buildings(
            features.buildings
        )
        self.logger.debug(f"After merging: {len(features.buildings)} building clusters")

        return features

    def _process_single_feature(
        self, feature: Dict[str, Any], features: ProcessedFeatures, transform: callable
    ) -> None:
        """
        Process a single GeoJSON feature.

        Args:
            feature: GeoJSON feature dictionary
            features: ProcessedFeatures container to add processed feature
            transform: Coordinate transformation function
        """
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)

        if not coords:
            self.logger.debug("Skipping feature with no coordinates")
            return

        if "building" in props:
            self._process_building(coords, props, features, transform)
        elif "highway" in props:
            self._process_road(coords, props, features, transform)
        elif (
            props.get("amenity") == "parking"
            or props.get("parking") == "surface"
            or props.get("service") == "parking_aisle"
        ):
            self._process_parking(coords, props, features, transform)
        elif "railway" in props:
            self._process_railway(coords, props, features, transform)
        elif "natural" in props and props["natural"] == "water":
            self._process_water(coords, props, features, transform)

    def _process_building(
        self,
        coords: List[Tuple[float, float]],
        props: Dict[str, Any],
        features: ProcessedFeatures,
        transform: callable,
    ) -> None:
        """Process a building feature."""
        # Check building area
        area_m2 = self.geometry.approximate_polygon_area_m2(coords)
        min_area = self.style_manager.style.get("min_building_area", 600.0)

        if area_m2 < min_area:
            self.logger.debug(f"Skipping small building with area {area_m2:.1f}m²")
            return

        # Transform coordinates and store the building
        transformed = [transform(lon, lat) for lon, lat in coords]
        height = self.style_manager.scale_building_height(props)
        features.buildings.append({"coords": transformed, "height": height})

        self.logger.debug(
            f"Added building with height {height:.1f}mm and area {area_m2:.1f}m²"
        )

    def _process_road(
        self,
        coords: List[Tuple[float, float]],
        props: Dict[str, Any],
        features: ProcessedFeatures,
        transform: callable,
    ) -> None:
        """Process a road feature."""
        # Skip if it's a tunnel
        if props.get("tunnel") in ["yes", "true", "1"]:
            self.logger.debug(f"Skipping tunnel road of type '{props.get('highway')}'")
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) >= 2:  # Ensure we have enough points for a road
            road_type = props.get("highway", "unknown")
            features.roads.append(
                {"coords": transformed, "type": road_type, "is_parking": False}
            )
            self.logger.debug(
                f"Added road of type '{road_type}' with {len(transformed)} points"
            )

    def _process_parking(
        self,
        coords: List[Tuple[float, float]],
        props: Dict[str, Any],
        features: ProcessedFeatures,
        transform: callable,
    ) -> None:
        """Process a parking area feature."""
        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) >= 3:  # Ensure we have enough points for a polygon
            features.roads.append(
                {"coords": transformed, "type": "parking", "is_parking": True}
            )
            self.logger.debug(f"Added parking area with {len(transformed)} points")

    def _process_railway(
        self,
        coords: List[Tuple[float, float]],
        props: Dict[str, Any],
        features: ProcessedFeatures,
        transform: callable,
    ) -> None:
        """Process a railway feature."""
        # Skip if it's a tunnel
        if props.get("tunnel") in ["yes", "true", "1"]:
            self.logger.debug(
                f"Skipping tunnel railway of type '{props.get('railway')}'"
            )
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) >= 2:  # Ensure we have enough points
            features.railways.append(
                {"coords": transformed, "type": props.get("railway", "unknown")}
            )
            self.logger.debug(
                f"Added railway of type '{props.get('railway', 'unknown')}' "
                f"with {len(transformed)} points"
            )

    def _process_water(
        self,
        coords: List[Tuple[float, float]],
        props: Dict[str, Any],
        features: ProcessedFeatures,
        transform: callable,
    ) -> None:
        """Process a water feature."""
        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) >= 3:  # Ensure we have enough points for a polygon
            features.water.append(
                {"coords": transformed, "type": props.get("water", "unknown")}
            )
            self.logger.debug(
                f"Added water feature of type '{props.get('water', 'unknown')}' "
                f"with {len(transformed)} points"
            )
