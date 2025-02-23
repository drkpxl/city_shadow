# lib/feature_processor/building_processor.py
from shapely.geometry import Polygon
from .base_processor import BaseProcessor

class BuildingProcessor(BaseProcessor):
    def process_building(self, feature, features, transform):
        """
        Process a regular building.
        """
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        area_m2 = self.geometry.approximate_polygon_area_m2(coords)
        min_area = self.style_manager.style.get("min_building_area", 600.0)

        # Only skip small buildings if not using block-combine style.
        if (self.style_manager.style.get("artistic_style") != "block-combine") and (area_m2 < min_area):
            if self.debug:
                print(f"Skipping small building with area {area_m2:.1f}m²")
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        height = self.style_manager.scale_building_height(props)

        features["buildings"].append({"coords": transformed, "height": height})
        if self.debug:
            print(f"Added building with height {height:.1f}mm and area {area_m2:.1f}m²")
