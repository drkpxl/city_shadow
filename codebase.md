# __init__.py

```py

```

# .gitignore

```
codebase.md
.aidigestignore
*.log

```

# geojson_to_shadow_city.py

```py
# geojson_to_shadow_city.py

import argparse
import time
from lib.converter import EnhancedCityConverter
from lib.preprocessor import GeoJSONPreprocessor
from lib.preview import OpenSCADIntegration

def main():
    parser = argparse.ArgumentParser(
        description='Convert GeoJSON to artistic 3D city model'
    )
    # Existing arguments
    parser.add_argument('input_json', help='Input GeoJSON file')
    parser.add_argument('output_scad', help='Output OpenSCAD file')
    parser.add_argument('--size', type=float, default=200,
                        help='Size in mm (default: 200)')
    parser.add_argument('--height', type=float, default=20,
                        help='Maximum height in mm (default: 20)')
    parser.add_argument('--style', choices=['modern', 'classic', 'minimal'],
                        default='modern', help='Artistic style')
    parser.add_argument('--detail', type=float, default=1.0,
                        help='Detail level 0-2 (default: 1.0)')
    parser.add_argument('--merge-distance', type=float, default=2.0,
                        help='Distance threshold for merging buildings (default: 2.0)')
    parser.add_argument('--cluster-size', type=float, default=3.0,
                        help='Size threshold for building clusters (default: 3.0)')
    parser.add_argument('--height-variance', type=float, default=0.2,
                        help='Height variation 0-1 (default: 0.2)')
    parser.add_argument('--road-width', type=float, default=2.0,
                        help='Width of roads in mm (default: 2.0)')
    parser.add_argument('--water-depth', type=float, default=1.4,
                        help='Depth of water features in mm (default: 1.4)')
    parser.add_argument('--min-building-area', type=float, default=600.0,
                        help='Minimum building footprint area in m^2 (default: 600)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug output')

    # Preprocessing arguments
    preprocess_group = parser.add_argument_group('Preprocessing options')
    preprocess_group.add_argument('--preprocess', action='store_true',
                               help='Enable GeoJSON preprocessing')
    preprocess_group.add_argument('--crop-distance', type=float,
                               help='Distance in meters from center to crop features')
    preprocess_group.add_argument('--crop-bbox', type=float, nargs=4,
                               metavar=('SOUTH', 'WEST', 'NORTH', 'EAST'),
                               help='Bounding box coordinates for cropping')

    # New preview and integration arguments
    preview_group = parser.add_argument_group('Preview and Integration')
    preview_group.add_argument('--preview', action='store_true',
                            help='Generate PNG preview of the model')
    preview_group.add_argument('--preview-size', type=int, nargs=2, 
                            metavar=('WIDTH', 'HEIGHT'),
                            default=[800, 600],
                            help='Preview image size in pixels')
    preview_group.add_argument('--watch', action='store_true',
                            help='Watch SCAD file and auto-reload in OpenSCAD')
    preview_group.add_argument('--openscad-path',
                            help='Path to OpenSCAD executable')

    args = parser.parse_args()

    try:
        # Initialize style settings
        style_settings = {
            'artistic_style': args.style,
            'detail_level': args.detail,
            'merge_distance': args.merge_distance,
            'cluster_size': args.cluster_size,
            'height_variance': args.height_variance,
            'min_building_area': args.min_building_area
        }

        # Create converter instance
        converter = EnhancedCityConverter(
            size_mm=args.size,
            max_height_mm=args.height,
            style_settings=style_settings
        )

        # Update feature specifications
        converter.layer_specs['roads']['width'] = args.road_width
        converter.layer_specs['water']['depth'] = args.water_depth
        converter.debug = args.debug

        # Preprocess if requested
        if args.preprocess:
            if not (args.crop_distance or args.crop_bbox):
                parser.error("When --preprocess is enabled, either --crop-distance or --crop-bbox must be specified")
            
            preprocessor = GeoJSONPreprocessor(
                bbox=args.crop_bbox,
                distance_meters=args.crop_distance
            )
            preprocessor.debug = args.debug
            
            # Process and pass the data directly to converter
            converter.convert_preprocessed(args.input_json, args.output_scad, preprocessor)
        else:
            # Standard conversion without preprocessing
            converter.convert(args.input_json, args.output_scad)

        # Handle preview and integration features
        if args.preview or args.watch:
            try:
                integration = OpenSCADIntegration(args.openscad_path)
                
                if args.preview:
                    preview_file = args.output_scad.replace('.scad', '_preview.png')
                    print(f"\nGenerating preview image: {preview_file}")
                    integration.generate_preview(
                        args.output_scad,
                        preview_file,
                        args.preview_size
                    )
                    
                if args.watch:
                    print("\nStarting OpenSCAD integration...")
                    print("Press Ctrl+C to stop watching")
                    integration.watch_and_reload(args.output_scad)
                    try:
                        while True:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        integration.stop_watching()
                        print("\nStopped watching SCAD file")
            
            except Exception as e:
                print(f"Warning: Preview/integration features failed: {e}")
                if args.watch:
                    print("Try opening OpenSCAD manually")

    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == '__main__':
    main()
```

