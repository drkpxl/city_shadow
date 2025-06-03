#!/usr/bin/env python3
import argparse
import sys
from lib.converter import EnhancedCityConverter
from lib.preprocessor import GeoJSONPreprocessor
from lib.preview.openscad_integration import OpenSCADIntegration

def emit_progress(progress, message):
    """Emit progress updates that can be parsed by the Node.js server"""
    print(f"Progress: {progress}% - {message}", flush=True)

def main():
    parser = argparse.ArgumentParser(
        description="Convert GeoJSON to artistic 3D city model"
    )
    # Basic arguments
    parser.add_argument("input_json", help="Input GeoJSON file")
    parser.add_argument("output_scad", help="Output OpenSCAD file")
    parser.add_argument(
        "--size", type=float, default=150, help="Size in mm (default: 200)"
    )
    parser.add_argument(
        "--height", type=float, default=20, help="Maximum height in mm (default: 20)"
    )
    parser.add_argument(
        "--roof-style",
        type=str,
        default="flat,pitched,tiered,sawtooth,modern,stepped",
        help="Comma-separated list of roof styles to use",
    )
    parser.add_argument(
        "--detail", type=float, default=1.0, help="Detail level 0-2 (default: 1.0)"
    )
    parser.add_argument(
        "--merge-distance",
        type=float,
        default=2.0,
        help="Distance threshold for merging buildings (default: 2.0)",
    )
    parser.add_argument(
        "--cluster-size",
        type=float,
        default=3.0,
        help="Size threshold for building clusters (default: 3.0)",
    )
    parser.add_argument(
        "--height-variance",
        type=float,
        default=0.2,
        help="Height variation 0-1 (default: 0.2)",
    )
    parser.add_argument(
        "--road-width",
        type=float,
        default=1.2,
        help="Width of roads in mm (default: 2.0)",
    )
    parser.add_argument(
        "--water-depth",
        type=float,
        default=2,
        help="Depth of water features in mm (default: 1.4)",
    )
    parser.add_argument(
        "--min-building-area",
        type=float,
        default=600.0,
        help="Minimum building footprint area in m^2 (default: 600)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable detailed debug output")

    # Bridge parameters
    parser.add_argument(
        "--bridge-height",
        type=float,
        default=2.0,
        help="Bridge deck height above the base (default: 2.0)",
    )
    parser.add_argument(
        "--bridge-thickness",
        type=float,
        default=0.6,
        help="Bridge deck thickness (default: 1.0)",
    )
    parser.add_argument(
        "--support-width",
        type=float,
        default=2.0,
        help="Bridge support column radius (default: 2.0)",
    )

    # Preprocessing arguments
    preprocess_group = parser.add_argument_group("Preprocessing options")
    preprocess_group.add_argument(
        "--preprocess", action="store_true", help="Enable GeoJSON preprocessing"
    )
    preprocess_group.add_argument(
        "--crop-distance",
        type=float,
        help="Distance in meters from center to crop features",
    )
    preprocess_group.add_argument(
        "--crop-bbox",
        type=float,
        nargs=4,
        metavar=("SOUTH", "WEST", "NORTH", "EAST"),
        help="Bounding box coordinates for cropping",
    )

    args = parser.parse_args()

    try:
        emit_progress(0, "Starting conversion process")
        
        # Parse and validate roof styles
        valid_roof_styles = ["flat", "pitched", "tiered", "sawtooth", "modern", "stepped"]
        roof_styles = [style.strip() for style in args.roof_style.split(",") if style.strip()]
        
        # Validate roof styles
        invalid_styles = [style for style in roof_styles if style not in valid_roof_styles]
        if invalid_styles:
            parser.error(f"Invalid roof styles: {', '.join(invalid_styles)}")
        
        # If no valid styles provided, use all styles
        if not roof_styles:
            roof_styles = valid_roof_styles
            
        print(f"Using roof styles: {', '.join(roof_styles)}", flush=True)
        
        # Prepare style settings; detailed logs are only enabled if --debug is passed.
        style_settings = {
            "roof_styles": roof_styles,  # Pass as list
            "detail_level": args.detail,
            "merge_distance": args.merge_distance,
            "cluster_size": args.cluster_size,
            "height_variance": args.height_variance,
            "min_building_area": args.min_building_area,
            "bridge_height": args.bridge_height,
            "bridge_thickness": args.bridge_thickness,
            "support_width": args.support_width,
        }

        emit_progress(10, "Initializing converter")
        
        # Create the converter and explicitly set debug based on the flag.
        converter = EnhancedCityConverter(
            size_mm=args.size, max_height_mm=args.height, style_settings=style_settings
        )
        converter.debug = args.debug  # When --debug is not passed, debug is False.
        converter.layer_specs["roads"]["width"] = args.road_width
        converter.layer_specs["water"]["depth"] = args.water_depth

        emit_progress(20, "Processing GeoJSON data")
        
        # Process input data (with optional preprocessing)
        if args.preprocess:
            if not (args.crop_distance or args.crop_bbox):
                parser.error("When --preprocess is enabled, either --crop-distance or --crop-bbox must be specified")
            preprocessor = GeoJSONPreprocessor(
                bbox=args.crop_bbox, distance_meters=args.crop_distance
            )
            preprocessor.debug = args.debug
            emit_progress(30, "Preprocessing GeoJSON data")
            converter.convert_preprocessed(args.input_json, args.output_scad, preprocessor)
        else:
            converter.convert(args.input_json, args.output_scad)
        
        emit_progress(50, "GeoJSON conversion completed")

        # Print a concise summary of processed features.
        print("\nConversion complete. Processed feature counts:", flush=True)
        features = converter.style_manager.current_features
        for category, items in features.items():
            print(f"  {category}: {len(items)}", flush=True)

        # Generate preview image.
        integration = OpenSCADIntegration()
        preview_size = [600, 600]
        preview_file = args.output_scad.replace(".scad", "_preview.png")
        emit_progress(60, "Generating preview image")
        print("\nGenerating preview image...", flush=True)
        integration.generate_preview(args.output_scad, preview_file, size=preview_size)
        print(f"Preview generated successfully: {preview_file}", flush=True)
        emit_progress(80, "Preview generated")

        # Generate STL files.
        emit_progress(85, "Generating STL files")
        print("\nGenerating STL files...", flush=True)
        stl_file = args.output_scad.replace(".scad", ".stl")
        integration.generate_stl(args.output_scad, stl_file)
        emit_progress(100, "Conversion complete")

    except Exception as e:
        print(f"Error: {str(e)}", flush=True)
        raise

if __name__ == "__main__":
    main()
