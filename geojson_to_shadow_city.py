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