# lib/__init__.py

```py

```

# lib/converter.py

```py
# lib/converter.py
import json
from .feature_processor import FeatureProcessor
from .scad_generator import ScadGenerator
from .style_manager import StyleManager

class EnhancedCityConverter:
    def __init__(self, size_mm=200, max_height_mm=20, style_settings=None):
        self.size = size_mm
        self.max_height = max_height_mm
        self.style_manager = StyleManager(style_settings)
        self.feature_processor = FeatureProcessor(self.style_manager)
        self.scad_generator = ScadGenerator(self.style_manager)
        self.debug = True
        self.debug_log = []
        
        # Initialize layer specifications
        self.layer_specs = self.style_manager.get_default_layer_specs()

    def print_debug(self, *args):
        """Log debug messages"""
        message = " ".join(str(arg) for arg in args)
        if self.debug:
            print(message)
            self.debug_log.append(message)

    def convert(self, input_file, output_file):
        """Convert GeoJSON to separate OpenSCAD files for main model and frame"""
        try:
            # Read input file
            with open(input_file) as f:
                data = json.load(f)
            
            # Process features
            self.print_debug("\nProcessing features...")
            features = self.feature_processor.process_features(data, self.size)
            
            # Generate main model SCAD code
            self.print_debug("\nGenerating main model OpenSCAD code...")
            main_scad = self.scad_generator.generate_openscad(
                features, 
                self.size, 
                self.layer_specs
            )
            
            # Generate frame SCAD code
            self.print_debug("\nGenerating frame OpenSCAD code...")
            frame_scad = self._generate_frame(self.size, self.max_height)
            
            # Determine output filenames
            main_file = output_file.replace('.scad', '_main.scad')
            frame_file = output_file.replace('.scad', '_frame.scad')
            
            # Write main model
            with open(main_file, 'w') as f:
                f.write(main_scad)
            
            # Write frame
            with open(frame_file, 'w') as f:
                f.write(frame_scad)
            
            self.print_debug(f"\nSuccessfully created main model: {main_file}")
            self.print_debug(f"Successfully created frame: {frame_file}")
            self.print_debug("Style settings used:")
            for key, value in self.style_manager.style.items():
                self.print_debug(f"  {key}: {value}")
            
            # Write debug log if needed
            if self.debug:
                log_file = output_file + '.log'
                with open(log_file, 'w') as f:
                    f.write('\n'.join(self.debug_log))
                self.print_debug(f"\nDebug log written to {log_file}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            raise

    def convert_preprocessed(self, input_file, output_file, preprocessor):
        """Convert GeoJSON to OpenSCAD with preprocessing"""
        try:
            # Read input file
            with open(input_file) as f:
                data = json.load(f)
            
            # Preprocess the data
            self.print_debug("\nPreprocessing GeoJSON data...")
            processed_data = preprocessor.process_geojson(data)
            
            # Process features
            self.print_debug("\nProcessing features...")
            features = self.feature_processor.process_features(processed_data, self.size)
            
            # Generate main model SCAD code
            self.print_debug("\nGenerating main model OpenSCAD code...")
            main_scad = self.scad_generator.generate_openscad(
                features, 
                self.size, 
                self.layer_specs
            )
            
            # Generate frame SCAD code
            self.print_debug("\nGenerating frame OpenSCAD code...")
            frame_scad = self._generate_frame(self.size, self.max_height)
            
            # Determine output filenames
            main_file = output_file.replace('.scad', '_main.scad')
            frame_file = output_file.replace('.scad', '_frame.scad')
            
            # Write main model
            with open(main_file, 'w') as f:
                f.write(main_scad)
            
            # Write frame
            with open(frame_file, 'w') as f:
                f.write(frame_scad)
            
            self.print_debug(f"\nSuccessfully created main model: {main_file}")
            self.print_debug(f"Successfully created frame: {frame_file}")
            self.print_debug("Style settings used:")
            for key, value in self.style_manager.style.items():
                self.print_debug(f"  {key}: {value}")
            
            # Write debug log if needed
            if self.debug:
                log_file = output_file + '.log'
                with open(log_file, 'w') as f:
                    f.write('\n'.join(self.debug_log))
                self.print_debug(f"\nDebug log written to {log_file}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            raise

    def _generate_frame(self, size, height):
        """
        Generate a frame that will fit around the main model.
        The frame's inner dimensions match the main model size exactly,
        with a 5mm border around all sides.
        """
        frame_size = size + 10  # Add 10mm to total size (5mm on each side)
        return f"""// Frame for city model
// Outer size: {frame_size}mm x {frame_size}mm x {height}mm
// Inner size: {size}mm x {size}mm x {height}mm
// Frame width: 5mm

difference() {{
    // Outer block (10mm larger than main model)
    cube([{frame_size}, {frame_size}, {height}]);
    
    // Inner cutout (sized to match main model exactly)
    translate([5, 5, 0])
        cube([{size}, {size}, {height}]);
}}"""
```

