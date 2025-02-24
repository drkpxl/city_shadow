# lib/style/height_manager.py
from typing import Dict, Any, Optional
from math import log10
from ..config import Config

class HeightManager:
    """
    Manages height calculations and scaling for buildings.
    Uses centralized configuration for consistent height handling.
    """
    
    def __init__(self, style_manager):
        """
        Initialize height manager with style manager reference.
        
        Args:
            style_manager: StyleManager instance for accessing style settings
        """
        self.style_manager = style_manager

    def scale_height(self, properties: Dict[str, Any]) -> float:
        """
        Scale building height based on properties and current style settings.
        
        Args:
            properties: Building properties including height information
            
        Returns:
            float: Scaled height in millimeters
        """
        height_m = self._extract_height(properties)
        base_height = self._scale_to_range(height_m)
        
        # Apply any style-specific modifiers
        return self._apply_style_modifiers(base_height, properties)

    def _extract_height(self, properties: Dict[str, Any]) -> float:
        """
        Extract height from building properties using various OSM tags.
        
        Args:
            properties: Building properties
            
        Returns:
            float: Extracted height in meters
        """
        # Try explicit height tag first
        if "height" in properties:
            try:
                # Handle formats like "25 m", "25m", "25"
                height_str = properties["height"].split()[0].strip('m')
                return float(height_str)
            except (ValueError, IndexError):
                pass

        # Try building:levels tag
        if "building:levels" in properties:
            try:
                levels = float(properties["building:levels"])
                return levels * Config.DEFAULT_LAYER_SPECS["buildings"]["levels_height"]
            except ValueError:
                pass

        # Try min_height tag
        if "min_height" in properties:
            try:
                min_height_str = properties["min_height"].split()[0].strip('m')
                return float(min_height_str)
            except (ValueError, IndexError):
                pass

        # Use default height based on building type
        building_type = properties.get("building", "").lower()
        if building_type in Config.INDUSTRIAL_BUILDINGS:
            return Config.INDUSTRIAL_SETTINGS["default_height"]
            
        return Config.DEFAULT_LAYER_SPECS["buildings"]["default_height"]

    def _scale_to_range(self, height_m: float) -> float:
        """
        Scale height to target range using logarithmic scaling.
        
        Args:
            height_m: Height in meters
            
        Returns:
            float: Scaled height in millimeters
        """
        specs = Config.DEFAULT_LAYER_SPECS["buildings"]
        min_height = specs["min_height"]
        max_height = specs["max_height"]

        # Log scaling from 1..100 meters -> min_height..max_height mm
        log_min = log10(1.0)
        log_max = log10(101.0)
        log_height = log10(height_m + 1.0)  # +1 to avoid log(0)
        
        # Calculate scaled height
        scale_factor = (log_height - log_min) / (log_max - log_min)
        scaled_height = min_height + scale_factor * (max_height - min_height)
        
        # Ensure height stays within bounds
        return max(min_height, min(scaled_height, max_height))

    def _apply_style_modifiers(self, base_height: float, properties: Dict[str, Any]) -> float:
        """
        Apply style-specific height modifications.
        
        Args:
            base_height: Base calculated height
            properties: Building properties
            
        Returns:
            float: Modified height in millimeters
        """
        style = self.style_manager.style.get("artistic_style")
        
        # Apply style-specific modifiers
        if style == "modern":
            # Modern style: Taller buildings with more variation
            height_variance = self.style_manager.style.get("height_variance", 0.2)
            variance_factor = 1.0 + (height_variance * 0.5)  # Up to 50% taller
            return base_height * variance_factor
            
        elif style == "classic":
            # Classic style: More consistent heights
            return base_height
            
        elif style == "minimal":
            # Minimal style: Slightly reduced heights
            return base_height * 0.8
            
        elif style == "block-combine":
            # Block combine: Heights based on cluster characteristics
            if properties.get("is_cluster", False):
                # Clustered buildings get a slight height bonus
                return base_height * 1.2
            
        return base_height

    def get_height_range(self, building_type: str) -> tuple[float, float]:
        """
        Get valid height range for a building type.
        
        Args:
            building_type: Type of building
            
        Returns:
            tuple[float, float]: Minimum and maximum heights in millimeters
        """
        if building_type in Config.INDUSTRIAL_BUILDINGS:
            specs = Config.BLOCK_TYPES["industrial"]
        else:
            specs = Config.BLOCK_TYPES["residential"]
            
        return specs["min_height"], specs["max_height"]

    def calculate_relative_height(
        self, 
        base_height: float, 
        importance_factor: float = 1.0
    ) -> float:
        """
        Calculate height relative to base height with importance scaling.
        
        Args:
            base_height: Base height to scale from
            importance_factor: Factor to scale height (1.0 = no change)
            
        Returns:
            float: Calculated relative height
        """
        specs = Config.DEFAULT_LAYER_SPECS["buildings"]
        min_height = specs["min_height"]
        max_height = specs["max_height"]
        
        # Scale height by importance while keeping within bounds
        scaled_height = base_height * importance_factor
        return max(min_height, min(scaled_height, max_height))