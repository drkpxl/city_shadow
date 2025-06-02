# lib/feature_processor/building_processor.py
from shapely.geometry import Polygon
from .base_processor import BaseProcessor
import random

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
        #if (self.style_manager.style.get("artistic_style") != "block-combine") and (area_m2 < min_area):
        if area_m2 < min_area:
            if self.debug:
                print(f"Skipping small building with area {area_m2:.1f}m²")
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        height = self.style_manager.scale_building_height(props)
        
        # Get roof styles from style manager
        available_roof_styles = self.style_manager.style.get('roof_styles', None)
        
        # If roof_styles list exists, use it. Otherwise fall back to old behavior
        if available_roof_styles and isinstance(available_roof_styles, list):
            # Choose randomly from the selected styles
            roof_style = random.choice(available_roof_styles)
        else:
            # Backward compatibility with single roof_style
            roof_style_setting = self.style_manager.style.get('roof_style', 'mixed')
            if roof_style_setting == 'mixed':
                roof_styles = ['flat', 'pitched', 'tiered', 'sawtooth', 'modern', 'stepped']
                roof_style = random.choice(roof_styles)
            else:
                roof_style = roof_style_setting
            
        # Get roof parameters for the selected style
        roof_params = self._get_roof_params(roof_style)

        features["buildings"].append({
            "coords": transformed, 
            "height": height,
            "roof_style": roof_style,
            "roof_params": roof_params
        })
        if self.debug:
            print(f"Added building with height {height:.1f}mm, roof style {roof_style}, and area {area_m2:.1f}m²")
    
    def _get_roof_params(self, roof_style):
        """Get randomized parameters for the given roof style."""
        if roof_style == 'pitched':
            return {'height_factor': random.uniform(0.2, 0.4)}
        elif roof_style == 'tiered':
            return {'levels': random.randint(2, 4)}
        elif roof_style == 'flat':
            return {'border': random.uniform(0.8, 1.2)}
        elif roof_style == 'sawtooth':
            return {'angle': random.randint(25, 35)}
        elif roof_style == 'modern':
            return {'setback': random.uniform(1.8, 2.2)}
        elif roof_style == 'stepped':
            return {'levels': random.randint(2, 4)}
        else:
            return {}
