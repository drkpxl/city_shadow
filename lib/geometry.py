# lib/geometry.py
from math import sqrt, sin, cos, pi, atan2

class GeometryUtils:
    def create_coordinate_transformer(self, features, border_width, size):
        """Create a coordinate transformation function"""
        all_coords = []
        for feature in features:
            coords = self.extract_coordinates(feature)
            all_coords.extend(coords)
            
        if not all_coords:
            return lambda lon, lat: [size/2, size/2]

        # Calculate bounds and create transformer
        lons, lats = zip(*all_coords)
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        
        available_size = size - 2 * border_width
        
        def transform(lon, lat):
            x = (lon - min_lon) / (max_lon - min_lon)
            y = (lat - min_lat) / (max_lat - min_lat)
            final_x = border_width + (x * available_size)
            final_y = border_width + (y * available_size)
            return [final_x, final_y]

        return transform

    def extract_coordinates(self, feature):
        """Extract coordinates from GeoJSON feature"""
        geometry = feature['geometry']
        coords = []
        
        if geometry['type'] == 'Point':
            coords = [geometry['coordinates']]
        elif geometry['type'] == 'LineString':
            coords = geometry['coordinates']
        elif geometry['type'] == 'Polygon':
            coords = geometry['coordinates'][0]
        elif geometry['type'] == 'MultiPolygon':
            largest = max(geometry['coordinates'], key=lambda p: len(p[0]))
            coords = largest[0]
            
        return coords

    def calculate_centroid(self, points):
        """Calculate the centroid of a set of points"""
        x = sum(p[0] for p in points) / len(points)
        y = sum(p[1] for p in points) / len(points)
        return [x, y]

    def calculate_distance(self, p1, p2):
        """Calculate distance between two points"""
        return sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

    def calculate_polygon_area(self, points):
        """Calculate area of a polygon"""
        area = 0.0
        j = len(points) - 1
        for i in range(len(points)):
            area += (points[j][0] + points[i][0]) * (points[j][1] - points[i][1])
            j = i
        return abs(area) / 2.0

    def generate_polygon_points(self, points):
        """Generate polygon points string for OpenSCAD"""
        if len(points) < 3:
            return None
            
        if points[0] != points[-1]:
            points = points + [points[0]]
            
        return ', '.join(f'[{p[0]:.3f}, {p[1]:.3f}]' for p in points)

    def generate_buffered_polygon(self, points, width):
        """Generate buffered polygon for linear features"""
        if len(points) < 2:
            return None

        left_side = []
        right_side = []
        
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i+1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            length = sqrt(dx*dx + dy*dy)
            
            if length < 0.001:
                continue
                
            nx = -dy / length * width / 2
            ny = dx / length * width / 2
            
            left_side.append([p1[0] + nx, p1[1] + ny])
            right_side.append([p1[0] - nx, p1[1] - ny])
            
            if i == len(points) - 2:  # Last segment
                left_side.append([p2[0] + nx, p2[1] + ny])
                right_side.append([p2[0] - nx, p2[1] - ny])

        if len(left_side) < 2:
            return None

        polygon_points = left_side + list(reversed(right_side))
        return ', '.join(f'[{p[0]:.3f}, {p[1]:.3f}]' for p in polygon_points)