# lib/feature_processor.py

```py
# lib/feature_processor.py
from .geometry import GeometryUtils

class FeatureProcessor:
    def __init__(self, style_manager):
        self.style_manager = style_manager
        self.geometry = GeometryUtils()

    def process_features(self, geojson_data, size):
        """Process and enhance GeoJSON features"""
        transform = self.geometry.create_coordinate_transformer(
            geojson_data['features'],
            size
        )
        
        features = {
            'water': [],
            'roads': [],
            'railways': [],
            'buildings': []
        }
        
        # Process each feature type
        for feature in geojson_data['features']:
            self._process_single_feature(feature, features, transform)
        
        # Apply building merging/clustering
        features['buildings'] = self.style_manager.merge_nearby_buildings(features['buildings'])
        
        return features

    def _process_single_feature(self, feature, features, transform):
        """Process a single GeoJSON feature"""
        props = feature.get('properties', {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return
            
        # If this is a building, check area:
        if 'building' in props:
            area_m2 = self.geometry.approximate_polygon_area_m2(coords)
            min_area = self.style_manager.style.get('min_building_area', 600.0)
            
            if area_m2 < min_area:
                return  # skip small buildings
            
            # Otherwise, transform coordinates and store the building
            transformed = [transform(lon, lat) for lon, lat in coords]
            height = self.style_manager.scale_building_height(props)
            features['buildings'].append({
                'coords': transformed,
                'height': height
            })
        # Handle parking features explicitly
        elif props.get('amenity') == 'parking' or props.get('parking') == 'surface' or props.get('service') == 'parking_aisle':
            transformed = [transform(lon, lat) for lon, lat in coords]
            features['roads'].append({
                'coords': transformed,
                'is_parking': True
            })
        elif 'highway' in props:
            transformed = [transform(lon, lat) for lon, lat in coords]
            features['roads'].append({
                'coords': transformed,
                'is_parking': False
            })
        elif 'railway' in props:
            transformed = [transform(lon, lat) for lon, lat in coords]
            features['railways'].append(transformed)
        elif 'natural' in props and props['natural'] == 'water':
            transformed = [transform(lon, lat) for lon, lat in coords]
            features['water'].append(transformed)
```

# lib/geometry.py

```py
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
            return lambda lon, lat: [size/2, size/2]

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
        """Calculate area using the shoelace formula on transformed coordinates"""
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
```

# lib/preprocessor.py

```py
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
```

# lib/preview.py

