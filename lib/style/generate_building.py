class BuildingGenerator:
    """
    Generates OpenSCAD code for buildings with various roof styles.
    Maintains all original architectural features while removing redundancy.
    """
    
    def __init__(self, style_manager):
        self.style_manager = style_manager

    def generate_building_details(self, points_str, height, roof_style=None, roof_params=None):
        """Generate OpenSCAD code for a building with optional roof style."""
        if not roof_style or not roof_params:
            return self._basic_building(points_str, height)
            
        # Dispatch to specific roof generators
        if roof_style == 'pitched':
            return self._pitched_roof(points_str, height, roof_params)
        elif roof_style == 'tiered':
            return self._tiered_roof(points_str, height, roof_params)
        elif roof_style == 'flat':
            return self._flat_roof(points_str, height, roof_params)
        elif roof_style == 'sawtooth':
            return self._sawtooth_roof(points_str, height, roof_params)
        elif roof_style == 'modern':
            return self._modern_roof(points_str, height, roof_params)
        elif roof_style == 'stepped':
            return self._stepped_roof(points_str, height, roof_params)
            
        return self._basic_building(points_str, height)

    def _basic_building(self, points_str, height):
        return f"linear_extrude(height={height}, convexity=2) polygon([{points_str}]);"

    def _pitched_roof(self, points_str, height, params):
        roof_height = height * params.get('height_factor', 0.3)
        base_height = height - roof_height
        return f"""union() {{
            linear_extrude(height={base_height}, convexity=2) polygon([{points_str}]);
            translate([0, 0, {base_height}]) {{
                intersection() {{
                    linear_extrude(height={roof_height}, scale=0.6, convexity=2)
                        polygon([{points_str}]);
                    linear_extrude(height={roof_height}, convexity=2)
                        polygon([{points_str}]);
                }}
            }}
        }}"""

    def _tiered_roof(self, points_str, height, params):
        levels = params.get('levels', 2)
        level_height = height / (levels + 1)
        return f"""union() {{
            linear_extrude(height={level_height}, convexity=2) polygon([{points_str}]);
            {" ".join(self._tier_sections(points_str, level_height, levels))}
        }}"""

    def _tier_sections(self, points_str, level_height, levels):
        return [f"""
            translate([0, 0, {level_height * (i + 1)}])
                linear_extrude(height={level_height}, convexity=2)
                    offset(r=-{(i + 1) * 1.0})
                        polygon([{points_str}]);""" 
            for i in range(levels)]

    def _flat_roof(self, points_str, height, params):
        border = params.get('border', 1.0)
        return f"""union() {{
            linear_extrude(height={height}, convexity=2) polygon([{points_str}]);
            translate([0, 0, {height}])
                linear_extrude(height=1.0, convexity=2)
                    difference() {{
                        polygon([{points_str}]);
                        offset(r=-{border}) polygon([{points_str}]);
                    }}
        }}"""

    def _sawtooth_roof(self, points_str, height, params):
        angle = params.get('angle', 30)
        roof_height = height * 0.2
        return f"""union() {{
            linear_extrude(height={height - roof_height}, convexity=2) polygon([{points_str}]);
            translate([0, 0, {height - roof_height}])
                intersection() {{
                    linear_extrude(height={roof_height}, convexity=2) polygon([{points_str}]);
                    rotate([{angle}, 0, 0]) translate([0, 0, -50])
                        linear_extrude(height=100, convexity=4) polygon([{points_str}]);
                }}
        }}"""

    def _modern_roof(self, points_str, height, params):
        setback = params.get('setback', 2.0)
        roof_height = height * 0.2
        return f"""union() {{
            linear_extrude(height={height - roof_height}, convexity=2) polygon([{points_str}]);
            translate([0, 0, {height - roof_height}])
                linear_extrude(height={roof_height}, convexity=2)
                    offset(r=-{setback}) polygon([{points_str}]);
        }}"""

    def _stepped_roof(self, points_str, height, params):
        levels = params.get('levels', 2)
        step_height = height / (levels + 1)
        return f"""union() {{
            linear_extrude(height={step_height}, convexity=2) polygon([{points_str}]);
            {" ".join(self._step_sections(points_str, step_height, levels))}
        }}"""

    def _step_sections(self, points_str, step_height, levels):
        return [f"""
            translate([0, 0, {step_height * (i + 1)}])
                linear_extrude(height={step_height}, convexity=2)
                    offset(r=-{2.0 + (i * 1.5)}) polygon([{points_str}]);"""
            for i in range(levels)]