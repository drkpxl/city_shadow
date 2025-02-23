# lib/scad_generator.py
from .geometry import GeometryUtils
from .style.style_manager import StyleManager


class ScadGenerator:
    def __init__(self, style_manager):
        self.style_manager = style_manager
        self.geometry = GeometryUtils()

    def generate_openscad(self, features, size, layer_specs):
        """
        Generate complete OpenSCAD code for main model (excluding frame).
        We 'union' buildings & bridges, then 'difference' roads/water/rail.
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
        """Generate OpenSCAD code for building features (unioned on top)"""
        scad = []
        base_height = layer_specs["base"]["height"]

        for i, building in enumerate(building_features):
            points_str = self.geometry.generate_polygon_points(building["coords"])
            if not points_str:
                continue

            building_height = building["height"]
            is_cluster = building.get("is_cluster", False)
            is_industrial = building.get("is_industrial", False)

            # Choose appropriate building type label for comments
            building_type = (
                "Industrial Building"
                if is_industrial
                else "Building Cluster" if is_cluster else "Building"
            )

            details = self._generate_building_details(
                points_str, building_height, is_cluster, is_industrial
            )

            # Wrap building details in white color
            scad.append(
                f"""
    // {building_type} {i+1}
    translate([0, 0, {base_height}]) {{
        color("white")
        {{
            {details}
        }}
    }}"""
            )

        return "\n".join(scad)

    def _generate_building_details(
        self, points_str, height, is_cluster, is_industrial=False
    ):
        """Generate architectural details based on style and building type."""
        style = self.style_manager.style["artistic_style"]
        detail_level = self.style_manager.style["detail_level"]

        # Industrial buildings get special treatment
        if is_industrial:
            return self._generate_industrial_details(
                points_str, height, style, detail_level
            )

        # Simple extrusion for low detail or single buildings
        if not is_cluster or detail_level < 0.5:
            return f"""linear_extrude(height={height}, convexity=2)
    polygon([{points_str}]);"""

        # Style-specific details for regular buildings
        if style == "modern":
            return f"""
    union() {{
        linear_extrude(height={height}, convexity=2)
            polygon([{points_str}]);
        translate([0, 0, {height}])
            linear_extrude(height=0.8, convexity=2)
                offset(r=-0.8)
                    polygon([{points_str}]);
    }}"""
        elif style == "classic":
            return f"""
    union() {{
        linear_extrude(height={height}, convexity=2)
            polygon([{points_str}]);
        translate([0, 0, {height * 0.8}])
            linear_extrude(height={height * 0.2}, convexity=2)
                offset(r=-0.5)
                    polygon([{points_str}]);
    }}"""
        else:  # minimal
            return f"""linear_extrude(height={height}, convexity=2)
    polygon([{points_str}]);"""

    def _generate_industrial_details(self, points_str, height, style, detail_level):
        """Generate industrial-specific architectural details."""
        if style == "modern":
            # Modern industrial: Flat roof with mechanical details
            return f"""
    union() {{
        // Main structure
        linear_extrude(height={height}, convexity=2)
            polygon([{points_str}]);
        
        // Roof details (mechanical equipment, etc.)
        translate([0, 0, {height}]) {{
            linear_extrude(height=1.2, convexity=2)
                offset(r=-2)
                    polygon([{points_str}]);
        }}
    }}"""
        elif style == "classic":
            # Classic industrial: Sawtooth roof pattern
            return f"""
    union() {{
        // Main structure
        linear_extrude(height={height * 0.8}, convexity=2)
            polygon([{points_str}]);
        
        // Sawtooth roof
        translate([0, 0, {height * 0.8}])
            linear_extrude(height={height * 0.2}, convexity=2)
                offset(r=-1)
                    polygon([{points_str}]);
    }}"""
        else:  # minimal
            # Minimal industrial: Simple block with slight roof detail
            return f"""
    union() {{
        // Main structure
        linear_extrude(height={height}, convexity=2)
            polygon([{points_str}]);
        
        // Simple roof edge
        translate([0, 0, {height - 0.5}])
            linear_extrude(height=0.5, convexity=2)
                offset(r=-0.5)
                    polygon([{points_str}]);
    }}"""

    def _generate_water_features(self, water_features, layer_specs):
        """Generate OpenSCAD code for water features (subtractive)"""
        scad = []
        base_height = layer_specs["base"]["height"]
        water_depth = layer_specs["water"]["depth"]

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
                linear_extrude(height={water_depth + 0.1}, convexity=2)
                    polygon([{points_str}]);
            }}"""
                )

        return "\n".join(scad)

    def _generate_road_features(self, road_features, layer_specs):
        """Generate OpenSCAD code for roads (subtractive)"""
        scad = []
        base_height = layer_specs["base"]["height"]
        road_depth = layer_specs["roads"]["depth"]
        road_width = layer_specs["roads"]["width"]

        for i, road in enumerate(road_features):
            coords = road.get("coords", [])
            is_parking = road.get("is_parking", False)

            if is_parking and len(coords) >= 3:
                # Parking lot as polygon
                points_str = self.geometry.generate_polygon_points(coords)
            else:
                # Road as buffered line
                points_str = None
                if len(coords) >= 2:
                    points_str = self.geometry.generate_buffered_polygon(
                        coords, road_width
                    )

            if points_str:
                color_val = "green" if is_parking else "black"
                scad.append(
                    f"""
        // {"Parking Area" if is_parking else "Road"} {i+1}
        translate([0, 0, {base_height - road_depth}])
            color("{color_val}")
            {{
                linear_extrude(height={road_depth + 0.1}, convexity=2)
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
        bridge_height = 2.0  # Height above base
        bridge_thickness = 1  # Thickness for stability
        support_width = 2.0  # Width of bridge supports
        road_width = layer_specs["roads"]["width"]

        for i, bridge in enumerate(bridge_features):
            coords = bridge.get("coords", [])
            if len(coords) < 2:
                continue

            points_str = self.geometry.generate_buffered_polygon(coords, road_width)
            if points_str:
                start_point = coords[0]
                end_point = coords[-1]

                # Using red color for unspecified features (bridges)
                scad.append(
                    f"""
        // Bridge {i+1}
        union() {{
            color("orange")
            {{
                // Main bridge deck
                translate([0, 0, {base_height + bridge_height}])
                    linear_extrude(height={bridge_thickness}, convexity=2)
                        polygon([{points_str}]);
            }}
            // Bridge supports (remain uncolored for clarity)
            translate([{start_point[0]}, {start_point[1]}, {base_height}])
                cylinder(h={bridge_height}, r={support_width/2}, $fn=8);
            translate([{end_point[0]}, {end_point[1]}, {base_height}])
                cylinder(h={bridge_height}, r={support_width/2}, $fn=8);
        }}"""
                )

        return "\n".join(scad)