```py
import subprocess
import os
import sys
import tempfile
import threading
import time
from PIL import Image, ImageEnhance
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class OpenSCADIntegration:
    def __init__(self, openscad_path=None):
        """Initialize OpenSCAD integration with an optional path to the OpenSCAD executable."""
        self.openscad_path = openscad_path or self._find_openscad()
        if not self.openscad_path:
            raise RuntimeError("Could not find OpenSCAD executable")
            
        # For file watching
        self.observer = None
        self.watch_thread = None
        self.running = False

    def _find_openscad(self):
        """Find the OpenSCAD executable based on the current platform."""
        if sys.platform == "win32":
            possible_paths = [
                r"C:\Program Files\OpenSCAD\openscad.exe",
                r"C:\Program Files (x86)\OpenSCAD\openscad.exe",
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
        elif sys.platform == "darwin":
            possible_paths = [
                "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD",
                os.path.expanduser("~/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
        else:  # Linux
            try:
                return subprocess.check_output(["which", "openscad"]).decode().strip()
            except subprocess.CalledProcessError:
                pass
        return None

    def generate_preview(self, output_file, output_image, size=(1920, 1080)):
        """
        Generate a PNG preview of the main SCAD file (output_main.scad) using a shell command.
        
        This method assumes that the conversion process produces two SCAD files:
          - output_main.scad (the main 3D model)
          - output_frame.scad (the decorative frame)
          
        It derives the main file by replacing '.scad' with '_main.scad' in the provided output_file.
        """
        # Derive the main SCAD file from the provided output file.
        main_scad_file = output_file.replace('.scad', '_main.scad')
        main_scad_file = os.path.abspath(main_scad_file)
        output_image = os.path.abspath(output_image)
        print("SCAD file path:", main_scad_file)
        print("Output image path:", output_image)

        # Set environment variable explicitly
        env = os.environ.copy()
        env["OPENSCAD_HEADLESS"] = "1"

        # Build the command (adjust the image size if needed)
        command = [
            self.openscad_path,
            '--render',
            '--imgsize', f'{size[0]},{size[1]}',
            '--autocenter',
            '--colorscheme=Nature',
            '-o', output_image,
            main_scad_file
        ]

        print("Running command:", " ".join(command))
        try:
            result = subprocess.run(
                command,
                env=env,
                cwd=os.path.dirname(main_scad_file),
                capture_output=True,
                text=True,
                check=True
            )
            print("Subprocess stdout:", result.stdout)
            print("Subprocess stderr:", result.stderr)
            print(f"Preview image generated: {output_image}")
        except subprocess.CalledProcessError as e:
            print("Error generating preview:", e)
            print("Subprocess stdout:", e.stdout)
            print("Subprocess stderr:", e.stderr)

    def watch_and_reload(self, scad_file):
        """Watch the SCAD file and trigger a reload in OpenSCAD when it changes."""
        if not self.openscad_path:
            raise RuntimeError("OpenSCAD not found")

        # First, open the file in OpenSCAD.
        subprocess.Popen([self.openscad_path, scad_file])

        # Set up file watching.
        class SCDHandler(FileSystemEventHandler):
            def __init__(self, scad_path):
                self.scad_path = scad_path
                self.last_reload = 0
                self.reload_cooldown = 1.0  # seconds

            def on_modified(self, event):
                if event.src_path == self.scad_path:
                    current_time = time.time()
                    if current_time - self.last_reload >= self.reload_cooldown:
                        if sys.platform == "win32":
                            import win32gui
                            import win32con
                            def callback(hwnd, _):
                                if "OpenSCAD" in win32gui.GetWindowText(hwnd):
                                    win32gui.SetForegroundWindow(hwnd)
                                    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_F5, 0)
                            win32gui.EnumWindows(callback, None)
                        elif sys.platform == "darwin":
                            subprocess.run(["osascript", "-e", 
                                'tell application "OpenSCAD" to activate\n' +
                                'tell application "System Events"\n' +
                                'keystroke "r" using {command down}\n' +
                                'end tell'])
                        else:  # Linux
                            try:
                                subprocess.run(["xdotool", "search", "--name", "OpenSCAD", 
                                              "windowactivate", "--sync", "key", "F5"])
                            except:
                                print("Warning: xdotool not found. Auto-reload may not work on Linux.")
                        self.last_reload = current_time

        # Start watching the file.
        self.running = True
        event_handler = SCDHandler(os.path.abspath(scad_file))
        self.observer = Observer()
        self.observer.schedule(event_handler, os.path.dirname(scad_file), recursive=False)
        self.observer.start()

        def watch_thread():
            while self.running:
                time.sleep(1)
            self.observer.stop()
            self.observer.join()

        self.watch_thread = threading.Thread(target=watch_thread)
        self.watch_thread.start()

    def stop_watching(self):
        """Stop watching the SCAD file."""
        if self.running:
            self.running = False
            if self.watch_thread:
                self.watch_thread.join()
                self.watch_thread = None

```

