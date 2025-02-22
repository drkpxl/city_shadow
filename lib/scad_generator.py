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

        // Bridges (NEW)
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
            linear_extrude(height={water_depth + 0.1}, convexity=2)
                polygon([{points_str}]);
        """
                )

        return "\n".join(scad)

    def _generate_road_features(self, road_features, layer_specs):
        """Generate OpenSCAD code for roads (subtractive)"""
        scad = []
        base_height = layer_specs["base"]["height"]
        road_depth = layer_specs["roads"]["depth"]
        road_width = layer_specs["roads"]["width"]

        # Debug prints
        print(f"\nGenerating road features:")
        print(f"Number of roads: {len(road_features)}")
        print(f"Road depth: {road_depth}mm, width: {road_width}mm")

        for i, road in enumerate(road_features):
            coords = road.get("coords", [])
            is_parking = road.get("is_parking", False)
            if is_parking and len(coords) >= 3:
                # Polygon
                points_str = self.geometry.generate_polygon_points(coords)
            else:
                # Line-based (buffered polygon)
                points_str = None
                if len(coords) >= 2:
                    points_str = self.geometry.generate_buffered_polygon(
                        coords, road_width
                    )

            if points_str:
                scad.append(
                    f"""
        // Road {i+1}
        translate([0, 0, {base_height - road_depth}])
            linear_extrude(height={road_depth + 0.1}, convexity=2)
                polygon([{points_str}]);
        """
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
            linear_extrude(height={railway_depth + 0.1}, convexity=2)
                polygon([{points_str}]);
        """
                )

        return "\n".join(scad)

    def _generate_bridge_features(self, bridge_features, layer_specs):
        """
        Generate OpenSCAD code for bridges as
        1 mm above the base, 1 mm thick, with road-like width.
        """
        scad = []
        base_height = layer_specs["base"]["height"]
        bridge_thickness = 1.0  # thickness
        z_offset = base_height + 1.0  # place 1 mm above the top of the base
        bridge_width = layer_specs["roads"]["width"]  # or define a custom width

        for i, bridge in enumerate(bridge_features):
            coords = bridge.get("coords", [])
            if len(coords) < 2:
                continue
            points_str = self.geometry.generate_buffered_polygon(coords, bridge_width)
            if points_str:
                scad.append(
                    f"""
        // Bridge {i+1}
        // Placed 1mm above base, 1mm thick
        translate([0, 0, {z_offset}])
            linear_extrude(height={bridge_thickness}, convexity=2)
                polygon([{points_str}]);
        """
                )

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

            details = self._generate_building_details(
                points_str, building_height, is_cluster
            )

            scad.append(
                f"""
    // {"Building Cluster" if is_cluster else "Building"} {i+1}
    translate([0, 0, {base_height}]) {{
        {details}
    }}"""
            )

        return "\n".join(scad)

    def _generate_building_details(self, points_str, height, is_cluster):
        """Generate architectural details based on style"""
        style = self.style_manager.style["artistic_style"]
        detail_level = self.style_manager.style["detail_level"]

        # If it's a single building or minimal detail, extrude as-is
        if not is_cluster or detail_level < 0.5:
            return f"""linear_extrude(height={height}, convexity=2)
    polygon([{points_str}]);"""

        # Otherwise, add stylized top or sections
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
