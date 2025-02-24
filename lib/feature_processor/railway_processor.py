# lib/feature_processor/railway_processor.py
from typing import Dict, Any, Optional
from .linear_processor import LinearFeatureProcessor
from ..config import Config
from .bridge_processor import BridgeProcessor

class RailwayProcessor(LinearFeatureProcessor):
    """
    Handles railway features using centralized configuration.
    Inherits core linear processing functionality from LinearFeatureProcessor.
    """
    
    FEATURE_TYPE = Config.FEATURE_TYPES['RAILWAY']
    feature_category = 'railways'

    def __init__(self, geometry_utils, style_manager, debug=False):
        super().__init__(geometry_utils, style_manager, debug)
        self.bridge_processor = BridgeProcessor(geometry_utils, style_manager, debug)

    def process_railway(self, feature: Dict[str, Any], features: Dict[str, list], transform) -> None:
        """
        Process railway feature using base class logic with railway-specific settings.
        
        Args:
            feature: GeoJSON feature to process
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
        """
        props = feature.get("properties", {})
        
        # Get railway specifications from config
        railway_specs = self.style_manager.get_default_layer_specs()['railways']
        
        # Process the feature as a railway
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

        # Create railway feature with width
        feature_data = {
            "coords": transformed,
            "type": props.get(self.FEATURE_TYPE, "rail"),
            "width": railway_specs['width']
        }

        # Add service tag if present
        additional_tags = ["service", "bridge"]
        for tag in additional_tags:
            if tag in props:
                feature_data[tag] = props[tag]

        # Add to features collection
        features[self.feature_category].append(feature_data)
        
        self._log_debug(
            f"Added {self.FEATURE_TYPE} '{feature_data['type']}' with width {feature_data['width']:.1f}mm"
        )
        
        # Special bridge handling
        if props.get(Config.FEATURE_TYPES['BRIDGE']):
            # Process as a rail bridge
            self.bridge_processor.process_bridge(
                feature, 
                features, 
                transform, 
                bridge_type="rail"
            )