# lib/scad_generator.py

```py
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
```

# lib/style_manager.py

```py
# lib/style_manager.py
from math import log10, sin, cos, pi, atan2
from .geometry import GeometryUtils

class StyleManager:
    def __init__(self, style_settings=None):
        self.geometry = GeometryUtils()
        
        # Default style settings
        self.style = {
            'merge_distance': 2.0,
            'cluster_size': 3.0,
            'height_variance': 0.2,
            'detail_level': 1.0,
            'artistic_style': 'modern',
            'min_building_area': 600.0
        }
        
        # Override defaults with provided settings
        if style_settings:
            self.style.update(style_settings)

    def get_default_layer_specs(self):
        """Get default layer specifications without border insets"""
        return {
            'water': {
                'depth': 2,
            },
            'roads': {
                'depth': 1,
                'width': 2.0,
            },
            'railways': {
                'depth': 1.4,
                'width': 1.5,
            },
            'buildings': {
                'min_height': 2,
                'max_height': 6
            },
            'base': {
                'height': 10,  # Base height of 10mm
            }
        }

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
        # If merge_distance is 0, skip merging entirely
        if self.style['merge_distance'] <= 0:
            return buildings
            
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
        """Add variations to building coords based on style"""
        varied = []
        variance = self.style['height_variance']
        
        if self.style['artistic_style'] == 'modern':
            # Add angular variations
            from math import sin, pi
            for i, coord in enumerate(coords):
                x, y = coord
                offset = variance * sin(i * pi / len(coords))
                varied.append([x + offset, y + offset])
        
        elif self.style['artistic_style'] == 'classic':
            # Add curved variations
            from math import sin, cos, pi
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
            
        from math import atan2, pi, sin
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
```

# output_preview.png

This is a binary file of the type: Image

# output.png

This is a binary file of the type: Image

# output.scad.log

```log

Processing features...

Generating OpenSCAD code...

Successfully created output.scad
Style settings used:
  merge_distance: 3.0
  cluster_size: 3.0
  height_variance: 0.2
  detail_level: 0.3
  artistic_style: classic
```

# README.md

