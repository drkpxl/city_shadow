# geojson_to_shadow_city.py - Main entry point
import argparse
from lib.converter import EnhancedCityConverter

def main():
    parser = argparse.ArgumentParser(
        description='Convert GeoJSON to artistic 3D city model'
    )
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
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug output')
    
    args = parser.parse_args()
    
    # Configure style settings
    style_settings = {
        'artistic_style': args.style,
        'detail_level': args.detail,
        'merge_distance': args.merge_distance,
        'cluster_size': args.cluster_size,
        'height_variance': args.height_variance
    }
    
    converter = EnhancedCityConverter(
        size_mm=args.size,
        max_height_mm=args.height,
        style_settings=style_settings
    )
    
    # Update feature specifications
    converter.layer_specs['roads']['width'] = args.road_width
    converter.layer_specs['water']['depth'] = args.water_depth
    converter.debug = args.debug
    
    converter.convert(args.input_json, args.output_scad)

if __name__ == '__main__':
    main()