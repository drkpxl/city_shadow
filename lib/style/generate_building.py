class BuildingGenerator:
    """
    Generates OpenSCAD code for buildings with various roof styles and architectural features.
    Each building is self-contained within its own coordinate space and can have unique
    characteristics based on its type and parameters.
    """
    
    def __init__(self, style_manager):
        """
        Initialize the BuildingGenerator with a style manager.
        
        Args:
            style_manager: StyleManager instance for accessing global style settings
        """
        self.style_manager = style_manager

    def generate_building_details(self, points_str, height, roof_style=None, roof_params=None, block_type=None):
        """Generate a building with proper OpenSCAD syntax."""
        # Basic building without roof
        if not roof_style or not roof_params:
            return f"linear_extrude(height={height}, convexity=2) polygon([{points_str}]);"

        # Buildings with roofs
        if roof_style == 'pitched':
            roof_height = height * roof_params['height_factor']
            base_height = height - roof_height
            return f"""union() {{
                // Base building
                linear_extrude(height={base_height}, convexity=2) 
                    polygon([{points_str}]);
                // Roof
                translate([0, 0, {base_height}])
                intersection() {{
                    linear_extrude(height={roof_height}, scale=0.6, convexity=2)
                        polygon([{points_str}]);
                    linear_extrude(height={roof_height}, convexity=2)
                        polygon([{points_str}]);
                }}
            }}"""

        elif roof_style == 'tiered':
            num_levels = roof_params['levels']
            level_height = height / (num_levels + 1)
            
            tiers = []
            for i in range(num_levels):
                start_height = level_height * (i + 1)
                inset = (i + 1) * 1.0
                tiers.append(f"""
                    translate([0, 0, {start_height}])
                    intersection() {{
                        linear_extrude(height={level_height}, convexity=2)
                            offset(r=-{inset})
                                polygon([{points_str}]);
                        linear_extrude(height={level_height}, convexity=2)
                            polygon([{points_str}]);
                    }}""")
            
            return f"""union() {{
                // Base building
                linear_extrude(height={level_height}, convexity=2)
                    polygon([{points_str}]);
                {' '.join(tiers)}
            }}"""

        # Default to basic building if roof style not handled
        return f"linear_extrude(height={height}, convexity=2) polygon([{points_str}]);"
   
    def _generate_specific_roof(self, points_str, height, roof_style, roof_params):
        """Generate a building with a specific roof style."""
        generators = {
            'pitched': self._generate_pitched_roof,
            'tiered': self._generate_tiered_roof,
            'flat': self._generate_flat_roof,
            'sawtooth': self._generate_sawtooth_roof,
            'modern': self._generate_modern_roof,
            'stepped': self._generate_stepped_roof
        }
        
        if roof_style in generators:
            return generators[roof_style](points_str, height, roof_params)
        return self._generate_basic_building(points_str, height)
    def _generate_basic_building(self, points_str, height):
        """Generate a basic building without roof details."""
        return f"""
            linear_extrude(height={height}, convexity=2)
                polygon([{points_str}]);"""

    def _generate_pitched_roof(self, points_str, height, params):
        """
        Generate a pitched roof building.
        
        The roof is created by scaling the building's top section inward and upward.
        """
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
        """
        Generate a tiered roof with multiple levels.
        
        Creates a series of progressively smaller and higher sections.
        """
        num_levels = params['levels']
        level_height = height * 0.15
        base_height = height - (level_height * num_levels)
        
        tiers = []
        for i in range(num_levels):
            offset = (i + 1) * 1.5
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
        """
        Generate a flat roof with border detail.
        
        Creates a raised border around the roof's edge.
        """
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
        """
        Generate an industrial sawtooth roof.
        
        Creates an angled pattern typical of industrial buildings.
        """
        angle = params['angle']
        tooth_height = height * 0.2
        base_height = height - tooth_height
        
        return f"""
            union() {{
                // Base building
                linear_extrude(height={base_height}, convexity=2)
                    polygon([{points_str}]);
                
                // Sawtooth roof within building boundary
                translate([0, 0, {base_height}])
                    intersection() {{
                        linear_extrude(height={tooth_height}, convexity=2)
                            polygon([{points_str}]);
                        rotate([{angle}, 0, 0])
                            translate([0, 0, -50])
                                linear_extrude(height=100, convexity=4)
                                    polygon([{points_str}]);
                    }}
            }}"""

    def _generate_modern_roof(self, points_str, height, params):
        """
        Generate a modern style roof with setback.
        
        Creates a smaller top section set back from the building's edge.
        """
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

    def _generate_stepped_roof(self, points_str, height, params):
        """
        Generate a stepped roof with multiple levels.
        
        Creates a series of progressively smaller sections stepping upward.
        """
        num_levels = params['levels']
        step_height = height * 0.12
        base_height = height - (step_height * num_levels)
        
        steps = []
        for i in range(num_levels):
            offset = 2.0 + (i * 1.5)
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

        """
        Generate a complex roof with multiple architectural features.
        
        Creates an intricate roof design with multiple elements and variations.
        """
        variations = params.get('variations', 3)
        section_height = height * 0.15
        base_height = height - (section_height * variations)
        
        sections = []
        for i in range(variations):
            offset = 1.0 + (i * 0.8)
            section_start = base_height + (i * section_height)
            scale = 1.0 - (i * 0.15)
            
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