```md
# Shadow City Generator - Artist's Guide

Create beautiful, 3D-printable city maps from OpenStreetMap data. This tool generates two separate files - a main city model and a decorative frame that can be printed separately and assembled.

## Quick Start

\`\`\`bash
python geojson_to_shadow_city.py input.geojson output.scad [artistic options]
\`\`\`

This creates:
- `output_main.scad` - The city model
- `output_frame.scad` - A decorative frame that fits around the model

## Preprocessing Options

The Shadow City Generator includes preprocessing capabilities to help you refine your input data before generating the 3D model. This is particularly useful when working with large OpenStreetMap exports or when you want to focus on a specific area.

### Basic Preprocessing
\`\`\`bash
python geojson_to_shadow_city.py input.geojson output.scad --preprocess [options]
\`\`\`

### Distance-Based Cropping
Crop features to a specific radius from the center point:
\`\`\`bash
python geojson_to_shadow_city.py input.geojson output.scad \
  --preprocess \
  --crop-distance 1000  # Crop to 1000 meters from center
\`\`\`

### Bounding Box Cropping
Crop features to a specific geographic area:
\`\`\`bash
python geojson_to_shadow_city.py input.geojson output.scad \
  --preprocess \
  --crop-bbox 51.5074 -0.1278 51.5174 -0.1178  # south west north east
\`\`\`

## Artistic Options

### Overall Style
\`\`\`bash
--style [modern|classic|minimal]
\`\`\`
- `modern`: Sharp, angular designs with contemporary architectural details
- `classic`: Softer edges with traditional architectural elements
- `minimal`: Clean, simplified shapes without additional ornamentation

### Size and Scale
\`\`\`bash
--size 200        # Size of the model in millimeters (default: 200)
--height 20       # Maximum height of buildings in millimeters (default: 20)
\`\`\`

### Detail and Complexity
\`\`\`bash
--detail 1.0      # Detail level from 0-2 (default: 1.0)
\`\`\`
Higher values add more intricate architectural details and smoother transitions between elements.

### Building Features

#### Shaping Your City's Style

The Shadow City Generator gives you powerful creative control over how buildings appear in your model. You can create everything from precise architectural reproductions to artistic interpretations of urban spaces.

#### Building Size Selection
\`\`\`bash
--min-building-area 600
\`\`\`
Think of this like adjusting the level of detail in your city:
- Low values (200-400): Include small buildings like houses and shops
- Medium values (600-800): Focus on medium-sized structures
- High values (1000+): Show only larger buildings like offices and apartments

#### Artistic Building Combinations
\`\`\`bash
--merge-distance 2.0
\`\`\`
This is where the real artistic magic happens. This setting determines how buildings flow together:
- `--merge-distance 0`: Each building stands alone - perfect for architectural studies or precise city representations
- `--merge-distance 1-2`: Nearby buildings gently blend together, creating small architectural groupings
- `--merge-distance 3-5`: Buildings flow into each other more dramatically, forming artistic interpretations of city blocks
- `--merge-distance 6+`: Creates bold, abstract representations where buildings merge into sculptural forms

Think of it like adjusting the "softness" of your city's appearance:
- Sharp and distinct: Use 0
- Gentle grouping: Use 1-2
- Flowing forms: Use 3-5
- Abstract sculpture: Use 6+

#### Height Artistry
\`\`\`bash
--height-variance 0.2
\`\`\`
This adds personality to your buildings' heights:
- `0.0`: All buildings in a group stay the same height
- `0.1-0.2`: Subtle height variations for natural feel
- `0.3-0.5`: More dramatic height differences
- `0.6+`: Bold, artistic height variations

### Road and Water Features
\`\`\`bash
--road-width 2.0          # Width of roads in millimeters (default: 2.0)
--water-depth 1.4         # Depth of water features in millimeters (default: 1.4)
\`\`\`

### Building Clusters
\`\`\`bash
--cluster-size 3.0        # Size threshold for building clusters (default: 3.0)
\`\`\`
Controls how building clusters are formed when merging nearby structures.

## Creative Examples

### Contemporary Downtown with Focused Area
\`\`\`bash
python geojson_to_shadow_city.py input.geojson output.scad \
  --preprocess \
  --crop-distance 800 \
  --style modern \
  --detail 0.5 \
  --merge-distance 0 \
  --min-building-area 1000 \
  --road-width 1.5
\`\`\`
Creates a sleek, modern cityscape focusing on an 800-meter radius from the center.

### Historic District Section
\`\`\`bash
python geojson_to_shadow_city.py input.geojson output.scad \
  --preprocess \
  --crop-bbox 51.5074 -0.1278 51.5174 -0.1178 \
  --style classic \
  --detail 1.5 \
  --merge-distance 3 \
  --min-building-area 400 \
  --height-variance 0.3
\`\`\`
Produces an organic feel with clustered buildings and traditional architectural details within a specific area.

### Minimalist Urban Plan
\`\`\`bash
python geojson_to_shadow_city.py input.geojson output.scad \
  --style minimal \
  --detail 0.3 \
  --merge-distance 0 \
  --road-width 1.5 \
  --water-depth 2
\`\`\`
Creates a stark, minimalist view emphasizing urban layout and form.

## Printing Guide

1. Print the main model (`output_main.scad`) and frame (`output_frame.scad`) separately
2. The frame has a 5mm border and will be slightly larger than the main model
3. Suggested print settings:
   - Layer height: 0.2mm for good detail
   - Consider different colors for frame and city
   - Frame often looks best in white or a contrasting color

## Workflow Tips

### For Large City Areas
1. Export your area from OpenStreetMap using Overpass Turbo
2. Use preprocessing to focus on your area of interest:
   \`\`\`bash
   python geojson_to_shadow_city.py input.geojson output.scad \
     --preprocess --crop-distance 1000
   \`\`\`
3. Adjust artistic settings and preview in OpenSCAD
4. Iterate until you achieve the desired look
5. Slice and print

### For Specific Districts
1. Export a larger area from OpenStreetMap
2. Use bounding box preprocessing to isolate your district:
   \`\`\`bash
   python geojson_to_shadow_city.py input.geojson output.scad \
     --preprocess --crop-bbox SOUTH WEST NORTH EAST
   \`\`\`
3. Fine-tune artistic settings
4. Preview and adjust as needed
5. Slice and print

## Artistic Adjustments

### For a Cleaner Look
- Increase `--min-building-area`
- Decrease `--detail`
- Use `--style minimal`
- Set `--merge-distance` to 0

### For a More Artistic Interpretation
- Increase `--merge-distance`
- Increase `--height-variance`
- Use `--style classic`
- Increase `--detail`

### For Emphasizing Urban Features
- Adjust `--road-width` to highlight street patterns
- Increase `--water-depth` to emphasize waterways
- Lower `--min-building-area` to include more architectural detail

### For a Simplified View
- Use `--style minimal`
- Set `--detail` to 0.3 or lower
- Increase `--min-building-area`
- Set `--merge-distance` to 0

## Preview and OpenSCAD Integration

The Shadow City Generator now includes features to streamline your workflow with OpenSCAD integration and preview generation.

### Quick Preview
Generate a PNG preview of your model without opening OpenSCAD:
\`\`\`bash
python geojson_to_shadow_city.py input.geojson output.scad --preview
\`\`\`

Customize preview size:
\`\`\`bash
python geojson_to_shadow_city.py input.geojson output.scad --preview --preview-size 1024 768
\`\`\`

### Auto-Reload Integration
Watch for changes and automatically reload in OpenSCAD:
\`\`\`bash
python geojson_to_shadow_city.py input.geojson output.scad --watch
\`\`\`

### Combined Workflow
Generate preview and enable auto-reload:
\`\`\`bash
python geojson_to_shadow_city.py input.geojson output.scad --preview --watch
\`\`\`

### Installation Requirements

1. Install Python dependencies:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

2. Platform-specific requirements:

#### Windows
No additional requirements (uses pywin32, installed via requirements.txt)

#### Linux
Install xdotool for auto-reload functionality:
\`\`\`bash
sudo apt-get install xdotool  # Ubuntu/Debian
sudo dnf install xdotool      # Fedora
sudo pacman -S xdotool        # Arch Linux
\`\`\`

#### macOS
No additional requirements (uses built-in osascript)

### Custom OpenSCAD Path
If OpenSCAD isn't found automatically, specify its path:
\`\`\`bash
python geojson_to_shadow_city.py input.geojson output.scad --openscad-path "/path/to/openscad"
\`\`\`

### Workflow Tips

1. **Development Workflow**
   \`\`\`bash
   python geojson_to_shadow_city.py input.geojson output.scad --watch
   \`\`\`
   - Make changes to parameters
   - See updates automatically in OpenSCAD
   - Press Ctrl+C when done

2. **Quick Iterations**
   \`\`\`bash
   python geojson_to_shadow_city.py input.geojson output.scad --preview
   \`\`\`
   - Quickly preview changes without opening OpenSCAD
   - Great for rapid parameter testing

3. **Production Workflow**
   \`\`\`bash
   python geojson_to_shadow_city.py input.geojson output.scad --preview --preview-size 1920 1080
   \`\`\`
   - Generate high-resolution previews
   - Perfect for documentation or sharing designs
\`\`\`

### 5. Installation Steps

1. Install the new Python requirements:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

2. Create the new `lib/preview.py` file with the content shown above

3. Update `geojson_to_shadow_city.py` with the new content

4. Update README.md with the new section

5. Platform-specific setup:
   - Windows: No additional steps needed
   - Linux: Install xdotool using package manager
   - macOS: No additional steps needed

The integration now provides:
- Automatic preview generation
- Auto-reload functionality
- Cross-platform support
- High-resolution preview options
- Streamlined development workflow
```

# requirements.txt

```txt
# Core requirements
argparse>=1.4.0
math>=3.8.0
json>=2.0.9

# Requirements for preview and integration
Pillow>=9.0.0  # For image handling
watchdog>=2.1.0  # For file watching
# Platform-specific requirements (comment out what you don't need):
pywin32>=228; sys_platform == 'win32'  # For Windows auto-reload
# Note: Linux requires xdotool (install via package manager)
```

