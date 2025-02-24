# lib/geometry.py
from math import sqrt, sin, cos, pi, atan2, radians


class GeometryUtils:
    def create_coordinate_transformer(self, features, size):
        """Create a coordinate transformation function without border inset"""
        all_coords = []
        for feature in features:
            coords = self.extract_coordinates(feature)
            all_coords.extend(coords)

        if not all_coords:
            return lambda lon, lat: [size / 2, size / 2]

        # Calculate bounds
        lons, lats = zip(*all_coords)
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)

        def transform(lon, lat):
            x = (lon - min_lon) / (max_lon - min_lon) if (max_lon != min_lon) else 0.5
            y = (lat - min_lat) / (max_lat - min_lat) if (max_lat != min_lat) else 0.5
            return [x * size, y * size]

        return transform

    def extract_coordinates(self, feature):
        """Extract coordinates from GeoJSON feature"""
        geometry = feature["geometry"]
        coords = []

        if geometry["type"] == "Point":
            coords = [geometry["coordinates"]]
        elif geometry["type"] == "LineString":
            coords = geometry["coordinates"]
        elif geometry["type"] == "Polygon":
            coords = geometry["coordinates"][0]
        elif geometry["type"] == "MultiPolygon":
            # Take the largest polygon by vertex count
            largest = max(geometry["coordinates"], key=lambda p: len(p[0]))
            coords = largest[0]
        elif geometry["type"] == "MultiLineString":
            # Optionally handle multi-linestring
            # Here you might want to merge or just pick the largest ring
            # For simplicity, let's just flatten them
            for line in geometry["coordinates"]:
                coords.extend(line)

        return coords

    def calculate_centroid(self, points):
        """Calculate the centroid of a set of points"""
        x = sum(p[0] for p in points) / len(points)
        y = sum(p[1] for p in points) / len(points)
        return [x, y]

    def calculate_distance(self, p1, p2):
        """Calculate distance between two points"""
        return sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

    def calculate_polygon_area(self, points):
        """Calculate area using the shoelace formula on transformed coords"""
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
        return ", ".join(f"[{p[0]:.3f}, {p[1]:.3f}]" for p in points)

    def generate_buffered_polygon(self, points, width):
        """Generate buffered polygon for linear features"""
        if len(points) < 2:
            return None

        left_side = []
        right_side = []

        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            length = sqrt(dx * dx + dy * dy)
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
        return ", ".join(f"[{p[0]:.3f}, {p[1]:.3f}]" for p in polygon_points)

    def approximate_polygon_area_m2(self, coords):
        """Approximate the area of a lat/lon polygon in square meters"""
        if len(coords) < 3:
            return 0.0

        # Center for projection
        lons = [pt[0] for pt in coords]
        lats = [pt[1] for pt in coords]
        lon_center = sum(lons) / len(lons)
        lat_center = sum(lats) / len(lats)

        R = 6371000.0  # Earth radius in meters

        # Convert each coordinate to x, y relative to center
        xy_points = []
        for lon, lat in coords:
            x = radians(lon - lon_center) * R * cos(radians(lat_center))
            y = radians(lat - lat_center) * R
            xy_points.append((x, y))

        # Shoelace formula
        area = 0.0
        n = len(xy_points)
        for i in range(n):
            j = (i + 1) % n
            area += xy_points[i][0] * xy_points[j][1]
            area -= xy_points[j][0] * xy_points[i][1]

        return abs(area) / 2.0

    def generate_offset_line(self, points, offset):
        """
        Generate a line offset from the original line by the specified distance.
        Used for bridge railings and other parallel structures.
        
        Args:
            points: Original line points
            offset: Distance to offset (positive for left, negative for right)
            
        Returns:
            str: String representation of polygon points for OpenSCAD
        """
        if len(points) < 2:
            return None
        
        offset_points = []
        
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            length = sqrt(dx * dx + dy * dy)
            
            if length < 0.001:
                continue
                
            # Calculate perpendicular vector
            nx = -dy / length * abs(offset)
            ny = dx / length * abs(offset)
            
            # Adjust direction based on offset sign
            if offset < 0:
                nx, ny = -nx, -ny
                
            # Add offset point
            offset_points.append([p1[0] + nx, p1[1] + ny])
            
            # Add last point for last segment
            if i == len(points) - 2:
                offset_points.append([p2[0] + nx, p2[1] + ny])
        
        if len(offset_points) < 2:
            return None
            
        # Create railing with width
        railing_width = 0.3  # Width of the railing
        
        # Calculate perpendicular points to give the railing thickness
        final_points = []
        
        for i in range(len(offset_points)):
            p = offset_points[i]
            
            # For first or last point, calculate perpendicular using the connecting segment
            if i == 0:
                next_p = offset_points[i+1]
                dx = next_p[0] - p[0]
                dy = next_p[1] - p[1]
            elif i == len(offset_points) - 1:
                prev_p = offset_points[i-1]
                dx = p[0] - prev_p[0]
                dy = p[1] - prev_p[1]
            else:
                # For middle points, use average direction
                prev_p = offset_points[i-1]
                next_p = offset_points[i+1]
                dx1 = p[0] - prev_p[0]
                dy1 = p[1] - prev_p[1]
                dx2 = next_p[0] - p[0]
                dy2 = next_p[1] - p[1]
                dx = (dx1 + dx2) / 2
                dy = (dy1 + dy2) / 2
            
            # Normalize and calculate perpendicular
            length = sqrt(dx * dx + dy * dy)
            if length < 0.001:
                continue
                
            nx = -dy / length * railing_width / 2
            ny = dx / length * railing_width / 2
            
            # Add both sides of the railing
            final_points.append([p[0] + nx, p[1] + ny])
        
        # Add points in reverse order to complete the polygon
        for i in range(len(offset_points) - 1, -1, -1):
            p = offset_points[i]
            
            if i == 0:
                next_p = offset_points[i+1]
                dx = next_p[0] - p[0]
                dy = next_p[1] - p[1]
            elif i == len(offset_points) - 1:
                prev_p = offset_points[i-1]
                dx = p[0] - prev_p[0]
                dy = p[1] - prev_p[1]
            else:
                prev_p = offset_points[i-1]
                next_p = offset_points[i+1]
                dx1 = p[0] - prev_p[0]
                dy1 = p[1] - prev_p[1]
                dx2 = next_p[0] - p[0]
                dy2 = next_p[1] - p[1]
                dx = (dx1 + dx2) / 2
                dy = (dy1 + dy2) / 2
            
            length = sqrt(dx * dx + dy * dy)
            if length < 0.001:
                continue
                
            nx = -dy / length * railing_width / 2
            ny = dx / length * railing_width / 2
            
            final_points.append([p[0] - nx, p[1] - ny])
        
        # Format as polygon points string
        return ", ".join(f"[{p[0]:.3f}, {p[1]:.3f}]" for p in final_points)