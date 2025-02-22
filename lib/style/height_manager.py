# lib/style/height_manager.py
from math import log10


class HeightManager:
    def __init__(self, style_manager):
        self.style_manager = style_manager

    def scale_height(self, properties):
        """Scale building height based on properties."""
        height_m = self._extract_height(properties)
        return self._scale_to_range(height_m)

    def _extract_height(self, properties):
        """Extract height from building properties."""
        default_height = 5.0

        if "height" in properties:
            try:
                return float(properties["height"].split()[0])
            except (ValueError, IndexError):
                pass
        elif "building:levels" in properties:
            try:
                levels = float(properties["building:levels"])
                return levels * 3  # assume 3m per level
            except ValueError:
                pass

        return default_height

    def _scale_to_range(self, height_m):
        """Scale height to target range using logarithmic scaling."""
        layer_specs = self.style_manager.get_default_layer_specs()
        min_height = layer_specs["buildings"]["min_height"]
        max_height = layer_specs["buildings"]["max_height"]

        # Log scaling from 1..100 meters -> min_height..max_height in mm
        log_min = log10(1.0)
        log_max = log10(101.0)
        log_height = log10(height_m + 1.0)  # +1 to avoid log(0)
        scaled = (log_height - log_min) / (log_max - log_min)
        final_height = min_height + scaled * (max_height - min_height)
        return round(final_height, 2)
