# lib/feature_processor/bridge_processor.py
from typing import Dict, Any, List, Optional, Tuple
from shapely.geometry import LineString, Point, MultiLineString, MultiPolygon, Polygon
from shapely.ops import linemerge, unary_union
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
        
        # Get bridge settings from Config
        bridge_specs = self.style_manager.get_default_layer_specs()['bridges']
        
        # Calculate bridge area and minimum size
        bridge_area = self._calculate_bridge_area(transformed, bridge_type)
        min_bridge_size = bridge_specs['min_size']
        
        # Only process if it meets the minimum size requirement
        if bridge_area >= min_bridge_size:
            # Determine if bridge crosses water
            crosses_water = self._check_water_crossing(transformed, features.get("water", []))
            
            # Store bridge data
            features["bridges"].append({
                "coords": transformed,
                "type": self._get_bridge_feature_type(props, bridge_type),
                "bridge_type": bridge_type,
                "height": bridge_specs['height'],
                "thickness": bridge_specs['thickness'],
                "support_width": self._get_support_width(bridge_specs, bridge_type),
                "crosses_water": crosses_water,
                # Include railing flag for railway bridges
                "needs_railings": bridge_type == "rail"
            })
            
            self._log_debug(
                f"Added {bridge_type} bridge with area {bridge_area:.1f}m² " +
                f"and feature type '{self._get_bridge_feature_type(props, bridge_type)}'" +
                (", crossing water" if crosses_water else "")
            )
    
    def _is_bridge(self, props: Dict[str, Any]) -> bool:
        """
        Check if the feature is marked as a bridge.
        
        Args:
            props: Feature properties
            
        Returns:
            bool: True if the feature is a bridge
        """
        bridge_value = props.get(Config.FEATURE_TYPES['BRIDGE'])
        return bridge_value in ["yes", "true", "1", True]
    
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
        
        # Calculate the width using bridge-type-specific width from Config
        bridge_specs = self.style_manager.get_default_layer_specs()['bridges']
        width = bridge_specs['assumed_width'][bridge_type]
        
        # Approximate area as length * width
        return length * width
    
    def _get_support_width(self, bridge_specs: Dict[str, Any], bridge_type: str) -> float:
        """
        Get the appropriate support width for the bridge type from Config.
        
        Args:
            bridge_specs: Bridge specifications from Config
            bridge_type: Type of bridge ("road" or "rail")
            
        Returns:
            float: Support width in millimeters
        """
        # Handle support_width being either a dict or float
        if isinstance(bridge_specs['support_width'], dict):
            return bridge_specs['support_width'].get(bridge_type, 2.0)
        else:
            # Fall back to using support_width directly if it's not a dict
            return float(bridge_specs['support_width'])
    
    def _check_water_crossing(self, coords: List[List[float]], water_features: List[Dict[str, Any]]) -> bool:
        """
        Check if bridge crosses any water features.
        
        Args:
            coords: Bridge coordinates
            water_features: List of water features
            
        Returns:
            bool: True if bridge crosses water
        """
        if not water_features:
            return False
            
        try:
            bridge_line = LineString(coords)
            
            for water in water_features:
                water_coords = water.get("coords", [])
                if len(water_coords) >= 3:
                    water_poly = Polygon(water_coords)
                    if bridge_line.intersects(water_poly):
                        return True
            
            return False
        except Exception as e:
            self._log_debug(f"Error checking water crossing: {str(e)}")
            return False
    
    def detect_implicit_bridges(self, features: Dict[str, list]) -> None:
        """
        Detect bridges that aren't explicitly tagged by finding road/rail crossings over water.
        
        Args:
            features: Dictionary of feature collections
        """
        # Only process if we have both roads/rails and water
        if not features.get("water") or (not features.get("roads") and not features.get("railways")):
            return
        
        water_union = self._create_water_union(features["water"])
        if not water_union:
            return
        
        # Process road intersections with water
        self._detect_implicit_bridges_by_type(features, water_union, "roads", "road")
        
        # Process railway intersections with water
        self._detect_implicit_bridges_by_type(features, water_union, "railways", "rail")
    
    def _detect_implicit_bridges_by_type(
        self, 
        features: Dict[str, list], 
        water_union: Polygon, 
        feature_type: str, 
        bridge_type: str
    ) -> None:
        """
        Detect implicit bridges for a specific feature type.
        
        Args:
            features: Dictionary of feature collections
            water_union: Union of all water polygons
            feature_type: Type of feature ("roads" or "railways")
            bridge_type: Type of bridge ("road" or "rail")
        """
        bridge_specs = self.style_manager.get_default_layer_specs()['bridges']
        added_count = 0
        
        for feature in features.get(feature_type, []):
            # Skip if already processed as a bridge
            if feature.get("bridge"):
                continue
                
            coords = feature.get("coords", [])
            if len(coords) < 2:
                continue
                
            line = LineString(coords)
            if line.intersects(water_union):
                # Get intersection points
                intersection = line.intersection(water_union.boundary)
                
                # Handle different intersection types
                if intersection.geom_type == 'MultiPoint' and len(intersection.geoms) >= 2:
                    # Find the segment of the line that crosses water
                    bridge_segment = self._extract_bridge_segment(line, intersection, water_union)
                    
                    if bridge_segment and len(bridge_segment.coords) >= 2:
                        # Add as implicit bridge
                        features["bridges"].append({
                            "coords": list(bridge_segment.coords),
                            "type": feature.get("type", "unknown"),
                            "bridge_type": bridge_type,
                            "height": bridge_specs['height'],
                            "thickness": bridge_specs['thickness'],
                            "support_width": self._get_support_width(bridge_specs, bridge_type),
                            "crosses_water": True,
                            "is_implicit": True,
                            "needs_railings": bridge_type == "rail"
                        })
                        added_count += 1
        
        if added_count > 0:
            self._log_debug(f"Added {added_count} implicit {bridge_type} bridges over water")
    
    def _create_water_union(self, water_features: List[Dict[str, Any]]) -> Optional[Polygon]:
        """
        Create a union of all water polygons.
        
        Args:
            water_features: List of water features
            
        Returns:
            Optional[Polygon]: Union of water polygons, or None if no valid water
        """
        water_polys = []
        
        for water in water_features:
            coords = water.get("coords", [])
            if len(coords) >= 3:
                try:
                    poly = Polygon(coords)
                    if poly.is_valid and not poly.is_empty:
                        water_polys.append(poly)
                except Exception:
                    continue
        
        if not water_polys:
            return None
            
        try:
            return unary_union(water_polys)
        except Exception as e:
            self._log_debug(f"Error creating water union: {str(e)}")
            return None
    
    def _extract_bridge_segment(self, line: LineString, intersection, water_union: Polygon) -> Optional[LineString]:
        """
        Extract the segment of a line that crosses water.
        
        Args:
            line: The full line
            intersection: Intersection points with water boundary
            water_union: Union of water polygons
            
        Returns:
            Optional[LineString]: Bridge segment, or None if no valid segment
        """
        try:
            # Handle different types of intersections
            if intersection.geom_type == 'Point':
                # Single point intersection - not a crossing
                return None
            elif intersection.geom_type == 'MultiPoint':
                # Find closest pair of points that define a crossing
                points = list(intersection.geoms)
                if len(points) < 2:
                    return None
                    
                # Split the line at intersection points
                distances = [line.project(p) for p in points]
                segments = []
                
                # Sort distances
                sorted_points = sorted(zip(distances, points), key=lambda x: x[0])
                
                # Check consecutive pairs for valid crossings
                for i in range(len(sorted_points) - 1):
                    d1, p1 = sorted_points[i]
                    d2, p2 = sorted_points[i + 1]
                    
                    # Create segment between these points
                    mid_point = LineString([p1, p2]).interpolate(0.5, normalized=True)
                    
                    # If the midpoint is inside the water, this is a valid crossing
                    if water_union.contains(mid_point):
                        segment = LineString([p1, p2])
                        segments.append(segment)
                
                # If we found at least one segment, return the first one
                if segments:
                    return segments[0]
            
            return None
        except Exception as e:
            self._log_debug(f"Error extracting bridge segment: {str(e)}")
            return None