# lib/preprocessor.py (new file)

from copy import deepcopy
from math import radians, cos, sin, sqrt
import statistics
import json

class GeoJSONPreprocessor:
    def __init__(self, bbox=None, distance_meters=None):
        self.bbox = bbox  # [south, west, north, east]
        self.distance = distance_meters
        self.debug = True

    def is_within_bbox(self, lon, lat):
        """Check if a point is within the bounding box"""
        if not self.bbox:
            return True
        south, west, north, east = self.bbox
        return west <= lon <= east and south <= lat <= north

    def is_within_distance(self, lon, lat, center_lon, center_lat):
        """Check if a point is within the distance bounds from center"""
        if not self.distance:
            return True
        meters_per_degree = 111319.9
        lat_rad = radians(lat)
        x = (lon - center_lon) * meters_per_degree * cos(lat_rad)
        y = (lat - center_lat) * meters_per_degree
        distance = sqrt(x*x + y*y)
        return distance <= self.distance

    def is_within_bounds(self, lon, lat, center_lon=None, center_lat=None):
        """Check if a point is within either bbox or distance bounds"""
        bbox_check = self.is_within_bbox(lon, lat)
        if center_lon is not None and center_lat is not None and self.distance:
            distance_check = self.is_within_distance(lon, lat, center_lon, center_lat)
            return bbox_check and distance_check
        return bbox_check

    def extract_coordinates(self, feature):
        """Extract all coordinates from a feature regardless of geometry type"""
        geometry = feature['geometry']
        coords = []
        
        if geometry['type'] == 'Point':
            coords = [geometry['coordinates']]
        elif geometry['type'] == 'LineString':
            coords = geometry['coordinates']
        elif geometry['type'] == 'Polygon':
            for ring in geometry['coordinates']:
                coords.extend(ring)
        elif geometry['type'] == 'MultiPolygon':
            for polygon in geometry['coordinates']:
                for ring in polygon:
                    coords.extend(ring)
        elif geometry['type'] == 'MultiLineString':
            for line in geometry['coordinates']:
                coords.extend(line)
                
        return coords

    def crop_feature(self, feature, center_lon=None, center_lat=None):
        """Crop a feature to the bounded area"""
        geometry = feature['geometry']
        
        if geometry['type'] == 'Point':
            lon, lat = geometry['coordinates']
            if self.is_within_bounds(lon, lat, center_lon, center_lat):
                return feature
            return None
            
        elif geometry['type'] == 'LineString':
            new_coords = [
                coord for coord in geometry['coordinates']
                if self.is_within_bounds(coord[0], coord[1], center_lon, center_lat)
            ]
            if len(new_coords) >= 2:
                new_feature = deepcopy(feature)
                new_feature['geometry']['coordinates'] = new_coords
                return new_feature
            return None
            
        elif geometry['type'] in ['Polygon', 'MultiPolygon']:
            def crop_polygon(coords):
                new_coords = [
                    coord for coord in coords
                    if self.is_within_bounds(coord[0], coord[1], center_lon, center_lat)
                ]
                if len(new_coords) >= 3:
                    if new_coords[0] != new_coords[-1]:
                        new_coords.append(new_coords[0])
                    return new_coords
                return None

            if geometry['type'] == 'Polygon':
                new_exterior = crop_polygon(geometry['coordinates'][0])
                if new_exterior:
                    new_feature = deepcopy(feature)
                    new_feature['geometry']['coordinates'] = [new_exterior]
                    return new_feature
                    
            else:  # MultiPolygon
                new_polygons = []
                for polygon in geometry['coordinates']:
                    new_poly = crop_polygon(polygon[0])
                    if new_poly:
                        new_polygons.append([new_poly])
                if new_polygons:
                    new_feature = deepcopy(feature)
                    new_feature['geometry']['coordinates'] = new_polygons
                    return new_feature
                    
        return None

    def process_geojson(self, input_data):
        """Process the GeoJSON data"""
        center_lon = center_lat = None
        if self.distance:
            # If using distance, calculate center from features
            all_coords = []
            for feature in input_data['features']:
                coords = self.extract_coordinates(feature)
                all_coords.extend(coords)
                
            if not all_coords:
                raise ValueError("No coordinates found in features")
                
            lons, lats = zip(*all_coords)
            center_lon = statistics.median(lons)
            center_lat = statistics.median(lats)
            
            if self.debug:
                print(f"Using center point: {center_lon:.6f}, {center_lat:.6f}")
        elif self.bbox:
            if self.debug:
                print(f"Using bounding box: {self.bbox}")
        
        # Crop features
        new_features = []
        for feature in input_data['features']:
            cropped = self.crop_feature(feature, center_lon, center_lat)
            if cropped:
                new_features.append(cropped)
                
        if self.debug:
            print(f"Original features: {len(input_data['features'])}")
            print(f"Cropped features: {len(new_features)}")
            
        # Create new GeoJSON
        output_data = {
            'type': 'FeatureCollection',
            'features': new_features
        }
        
        return output_data

def main():
    parser = argparse.ArgumentParser(description='Preprocess GeoJSON for 3D city modeling')
    parser.add_argument('input_file', help='Input GeoJSON file')
    parser.add_argument('output_file', help='Output GeoJSON file')
    parser.add_argument('--distance', type=float,
                      help='Distance in meters from center to crop')
    parser.add_argument('--bbox', type=float, nargs=4,
                      metavar=('SOUTH', 'WEST', 'NORTH', 'EAST'),
                      help='Bounding box coordinates (south west north east)')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug output')
    
    args = parser.parse_args()
    
    if not args.distance and not args.bbox:
        parser.error("Either --distance or --bbox must be specified")
    
    try:
        # Read input file
        with open(args.input_file, 'r') as f:
            input_data = json.load(f)
            
        # Process data
        processor = GeoJSONPreprocessor(
            bbox=args.bbox if args.bbox else None,
            distance_meters=args.distance if args.distance else None
        )
        processor.debug = args.debug
        output_data = processor.process_geojson(input_data)
        
        # Write output file
        with open(args.output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
            
        print(f"Successfully processed GeoJSON data and saved to {args.output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == '__main__':
    main()