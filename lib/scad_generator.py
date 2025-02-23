# lib/scad_generator.py

from .geometry import GeometryUtils
from .style.style_manager import StyleManager


class ScadGenerator:
    def __init__(self, style_manager):
        self.style_manager = style_manager
        self.geometry = GeometryUtils()

    def generate_openscad(self, features, size, layer_specs):
        """
        Generate complete OpenSCAD code for the main model (excluding frame).
        We'll union buildings, parks, etc. and difference roads/water/rail.
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
        {self._generate_park_features(features.get('parks', []), layer_specs)}
    }}

    // Subtractive features: roads, water, rail
    union() {{
        {self._generate_water_features(features['water'], layer_specs)}
        {self._generate_road_features(features['roads'], layer_specs)}
        {self._generate_railway_features(features['railways'], layer_specs)}
    }}
}}"""
        ]

        return "\n".join(scad)

    def _generate_building_features(self, building_features, layer_specs):
        """Generate OpenSCAD code for building features (unioned on top)."""
        scad = []
        base_height = layer_specs["base"]["height"]

        for i, building in enumerate(building_features):
            points_str = self.geometry.generate_polygon_points(building["coords"])
            if not points_str:
                continue

            building_height = building["height"]
            is_cluster = building.get("is_cluster", False)
            is_industrial = building.get("is_industrial", False)
            is_block = building.get("is_block", False)

            # [ADDED/CHANGED] Pass along 'roof_style' if present
            roof_style = building.get("roof_style", None)

            details = self._generate_building_details(
                points_str,
                building_height,
                is_cluster=is_cluster,
                is_industrial=is_industrial,
                is_block=is_block,
                roof_style=roof_style
            )

            scad.append(
                f"""
    // Building {i+1}
    translate([0, 0, {base_height}]) {{
        {details}
    }}"""
            )

        return "\n".join(scad)

    def _generate_building_details(self, points_str, height, is_cluster=False,
                                   is_industrial=False, is_block=False,
                                   roof_style=None):
        """
        Generate architectural details based on style and building type.
        """

        style = self.style_manager.style["artistic_style"]
        detail_level = self.style_manager.style["detail_level"]

        # [ADDED for block roofs]
        # If this building has 'is_block=True' and a 'roof_style', pick that style snippet.
        if is_block and roof_style:
            return self._generate_block_roof(points_str, height, roof_style)

        # Industrial buildings
        if is_industrial:
            return self._generate_industrial_details(points_str, height, style, detail_level)

        # If it's not a cluster or we have very low detail, do a simple extrusion
        if not is_cluster or detail_level < 0.5:
            return f"""linear_extrude(height={height}, convexity=2)
    polygon([{points_str}]);"""

        # Otherwise handle normal "modern"/"classic"/"minimal" styles for multi-building clusters
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
        else:  # minimal or fallback
            return f"""linear_extrude(height={height}, convexity=2)
    polygon([{points_str}]);"""

    # [ADDED new helper to handle block roofs]
    def _generate_block_roof(self, points_str, height, roof_style):
        """
        For block-combine polygons, pick a roof style snippet based on 'roof_style'.
        """
        if roof_style == "flat":
            return f"""linear_extrude(height={height}, convexity=2)
    polygon([{points_str}]);"""

        elif roof_style == "sawtooth":
            return f"""
    union() {{
        linear_extrude(height={height * 0.8}, convexity=2)
            polygon([{points_str}]);
        translate([0, 0, {height * 0.8}])
            linear_extrude(height={height * 0.2}, convexity=2)
                offset(r=-1)
                    polygon([{points_str}]);
    }}"""

        elif roof_style == "step":
            return f"""
    union() {{
        linear_extrude(height={height * 0.7}, convexity=2)
            polygon([{points_str}]);
        translate([0, 0, {height * 0.7}])
            linear_extrude(height={height * 0.3}, convexity=2)
                offset(r=-0.8)
                    polygon([{points_str}]);
    }}"""

        else:  # e.g. "modern"
            return f"""
    union() {{
        linear_extrude(height={height}, convexity=2)
            polygon([{points_str}]);
        translate([0, 0, {height}])
            linear_extrude(height=1.0, convexity=2)
                offset(r=-1.5)
                    polygon([{points_str}]);
    }}"""

    def _generate_industrial_details(self, points_str, height, style, detail_level):
        """
        Generate special extrusions for industrial buildings (with different roof shapes).
        """
        if style == "modern":
            # Modern industrial: flat roof + mechanical details
            return f"""
    union() {{
        // Main structure
        linear_extrude(height={height}, convexity=2)
            polygon([{points_str}]);
        
        // Roof detail
        translate([0, 0, {height}]) {{
            linear_extrude(height=1.2, convexity=2)
                offset(r=-2)
                    polygon([{points_str}]);
        }}
    }}"""
        elif style == "classic":
            # Classic industrial: sawtooth roof
            return f"""
    union() {{
        linear_extrude(height={height * 0.8}, convexity=2)
            polygon([{points_str}]);

        // Sawtooth roof
        translate([0, 0, {height * 0.8}])
            linear_extrude(height={height * 0.2}, convexity=2)
                offset(r=-1)
                    polygon([{points_str}]);
    }}"""
        else:
            # minimal or fallback: block + slight roof edge
            return f"""
    union() {{
        linear_extrude(height={height}, convexity=2)
            polygon([{points_str}]);
        
        translate([0, 0, {height - 0.5}])
            linear_extrude(height=0.5, convexity=2)
                offset(r=-0.5)
                    polygon([{points_str}]);
    }}"""

    def _generate_park_features(self, park_features, layer_specs):
        """
        Extrude 'parks' or green areas from (base_height + start_offset) up to thickness.
        """
        scad = []
        base_height = layer_specs["base"]["height"]

        park_start = layer_specs["parks"].get("start_offset", 0.2)
        park_thickness = layer_specs["parks"].get("thickness", 0.4)

        for i, park in enumerate(park_features):
            coords = park.get("coords", [])
            if len(coords) < 3:
                continue
            points_str = self.geometry.generate_polygon_points(coords)
            if points_str:
                scad.append(f"""
        // Park {i+1}
        translate([0, 0, {base_height + park_start}])
            linear_extrude(height={park_thickness}, convexity=2)
                polygon([{points_str}]);""")

        return "\n".join(scad)

    def _generate_water_features(self, water_features, layer_specs):
        """Generate OpenSCAD code for water features (subtractive)."""
        scad = []
        base_height = layer_specs["base"]["height"]
        water_depth = layer_specs["water"]["depth"]

        for i, water in enumerate(water_features):
            coords = water.get("coords", [])
            points_str = self.geometry.generate_polygon_points(coords)
            if points_str:
                scad.append(
                    f"""
        // Water body {i+1}
        translate([0, 0, {base_height - water_depth}])
            linear_extrude(height={water_depth + 0.1}, convexity=2)
                polygon([{points_str}]);"""
                )

        return "\n".join(scad)

    def _generate_road_features(self, road_features, layer_specs):
        """Generate OpenSCAD code for roads (subtractive)."""
        scad = []
        base_height = layer_specs["base"]["height"]
        road_depth = layer_specs["roads"]["depth"]
        road_width = layer_specs["roads"]["width"]

        for i, road in enumerate(road_features):
            coords = road.get("coords", [])
            is_parking = road.get("is_parking", False)

            if is_parking and len(coords) >= 3:
                # Parking as polygon
                points_str = self.geometry.generate_polygon_points(coords)
            else:
                # Road as buffered line
                points_str = None
                if len(coords) >= 2:
                    points_str = self.geometry.generate_buffered_polygon(coords, road_width)

            if points_str:
                scad.append(
                    f"""
        // {"Parking Area" if is_parking else "Road"} {i+1}
        translate([0, 0, {base_height - road_depth}])
            linear_extrude(height={road_depth + 0.1}, convexity=2)
                polygon([{points_str}]);"""
                )

        return "\n".join(scad)

    def _generate_railway_features(self, railway_features, layer_specs):
        """Generate OpenSCAD code for railways (subtractive)."""
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
                polygon([{points_str}]);"""
                )

        return "\n".join(scad)

    def _generate_bridge_features(self, bridge_features, layer_specs):
        """Generate OpenSCAD code for bridges with basic 3D-printing supports."""
        scad = []
        base_height = layer_specs["base"]["height"]
        bridge_height = 2.0      # Height above the base
        bridge_thickness = 1.0   # Bridge deck thickness
        support_width = 2.0      # Support column radius
        road_width = layer_specs["roads"]["width"]

        for i, bridge in enumerate(bridge_features):
            coords = bridge.get("coords", [])
            if len(coords) < 2:
                continue

            points_str = self.geometry.generate_buffered_polygon(coords, road_width)
            if points_str:
                start_point = coords[0]
                end_point = coords[-1]

                scad.append(
                    f"""
        // Bridge {i+1}
        union() {{
            // Bridge deck
            translate([0, 0, {base_height + bridge_height}])
                linear_extrude(height={bridge_thickness}, convexity=2)
                    polygon([{points_str}]);
            
            // Bridge supports at endpoints
            translate([{start_point[0]}, {start_point[1]}, {base_height}])
                cylinder(h={bridge_height}, r={support_width/2}, $fn=8);
            translate([{end_point[0]}, {end_point[1]}, {base_height}])
                cylinder(h={bridge_height}, r={support_width/2}, $fn=8);
        }}"""
                )

        return "\n".join(scad)
