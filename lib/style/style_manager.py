# lib/style/style_manager.py
from .building_merger import BuildingMerger
from .height_manager import HeightManager
from .artistic_effects import ArtisticEffects


class StyleManager:
    def __init__(self, style_settings=None):
        # Initialize default style settings
        self.style = {
            "merge_distance": 2.0,
            "cluster_size": 3.0,
            "height_variance": 0.2,
            "detail_level": 1.0,
            "artistic_style": "modern",
            "min_building_area": 600.0,
        }

        # Override defaults with provided settings
        if style_settings:
            self.style.update(style_settings)

        # Initialize components
        self.building_merger = BuildingMerger(self)
        self.height_manager = HeightManager(self)
        self.artistic_effects = ArtisticEffects(self)
        self.current_features = {}

    def get_default_layer_specs(self):
        """Get default layer specifications."""
        return {
            "water": {"depth": 3},
            "roads": {"depth": 0.4, "width": 2.0},
            "railways": {"depth": 0.6, "width": 1.5},
            "parks": {
                "start_offset": 0.2,  # top of base + 0.2
                "thickness": 0.4
            },
            "buildings": {"min_height": 2, "max_height": 6},
            "base": {"height": 10},
        }

    def scale_building_height(self, properties):
        """Scale building height using HeightManager."""
        return self.height_manager.scale_height(properties)

    def merge_nearby_buildings(self, buildings, barrier_union=None):
        """Merge buildings using BuildingMerger."""
        return self.building_merger.merge_buildings(buildings, barrier_union)

    def set_current_features(self, features):
        """Store current features."""
        self.current_features = features
