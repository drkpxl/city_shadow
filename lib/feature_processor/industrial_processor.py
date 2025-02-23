# lib/feature_processor/industrial_processor.py
from shapely.geometry import Polygon
from .base_processor import BaseProcessor

class IndustrialProcessor(BaseProcessor):
    # Define industrial-related tags to look for
    INDUSTRIAL_LANDUSE = {
        'industrial',
        'construction',
        'depot',
        'logistics',
        'port',
        'warehouse'
    }
    
    INDUSTRIAL_BUILDINGS = {
        'industrial',
        'warehouse',
        'factory',
        'manufacturing',
        'hangar'
    }

    def process_industrial_building(self, feature, features, transform):
        """Process an industrial building with specific handling."""
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        area_m2 = self.geometry.approximate_polygon_area_m2(coords)
        min_area = self.style_manager.style.get("min_building_area", 600.0)

        # Only skip small industrial buildings if not in block-combine mode.
        if (self.style_manager.style.get("artistic_style") != "block-combine") and (area_m2 < min_area):
            if self.debug:
                print(f"Skipping small industrial building with area {area_m2:.1f}m²")
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        
        # Calculate height using our detailed calculator
        layer_specs = self.style_manager.get_default_layer_specs()
        min_height = layer_specs["buildings"]["min_height"]
        max_height = layer_specs["buildings"]["max_height"]
        
        # Use explicit height if available, otherwise use industrial multiplier
        height_m = self._get_explicit_height(props)
        if height_m is not None:
            base_height = self.style_manager.scale_building_height({
                "height": str(height_m)
            })
            height = base_height * 1.5  # 50% bonus
        else:
            # Default to twice minimum height for industrial buildings
            height = min(max_height, min_height * 2.0)

        features["industrial"].append({
            "coords": transformed,
            "height": height,
            "is_industrial": True,
            "building_type": props.get("building", "industrial")
        })
        
        if self.debug:
            print(f"Added industrial building, height {height:.1f}mm, area {area_m2:.1f}m²")

    def process_industrial_area(self, feature, features, transform):
        """Process industrial landuse areas as buildings."""
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        # Check if this is an industrial area
        landuse = props.get("landuse", "").lower()
        if landuse not in self.INDUSTRIAL_LANDUSE:
            return

        transformed = [transform(lon, lat) for lon, lat in coords]

        area_m2 = self.geometry.approximate_polygon_area_m2(coords)
        min_area = self.style_manager.style.get("min_building_area", 600.0)

        # Only skip small industrial areas if not using block-combine style.
        if (self.style_manager.style.get("artistic_style") != "block-combine") and (area_m2 < min_area):
            if self.debug:
                print(f"Skipping small industrial area with area {area_m2:.1f}m²")
            return

        layer_specs = self.style_manager.get_default_layer_specs()
        min_height = layer_specs["buildings"]["min_height"]
        max_height = layer_specs["buildings"]["max_height"]
        
        # Different heights for different types
        height_multipliers = {
            'industrial': 2.0,
            'construction': 1.5,
            'depot': 1.5,
            'logistics': 1.8,
            'port': 2.0,
            'warehouse': 1.7
        }
        
        multiplier = height_multipliers.get(landuse, 1.5)
        height = min(max_height, min_height * multiplier)

        features["industrial"].append({
            "coords": transformed,
            "height": height,
            "is_industrial": True,
            "landuse_type": landuse
        })

        if self.debug:
            print(f"Added industrial area type '{landuse}' with height {height:.1f}mm")

    def should_process_as_industrial(self, properties):
        """Check if a feature should be processed as industrial."""
        if not properties:
            return False
            
        # Check building tag
        building = properties.get("building", "").lower()
        if building in self.INDUSTRIAL_BUILDINGS:
            return True
            
        # Check landuse tag
        landuse = properties.get("landuse", "").lower()
        if landuse in self.INDUSTRIAL_LANDUSE:
            return True
            
        return False

    def _get_explicit_height(self, properties):
        """Extract explicit height from properties if available."""
        if "height" in properties:
            try:
                height_str = properties["height"].split()[0]  # Handle "10 m" format
                return float(height_str)
            except (ValueError, IndexError):
                pass
                
        if "building:levels" in properties:
            try:
                levels = float(properties["building:levels"])
                return levels * 3  # assume 3m per level
            except ValueError:
                pass
                
        return None
