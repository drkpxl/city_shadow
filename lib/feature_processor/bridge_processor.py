# lib/feature_processor/bridge_processor.py
from typing import Dict, Any, List, Optional, Tuple
from shapely.geometry import LineString, Point
from .base_processor import BaseProcessor
from ..config import Config
from ..geometry import GeometryUtils
from typing import Dict, Any, List, Optional, Tuple
from shapely.geometry import LineString, Point
from .base_processor import BaseProcessor
from ..config import Config
from ..geometry import GeometryUtils

class BridgeProcessor(BaseProcessor):
    """
    Unified processor for both road and railway bridges.
    
    This class handles the shared processing logic for all bridge types,
    providing consistent treatment for various bridge structures.
    """
    
    def __init__(self, geometry_utils, style_manager, debug=False):
        super().__init__(geometry_utils, style_manager, debug)
        self.geometry = geometry_utils
    
    def process_bridge(
        self, 
        feature: Dict[str, Any], 
        features: Dict[str, list], 
        transform,
        bridge_type: str = "road"
    ) -> None:
        """
        Process a bridge feature with type-specific settings.
        
        Args:
            feature: GeoJSON feature to process
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
            bridge_type: Type of bridge ("road" or "rail")
        """
        props = feature.get("properties", {})
        
        # Skip if not a bridge
        if not self._is_bridge(props):
            return
            
        coords = self.geometry.extract_coordinates(feature)
        if not coords or len(coords) < 2:
            return
            
        transformed = [transform(lon, lat) for lon, lat in coords]
        
        # Calculate bridge area and minimum size
        bridge_specs = self.style_manager.get_default_layer_specs()['bridges']
        bridge_area = self._calculate_bridge_area(transformed, bridge_type)
        min_bridge_size = bridge_specs['min_size']
        
        # Only process if it meets the minimum size requirement
        if bridge_area >= min_bridge_size:
            features["bridges"].append({
                "coords": transformed,
                "type": self._get_bridge_feature_type(props, bridge_type),
                "bridge_type": bridge_type,
                "height": bridge_specs['height'],
                "thickness": bridge_specs['thickness'],
                "support_width": bridge_specs['support_width'][bridge_type]
            })
            
            self._log_debug(
                f"Added {bridge_type} bridge with area {bridge_area:.1f}m² " +
                f"and feature type '{self._get_bridge_feature_type(props, bridge_type)}'"
            )
    
    def _is_bridge(self, props: Dict[str, Any]) -> bool:
        """
        Check if the feature is marked as a bridge.
        
        Args:
            props: Feature properties
            
        Returns:
            bool: True if the feature is a bridge
        """
        return props.get(Config.FEATURE_TYPES['BRIDGE']) in ["yes", "true", "1"]
    
    def _get_bridge_feature_type(self, props: Dict[str, Any], bridge_type: str) -> str:
        """
        Get the specific feature type for the bridge.
        
        Args:
            props: Feature properties
            bridge_type: Type of bridge ("road" or "rail")
            
        Returns:
            str: Specific feature type
        """
        if bridge_type == "road":
            return props.get(Config.FEATURE_TYPES['HIGHWAY'], "bridge")
        elif bridge_type == "rail":
            return props.get(Config.FEATURE_TYPES['RAILWAY'], "rail_bridge")
        else:
            return "bridge"
    
    def _calculate_bridge_area(self, coords: List[List[float]], bridge_type: str) -> float:
        """
        Calculate the approximate area of a bridge based on its coordinates.
        
        Args:
            coords: List of coordinate pairs
            bridge_type: Type of bridge ("road" or "rail")
            
        Returns:
            float: Approximate area in square meters
        """
        if len(coords) < 2:
            return 0.0
            
        # Calculate the length of the bridge (distance between first and last point)
        line = LineString(coords)
        length = line.length
        
        # Calculate the width using bridge-type-specific width
        bridge_specs = self.style_manager.get_default_layer_specs()['bridges']
        width = bridge_specs['assumed_width'][bridge_type]
        
        # Approximate area as length * width
        return length * width
    
    def _log_debug(self, message: str) -> None:
        """Wrapper for debug logging."""
        if self.debug:
            print(message)