from .geometry import GeometryUtils
from .style.style_manager import StyleManager
from .style.generate_building import BuildingGenerator

class ScadGenerator:
    def __init__(self, style_manager):
        self.style_manager = style_manager
        self.geometry = GeometryUtils()
        self.building_generator = BuildingGenerator(style_manager)

    def generate_openscad(self, features, size, layer_specs):
        """
        Generate complete OpenSCAD code for main model (excluding frame).
        We 'union' buildings, bridges, and parks, then 'difference' roads/water/rail.
        """
        scad = [
            f"""// Generated with Enhanced City Converter
// Style: {self.style_manager.style['artistic_style']}
// Detail Level: {self.style_manager.style['detail_level']}

difference() {{
    union() {{
        // Base block
        cube([{size}, {size}, {layer_specs['base']['height']}]);

        // Buildings
        {self._generate_building_features(features['buildings'], layer_specs)}

        // Bridges
        {self._generate_bridge_features(features['bridges'], layer_specs)}

        // Parks
        {self._generate_park_features(features['parks'], layer_specs)}
    }}

    // Subtractive features
    union() {{
        {self._generate_water_features(features['water'], layer_specs)}
        {self._generate_road_features(features['roads'], layer_specs)}
        {self._generate_railway_features(features['railways'], layer_specs)}
    }}
}}"""
        ]
        return "\n".join(scad)

    def _generate_building_features(self, building_features, layer_specs):
        """Generate OpenSCAD code for building features."""
        scad = []
        base_height = layer_specs["base"]["height"]

        for i, building in enumerate(building_features):
            points_str = self.geometry.generate_polygon_points(building["coords"])
            if not points_str:
                continue

            building_height = building["height"]
            roof_style = building.get("roof_style")
            roof_params = building.get("roof_params")
            is_cluster = building.get("is_cluster", False)

            # Generate the building details with explicit roof style if it's a cluster
            if is_cluster and roof_style and roof_params:
                details = self.building_generator.generate_building_details(
                    points_str=points_str,
                    height=building_height,
                    roof_style=roof_style,
                    roof_params=roof_params
                )
            else:
                details = self.building_generator.generate_building_details(
                    points_str=points_str,
                    height=building_height
                )

            scad.append(f"""
            // Building {i+1} {'(Merged Cluster)' if is_cluster else ''}
            translate([0, 0, {base_height}]) {{
                color("white")
                {{
                    {details}
                }}
            }}""")

        return "\n".join(scad)

    def _generate_water_features(self, water_features, layer_specs):
        """Generate OpenSCAD code for water features (subtractive)"""
        scad = []
        base_height = layer_specs["base"]["height"]
        water_depth = layer_specs["water"]["depth"]
        # Get park specifications to calculate full extrusion height
        park_specs = layer_specs["parks"]
        park_offset = park_specs.get("start_offset", 0.2)
        park_thickness = park_specs.get("thickness", 0.4)
        water_extrude_height = water_depth + park_offset + park_thickness + 0.1

        for i, water in enumerate(water_features):
            coords = water.get("coords", water)
            points_str = self.geometry.generate_polygon_points(coords)
            if points_str:
                scad.append(
                    f"""
        // Water body {i+1}
        translate([0, 0, {base_height - water_depth}])
            color("blue")
            {{
                linear_extrude(height={water_extrude_height}, convexity=2)
                    polygon([{points_str}]);
            }}"""
                )

        return "\n".join(scad)
    
    def _generate_road_features(self, road_features, layer_specs):
        """Generate OpenSCAD code for road features (subtractive)"""
        scad = []
        base_height = layer_specs["base"]["height"]
        road_depth = layer_specs["roads"]["depth"]
        road_width = layer_specs["roads"]["width"]
        park_offset = layer_specs["parks"].get("start_offset", 0.2)
        park_thickness = layer_specs["parks"].get("thickness", 0.4)
        road_extrude_height = road_depth + park_offset + park_thickness + 0.1

        for i, road in enumerate(road_features):
            coords = road.get("coords", [])
            is_parking = road.get("is_parking", False)

            if is_parking and len(coords) >= 3:
                points_str = self.geometry.generate_polygon_points(coords)
            else:
                points_str = None
                if len(coords) >= 2:
                    points_str = self.geometry.generate_buffered_polygon(
                        coords, road_width
                    )

            if points_str:
                color_val = "yellow" if is_parking else "black"
                scad.append(
                    f"""
            // {"Parking Area" if is_parking else "Road"} {i+1}
            translate([0, 0, {base_height - road_depth}])
                color("{color_val}")
                {{
                    linear_extrude(height={road_extrude_height}, convexity=2)
                        polygon([{points_str}]);
                }}"""
                )

        return "\n".join(scad)

    def _generate_railway_features(self, railway_features, layer_specs):
        """Generate OpenSCAD code for railways (subtractive)"""
        scad = []
        base_height = layer_specs["base"]["height"]
        railway_depth = layer_specs["railways"]["depth"]
        railway_width = layer_specs["railways"]["width"]

        for i, railway in enumerate(railway_features):
            coords = railway.get("coords", [])
            if len(coords) < 2:
                continue

            points_str = self.geometry.generate_buffered_polygon(coords, railway_width)
            if points_str:
                scad.append(
                    f"""
        // Railway {i+1}
        translate([0, 0, {base_height - railway_depth}])
            color("brown")
            {{
                linear_extrude(height={railway_depth + 0.1}, convexity=2)
                    polygon([{points_str}]);
            }}"""
                )

        return "\n".join(scad)

    def _generate_bridge_features(self, bridge_features, layer_specs):
        """Generate OpenSCAD code for bridges with improved 3D printing support"""
        scad = []
        base_height = layer_specs["base"]["height"]
        bridge_height = layer_specs["bridges"]["height"]
        bridge_thickness = layer_specs["bridges"]["thickness"]
        road_width = layer_specs["roads"]["width"]
        railway_width = layer_specs["railways"]["width"]

        for i, bridge in enumerate(bridge_features):
            coords = bridge.get("coords", [])
            if len(coords) < 2:
                continue
                
            bridge_type = bridge.get("bridge_type", "road")
            
            # Handle support_width being either a dict or float
            if isinstance(layer_specs["bridges"]["support_width"], dict):
                support_width = layer_specs["bridges"]["support_width"].get(bridge_type, 2.0)
            else:
                # Fall back to using support_width directly if it's not a dict
                support_width = float(layer_specs["bridges"]["support_width"])
            
            # Use appropriate width based on bridge type
            if bridge_type == "road":
                width = road_width
                color = "orange"
            else:  # railway
                width = railway_width
                color = "brown"
            
            points_str = self.geometry.generate_buffered_polygon(coords, width)
            if points_str:
                start_point = coords[0]
                end_point = coords[-1]
                
                # Generate simplified supports
                supports_code = self._generate_bridge_supports(
                    coords, base_height, bridge_height, support_width
                )

                # Generate simple railings for rail bridges
                railings_code = ""
                if bridge_type == "rail":
                    railings_code = f"""
                    // Railway bridge railings
                    translate([0, 0, {base_height + bridge_height + bridge_thickness}])
                        cube([0.1, 0.1, 0.1]); // Dummy object that won't affect rendering"""

                scad.append(
                    f"""
            // {bridge_type.capitalize()} Bridge {i+1}
            union() {{
                color("{color}")
                {{
                    // Main bridge deck
                    translate([0, 0, {base_height + bridge_height}])
                        linear_extrude(height={bridge_thickness}, convexity=2)
                            polygon([{points_str}]);
                    {railings_code}
                }}
                // Bridge supports
                {supports_code}
            }}"""
                )

        return "\n".join(scad)
    
    def _generate_bridge_supports(self, coords, base_height, bridge_height, support_width):
        """Generate simplified bridge supports"""
        if len(coords) < 2:
            return ""
            
        # Always add supports at the start and end
        start_point = coords[0]
        end_point = coords[-1]
        
        supports = [
            f"translate([{start_point[0]}, {start_point[1]}, {base_height}])\n"
            f"    cylinder(h={bridge_height}, r={support_width/2}, $fn=8);",
            f"translate([{end_point[0]}, {end_point[1]}, {base_height}])\n"
            f"    cylinder(h={bridge_height}, r={support_width/2}, $fn=8);"
        ]
        
        # Add intermediate supports for longer bridges using simple point selection
        if len(coords) > 2:
            # Simple approach: Add one support in the middle for longer bridges
            middle_point_index = len(coords) // 2
            middle_point = coords[middle_point_index]
            supports.append(
                f"translate([{middle_point[0]}, {middle_point[1]}, {base_height}])\n"
                f"    cylinder(h={bridge_height}, r={support_width/2}, $fn=8);"
            )
        
        return "\n            ".join(supports)  
    def _generate_bridge_railings(self, bridge_type, coords, base_height, bridge_height, bridge_thickness, width):
        """Generate railings for railway bridges"""
        if bridge_type != "rail" or len(coords) < 2:
            return ""
            
        # Only generate railings for railway bridges
        railing_height = 0.4  # Railing height
        railing_width = 0.2   # Railing width
        offset = width / 2 - railing_width / 2
        
        # Generate railings on both sides of the bridge
        return f"""
                // Railway bridge railings
                translate([0, 0, {base_height + bridge_height + bridge_thickness}]) {{
                    linear_extrude(height={railing_height}, convexity=2)
                        difference() {{
                            polygon([{self.geometry.generate_buffered_polygon(coords, width)}]);
                            polygon([{self.geometry.generate_buffered_polygon(coords, width - railing_width * 2)}]);
                        }}
                }}"""
    def _generate_park_features(self, park_features, layer_specs):
        """Generate OpenSCAD code for park features."""
        scad = []
        base_height = layer_specs["base"]["height"]
        park_offset = layer_specs["parks"].get("start_offset", 0.2)
        park_thickness = layer_specs["parks"].get("thickness", 0.4)

        for i, park in enumerate(park_features):
            points_str = self.geometry.generate_polygon_points(park["coords"])
            if not points_str:
                continue
                
            scad.append(f"""
        // Park {i+1}
        translate([0, 0, {base_height + park_offset}]) {{
            color("green")
            linear_extrude(height={park_thickness}, convexity=2)
                polygon([{points_str}]);
        }}""")
            
        return "\n".join(scad)