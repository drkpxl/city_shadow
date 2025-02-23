#!/usr/bin/env python3
import argparse
import time
from lib.converter import EnhancedCityConverter
from lib.preprocessor import GeoJSONPreprocessor
from lib.preview.openscad_integration import OpenSCADIntegration


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
        "--style",
        choices=["modern", "classic", "minimal", "block-combine"],
        default="modern",
        help="Artistic style",
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
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

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
        # Initialize style settings
        style_settings = {
            "artistic_style": args.style,
            "detail_level": args.detail,
            "merge_distance": args.merge_distance,
            "cluster_size": args.cluster_size,
            "height_variance": args.height_variance,
            "min_building_area": args.min_building_area,
            "bridge_height": args.bridge_height,
            "bridge_thickness": args.bridge_thickness,
            "support_width": args.support_width,
        }

        # Create converter instance
        converter = EnhancedCityConverter(
            size_mm=args.size, max_height_mm=args.height, style_settings=style_settings
        )

        # Update feature specifications
        converter.layer_specs["roads"]["width"] = args.road_width
        converter.layer_specs["water"]["depth"] = args.water_depth
        converter.debug = args.debug

        # Preprocess if requested
        if args.preprocess:
            if not (args.crop_distance or args.crop_bbox):
                parser.error(
                    "When --preprocess is enabled, either --crop-distance or --crop-bbox must be specified"
                )

            preprocessor = GeoJSONPreprocessor(
                bbox=args.crop_bbox, distance_meters=args.crop_distance
            )
            preprocessor.debug = args.debug

            # Process and pass the data directly to converter
            converter.convert_preprocessed(
                args.input_json, args.output_scad, preprocessor
            )
        else:
            # Standard conversion without preprocessing
            converter.convert(args.input_json, args.output_scad)
        # Set up OpenSCAD integration
        integration = OpenSCADIntegration()

        # Generate preview images with fixed size
        preview_file = args.output_scad.replace(".scad", "_preview.png")
        print("\nGenerating preview image...")
        integration.generate_preview(
            args.output_scad, preview_file, size=[1080, 1080]
        )

        # Generate STL files
        print("\nGenerating STL files...")
        stl_file = args.output_scad.replace(".scad", ".stl")
        integration.generate_stl(args.output_scad, stl_file)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()