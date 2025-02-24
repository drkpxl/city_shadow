# lib/style/style_manager.py
from typing import Dict, Any, Optional
from ..config import Config
from .building_merger import BuildingMerger
from .height_manager import HeightManager
from .artistic_effects import ArtisticEffects
from .block_combiner import BlockCombiner

class StyleManager:
    """
    Manages style settings and coordinates style-related components for the city model.
    Uses centralized configuration for consistent styling across the application.
    """
    
    def __init__(self, style_settings: Optional[Dict[str, Any]] = None):
        """
        Initialize style manager with optional custom settings.
        
        Args:
            style_settings: Optional dictionary of style settings to override defaults
        """
        # Initialize with default style settings
        self.style = dict(Config.DEFAULT_STYLE)
        
        # Override defaults with provided settings
        if style_settings:
            self._validate_and_update_style(style_settings)
            
        # Initialize style components
        self.building_merger = BuildingMerger(self)
        self.height_manager = HeightManager(self)
        self.artistic_effects = ArtisticEffects(self)
        self.block_combiner = BlockCombiner(self)
        self.current_features = {}

    def _validate_and_update_style(self, settings: Dict[str, Any]) -> None:
        """
        Validate and update style settings.
        
        Args:
            settings: Dictionary of style settings to validate and apply
        """
        for key, value in settings.items():
            if key in Config.DEFAULT_STYLE:
                if key == 'artistic_style' and value not in Config.ARTISTIC_STYLES:
                    raise ValueError(f"Invalid artistic style: {value}. Must be one of {Config.ARTISTIC_STYLES}")
                self.style[key] = value

    def get_default_layer_specs(self) -> Dict[str, Any]:
        """
        Get default layer specifications from config.
        
        Returns:
            Dictionary containing layer specifications
        """
        return dict(Config.DEFAULT_LAYER_SPECS)

    def scale_building_height(self, properties: Dict[str, Any]) -> float:
        """
        Scale building height using HeightManager.
        
        Args:
            properties: Dictionary of building properties
            
        Returns:
            Scaled height value
        """
        return self.height_manager.scale_height(properties)

    def merge_nearby_buildings(self, buildings: list, barrier_union=None) -> list:
        """
        Choose and execute building merging strategy based on style.
        
        Args:
            buildings: List of building features
            barrier_union: Optional union of barrier geometries
            
        Returns:
            List of processed building features
        """
        if self.style["artistic_style"] == "block-combine":
            return self.block_combiner.combine_buildings_by_block(self.current_features)
        else:
            return self.building_merger.merge_buildings(buildings, barrier_union)

    def set_current_features(self, features: Dict[str, list]) -> None:
        """
        Store current features for reference by style components.
        
        Args:
            features: Dictionary of feature collections by type
        """
        self.current_features = features

    def get_industrial_height_multiplier(self, building_type: str) -> float:
        """
        Get height multiplier for industrial building type.
        
        Args:
            building_type: Type of industrial building
            
        Returns:
            Height multiplier value
        """
        return Config.get_industrial_height_multiplier(building_type)

    def get_road_width(self, road_type: str) -> float:
        """
        Get width multiplier for road type.
        
        Args:
            road_type: Type of road
            
        Returns:
            Road width multiplier
        """
        return Config.get_road_width(road_type)

    def get_roof_style_params(self, style_name: str) -> Dict[str, Any]:
        """
        Get parameters for a specific roof style.
        
        Args:
            style_name: Name of the roof style
            
        Returns:
            Dictionary of roof style parameters
        """
        return Config.ROOF_STYLES.get(style_name, {})

    def get_processing_settings(self) -> Dict[str, Any]:
        """
        Get current processing settings based on style.
        
        Returns:
            Dictionary of processing settings
        """
        settings = dict(Config.PROCESSING_SETTINGS)
        # Adjust settings based on current style
        if self.style["artistic_style"] == "block-combine":
            settings["area_threshold"] = max(
                settings["area_threshold"],
                self.style.get("min_building_area", 600.0)
            )
        return settings