class BuildingGenerator:
    """
    Generates OpenSCAD code for buildings with clean, non-overlapping roofs
    that respect block boundaries and barriers.
    """
    
    def __init__(self, style_manager):
        self.style_manager = style_manager

    def generate_building_details(self, points_str, height, roof_style=None, roof_params=None, block_type=None):
        """Generate a building with appropriate roof style."""
        if not roof_style or not roof_params:
            return self._generate_basic_building(points_str, height)

        if roof_style == 'pitched':
            return self._generate_pitched_roof(points_str, height, roof_params)
        elif roof_style == 'tiered':
            return self._generate_tiered_roof(points_str, height, roof_params)
        elif roof_style == 'flat':
            return self._generate_flat_roof(points_str, height, roof_params)
        elif roof_style == 'sawtooth':
            return self._generate_sawtooth_roof(points_str, height, roof_params)
        elif roof_style == 'modern':
            return self._generate_modern_roof(points_str, height, roof_params)
        elif roof_style == 'complex':
            return self._generate_complex_roof(points_str, height, roof_params)
        elif roof_style == 'stepped':
            return self._generate_stepped_roof(points_str, height, roof_params)
        else:
            return self._generate_basic_building(points_str, height)

    def _generate_basic_building(self, points_str, height):
        """Generate a basic building without roof details."""
        return f"""
            linear_extrude(height={height}, convexity=2)
                polygon([{points_str}]);"""

    def _generate_pitched_roof(self, points_str, height, params):
        """Generate a pitched roof building."""
        roof_height = height * params['height_factor']
        base_height = height - roof_height
        
        return f"""
            union() {{
                // Base building
                linear_extrude(height={base_height}, convexity=2)
                    polygon([{points_str}]);
                
                // Pitched roof
                translate([0, 0, {base_height}])
                    linear_extrude(height={roof_height}, scale=0.6, convexity=2)
                        polygon([{points_str}]);
            }}"""

    def _generate_tiered_roof(self, points_str, height, params):
        """Generate a tiered roof with multiple levels."""
        num_levels = params['levels']
        level_height = height * 0.15  # Each tier is 15% of total height
        base_height = height - (level_height * num_levels)
        
        tiers = []
        for i in range(num_levels):
            offset = (i + 1) * 1.5  # Increasing inset for each tier
            tier_start = base_height + (i * level_height)
            tiers.append(f"""
                // Tier {i + 1}
                translate([0, 0, {tier_start}])
                    linear_extrude(height={level_height}, convexity=2)
                        offset(r=-{offset})
                            polygon([{points_str}]);""")
        
        return f"""
            union() {{
                // Base building
                linear_extrude(height={base_height}, convexity=2)
                    polygon([{points_str}]);
                {' '.join(tiers)}
            }}"""

    def _generate_flat_roof(self, points_str, height, params):
        """Generate a flat roof with border detail."""
        border = params['border']
        return f"""
            union() {{
                // Main building
                linear_extrude(height={height}, convexity=2)
                    polygon([{points_str}]);
                
                // Roof border
                translate([0, 0, {height}])
                    linear_extrude(height=1.0, convexity=2)
                        difference() {{
                            polygon([{points_str}]);
                            offset(r=-{border})
                                polygon([{points_str}]);
                        }}
            }}"""

    def _generate_sawtooth_roof(self, points_str, height, params):
        """Generate an industrial sawtooth roof."""
        angle = params['angle']
        tooth_height = height * 0.2
        base_height = height - tooth_height
        
        return f"""
            union() {{
                // Base building
                linear_extrude(height={base_height}, convexity=2)
                    polygon([{points_str}]);
                
                // Sawtooth roof
                translate([0, 0, {base_height}]) {{
                    intersection() {{
                        linear_extrude(height={tooth_height}, convexity=2)
                            polygon([{points_str}]);
                        
                        // Sawtooth pattern
                        rotate([{angle}, 0, 0])
                            translate([0, 0, -50])
                                linear_extrude(height=100, convexity=4)
                                    polygon([{points_str}]);
                    }}
                }}
            }}"""

    def _generate_modern_roof(self, points_str, height, params):
        """Generate a modern style roof with setback."""
        setback = params['setback']
        top_height = height * 0.2
        base_height = height - top_height
        
        return f"""
            union() {{
                // Base building
                linear_extrude(height={base_height}, convexity=2)
                    polygon([{points_str}]);
                
                // Setback top section
                translate([0, 0, {base_height}])
                    linear_extrude(height={top_height}, convexity=2)
                        offset(r=-{setback})
                            polygon([{points_str}]);
            }}"""

    def _generate_complex_roof(self, points_str, height, params):
        """Generate a complex roof with multiple variations."""
        variations = params['variations']
        section_height = height * 0.15
        base_height = height - (section_height * variations)
        
        sections = []
        for i in range(variations):
            offset = 1.0 + (i * 0.8)  # Progressive offset
            section_start = base_height + (i * section_height)
            scale = 1.0 - (i * 0.15)  # Progressive scale reduction
            
            sections.append(f"""
                // Complex section {i + 1}
                translate([0, 0, {section_start}])
                    linear_extrude(height={section_height}, scale={scale}, convexity=2)
                        offset(r=-{offset})
                            polygon([{points_str}]);""")
        
        return f"""
            union() {{
                // Base building
                linear_extrude(height={base_height}, convexity=2)
                    polygon([{points_str}]);
                {' '.join(sections)}
            }}"""

    def _generate_stepped_roof(self, points_str, height, params):
        """Generate a stepped industrial roof."""
        num_levels = params['levels']
        step_height = height * 0.12
        base_height = height - (step_height * num_levels)
        
        steps = []
        for i in range(num_levels):
            offset = 2.0 + (i * 1.5)  # Increasing step size
            step_start = base_height + (i * step_height)
            steps.append(f"""
                // Step {i + 1}
                translate([0, 0, {step_start}])
                    linear_extrude(height={step_height}, convexity=2)
                        offset(r=-{offset})
                            polygon([{points_str}]);""")
        
        return f"""
            union() {{
                // Base building
                linear_extrude(height={base_height}, convexity=2)
                    polygon([{points_str}]);
                {' '.join(steps)}
            }}"""