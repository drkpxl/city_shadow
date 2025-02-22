# lib/scad_generator.py
from .geometry import GeometryUtils

class ScadGenerator:
    def __init__(self, style_manager):
        self.style_manager = style_manager
        self.geometry = GeometryUtils()

    def generate_openscad(self, features, size, layer_specs):
        """Generate complete OpenSCAD code for main model without frame"""
        # Start with header and base
        scad = self._generate_header(size, layer_specs)
        
        # Add features
        scad.extend(self._generate_water_features(features['water'], layer_specs))
        scad.append('        }')  # Close water features union
        scad.extend(self._generate_road_features(features['roads'], layer_specs))
        scad.extend(self._generate_railway_features(features['railways'], layer_specs))
        scad.append('    }')  # Close main difference
        scad.extend(self._generate_building_features(features['buildings'], layer_specs))
        
        # Close main union
        scad.append('}')
        return '\n'.join(scad)

    def _generate_header(self, size, layer_specs):
        """Generate OpenSCAD file header and base structure"""
        return [
            f'''// Generated with Enhanced City Converter
// Style: {self.style_manager.style['artistic_style']}
// Detail Level: {self.style_manager.style['detail_level']}

// Main city model without frame
union() {{
    difference() {{
        // Base
        cube([{size}, {size}, {layer_specs['base']['height']}]);
        
        // Start features
        union() {{'''
        ]

    def _generate_water_features(self, water_features, layer_specs):
        """Generate OpenSCAD code for water features"""
        scad = []
        base_height = layer_specs['base']['height']
        water_depth = layer_specs['water']['depth']
        
        for i, water in enumerate(water_features):
            points_str = self.geometry.generate_polygon_points(water)
            if points_str:
                scad.extend([
                    f'''
            // Water body {i+1}
            translate([0, 0, {base_height - water_depth}])
                linear_extrude(height={water_depth + 0.1}, convexity=2)
                    polygon([{points_str}]);'''
                ])
        
        return scad

    def _generate_road_features(self, road_features, layer_specs):
        """Generate OpenSCAD code for road features"""
        scad = []
        base_height = layer_specs['base']['height']
        road_depth = layer_specs['roads']['depth']
        road_width = layer_specs['roads']['width']
        
        for i, road in enumerate(road_features):
            if isinstance(road, dict):
                pts = road.get('coords', road)
                if road.get('is_parking'):
                    points_str = self.geometry.generate_polygon_points(pts)
                else:
                    points_str = self.geometry.generate_buffered_polygon(pts, road_width)
            else:
                pts = road
                points_str = self.geometry.generate_buffered_polygon(pts, road_width)
                
            if points_str:
                scad.extend([
                    f'''
        // Road {i+1}
        translate([0, 0, {base_height - road_depth}])
            linear_extrude(height={road_depth + 0.1}, convexity=2)
                polygon([{points_str}]);'''
                ])
        
        return scad

    def _generate_railway_features(self, railway_features, layer_specs):
        """Generate OpenSCAD code for railway features"""
        scad = []
        base_height = layer_specs['base']['height']
        railway_depth = layer_specs['railways']['depth']
        railway_width = layer_specs['railways']['width']
        
        for i, railway in enumerate(railway_features):
            points = self.geometry.generate_buffered_polygon(railway, railway_width)
            if points:
                scad.extend([
                    f'''
        // Railway {i+1}
        translate([0, 0, {base_height - railway_depth}])
            linear_extrude(height={railway_depth + 0.1}, convexity=2)
                polygon([{points}]);'''
                ])
        
        return scad

    def _generate_building_features(self, building_features, layer_specs):
        """Generate OpenSCAD code for building features"""
        scad = []
        base_height = layer_specs['base']['height']
        
        for i, building in enumerate(building_features):
            points_str = self.geometry.generate_polygon_points(building['coords'])
            if not points_str:
                continue
                
            is_cluster = building.get('is_cluster', False)
            building_height = building['height']
            
            # Generate building with appropriate style
            details = self._generate_building_details(
                points_str, 
                building_height, 
                is_cluster
            )
            
            scad.extend([
                f'''
    // {"Building Cluster" if is_cluster else "Building"} {i+1}
    translate([0, 0, {base_height}]) {{
        {details}
    }}'''
            ])
        
        return scad

    def _generate_building_details(self, points_str, height, is_cluster):
        """Generate architectural details based on style"""
        if not is_cluster or self.style_manager.style['detail_level'] < 0.5:
            return f'''
                linear_extrude(height={height}, convexity=2)
                    polygon([{points_str}]);'''
            
        if self.style_manager.style['artistic_style'] == 'modern':
            return f'''
                union() {{
                    linear_extrude(height={height}, convexity=2)
                        polygon([{points_str}]);
                    translate([0, 0, {height}])
                        linear_extrude(height=0.8, convexity=2)
                            offset(r=-0.8)
                                polygon([{points_str}]);
                }}'''
                
        elif self.style_manager.style['artistic_style'] == 'classic':
            return f'''
                union() {{
                    linear_extrude(height={height}, convexity=2)
                        polygon([{points_str}]);
                    translate([0, 0, {height * 0.8}])
                        linear_extrude(height={height * 0.2}, convexity=2)
                            offset(r=-0.5)
                                polygon([{points_str}]);
                }}'''
        
        else:  # minimal
            return f'''
                linear_extrude(height={height}, convexity=2)
                    polygon([{points_str}]);'''