# lib/feature_processor/industrial_processor.py
from shapely.geometry import Polygon
from .base_processor import BaseProcessor

class IndustrialProcessor(BaseProcessor):
    def process_industrial_building(self, feature, features, transform):
        """Process an industrial building with specific handling."""
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        area_m2 = self.geometry.approximate_polygon_area_m2(coords)
        min_area = self.style_manager.style.get("min_building_area", 600.0)

        if area_m2 < min_area:
            if self.debug:
                print(f"Skipping small industrial building with area {area_m2:.1f}m²")
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        height = self.style_manager.scale_building_height(props)

        # Ensure a minimum building height
        min_height = self.style_manager.get_default_layer_specs()["buildings"]["min_height"]
        height = max(height, min_height)

        features["industrial"].append(
            {"coords": transformed, "height": height, "is_industrial": True}
        )
        if self.debug:
            print(f"Added industrial building, height {height:.1f}mm, area {area_m2:.1f}m²")

    def process_industrial_area(self, feature, features, transform):
        """Process industrial landuse areas as potential buildings."""
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        # Transform coordinates
        transformed = [transform(lon, lat) for lon, lat in coords]

        # Use a minimum height for industrial areas
        min_height = self.style_manager.get_default_layer_specs()["buildings"]["min_height"]

        # If block-combine style, these will merge with others
        if self.style_manager.style["artistic_style"] == "block-combine":
            features["industrial"].append(
                {"coords": transformed, "height": min_height, "is_industrial": True}
            )
            if self.debug:
                print(f"Added industrial area with height {min_height}mm")
