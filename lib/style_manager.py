# lib/style_manager.py
from math import log10, sin, cos, pi, atan2
from .geometry import GeometryUtils

class StyleManager:
    def __init__(self, style_settings=None):
        self.border_width = 5
        self.base_height = 10
        self.geometry = GeometryUtils()
        
        # Default style settings
        self.style = {
            'merge_distance': 2.0,
            'cluster_size': 3.0,
            'height_variance': 0.2,
            'detail_level': 1.0,
            'artistic_style': 'modern'
        }
        
        # Override defaults with provided settings
        if style_settings:
            self.style.update(style_settings)

    def get_default_layer_specs(self):
        """Get default layer specifications"""
        return {
            'water': {
                'depth': 2,
                'inset': self.border_width
            },
            'roads': {
                'depth': 1.4,
                'width': 2.0,
                'inset': self.border_width
            },
            'railways': {
                'depth': 1.4,
                'width': 1.5,
                'inset': self.border_width
            },
            'buildings': {
                'min_height': 2,
                'max_height': 6
            },
            'base': {
                'height': self.base_height,
                'inset': self.border_width
            }
        }

    def get_border_width(self):
        """Get border width setting"""
        return self.border_width

    def scale_building_height(self, properties):
        """Scale building height using log scaling"""
        default_height = 5
        
        height_m = None
        if 'height' in properties:
            try:
                height_m = float(properties['height'].split()[0])
            except (ValueError, IndexError):
                pass
        elif 'building:levels' in properties:
            try:
                levels = float(properties['building:levels'])
                height_m = levels * 3
            except ValueError:
                pass
        
        height_m = height_m if height_m is not None else default_height
            
        min_height = self.get_default_layer_specs()['buildings']['min_height']
        max_height = self.get_default_layer_specs()['buildings']['max_height']
        
        log_height = log10(height_m + 1)
        log_min = log10(1)
        log_max = log10(101)
        
        scaled_height = (log_height - log_min) / (log_max - log_min)
        final_height = min_height + scaled_height * (max_height - min_height)
        
        return round(final_height, 2)

    def merge_nearby_buildings(self, buildings):
        """Merge buildings that are close to each other into clusters"""
        clusters = []
        processed = set()
        
        for i, building in enumerate(buildings):
            if i in processed:
                continue
                
            cluster = [building]
            processed.add(i)
            
            # Find nearby buildings
            center = self.geometry.calculate_centroid(building['coords'])
            
            for j, other in enumerate(buildings):
                if j in processed:
                    continue
                    
                other_center = self.geometry.calculate_centroid(other['coords'])
                distance = self.geometry.calculate_distance(center, other_center)
                
                if distance < self.style['merge_distance']:
                    cluster.append(other)
                    processed.add(j)
            
            clusters.append(self._merge_building_cluster(cluster))
        
        return clusters

    def _merge_building_cluster(self, cluster):
        """Merge a cluster of buildings into a single artistic structure"""
        if len(cluster) == 1:
            return cluster[0]
            
        # Calculate weighted height for the cluster
        total_area = 0
        weighted_height = 0
        for building in cluster:
            area = self.geometry.calculate_polygon_area(building['coords'])
            total_area += area
            weighted_height += building['height'] * area
        
        avg_height = weighted_height / total_area if total_area > 0 else cluster[0]['height']
        
        # Combine polygons with artistic variation
        combined_coords = []
        for building in cluster:
            coords = building['coords']
            varied_coords = self._add_artistic_variation(coords)
            combined_coords.extend(varied_coords)
        
        # Create hull around combined coordinates
        hull = self._create_artistic_hull(combined_coords)
        
        return {
            'coords': hull,
            'height': avg_height,
            'is_cluster': True,
            'size': len(cluster)
        }

    def _add_artistic_variation(self, coords):
        """Add variations to building coordinates based on artistic style"""
        varied = []
        variance = self.style['height_variance']
        
        if self.style['artistic_style'] == 'modern':
            # Add angular variations
            for i, coord in enumerate(coords):
                x, y = coord
                offset = variance * sin(i * pi / len(coords))
                varied.append([x + offset, y + offset])
        
        elif self.style['artistic_style'] == 'classic':
            # Add curved variations
            for i, coord in enumerate(coords):
                x, y = coord
                angle = 2 * pi * i / len(coords)
                offset_x = variance * cos(angle)
                offset_y = variance * sin(angle)
                varied.append([x + offset_x, y + offset_y])
        
        else:  # minimal
            varied = coords
            
        return varied

    def _create_artistic_hull(self, points):
        """Create an artistic hull around points based on style settings"""
        if len(points) < 3:
            return points
            
        center = self.geometry.calculate_centroid(points)
        sorted_points = sorted(points, 
            key=lambda p: atan2(p[1] - center[1], p[0] - center[0]))
        
        hull = []
        detail_level = self.style['detail_level']
        
        for i in range(len(sorted_points)):
            p1 = sorted_points[i]
            p2 = sorted_points[(i + 1) % len(sorted_points)]
            
            hull.append(p1)
            
            if detail_level > 0.5:
                # Add intermediate points for visual interest
                dist = self.geometry.calculate_distance(p1, p2)
                if dist > self.style['cluster_size']:
                    # Number of intermediate points based on detail level
                    num_points = int(detail_level * dist / self.style['cluster_size'])
                    for j in range(num_points):
                        t = (j + 1) / (num_points + 1)
                        mid_x = p1[0] + t * (p2[0] - p1[0])
                        mid_y = p1[1] + t * (p2[1] - p1[1])
                        offset = self.style['height_variance'] * sin(t * pi)
                        hull.append([mid_x + offset, mid_y - offset])
        
        return hull