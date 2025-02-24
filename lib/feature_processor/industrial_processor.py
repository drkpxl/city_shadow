# lib/feature_processor/industrial_processor.py
from typing import Dict, Any, Optional, List, Tuple
from shapely.geometry import Polygon
from .base_processor import BaseProcessor
from ..config import Config

class IndustrialProcessor(BaseProcessor):
    """
    Handles processing of industrial buildings and areas, using centralized configuration
    for consistent handling of industrial features.
    """
    
    def process_industrial_building(self, feature: Dict[str, Any], features: Dict[str, list], transform) -> None:
        """
        Process an industrial building with specific industrial characteristics.
        
        Args:
            feature: GeoJSON feature to process
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
        """
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return
            
        area_m2 = self.geometry.approximate_polygon_area_m2(coords)
        min_area = Config.INDUSTRIAL_SETTINGS['min_area']
        
        # Skip small buildings unless using block-combine style
        if (self.style_manager.style.get("artistic_style") != "block-combine") and (area_m2 < min_area):
            self._log_debug(f"Skipping small industrial building with area {area_m2:.1f}m²")
            return
            
        transformed = [transform(lon, lat) for lon, lat in coords]
        height = self._calculate_industrial_height(props)
        
        features["industrial"].append({
            "coords": transformed,
            "height": height,
            "is_industrial": True,
            "building_type": props.get("building", "industrial")
        })
        
        self._log_debug(f"Added industrial building, height {height:.1f}mm, area {area_m2:.1f}m²")

    def process_industrial_area(self, feature: Dict[str, Any], features: Dict[str, list], transform) -> None:
        """
        Process industrial landuse areas as specialized building features.
        
        Args:
            feature: GeoJSON feature to process
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
        """
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return
            
        # Verify industrial landuse type
        landuse = props.get("landuse", "").lower()
        if landuse not in Config.INDUSTRIAL_LANDUSE:
            return
            
        transformed = [transform(lon, lat) for lon, lat in coords]
        area_m2 = self.geometry.approximate_polygon_area_m2(coords)
        
        # Skip small areas unless using block-combine style
        if (self.style_manager.style.get("artistic_style") != "block-combine") and (area_m2 < Config.INDUSTRIAL_SETTINGS['min_area']):
            self._log_debug(f"Skipping small industrial area with area {area_m2:.1f}m²")
            return
            
        height = self._calculate_industrial_area_height(landuse)
        
        features["industrial"].append({
            "coords": transformed,
            "height": height,
            "is_industrial": True,
            "landuse_type": landuse
        })
        
        self._log_debug(f"Added industrial area type '{landuse}' with height {height:.1f}mm")

    def should_process_as_industrial(self, properties: Dict[str, Any]) -> bool:
        """
        Check if a feature should be processed as industrial using Config helper.
        
        Args:
            properties: Feature properties to check
            
        Returns:
            bool: True if feature should be processed as industrial
        """
        return Config.is_industrial_feature(properties)

    def _calculate_industrial_height(self, properties: Dict[str, Any]) -> float:
        """
        Calculate height for industrial building using explicit height or type-based multiplier.
        
        Args:
            properties: Building properties
            
        Returns:
            float: Calculated height in mm
        """
        explicit_height = self._get_explicit_height(properties)
        if explicit_height is not None:
            # Apply industrial multiplier to explicit height
            base_height = self.style_manager.scale_building_height({
                "height": str(explicit_height)
            })
            return base_height * 1.5  # 50% bonus for industrial buildings
            
        # Use type-based height calculation
        building_type = properties.get("building", "industrial")
        multiplier = Config.get_industrial_height_multiplier(building_type)
        
        layer_specs = self.style_manager.get_default_layer_specs()
        min_height = layer_specs["buildings"]["min_height"]
        max_height = layer_specs["buildings"]["max_height"]
        
        return min(max_height, min_height * multiplier)

    def _calculate_industrial_area_height(self, landuse_type: str) -> float:
        """
        Calculate height for industrial landuse area.
        
        Args:
            landuse_type: Type of industrial landuse
            
        Returns:
            float: Calculated height in mm
        """
        multiplier = Config.get_industrial_height_multiplier(landuse_type)
        
        layer_specs = self.style_manager.get_default_layer_specs()
        min_height = layer_specs["buildings"]["min_height"]
        max_height = layer_specs["buildings"]["max_height"]
        
        return min(max_height, min_height * multiplier)

    def _get_explicit_height(self, properties: Dict[str, Any]) -> Optional[float]:
        """
        Extract explicit height from properties if available.
        
        Args:
            properties: Feature properties
            
        Returns:
            Optional[float]: Explicit height in meters if available
        """
        if "height" in properties:
            try:
                height_str = properties["height"].split()[0]  # Handle "10 m" format
                return float(height_str)
            except (ValueError, IndexError):
                pass
                
        if "building:levels" in properties:
            try:
                levels = float(properties["building:levels"])
                return levels * Config.DEFAULT_LAYER_SPECS["buildings"]["levels_height"]
            except ValueError:
                pass
                
        return None

    def _log_debug(self, message: str) -> None:
        """
        Wrapper for debug logging.
        
        Args:
            message: Debug message to log
        """
        if self.debug:
            print(message)