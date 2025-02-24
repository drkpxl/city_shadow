# lib/feature_processor/road_processor.py
from typing import Dict, Any, List, Optional
from shapely.geometry import LineString, Polygon
from .linear_processor import LinearFeatureProcessor
from ..config import Config

class RoadProcessor(LinearFeatureProcessor):
    """
    Handles road and bridge features, using centralized configuration.
    Inherits core linear processing functionality from LinearFeatureProcessor.
    """
    
    FEATURE_TYPE = Config.FEATURE_TYPES['HIGHWAY']
    feature_category = 'roads'

    def process_road_or_bridge(self, feature: Dict[str, Any], features: Dict[str, list], transform) -> None:
        """
        Process roads and bridges with specialized handling.
        
        Args:
            feature: GeoJSON feature to process
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
        """
        props = feature.get("properties", {})
        road_type = props.get(self.FEATURE_TYPE)
        
        # Calculate actual road width based on road type
        base_width = self.style_manager.get_default_layer_specs()['roads']['width']
        type_multiplier = Config.get_road_width(road_type)
        actual_width = base_width * type_multiplier
        
        # Process common road features with calculated width
        self._process_linear_feature(
            feature, 
            features, 
            transform,
            width_override=actual_width,
            additional_tags=["bridge"]  # Preserve bridge status
        )
        
        # Special bridge handling if needed
        if props.get(Config.FEATURE_TYPES['BRIDGE']):
            self._process_bridge(feature, features, transform, props)

    def _process_linear_feature(
        self, 
        feature: Dict[str, Any], 
        features: Dict[str, list],
        transform,
        width_override: Optional[float] = None,
        additional_tags: Optional[List[str]] = None
    ) -> None:
        """
        Enhanced linear feature processing with width override capability.
        
        Args:
            feature: GeoJSON feature to process
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
            width_override: Optional specific width to use
            additional_tags: Optional additional properties to preserve
        """
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        # Skip tunnels
        if self._is_tunnel(props):
            self._log_debug(f"Skipping tunnel {self.FEATURE_TYPE}: {props.get(self.FEATURE_TYPE)}")
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) < 2:
            return

        # Create feature dictionary
        feature_data = {
            "coords": transformed,
            "type": props.get(self.FEATURE_TYPE, "unknown"),
            "is_parking": False,
            "width": width_override or self.style_manager.get_default_layer_specs()['roads']['width']
        }

        # Preserve additional properties if specified
        if additional_tags:
            for tag in additional_tags:
                if tag in props:
                    feature_data[tag] = props[tag]

        features[self.feature_category].append(feature_data)
        
        self._log_debug(
            f"Added {self.FEATURE_TYPE} '{feature_data['type']}' with width {feature_data['width']:.1f}mm, {len(transformed)} points"
        )

    def _process_bridge(
        self, 
        feature: Dict[str, Any], 
        features: Dict[str, list], 
        transform,
        props: Dict[str, Any]
    ) -> None:
        """
        Handle bridge-specific processing with bridge settings from config.
        
        Args:
            feature: GeoJSON feature to process
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
            props: Feature properties
        """
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) >= 2:
            # Get bridge settings from config
            bridge_specs = self.style_manager.get_default_layer_specs()['bridges']
            
            features["bridges"].append({
                "coords": transformed,
                "type": props.get(self.FEATURE_TYPE, "bridge"),
                "height": bridge_specs['height'],
                "thickness": bridge_specs['thickness'],
                "support_width": bridge_specs['support_width']
            })
            
            self._log_debug(f"Added bridge of type '{props.get(self.FEATURE_TYPE, 'bridge')}'")

    def process_parking(self, feature: Dict[str, Any], features: Dict[str, list], transform) -> None:
        """
        Process parking areas as special road features.
        
        Args:
            feature: GeoJSON feature to process
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
        """
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) >= 3:  # Minimum points for a polygon
            features[self.feature_category].append({
                "coords": transformed,
                "type": "parking",
                "is_parking": True,
                "width": self.style_manager.get_default_layer_specs()['roads']['width']
            })
            
            self._log_debug(f"Added parking area with {len(transformed)} points")

    def is_parking_area(self, props: Dict[str, Any]) -> bool:
        """
        Check if feature represents a parking area.
        
        Args:
            props: Feature properties
            
        Returns:
            bool: True if the feature is a parking area
        """
        return any(
            props.get(key) in ["parking", "surface", "parking_aisle"]
            for key in [Config.FEATURE_TYPES['AMENITY'], "parking", "service"]
        )

    def _is_tunnel(self, props: Dict[str, Any]) -> bool:
        """
        Check if the feature is a tunnel.
        
        Args:
            props: Feature properties
            
        Returns:
            bool: True if the feature is a tunnel
        """
        return props.get("tunnel") in ["yes", "true", "1"]

    def _log_debug(self, message: str) -> None:
        """
        Wrapper for debug logging.
        
        Args:
            message: Debug message to log
        """
        if self.debug:
            print(message)