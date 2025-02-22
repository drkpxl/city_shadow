# lib/scad_generator.py
from .geometry import GeometryUtils


class ScadGenerator:
    def __init__(self, style_manager):
        self.style_manager = style_manager
        self.geometry = GeometryUtils()

    def generate_openscad(self, features, size, layer_specs):
        """Generate complete OpenSCAD code for main model without frame"""
        scad = [
            f"""// Generated with Enhanced City Converter
// Style: {self.style_manager.style['artistic_style']}
// Detail Level: {self.style_manager.style['detail_level']}

// Main city model without frame
difference() {{  // Main difference that affects everything
    union() {{
        // Base
        cube([{size}, {size}, {layer_specs['base']['height']}]);
        
        // Add buildings on top of base
        {self._generate_building_features(features['buildings'], layer_specs)}
    }}
    
    // Subtractive features (water, roads, railways)
    union() {{
        {self._generate_water_features(features['water'], layer_specs)}
        {self._generate_road_features(features['roads'], layer_specs)}
        {self._generate_railway_features(features['railways'], layer_specs)}
    }}
}}"""
        ]

        return "\n".join(scad)

    def _generate_water_features(self, water_features, layer_specs):
        """Generate OpenSCAD code for water features"""
        scad = []
        base_height = layer_specs["base"]["height"]
        water_depth = layer_specs["water"]["depth"]

        for i, water in enumerate(water_features):
            coords = water.get("coords", water)
            points_str = self.geometry.generate_polygon_points(coords)
            if points_str:
                scad.extend(
                    [
                        f"""
        // Water body {i+1}
        translate([0, 0, {base_height - water_depth}])
            linear_extrude(height={water_depth + 0.1}, convexity=2)
                polygon([{points_str}]);"""
                    ]
                )

        return "\n".join(scad)

    def _generate_road_features(self, road_features, layer_specs):
        """Generate OpenSCAD code for road features"""
        scad = []
        base_height = layer_specs["base"]["height"]
        road_depth = layer_specs["roads"]["depth"]
        road_width = layer_specs["roads"]["width"]

        print(f"\nGenerating road features:")
        print(f"Number of roads: {len(road_features)}")
        print(f"Road depth: {road_depth}mm")
        print(f"Road width: {road_width}mm")

        for i, road in enumerate(road_features):
            if isinstance(road, dict):
                coords = road.get("coords", [])
                is_parking = road.get("is_parking", False)
                points_str = None

                if is_parking and len(coords) >= 3:
                    points_str = self.geometry.generate_polygon_points(coords)
                elif len(coords) >= 2:
                    points_str = self.geometry.generate_buffered_polygon(
                        coords, road_width
                    )
            else:
                points_str = self.geometry.generate_buffered_polygon(road, road_width)

            if points_str:
                scad.extend(
                    [
                        f"""
        // Road {i+1}
        translate([0, 0, {base_height - road_depth}])
            linear_extrude(height={road_depth + 0.1}, convexity=2)
                polygon([{points_str}]);"""
                    ]
                )

        return "\n".join(scad)

    def _generate_railway_features(self, railway_features, layer_specs):
        """Generate OpenSCAD code for railway features"""
        scad = []
        base_height = layer_specs["base"]["height"]
        railway_depth = layer_specs["railways"]["depth"]
        railway_width = layer_specs["railways"]["width"]

        for i, railway in enumerate(railway_features):
            coords = railway.get("coords", []) if isinstance(railway, dict) else railway
            if len(coords) >= 2:
                points_str = self.geometry.generate_buffered_polygon(
                    coords, railway_width
                )
                if points_str:
                    scad.extend(
                        [
                            f"""
        // Railway {i+1}
        translate([0, 0, {base_height - railway_depth}])
            linear_extrude(height={railway_depth + 0.1}, convexity=2)
                polygon([{points_str}]);"""
                        ]
                    )

        return "\n".join(scad)

    def _generate_building_features(self, building_features, layer_specs):
        """Generate OpenSCAD code for building features"""
        scad = []
        base_height = layer_specs["base"]["height"]

        for i, building in enumerate(building_features):
            points_str = self.geometry.generate_polygon_points(building["coords"])
            if not points_str:
                continue

            is_cluster = building.get("is_cluster", False)
            building_height = building["height"]

            # Generate building with appropriate style
            details = self._generate_building_details(
                points_str, building_height, is_cluster
            )

            scad.extend(
                [
                    f"""
    // {"Building Cluster" if is_cluster else "Building"} {i+1}
    translate([0, 0, {base_height}]) {{
        {details}
    }}"""
                ]
            )

        return "\n".join(scad)

    def _generate_building_details(self, points_str, height, is_cluster):
        """Generate architectural details based on style"""
        if not is_cluster or self.style_manager.style["detail_level"] < 0.5:
            return f"""
                linear_extrude(height={height}, convexity=2)
                    polygon([{points_str}]);"""

        if self.style_manager.style["artistic_style"] == "modern":
            return f"""
                union() {{
                    linear_extrude(height={height}, convexity=2)
                        polygon([{points_str}]);
                    translate([0, 0, {height}])
                        linear_extrude(height=0.8, convexity=2)
                            offset(r=-0.8)
                                polygon([{points_str}]);
                }}"""

        elif self.style_manager.style["artistic_style"] == "classic":
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
            return f"""
                linear_extrude(height={height}, convexity=2)
                    polygon([{points_str}]);"""
