# lib/feature_processor/railway_processor.py
from typing import Dict, Any, Optional
from .linear_processor import LinearFeatureProcessor
from ..config import Config

class RailwayProcessor(LinearFeatureProcessor):
    """
    Handles railway features using centralized configuration.
    Inherits core linear processing functionality from LinearFeatureProcessor.
    """
    
    FEATURE_TYPE = Config.FEATURE_TYPES['RAILWAY']
    feature_category = 'railways'

    def process_railway(self, feature: Dict[str, Any], features: Dict[str, list], transform) -> None:
        """
        Process railway feature using base class logic with railway-specific settings.
        
        Args:
            feature: GeoJSON feature to process
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
        """
        # Get railway specifications from config
        railway_specs = self.style_manager.get_default_layer_specs()['railways']
        
        # Process using base class with railway width
        self._process_linear_feature(
            feature,
            features,
            transform,
            width_override=railway_specs['width'],
            additional_tags=["service"]  # Preserve service type
        )
        
    def _process_linear_feature(
        self, 
        feature: Dict[str, Any], 
        features: Dict[str, list],
        transform,
        width_override: Optional[float] = None,
        additional_tags: Optional[list] = None
    ) -> None:
        """
        Enhanced linear feature processing with railway-specific handling.
        
        Args:
            feature: GeoJSON feature to process
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
            width_override: Optional specific width to use
            additional_tags: Optional additional properties to preserve
        """
        props = feature.get("properties", {})
        
        # Skip if tunnel
        if self._is_tunnel(props):
            self._log_debug(f"Skipping tunnel {self.FEATURE_TYPE}: {props.get(self.FEATURE_TYPE)}")
            return
            
        coords = self.geometry.extract_coordinates(feature)
        if not coords or len(coords) < 2:
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        
        feature_data = {
            "coords": transformed,
            "type": props.get(self.FEATURE_TYPE, "rail"),
            "width": width_override or self.style_manager.get_default_layer_specs()['railways']['width']
        }

        # Add additional properties if specified
        if additional_tags:
            for tag in additional_tags:
                if tag in props:
                    feature_data[tag] = props[tag]

        features[self.feature_category].append(feature_data)
        
        self._log_debug(
            f"Added {self.FEATURE_TYPE} '{feature_data['type']}' with width {feature_data['width']:.1f}mm"
        )

    def _log_debug(self, message: str) -> None:
        """Wrapper for debug logging."""
        if self.debug:
            print(message)