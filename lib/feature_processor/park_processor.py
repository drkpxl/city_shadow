# lib/feature_processor/park_processor.py
from typing import Dict, Any, Optional
from shapely.geometry import Polygon
from .base_processor import BaseProcessor
from ..config import Config

class ParkProcessor(BaseProcessor):
    """
    Processes OSM features for green spaces and parks.
    Uses centralized configuration for consistent handling of leisure and landuse features.
    """

    def process_park(self, feature: Dict[str, Any], features: Dict[str, list], transform) -> None:
        """
        Process a park or green space feature, applying appropriate settings and transformations.
        
        Args:
            feature: GeoJSON feature to process
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
        """
        props = feature.get("properties", {})
        geometry_type = feature["geometry"]["type"]

        # Skip if not a recognized green space type
        if not self._is_valid_green_space(props):
            return

        # Extract and validate coordinates
        coords = self.geometry.extract_coordinates(feature)
        if not coords or len(coords) < 3:
            return

        # Check minimum area requirement
        area_m2 = self.geometry.approximate_polygon_area_m2(coords)
        min_area = Config.DEFAULT_LAYER_SPECS["parks"]["min_area"]
        
        if area_m2 < min_area:
            self._log_debug(f"Skipping small green space with area {area_m2:.1f}m²")
            return

        # Process valid polygon geometries
        if geometry_type in ["Polygon", "MultiPolygon"]:
            self._process_green_space_polygon(coords, features, transform, props)

    def _process_green_space_polygon(
        self, 
        coords: list, 
        features: Dict[str, list], 
        transform,
        props: Dict[str, Any]
    ) -> None:
        """
        Process a valid green space polygon with appropriate styling.
        
        Args:
            coords: List of coordinate pairs
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
            props: Feature properties
        """
        transformed = [transform(lon, lat) for lon, lat in coords]
        
        # Get park specifications from config
        park_specs = self.style_manager.get_default_layer_specs()["parks"]
        
        feature_data = {
            "coords": transformed,
            "type": self._determine_green_space_type(props),
            "height": park_specs["thickness"],
            "offset": park_specs["start_offset"]
        }
        
        features["parks"].append(feature_data)
        
        self._log_debug(
            f"Added {feature_data['type']} green space with {len(transformed)} points"
        )

    def _is_valid_green_space(self, props: Dict[str, Any]) -> bool:
        """
        Check if properties indicate a valid green space using Config settings.
        
        Args:
            props: Feature properties
            
        Returns:
            bool: True if feature is a valid green space
        """
        return Config.is_green_space(props)

    def _determine_green_space_type(self, props: Dict[str, Any]) -> str:
        """
        Determine the specific type of green space for styling purposes.
        
        Args:
            props: Feature properties
            
        Returns:
            str: Specific type of green space
        """
        # Check landuse first
        landuse = props.get("landuse", "").lower()
        if landuse in Config.GREEN_LANDUSE:
            return landuse

        # Check leisure second
        leisure = props.get("leisure", "").lower()
        if leisure in Config.GREEN_LEISURE:
            return leisure

        # Default fallback
        return "park"

    def _get_height_for_type(self, green_space_type: str) -> float:
        """
        Get appropriate height for specific type of green space.
        
        Args:
            green_space_type: Type of green space
            
        Returns:
            float: Height in mm for the green space
        """
        park_specs = self.style_manager.get_default_layer_specs()["parks"]
        
        # Could extend this with type-specific heights in the future
        return park_specs["thickness"]

    def _should_add_features(self, green_space_type: str) -> bool:
        """
        Determine if additional features should be added based on type.
        
        Args:
            green_space_type: Type of green space
            
        Returns:
            bool: True if additional features should be added
        """
        # Could be extended to add trees, benches, etc. based on type
        return green_space_type in {"park", "garden", "recreation_ground"}

    def _log_debug(self, message: str) -> None:
        """
        Wrapper for debug logging.
        
        Args:
            message: Debug message to log
        """
        if self.debug:
            print(message)