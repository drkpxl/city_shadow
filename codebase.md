# __init__.py

```py

```

# .gitignore

```
codebase.md
.aidigestignore
*.log
node_modules/
outputs/
uploads/
```

# geojson_to_shadow_city.py

```py
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
        "--size", type=float, default=200, help="Size in mm (default: 200)"
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
        default=2.0,
        help="Width of roads in mm (default: 2.0)",
    )
    parser.add_argument(
        "--water-depth",
        type=float,
        default=1.4,
        help="Depth of water features in mm (default: 1.4)",
    )
    parser.add_argument(
        "--min-building-area",
        type=float,
        default=600.0,
        help="Minimum building footprint area in m^2 (default: 600)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    # NEW arguments for bridge parameters:
    parser.add_argument(
        "--bridge-height",
        type=float,
        default=2.0,
        help="Bridge deck height above the base (default: 2.0)",
    )
    parser.add_argument(
        "--bridge-thickness",
        type=float,
        default=1.0,
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

    # Export format group
    export_group = parser.add_argument_group("Export Options")
    export_group.add_argument(
        "--export",
        choices=["preview", "stl", "both"],
        help="Export format (preview image, STL, or both)",
    )
    export_group.add_argument(
        "--output-stl", help="Output STL filename (default: based on SCAD filename)"
    )
    export_group.add_argument(
        "--no-repair",
        action="store_true",
        help="Disable automatic geometry repair attempts",
    )
    export_group.add_argument(
        "--force",
        action="store_true",
        help="Force STL generation even if validation fails",
    )

    # Preview options
    preview_group = parser.add_argument_group("Preview and Integration")
    preview_group.add_argument(
        "--preview-size",
        type=int,
        nargs=2,
        metavar=("WIDTH", "HEIGHT"),
        default=[1080, 1080],
        help="Preview image size in pixels",
    )
    preview_group.add_argument(
        "--preview-file",
        help="Preview image filename (default: based on SCAD filename)",
    )
    preview_group.add_argument(
        "--watch",
        action="store_true",
        help="Watch SCAD file and auto-reload in OpenSCAD",
    )
    preview_group.add_argument("--openscad-path", help="Path to OpenSCAD executable")

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

            # NEW lines for bridging:
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

        # Handle exports if requested
        if args.export or args.watch:
            integration = OpenSCADIntegration(args.openscad_path)

            # Determine output filenames
            stl_file = args.output_stl or args.output_scad.replace(".scad", ".stl")
            preview_file = args.preview_file or args.output_scad.replace(
                ".scad", "_preview.png"
            )

            if args.export in ["preview", "both"]:
                print("\nGenerating preview image...")
                integration.generate_preview(
                    args.output_scad, preview_file, size=args.preview_size
                )

            if args.export in ["stl", "both"]:
                print("\nGenerating STL file...")
                try:
                    integration.generate_stl(
                        args.output_scad, stl_file, repair=not args.no_repair
                    )
                except Exception as e:
                    if args.force:
                        print(f"Warning: {str(e)}")
                        print("Forcing STL generation due to --force flag...")
                        integration.generate_stl(
                            args.output_scad, stl_file, repair=False
                        )
                    else:
                        raise

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
        print(f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()

```

# lib/__init__.py

```py

```

# lib/converter.py

```py
# lib/converter.py
import json
from .feature_processor.feature_processor import FeatureProcessor
from .scad_generator import ScadGenerator
from .style.style_manager import StyleManager


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

        # ADDED FOR BRIDGES: store user values in layer_specs
        self.layer_specs["bridges"] = {
            "height": style_settings.get("bridge_height", 2.0),
            "thickness": style_settings.get("bridge_thickness", 1.0),
            "support_width": style_settings.get("support_width", 2.0),
        }

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
                features, self.size, self.layer_specs
            )

            # Generate frame SCAD code
            self.print_debug("\nGenerating frame OpenSCAD code...")
            frame_scad = self._generate_frame(self.size, self.max_height)

            # Determine output filenames
            main_file = output_file.replace(".scad", "_main.scad")
            frame_file = output_file.replace(".scad", "_frame.scad")

            # Write main model
            with open(main_file, "w") as f:
                f.write(main_scad)

            # Write frame
            with open(frame_file, "w") as f:
                f.write(frame_scad)

            self.print_debug(f"\nSuccessfully created main model: {main_file}")
            self.print_debug(f"Successfully created frame: {frame_file}")
            self.print_debug("Style settings used:")
            for key, value in self.style_manager.style.items():
                self.print_debug(f"  {key}: {value}")

            # Write debug log if needed
            if self.debug:
                log_file = output_file + ".log"
                with open(log_file, "w") as f:
                    f.write("\n".join(self.debug_log))
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
            features = self.feature_processor.process_features(
                processed_data, self.size
            )

            # Generate main model SCAD code
            self.print_debug("\nGenerating main model OpenSCAD code...")
            main_scad = self.scad_generator.generate_openscad(
                features, self.size, self.layer_specs
            )

            # Generate frame SCAD code
            self.print_debug("\nGenerating frame OpenSCAD code...")
            frame_scad = self._generate_frame(self.size, self.max_height)

            # Determine output filenames
            main_file = output_file.replace(".scad", "_main.scad")
            frame_file = output_file.replace(".scad", "_frame.scad")

            # Write main model
            with open(main_file, "w") as f:
                f.write(main_scad)

            # Write frame
            with open(frame_file, "w") as f:
                f.write(frame_scad)

            self.print_debug(f"\nSuccessfully created main model: {main_file}")
            self.print_debug(f"Successfully created frame: {frame_file}")
            self.print_debug("Style settings used:")
            for key, value in self.style_manager.style.items():
                self.print_debug(f"  {key}: {value}")

            # Write debug log if needed
            if self.debug:
                log_file = output_file + ".log"
                with open(log_file, "w") as f:
                    f.write("\n".join(self.debug_log))
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
        frame_size = size + 10  # Add 10mm total (5mm each side)
        return f"""// Frame for city model
// Outer size: {frame_size}mm x {frame_size}mm x {height}mm
// Inner size: {size}mm x {size}mm x {height}mm
// Frame width: 5mm

difference() {{
    cube([{frame_size}, {frame_size}, {height}]);
    translate([5, 5, 0])
        cube([{size}, {size}, {height}]);
}}"""

```

# lib/feature_processor/__init__.py

```py
# lib/feature_processor/__init__.py
"""
Feature Processor package for handling different OSM feature types.
"""

```

# lib/feature_processor/barrier_processor.py

```py
# lib/feature_processor/barrier_processor.py
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

def create_barrier_union(roads, railways, water, road_buffer=2.0, railway_buffer=2.0):
    """Combine roads, railways, and water into one shapely geometry used as a 'barrier'."""
    barrier_geoms = []

    # Roads -> buffered lines
    for road in roads:
        line = LineString(road["coords"])
        barrier_geoms.append(line.buffer(road_buffer))

    # Railways -> buffered lines
    for rail in railways:
        line = LineString(rail["coords"])
        barrier_geoms.append(line.buffer(railway_buffer))

    # Water -> polygons (no buffer)
    for wfeat in water:
        poly = Polygon(wfeat["coords"])
        barrier_geoms.append(poly)

    if barrier_geoms:
        return unary_union(barrier_geoms)
    else:
        return None

```

# lib/feature_processor/base_processor.py

```py
# lib/feature_processor/base_processor.py

class BaseProcessor:
    """
    Base class for specialized feature processors.
    Provides a place to store shared methods or initializations.
    """
    def __init__(self, geometry_utils, style_manager, debug=False):
        self.geometry = geometry_utils
        self.style_manager = style_manager
        self.debug = debug

```

# lib/feature_processor/building_processor.py

```py
# lib/feature_processor/building_processor.py
from shapely.geometry import Polygon
from .base_processor import BaseProcessor

class BuildingProcessor(BaseProcessor):
    def process_building(self, feature, features, transform):
        """
        Process a regular building.
        """
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        area_m2 = self.geometry.approximate_polygon_area_m2(coords)
        min_area = self.style_manager.style.get("min_building_area", 600.0)

        if area_m2 < min_area:
            if self.debug:
                print(f"Skipping small building with area {area_m2:.1f}m²")
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        height = self.style_manager.scale_building_height(props)

        features["buildings"].append({"coords": transformed, "height": height})
        if self.debug:
            print(f"Added building with height {height:.1f}mm and area {area_m2:.1f}m²")

```

# lib/feature_processor/feature_processor.py

```py
# file: feature_processor.py

from shapely.geometry import box
from .building_processor import BuildingProcessor
from .industrial_processor import IndustrialProcessor
from .road_processor import RoadProcessor
from .railway_processor import RailwayProcessor
from .water_processor import WaterProcessor
from .barrier_processor import create_barrier_union
from .park_processor import ParkProcessor
from ..geometry import GeometryUtils

class FeatureProcessor:
    def __init__(self, style_manager):
        self.style_manager = style_manager
        self.geometry = GeometryUtils()  # uses the same GeometryUtils
        self.debug = True  # set True for debug prints

        # Create sub-processor instances
        self.building_proc = BuildingProcessor(self.geometry, style_manager, debug=self.debug)
        self.industrial_proc = IndustrialProcessor(self.geometry, style_manager, debug=self.debug)
        self.road_proc = RoadProcessor(self.geometry, style_manager, debug=self.debug)
        self.rail_proc = RailwayProcessor(self.geometry, style_manager, debug=self.debug)
        self.water_proc = WaterProcessor(self.geometry, style_manager, debug=self.debug)
        self.park_proc = ParkProcessor(self.geometry, style_manager, debug=self.debug)
        
    def process_features(self, geojson_data, size):
        """
        Parse the GeoJSON and gather features by category.
        Updated to better handle industrial areas.
        """
        # Create lat/lon -> model transform
        transform = self.geometry.create_coordinate_transformer(geojson_data["features"], size)

        # Initialize buckets
        features = {
            "water": [],
            "roads": [],
            "railways": [],
            "buildings": [],
            "bridges": [],
            "industrial": [],
            "parks": []
        }

        # First pass: process all features
        for feature in geojson_data["features"]:
            props = feature.get("properties", {})

            # Check for industrial features first
            if self.industrial_proc.should_process_as_industrial(props):
                if props.get("building"):
                    self.industrial_proc.process_industrial_building(feature, features, transform)
                else:
                    self.industrial_proc.process_industrial_area(feature, features, transform)
                continue

            # Process other feature types...
            if props.get("natural") == "water":
                self.water_proc.process_water(feature, features, transform)
            elif "building" in props:
                self.building_proc.process_building(feature, features, transform)
            elif self.road_proc.is_parking_area(props):
                self.road_proc.process_parking(feature, features, transform)
            elif "highway" in props:
                self.road_proc.process_road_or_bridge(feature, features, transform)
            elif "railway" in props:
                self.rail_proc.process_railway(feature, features, transform)
            elif ("leisure" in props) or ("landuse" in props):
                self.park_proc.process_park(feature, features, transform)

        # Store features in style manager
        self.style_manager.set_current_features(features)

        # Debug summary
        if self.debug:
            print(f"\nProcessed feature counts:")
            for cat, items in features.items():
                print(f"  {cat}: {len(items)}")
                if cat == "industrial":
                    buildings = sum(1 for x in items if "building_type" in x)
                    areas = sum(1 for x in items if "landuse_type" in x)
                    print(f"    - Industrial buildings: {buildings}")
                    print(f"    - Industrial areas: {areas}")

        # Create barrier union and merge buildings
        barrier_union = create_barrier_union(
            roads=features["roads"],
            railways=features["railways"],
            water=features["water"],
            road_buffer=1.0,
            railway_buffer=1.0,
        )

        # Merge buildings + industrial
        all_buildings = features["buildings"] + features["industrial"]
        merged_bldgs = self.style_manager.merge_nearby_buildings(all_buildings, barrier_union)
        features["buildings"] = merged_bldgs

        return features

    def _compute_bounding_polygon(self, size):
        """
        Returns a Shapely Polygon from (0,0) to (size,size).
        We subtract coastline lines from this area to create
        an 'ocean' polygon, so it becomes everything outside
        the coastline but within the bounding box.
        """
        return box(0, 0, size, size)
```

# lib/feature_processor/industrial_processor.py

```py
# lib/feature_processor/industrial_processor.py
from shapely.geometry import Polygon
from .base_processor import BaseProcessor

class IndustrialProcessor(BaseProcessor):
    # Define industrial-related tags to look for
    INDUSTRIAL_LANDUSE = {
        'industrial',
        'construction',
        'depot',
        'logistics',
        'port',
        'warehouse'
    }
    
    INDUSTRIAL_BUILDINGS = {
        'industrial',
        'warehouse',
        'factory',
        'manufacturing',
        'hangar'
    }

    def process_industrial_building(self, feature, features, transform):
        """Process an industrial building with specific handling."""
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        # Get area and check against minimum
        area_m2 = self.geometry.approximate_polygon_area_m2(coords)
        min_area = self.style_manager.style.get("min_building_area", 600.0)

        if area_m2 < min_area:
            if self.debug:
                print(f"Skipping small industrial building with area {area_m2:.1f}m²")
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        
        # Calculate height using our detailed calculator
        layer_specs = self.style_manager.get_default_layer_specs()
        min_height = layer_specs["buildings"]["min_height"]
        max_height = layer_specs["buildings"]["max_height"]
        
        # Use explicit height if available, otherwise use industrial multiplier
        height_m = self._get_explicit_height(props)
        if height_m is not None:
            base_height = self.style_manager.scale_building_height({
                "height": str(height_m)
            })
            height = base_height * 1.5  # 50% bonus
        else:
            # Default to twice minimum height for industrial buildings
            height = min(max_height, min_height * 2.0)

        features["industrial"].append({
            "coords": transformed,
            "height": height,
            "is_industrial": True,
            "building_type": props.get("building", "industrial")
        })
        
        if self.debug:
            print(f"Added industrial building, height {height:.1f}mm, area {area_m2:.1f}m²")

    def process_industrial_area(self, feature, features, transform):
        """Process industrial landuse areas as buildings."""
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        # Check if this is an industrial area
        landuse = props.get("landuse", "").lower()
        if landuse not in self.INDUSTRIAL_LANDUSE:
            return

        # Transform coordinates
        transformed = [transform(lon, lat) for lon, lat in coords]

        # Calculate area and filter small areas
        area_m2 = self.geometry.approximate_polygon_area_m2(coords)
        min_area = self.style_manager.style.get("min_building_area", 600.0)

        if area_m2 < min_area:
            if self.debug:
                print(f"Skipping small industrial area with area {area_m2:.1f}m²")
            return

        # Set height based on landuse type
        layer_specs = self.style_manager.get_default_layer_specs()
        min_height = layer_specs["buildings"]["min_height"]
        max_height = layer_specs["buildings"]["max_height"]
        
        # Different heights for different types
        height_multipliers = {
            'industrial': 2.0,
            'construction': 1.5,
            'depot': 1.5,
            'logistics': 1.8,
            'port': 2.0,
            'warehouse': 1.7
        }
        
        multiplier = height_multipliers.get(landuse, 1.5)
        height = min(max_height, min_height * multiplier)

        features["industrial"].append({
            "coords": transformed,
            "height": height,
            "is_industrial": True,
            "landuse_type": landuse
        })

        if self.debug:
            print(f"Added industrial area type '{landuse}' with height {height:.1f}mm")

    def should_process_as_industrial(self, properties):
        """Check if a feature should be processed as industrial."""
        if not properties:
            return False
            
        # Check building tag
        building = properties.get("building", "").lower()
        if building in self.INDUSTRIAL_BUILDINGS:
            return True
            
        # Check landuse tag
        landuse = properties.get("landuse", "").lower()
        if landuse in self.INDUSTRIAL_LANDUSE:
            return True
            
        return False

    def _get_explicit_height(self, properties):
        """Extract explicit height from properties if available."""
        # Check explicit height tag
        if "height" in properties:
            try:
                height_str = properties["height"].split()[0]  # Handle "10 m" format
                return float(height_str)
            except (ValueError, IndexError):
                pass
                
        # Check building levels
        if "building:levels" in properties:
            try:
                levels = float(properties["building:levels"])
                return levels * 3  # assume 3m per level
            except ValueError:
                pass
                
        return None
```

# lib/feature_processor/park_processor.py

```py
# lib/feature_processor/park_processor.py
from .base_processor import BaseProcessor

class ParkProcessor(BaseProcessor):
    """
    Processes OSM features for 'leisure' areas and green 'landuse' types
    (grass, forest, etc.) into a dedicated layer.
    """

    GREEN_LANDUSE_VALUES = {"grass", "forest", "meadow", "village_green", "farmland", "orchard"}
    GREEN_LEISURE_VALUES = {"park", "garden", "golf_course", "recreation_ground", "pitch", "playground"}

    def process_park(self, feature, features, transform):
        """
        Extract polygons that are either 'leisure' or 'landuse' in the 'green' family
        and store them into the `features["parks"]` bucket for later extrusion.
        """
        props = feature.get("properties", {})
        geometry_type = feature["geometry"]["type"]

        # Identify if feature is in one of our 'green' categories
        landuse = props.get("landuse", "").lower()
        leisure = props.get("leisure", "").lower()

        # If it's landuse in GREEN_LANDUSE_VALUES or leisure in GREEN_LEISURE_VALUES
        if (landuse in self.GREEN_LANDUSE_VALUES) or (leisure in self.GREEN_LEISURE_VALUES):
            # Extract raw coords
            coords = self.geometry.extract_coordinates(feature)
            if not coords:
                return

            # For polygons only: if it has at least 3 points
            # (We can skip linestring “parks” or points)
            if geometry_type in ["Polygon", "MultiPolygon"] and len(coords) >= 3:
                # Apply your standard lat/lon -> XY transform
                transformed = [transform(lon, lat) for lon, lat in coords]
                # Store them so we can extrude later in scad_generator
                features["parks"].append({"coords": transformed})

```

# lib/feature_processor/railway_processor.py

```py
# lib/feature_processor/railway_processor.py
from .base_processor import BaseProcessor

class RailwayProcessor(BaseProcessor):
    def process_railway(self, feature, features, transform):
        """Process a railway feature."""
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        # Skip tunnels
        if props.get("tunnel") in ["yes", "true", "1"]:
            if self.debug:
                print(f"Skipping tunnel railway: {props.get('railway')}")
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) >= 2:
            features["railways"].append({"coords": transformed, "type": props.get("railway", "unknown")})
            if self.debug:
                print(f"Added railway '{props.get('railway', 'unknown')}', {len(transformed)} points")

```

# lib/feature_processor/road_processor.py

```py
# lib/feature_processor/road_processor.py
from .base_processor import BaseProcessor

class RoadProcessor(BaseProcessor):
    def process_road_or_bridge(self, feature, features, transform):
        """Handle a road or bridge feature."""
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        # Skip tunnels
        if props.get("tunnel") in ["yes", "true", "1"]:
            if self.debug:
                print(f"Skipping tunnel road: {props.get('highway')}")
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) < 2:
            return

        # Bridge
        if props.get("bridge") and props.get("bridge").lower() not in ["no", "false", "0"]:
            bridge_type = props.get("highway", "bridge")
            features["bridges"].append({"coords": transformed, "type": bridge_type})
            if self.debug:
                print(f"Added bridge of type '{bridge_type}', {len(transformed)} points")
        else:
            # Regular road
            road_type = props.get("highway", "unknown")
            features["roads"].append({"coords": transformed, "type": road_type, "is_parking": False})
            if self.debug:
                print(f"Added road of type '{road_type}', {len(transformed)} points")

    def process_parking(self, feature, features, transform):
        """Process a parking area."""
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) >= 3:  # polygon
            features["roads"].append({"coords": transformed, "type": "parking", "is_parking": True})
            if self.debug:
                print(f"Added parking area with {len(transformed)} points")

    def is_parking_area(self, props):
        """Check if feature is a parking area by OSM tags."""
        return (
            props.get("amenity") == "parking"
            or props.get("parking") == "surface"
            or props.get("service") == "parking_aisle"
        )

```

# lib/feature_processor/water_processor.py

```py
from .base_processor import BaseProcessor

class WaterProcessor(BaseProcessor):
    def process_water(self, feature, features, transform):
        # Extract props and coords from the incoming `feature`
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        # Apply the coordinate transform
        transformed = [transform(lon, lat) for lon, lat in coords]

        # If it's large enough to be considered water
        if len(transformed) >= 3:
            features["water"].append({
                "coords": transformed,
                "type": props.get("water", "unknown")
            })
            if self.debug:
                print(f"Added water feature with {len(transformed)} points")

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

```

# lib/preprocessor.py

```py
# lib/preprocessor.py
from copy import deepcopy
import json
import statistics
from math import radians, cos, sin, sqrt, pi
from shapely.geometry import shape, mapping, box, Point


class GeoJSONPreprocessor:
    def __init__(self, bbox=None, distance_meters=None):
        """
        bbox: [south, west, north, east]
        distance_meters: radius (in meters) to crop from the center
        """
        self.bbox = bbox
        self.distance = distance_meters
        self.debug = True

    def create_cropping_geometry(self, features):
        """
        Create a Shapely geometry to use for cropping. Either a bounding box
        or a circular buffer.
        """
        if self.distance:
            # Calculate center from all features
            all_coords = []
            for feature in features:
                all_coords.extend(self.extract_coordinates(feature))
            if not all_coords:
                raise ValueError("No coordinates found in features")
            lons, lats = zip(*all_coords)
            center_lon = statistics.median(lons)
            center_lat = statistics.median(lats)
            # Convert distance in meters to degrees (approximation)
            radius_degrees = self.distance / 111320.0
            cropping_geom = Point(center_lon, center_lat).buffer(radius_degrees)
            if self.debug:
                print(
                    f"Using circular cropping geometry with center: ({center_lon:.6f}, {center_lat:.6f}) and radius (deg): {radius_degrees:.6f}"
                )
            return cropping_geom
        elif self.bbox:
            # bbox provided as [south, west, north, east]
            south, west, north, east = self.bbox
            cropping_geom = box(west, south, east, north)
            if self.debug:
                print(f"Using bounding box cropping geometry: {self.bbox}")
            return cropping_geom
        else:
            return None

    def extract_coordinates(self, feature):
        """Extract all coordinates from a feature regardless of geometry type"""
        geometry = feature["geometry"]
        coords = []

        if geometry["type"] == "Point":
            coords = [geometry["coordinates"]]
        elif geometry["type"] == "LineString":
            coords = geometry["coordinates"]
        elif geometry["type"] == "Polygon":
            for ring in geometry["coordinates"]:
                coords.extend(ring)
        elif geometry["type"] == "MultiPolygon":
            for polygon in geometry["coordinates"]:
                for ring in polygon:
                    coords.extend(ring)
        elif geometry["type"] == "MultiLineString":
            for line in geometry["coordinates"]:
                coords.extend(line)

        return coords

    def crop_feature(self, feature, cropping_geom):
        """
        Crop a feature to the cropping geometry using geometric intersection.
        Returns a new feature with the clipped geometry, or None if no intersection.
        """
        try:
            geom = shape(feature["geometry"])
        except Exception as e:
            if self.debug:
                print(f"Failed to parse geometry: {e}")
            return None

        clipped = geom.intersection(cropping_geom)
        if clipped.is_empty:
            return None

        # If geometrycollection, pick a valid geometry
        if clipped.geom_type == "GeometryCollection":
            # Use clipped.geoms under Shapely >= 2.0
            valid_geoms = [
                g
                for g in clipped.geoms
                if g.geom_type in ["Polygon", "MultiPolygon", "LineString", "MultiLineString"]
            ]
            if not valid_geoms:
                return None
            # Pick the largest polygon if available; else first valid
            polygons = [
                g for g in valid_geoms if g.geom_type in ["Polygon", "MultiPolygon"]
            ]
            clipped = max(polygons, key=lambda g: g.area) if polygons else valid_geoms[0]

        new_feature = deepcopy(feature)
        new_feature["geometry"] = mapping(clipped)
        return new_feature

    def process_geojson(self, input_data):
        """
        Process the GeoJSON data by clipping each feature to the defined cropping geometry.
        """
        features = input_data.get("features", [])
        cropping_geom = self.create_cropping_geometry(features)
        if cropping_geom is None:
            raise ValueError(
                "No cropping geometry defined (neither bbox nor distance provided)"
            )

        new_features = []
        for feature in features:
            cropped = self.crop_feature(feature, cropping_geom)
            if cropped:
                new_features.append(cropped)

        if self.debug:
            print(f"Original features: {len(features)}")
            print(f"Cropped features: {len(new_features)}")

        output_data = {"type": "FeatureCollection", "features": new_features}
        return output_data


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Preprocess GeoJSON for 3D city modeling"
    )
    parser.add_argument("input_file", help="Input GeoJSON file")
    parser.add_argument("output_file", help="Output GeoJSON file")
    parser.add_argument(
        "--distance", type=float, help="Distance in meters from center to crop"
    )
    parser.add_argument(
        "--bbox",
        type=float,
        nargs=4,
        metavar=("SOUTH", "WEST", "NORTH", "EAST"),
        help="Bounding box coordinates (south west north east)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    args = parser.parse_args()

    if not args.distance and not args.bbox:
        parser.error("Either --distance or --bbox must be specified")

    try:
        with open(args.input_file, "r") as f:
            input_data = json.load(f)

        processor = GeoJSONPreprocessor(
            bbox=args.bbox if args.bbox else None,
            distance_meters=args.distance if args.distance else None,
        )
        processor.debug = args.debug
        output_data = processor.process_geojson(input_data)

        with open(args.output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"Successfully processed GeoJSON data and saved to {args.output_file}")

    except Exception as e:
        print(f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()

```

# lib/preview/__init__.py

```py
from .openscad_integration import OpenSCADIntegration

```

# lib/preview/export_manager.py

```py
# lib/preview/export_manager.py
import os
import subprocess


class ExportManager:
    def __init__(self, openscad_path):
        self.openscad_path = openscad_path
        self.export_quality = {
            "fn": 256,
            "fa": 2,
            "fs": 0.2,
        }

    def generate_stl(self, scad_file, output_stl, repair=True):
        """Generate STL files for both main model and frame."""
        try:
            main_scad_file = scad_file.replace(".scad", "_main.scad")
            frame_scad_file = scad_file.replace(".scad", "_frame.scad")

            if not all(os.path.exists(f) for f in [main_scad_file, frame_scad_file]):
                raise FileNotFoundError("Required SCAD files not found")

            main_stl = output_stl.replace(".stl", "_main.stl")
            frame_stl = output_stl.replace(".stl", "_frame.stl")

            env = os.environ.copy()
            env["OPENSCAD_HEADLESS"] = "1"

            # Generate main model STL
            self._generate_single_stl(main_scad_file, main_stl, env)

            # Generate frame STL
            self._generate_single_stl(frame_scad_file, frame_stl, env)

            return True

        except Exception as e:
            print(f"Error generating STL: {str(e)}")
            raise

    def _generate_single_stl(self, input_file, output_file, env):
        """Generate STL for a single model."""
        command = [
            self.openscad_path,
            "--backend=Manifold",
            "--render",
            "--export-format=binstl",
            "-o",
            output_file,
        ]

        # Add quality settings
        for param, value in self.export_quality.items():
            command.extend(["-D", f"${param}={value}"])

        command.append(input_file)

        subprocess.run(command, env=env, capture_output=True, text=True, check=True)

```

# lib/preview/file_watcher.py

```py
# lib/preview/file_watcher.py
import os
import sys
import time
import threading
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileWatcher:
    def __init__(self):
        self.observer = None
        self.watch_thread = None
        self.running = False

    def watch_and_reload(self, scad_file, openscad_path):
        """Watch SCAD file and trigger auto-reload in OpenSCAD."""
        subprocess.Popen([openscad_path, scad_file])

        class SCDHandler(FileSystemEventHandler):
            def __init__(self, scad_path):
                self.scad_path = scad_path
                self.last_reload = 0
                self.reload_cooldown = 1.0

            def on_modified(self, event):
                if event.src_path == self.scad_path:
                    current_time = time.time()
                    if current_time - self.last_reload >= self.reload_cooldown:
                        self._reload_openscad()
                        self.last_reload = current_time

            def _reload_openscad(self):
                if sys.platform == "win32":
                    self._reload_windows()
                elif sys.platform == "darwin":
                    self._reload_macos()
                else:
                    self._reload_linux()

            def _reload_windows(self):
                import win32gui
                import win32con

                def callback(hwnd, _):
                    if "OpenSCAD" in win32gui.GetWindowText(hwnd):
                        win32gui.SetForegroundWindow(hwnd)
                        win32gui.PostMessage(
                            hwnd, win32con.WM_KEYDOWN, win32con.VK_F5, 0
                        )

                win32gui.EnumWindows(callback, None)

            def _reload_macos(self):
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        'tell application "OpenSCAD" to activate\n'
                        + 'tell application "System Events"\n'
                        + 'keystroke "r" using {command down}\n'
                        + "end tell",
                    ]
                )

            def _reload_linux(self):
                try:
                    subprocess.run(
                        [
                            "xdotool",
                            "search",
                            "--name",
                            "OpenSCAD",
                            "windowactivate",
                            "--sync",
                            "key",
                            "F5",
                        ]
                    )
                except:
                    print(
                        "Warning: xdotool not found. Auto-reload may not work on Linux."
                    )

        self.running = True
        event_handler = SCDHandler(os.path.abspath(scad_file))
        self.observer = Observer()
        self.observer.schedule(
            event_handler, os.path.dirname(scad_file), recursive=False
        )
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

# lib/preview/openscad_integration.py

```py
# lib/preview/openscad_integration.py
import subprocess
import os
import sys
from .preview_generator import PreviewGenerator
from .export_manager import ExportManager
from .file_watcher import FileWatcher


class OpenSCADIntegration:
    def __init__(self, openscad_path=None):
        self.openscad_path = openscad_path or self._find_openscad()
        if not self.openscad_path:
            raise RuntimeError("Could not find OpenSCAD executable")

        self.preview_generator = PreviewGenerator(self.openscad_path)
        self.export_manager = ExportManager(self.openscad_path)
        self.file_watcher = FileWatcher()

    def _find_openscad(self):
        """Find the OpenSCAD executable."""
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
                os.path.expanduser(
                    "~/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
                ),
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
        """Generate preview using PreviewGenerator."""
        return self.preview_generator.generate(output_file, output_image, size)

    def generate_stl(self, scad_file, output_stl, repair=True):
        """Generate STL using ExportManager."""
        return self.export_manager.generate_stl(scad_file, output_stl, repair)

    def watch_and_reload(self, scad_file):
        """Watch SCAD file using FileWatcher."""
        return self.file_watcher.watch_and_reload(scad_file, self.openscad_path)

    def stop_watching(self):
        """Stop file watching."""
        self.file_watcher.stop_watching()

```

# lib/preview/preview_generator.py

```py
# lib/preview/preview_generator.py
import os
import subprocess


class PreviewGenerator:
    def __init__(self, openscad_path):
        self.openscad_path = openscad_path

    def generate(self, output_file, output_image, size=(1920, 1080)):
        """Generate preview images for both main model and frame."""
        main_scad_file = output_file.replace(".scad", "_main.scad")
        frame_scad_file = output_file.replace(".scad", "_frame.scad")

        if not all(os.path.exists(f) for f in [main_scad_file, frame_scad_file]):
            raise FileNotFoundError("Required SCAD files not found")

        env = os.environ.copy()
        env["OPENSCAD_HEADLESS"] = "1"

        # Generate previews for main and frame
        return self._generate_model_preview(
            main_scad_file, frame_scad_file, output_image, size, env
        )

    def _generate_model_preview(self, main_file, frame_file, output_image, size, env):
        """Generate preview for a specific model file."""
        try:
            # Generate main preview
            main_preview = output_image.replace(".png", "_main.png")
            self._run_preview_command(main_file, main_preview, size, env)

            # Generate frame preview
            frame_preview = output_image.replace(".png", "_frame.png")
            self._run_preview_command(
                frame_file, frame_preview, size, env, is_frame=True
            )

            return True
        except subprocess.CalledProcessError as e:
            print("Error generating preview:", e)
            print("OpenSCAD output:", e.stdout)
            print("OpenSCAD errors:", e.stderr)
            return False

    def _run_preview_command(self, input_file, output_file, size, env, is_frame=False):
        """Run OpenSCAD command to generate preview."""
        command = [
            self.openscad_path,
            "--backend=Manifold",
            "--render",
            "--imgsize",
            f"{size[0]},{size[1]}",
            "--autocenter",
            "--colorscheme=DeepOcean",
        ]

        if is_frame:
            command.extend(["--viewall", "--projection=perspective"])

        command.extend(["-o", output_file, input_file])

        subprocess.run(command, env=env, capture_output=True, text=True, check=True)

```

# lib/scad_generator.py

```py
from .geometry import GeometryUtils
from .style.style_manager import StyleManager
from .style.generate_building import BuildingGenerator

class ScadGenerator:
    def __init__(self, style_manager):
        self.style_manager = style_manager
        self.geometry = GeometryUtils()
        self.building_generator = BuildingGenerator(style_manager)

    def generate_openscad(self, features, size, layer_specs):
        """
        Generate complete OpenSCAD code for main model (excluding frame).
        We 'union' buildings, bridges, and parks, then 'difference' roads/water/rail.
        """
        scad = [
            f"""// Generated with Enhanced City Converter
// Style: {self.style_manager.style['artistic_style']}
// Detail Level: {self.style_manager.style['detail_level']}

difference() {{
    union() {{
        // Base block
        cube([{size}, {size}, {layer_specs['base']['height']}]);

        // Buildings
        {self._generate_building_features(features['buildings'], layer_specs)}

        // Bridges
        {self._generate_bridge_features(features['bridges'], layer_specs)}

        // Parks
        {self._generate_park_features(features['parks'], layer_specs)}
    }}

    // Subtractive features
    union() {{
        {self._generate_water_features(features['water'], layer_specs)}
        {self._generate_road_features(features['roads'], layer_specs)}
        {self._generate_railway_features(features['railways'], layer_specs)}
    }}
}}"""
        ]
        return "\n".join(scad)

    def _generate_building_features(self, building_features, layer_specs):
        """Generate OpenSCAD code for building features."""
        scad = []
        base_height = layer_specs["base"]["height"]

        for i, building in enumerate(building_features):
            points_str = self.geometry.generate_polygon_points(building["coords"])
            if not points_str:
                continue

            building_height = building["height"]
            block_type = building.get("block_type", "residential")
            roof_style = building.get("roof_style", None)

            details = self.building_generator.generate_building_details(
                points_str, 
                building_height, 
                roof_style=roof_style,
                block_type=block_type
            )

            scad.append(
                f"""
    // Building {i+1}
    translate([0, 0, {base_height}]) {{
        color("white")
        {{
            {details}
        }}
    }}"""
            )

        return "\n".join(scad)

    def _generate_water_features(self, water_features, layer_specs):
        """Generate OpenSCAD code for water features (subtractive)"""
        scad = []
        base_height = layer_specs["base"]["height"]
        water_depth = layer_specs["water"]["depth"]

        for i, water in enumerate(water_features):
            coords = water.get("coords", water)
            points_str = self.geometry.generate_polygon_points(coords)
            if points_str:
                scad.append(
                    f"""
        // Water body {i+1}
        translate([0, 0, {base_height - water_depth}])
            color("blue")
            {{
                linear_extrude(height={water_depth + 0.1}, convexity=2)
                    polygon([{points_str}]);
            }}"""
                )

        return "\n".join(scad)

    def _generate_road_features(self, road_features, layer_specs):
        """Generate OpenSCAD code for road features (subtractive)"""
        scad = []
        base_height = layer_specs["base"]["height"]
        road_depth = layer_specs["roads"]["depth"]
        road_width = layer_specs["roads"]["width"]
        park_offset = layer_specs["parks"].get("start_offset", 0.2)
        park_thickness = layer_specs["parks"].get("thickness", 0.4)
        road_extrude_height = road_depth + park_offset + park_thickness + 0.1

        for i, road in enumerate(road_features):
            coords = road.get("coords", [])
            is_parking = road.get("is_parking", False)

            if is_parking and len(coords) >= 3:
                points_str = self.geometry.generate_polygon_points(coords)
            else:
                points_str = None
                if len(coords) >= 2:
                    points_str = self.geometry.generate_buffered_polygon(
                        coords, road_width
                    )

            if points_str:
                color_val = "yellow" if is_parking else "black"
                scad.append(
                    f"""
            // {"Parking Area" if is_parking else "Road"} {i+1}
            translate([0, 0, {base_height - road_depth}])
                color("{color_val}")
                {{
                    linear_extrude(height={road_extrude_height}, convexity=2)
                        polygon([{points_str}]);
                }}"""
                )

        return "\n".join(scad)

    def _generate_railway_features(self, railway_features, layer_specs):
        """Generate OpenSCAD code for railways (subtractive)"""
        scad = []
        base_height = layer_specs["base"]["height"]
        railway_depth = layer_specs["railways"]["depth"]
        railway_width = layer_specs["railways"]["width"]

        for i, railway in enumerate(railway_features):
            coords = railway.get("coords", [])
            if len(coords) < 2:
                continue

            points_str = self.geometry.generate_buffered_polygon(coords, railway_width)
            if points_str:
                scad.append(
                    f"""
        // Railway {i+1}
        translate([0, 0, {base_height - railway_depth}])
            color("brown")
            {{
                linear_extrude(height={railway_depth + 0.1}, convexity=2)
                    polygon([{points_str}]);
            }}"""
                )

        return "\n".join(scad)

    def _generate_bridge_features(self, bridge_features, layer_specs):
        """Generate OpenSCAD code for bridges with improved 3D printing support"""
        scad = []
        base_height = layer_specs["base"]["height"]
        bridge_height = layer_specs["bridges"]["height"]
        bridge_thickness = layer_specs["bridges"]["thickness"]
        support_width = layer_specs["bridges"]["support_width"]
        road_width = layer_specs["roads"]["width"]

        for i, bridge in enumerate(bridge_features):
            coords = bridge.get("coords", [])
            if len(coords) < 2:
                continue

            points_str = self.geometry.generate_buffered_polygon(coords, road_width)
            if points_str:
                start_point = coords[0]
                end_point = coords[-1]

                scad.append(
                    f"""
        // Bridge {i+1}
        union() {{
            color("orange")
            {{
                // Main bridge deck
                translate([0, 0, {base_height + bridge_height}])
                    linear_extrude(height={bridge_thickness}, convexity=2)
                        polygon([{points_str}]);
            }}
            // Bridge supports (remain uncolored for clarity)
            translate([{start_point[0]}, {start_point[1]}, {base_height}])
                cylinder(h={bridge_height}, r={support_width/2}, $fn=8);
            translate([{end_point[0]}, {end_point[1]}, {base_height}])
                cylinder(h={bridge_height}, r={support_width/2}, $fn=8);
        }}"""
                )

        return "\n".join(scad)

    def _generate_park_features(self, park_features, layer_specs):
        """Generate OpenSCAD code for park features."""
        scad = []
        base_height = layer_specs["base"]["height"]
        park_offset = layer_specs["parks"].get("start_offset", 0.2)
        park_thickness = layer_specs["parks"].get("thickness", 0.4)

        for i, park in enumerate(park_features):
            points_str = self.geometry.generate_polygon_points(park["coords"])
            if not points_str:
                continue
                
            scad.append(f"""
        // Park {i+1}
        translate([0, 0, {base_height + park_offset}]) {{
            color("green")
            linear_extrude(height={park_thickness}, convexity=2)
                polygon([{points_str}]);
        }}""")
            
        return "\n".join(scad)
```

# lib/style_manager.py

```py
# lib/style_manager.py
from math import log10, sin, cos, pi, atan2
from shapely.geometry import LineString
from .geometry import GeometryUtils
from .style.block_combiner import BlockCombiner


class StyleManager:
    def __init__(self, style_settings=None):
        self.geometry = GeometryUtils()
        self.block_combiner = BlockCombiner(self)
        self.current_features = {}

        # Default style settings
        self.style = {
            "merge_distance": 2.0,
            "cluster_size": 3.0,
            "height_variance": 0.2,
            "detail_level": 1.0,
            "artistic_style": "modern",
            "min_building_area": 600.0,
        }

        # Override defaults with provided settings
        if style_settings:
            self.style.update(style_settings)

    def get_default_layer_specs(self):
        """Get default layer specifications for roads, water, buildings, etc."""
        return {
            "water": {
                "depth": 3,
            },
            "roads": {
                "depth": 0.6,
                "width": 2.0,
            },
            "railways": {
                "depth": 0.2,
                "width": 1.5,
            },
            "buildings": {"min_height": 2, "max_height": 5},
            "base": {
                "height": 5,
            },
            "parks": {
                "start_offset": 0,  # Height offset above the base for parks
                "thickness": 0.5      # Extrusion thickness for parks
            },
        }

    def scale_building_height(self, properties):
        """
        Given a building's OSM properties, produce a scaled building height (in mm).
        Uses a simple log scaling approach to map real-world height to a small range.
        """
        default_height = 4.0

        height_m = None
        if "height" in properties:
            try:
                height_m = float(properties["height"].split()[0])
            except (ValueError, IndexError):
                pass
        elif "building:levels" in properties:
            try:
                levels = float(properties["building:levels"])
                height_m = levels * 3  # assume 3m per level
            except ValueError:
                pass

        if height_m is None:
            height_m = default_height

        layer_specs = self.get_default_layer_specs()
        min_height = layer_specs["buildings"]["min_height"]
        max_height = layer_specs["buildings"]["max_height"]

        # Log scaling from 1..100 meters -> min_height..max_height in mm
        log_min = log10(1.0)
        log_max = log10(101.0)
        log_height = log10(height_m + 1.0)  # +1 to avoid log(0)
        scaled = (log_height - log_min) / (log_max - log_min)
        final_height = min_height + scaled * (max_height - min_height)
        return round(final_height, 2)

    def merge_nearby_buildings(self, buildings, barrier_union=None):
        """Choose merging strategy based on style."""
        if self.style["artistic_style"] == "block-combine":
            return self.block_combiner.combine_buildings_by_block(self.current_features)
        else:
            return self._merge_buildings_by_distance(buildings, barrier_union)

    def _merge_buildings_by_distance(self, buildings, barrier_union=None):
        """Original distance-based merging logic"""
        merge_dist = self.style["merge_distance"]
        if merge_dist <= 0:
            return buildings

        indexed_buildings = []
        for idx, bldg in enumerate(buildings):
            ctd = self.geometry.calculate_centroid(bldg["coords"])
            indexed_buildings.append((idx, ctd, bldg))

        visited = set()
        clusters = []

        for i, centroidA, bldgA in indexed_buildings:
            if i in visited:
                continue

            stack = [i]
            cluster_bldgs = []
            visited.add(i)

            while stack:
                current_idx = stack.pop()
                _, current_centroid, current_bldg = indexed_buildings[current_idx]
                cluster_bldgs.append(current_bldg)

                for j, centroidB, bldgB in indexed_buildings:
                    if j in visited:
                        continue
                    dist = self.geometry.calculate_distance(current_centroid, centroidB)
                    if dist < merge_dist:
                        if not self._is_blocked_by_barrier(
                            current_centroid, centroidB, barrier_union
                        ):
                            visited.add(j)
                            stack.append(j)

            merged = self._merge_building_cluster(cluster_bldgs)
            clusters.append(merged)

        return clusters

    def _is_blocked_by_barrier(self, ptA, ptB, barrier_union):
        """Return True if the line from ptA to ptB intersects the barrier_union"""
        if barrier_union is None:
            return False
        line = LineString([ptA, ptB])
        return line.intersects(barrier_union)

    def _merge_building_cluster(self, cluster):
        """Merge building polygons in 'cluster' into one shape"""
        if len(cluster) == 1:
            return cluster[0]

        total_area = 0.0
        weighted_height = 0.0
        all_coords = []

        for b in cluster:
            coords = b["coords"]
            area = self.geometry.calculate_polygon_area(coords)
            total_area += area
            weighted_height += b["height"] * area
            all_coords.extend(coords)

        avg_height = (
            weighted_height / total_area if total_area > 0 else cluster[0]["height"]
        )
        hull_coords = self._create_artistic_hull(all_coords)

        return {
            "coords": hull_coords,
            "height": avg_height,
            "is_cluster": True,
            "size": len(cluster),
        }

    def _add_artistic_variation(self, coords):
        """Add small coordinate perturbations for artistic effect"""
        varied = []
        variance = self.style["height_variance"]
        style = self.style["artistic_style"]

        if style == "modern":
            for i, (x, y) in enumerate(coords):
                offset = variance * sin(i * pi / len(coords))
                varied.append([x + offset, y + offset])
        elif style == "classic":
            for i, (x, y) in enumerate(coords):
                angle = 2.0 * pi * i / len(coords)
                offset_x = variance * cos(angle)
                offset_y = variance * sin(angle)
                varied.append([x + offset_x, y + offset_y])
        else:  # minimal or block-combine
            varied = coords

        return varied

    def _create_artistic_hull(self, points):
        """Sort points by angle around centroid and optionally add detail"""
        if len(points) < 3:
            return points

        center = self.geometry.calculate_centroid(points)
        sorted_points = sorted(
            points, key=lambda p: atan2(p[1] - center[1], p[0] - center[0])
        )
        hull = []
        detail_level = self.style["detail_level"]

        for i in range(len(sorted_points)):
            p1 = sorted_points[i]
            p2 = sorted_points[(i + 1) % len(sorted_points)]
            hull.append(p1)

            if detail_level > 0.5:
                dist = self.geometry.calculate_distance(p1, p2)
                if dist > self.style["cluster_size"]:
                    num_points = int(detail_level * dist / self.style["cluster_size"])
                    for j in range(num_points):
                        t = (j + 1) / (num_points + 1)
                        mx = p1[0] + t * (p2[0] - p1[0])
                        my = p1[1] + t * (p2[1] - p1[1])
                        offset = self.style["height_variance"] * sin(t * pi)
                        hull.append([mx + offset, my - offset])

        hull = self._add_artistic_variation(hull)
        return hull

    def set_current_features(self, features):
        """Store current features for block-combine style to use"""
        self.current_features = features

```

# lib/style/__init__.py

```py
from .style_manager import StyleManager

```

# lib/style/artistic_effects.py

```py
# lib/style/artistic_effects.py
from math import sin, cos, pi, atan2


class ArtisticEffects:
    def __init__(self, style_manager):
        self.style_manager = style_manager

    def create_artistic_hull(self, points):
        """Create artistic hull from points based on style settings."""
        if len(points) < 3:
            return points

        from ..geometry import GeometryUtils

        geometry = GeometryUtils()

        center = geometry.calculate_centroid(points)
        sorted_points = self._sort_points_by_angle(points, center)
        hull = self._generate_hull_points(sorted_points, geometry)

        return self._add_artistic_variation(hull)

    def _sort_points_by_angle(self, points, center):
        """Sort points by angle around center."""
        return sorted(points, key=lambda p: atan2(p[1] - center[1], p[0] - center[0]))

    def _generate_hull_points(self, sorted_points, geometry):
        """Generate hull points with optional detail points."""
        hull = []
        detail_level = self.style_manager.style["detail_level"]
        cluster_size = self.style_manager.style["cluster_size"]

        for i in range(len(sorted_points)):
            p1 = sorted_points[i]
            p2 = sorted_points[(i + 1) % len(sorted_points)]
            hull.append(p1)

            if detail_level > 0.5:
                self._add_detail_points(
                    hull, p1, p2, detail_level, cluster_size, geometry
                )

        return hull

    def _add_detail_points(self, hull, p1, p2, detail_level, cluster_size, geometry):
        """Add intermediate detail points between two points."""
        dist = geometry.calculate_distance(p1, p2)
        if dist > cluster_size:
            num_points = int(detail_level * dist / cluster_size)
            for j in range(num_points):
                t = (j + 1) / (num_points + 1)
                mx = p1[0] + t * (p2[0] - p1[0])
                my = p1[1] + t * (p2[1] - p1[1])
                offset = self.style_manager.style["height_variance"] * sin(t * pi)
                hull.append([mx + offset, my - offset])

    def _add_artistic_variation(self, coords):
        """Add style-specific variations to coordinates."""
        varied = []
        variance = self.style_manager.style["height_variance"]
        style = self.style_manager.style["artistic_style"]

        if style == "modern":
            for i, (x, y) in enumerate(coords):
                offset = variance * sin(i * pi / len(coords))
                varied.append([x + offset, y + offset])
        elif style == "classic":
            for i, (x, y) in enumerate(coords):
                angle = 2.0 * pi * i / len(coords)
                offset_x = variance * cos(angle)
                offset_y = variance * sin(angle)
                varied.append([x + offset_x, y + offset_y])
        else:  # minimal or block-combine
            varied = coords

        return varied

```

# lib/style/block_combiner.py

```py
import random
from shapely.geometry import Polygon, MultiPolygon, box, LineString
from shapely.ops import unary_union
from shapely.validation import make_valid
from ..geometry import GeometryUtils

class BlockCombiner:
    """
    A refined block combiner that creates clean, printable 3D building blocks with:
    - Clear separation between blocks based on roads/water
    - Proper handling of industrial vs residential areas
    - Clean, non-overlapping roof structures
    - Building heights that make sense within blocks
    """

    def __init__(self, style_manager):
        self.style_manager = style_manager
        self.geometry = GeometryUtils()
        self.debug = False  # Enable/disable debug prints

        # Define block types and their characteristics
        self.BLOCK_TYPES = {
            'residential': {
                'min_height': 10.0,
                'max_height': 25.0,
                'roof_styles': [
                    {'name': 'pitched', 'height_factor': 0.3},
                    {'name': 'tiered', 'levels': 2},
                    {'name': 'flat', 'border': 1.0}
                ]
            },
            'industrial': {
                'min_height': 15.0,
                'max_height': 35.0,
                'roof_styles': [
                    {'name': 'sawtooth', 'angle': 30},
                    {'name': 'flat', 'border': 2.0},
                    {'name': 'stepped', 'levels': 3}
                ]
            },
            'commercial': {
                'min_height': 20.0,
                'max_height': 40.0,
                'roof_styles': [
                    {'name': 'modern', 'setback': 2.0},
                    {'name': 'tiered', 'levels': 3},
                    {'name': 'complex', 'variations': 4}
                ]
            }
        }

    def combine_buildings_by_block(self, features):
        """
        Main entry point that:
          1) Gathers all building footprints,
          2) Creates barrier geometry,
          3) Divides the map into blocks,
          4) Finds which footprints fall into each block,
          5) Processes them into final building shapes.
        """
        if self.debug:
            print("\n=== Block Combiner Debug ===")

        # 1. Gather footprints (buildings + industrial)
        building_footprints = self._gather_all_footprints(features)
        if self.debug:
            print(f"Found {len(building_footprints)} building footprints.")

        # 2. Create barrier geometry from roads/water
        barrier_union = self._create_barrier_union(features)

        # 3. Generate blocks by subtracting barriers from bounding area
        blocks = self._create_blocks_from_barriers(barrier_union)
        if self.debug:
            print(f"Generated {len(blocks)} blocks from barrier union.")

        # 4 & 5. For each block, find footprints, analyze, and process
        combined_buildings = []
        for block in blocks:
            block_buildings = self._find_buildings_in_block(block, building_footprints)
            block_info = self._analyze_block(block_buildings)
            processed_shapes = self._process_block_buildings(
                block, block_buildings, block_info, barrier_union
            )
            combined_buildings.extend(processed_shapes)

        # Optionally, you could also handle footprints not in any block.
        # For example, if some footprints fall outside the barrier bounding box.
        # That step is omitted here, but you can add it if needed.

        return combined_buildings

    def _gather_all_footprints(self, features):
        """
        Collect all building/industrial footprints into a unified list.
        This is the SINGLE version (the old duplicate method was removed).
        """
        footprints = []

        # Process "normal" building features
        for bldg in features.get('buildings', []):
            coords = bldg.get('coords')
            if not coords or len(coords) < 3:
                continue

            # Check building type from props if available
            props = bldg.get('properties', {})
            bldg_type = 'residential'  # default
            if props.get('building') in ['commercial', 'retail', 'office']:
                bldg_type = 'commercial'
            elif props.get('building') in ['industrial', 'warehouse', 'factory']:
                bldg_type = 'industrial'

            poly = Polygon(coords)
            if not poly.is_valid:
                poly = make_valid(poly)
            if poly.is_valid and not poly.is_empty:
                footprints.append({
                    'polygon': poly,
                    'type': bldg_type,
                    'height': bldg.get('height', 10.0),
                    'original': bldg
                })

        # Process industrial features (both buildings and landuse areas)
        for ind in features.get('industrial', []):
            coords = ind.get('coords')
            if not coords or len(coords) < 3:
                continue

            poly = Polygon(coords)
            if not poly.is_valid:
                poly = make_valid(poly)
            if poly.is_empty or not poly.is_valid:
                continue

            # If it's a big industrial area, we can subdivide or treat as one footprint
            if ind.get('landuse_type'):
                # For large industrial landuse, optionally subdivide
                # (You can keep it simpler if you prefer)
                area = poly.area
                if area > 1000:
                    # Buffer inward to create multiple smaller building footprints
                    buffered = poly.buffer(-2.0)
                    if buffered.is_valid and not buffered.is_empty:
                        footprints.append({
                            'polygon': buffered,
                            'type': 'industrial',
                            'height': ind.get('height', 15.0),
                            'original': ind
                        })
                else:
                    # Single building
                    footprints.append({
                        'polygon': poly,
                        'type': 'industrial',
                        'height': ind.get('height', 15.0),
                        'original': ind
                    })
            else:
                # It's an industrial building
                footprints.append({
                    'polygon': poly,
                    'type': 'industrial',
                    'height': ind.get('height', 15.0),
                    'original': ind
                })

        return footprints

    def _create_barrier_union(self, features):
        """
        Create a unified geometry of all barriers (roads, water, etc.).
        The result is used to subdivide the bounding box into 'blocks'.
        """
        barriers = []

        # Road buffer
        road_width = self.style_manager.get_default_layer_specs()["roads"]["width"]
        for road in features.get('roads', []):
            try:
                line = LineString(road["coords"])
                # Buffer roads by ~60% of the width to create a barrier
                buffered = line.buffer(road_width * 0.6)
                if buffered.is_valid and not buffered.is_empty:
                    barriers.append(buffered)
            except Exception:
                continue

        # Water buffer
        for water in features.get('water', []):
            try:
                poly = Polygon(water["coords"])
                if poly.is_valid and not poly.is_empty:
                    # Give water a 1.5m buffer for the barrier
                    barriers.append(poly.buffer(1.5))
            except Exception:
                continue

        if not barriers:
            return None

        unioned = unary_union(barriers)
        if not unioned.is_valid:
            unioned = make_valid(unioned)
        return unioned

    def _create_blocks_from_barriers(self, barrier_union):
        """
        Subtract the barrier geometry from its bounding box to get
        'blocks' (MultiPolygon) that remain between roads, water, etc.
        """
        if not barrier_union or barrier_union.is_empty:
            return []

        try:
            # Create bounding box around all barrier geometry
            minx, miny, maxx, maxy = barrier_union.bounds
            bounding_area = box(minx, miny, maxx, maxy)

            # Subtract barriers to form blocks
            blocks_area = bounding_area.difference(barrier_union)
            if blocks_area.is_empty:
                return []

            # If we get multiple polygons, handle them all
            if isinstance(blocks_area, MultiPolygon):
                blocks = []
                for b in blocks_area.geoms:
                    if b.area > 100:  # skip very tiny
                        simplified = b.simplify(0.5)
                        if simplified.is_valid and not simplified.is_empty:
                            blocks.append(simplified)
                return blocks
            else:
                # Single polygon result
                if blocks_area.area > 100:
                    simplified = blocks_area.simplify(0.5)
                    if simplified.is_valid and not simplified.is_empty:
                        return [simplified]
            return []
        except Exception as e:
            if self.debug:
                print(f"Error creating blocks: {e}")
            return []

    def _find_buildings_in_block(self, block, building_footprints):
        """
        Find all building footprints that intersect a given block polygon.
        """
        block_buildings = []
        for fp in building_footprints:
            try:
                shape = fp['polygon']
                if block.intersects(shape):
                    intersection = block.intersection(shape)
                    if not intersection.is_empty and intersection.area > 10:
                        # Copy footprint and store the clipped geometry
                        fp_copy = dict(fp)
                        fp_copy['polygon'] = intersection
                        block_buildings.append(fp_copy)
            except Exception:
                continue
        return block_buildings

    def _analyze_block(self, block_buildings):
        """
        Inspect the buildings in this block to figure out a suitable block type
        or average height. You can adapt this logic to your needs.
        """
        if not block_buildings:
            return {'type': 'residential', 'avg_height': 15.0}

        # Tally up building types & compute weighted average height
        type_counts = {'residential': 0, 'industrial': 0, 'commercial': 0}
        total_area = 0.0
        weighted_height = 0.0

        for b in block_buildings:
            area = b['polygon'].area
            total_area += area
            weighted_height += b['height'] * area
            if b['type'] in type_counts:
                type_counts[b['type']] += 1
            else:
                type_counts['residential'] += 1  # fallback

        # The dominant type is the block type
        block_type = max(type_counts, key=type_counts.get)
        avg_height = weighted_height / total_area if total_area > 0 else 15.0

        return {
            'type': block_type,
            'avg_height': avg_height,
            'building_count': len(block_buildings),
            'total_area': total_area
        }

    def _process_block_buildings(self, block, block_buildings, block_info, barrier_union):
        """
        Convert all footprints in this block into final 3D shapes,
        applying style rules, merging footprints, etc.
        """
        if not block_buildings:
            return []

        processed = []
        block_type = block_info['type']
        type_specs = self.BLOCK_TYPES.get(block_type, self.BLOCK_TYPES['residential'])

        # Union all footprints in this block
        try:
            footprints_union = unary_union([b['polygon'] for b in block_buildings])
            if not footprints_union.is_valid:
                footprints_union = make_valid(footprints_union)
        except Exception:
            return []

        # Possibly break a MultiPolygon into individual polygons
        polygons = []
        if isinstance(footprints_union, MultiPolygon):
            polygons.extend(footprints_union.geoms)
        else:
            polygons.append(footprints_union)

        for shape in polygons:
            if shape.is_empty or shape.area < 50:
                continue

            # Simplify & buffer inward a bit if you like
            cleaned = shape.simplify(0.5)
            if not cleaned.is_valid or cleaned.is_empty:
                continue

            # Optionally buffer inward to avoid collisions
            # (reduces the polygon edges slightly)
            final_poly = cleaned.buffer(-0.3)
            if final_poly.is_empty:
                continue

            # Respect barrier lines inside the block
            if barrier_union:
                clipped = final_poly.difference(barrier_union)
                if clipped.is_empty:
                    continue
            else:
                clipped = final_poly

            # At this point, 'clipped' is our final footprint
            if clipped.is_empty or clipped.area < 10:
                continue

            # Convert to single polygons if it's still a MultiPolygon
            if isinstance(clipped, MultiPolygon):
                sub_polys = list(clipped.geoms)
            else:
                sub_polys = [clipped]

            for spoly in sub_polys:
                if spoly.is_empty or spoly.area < 10:
                    continue

                # Determine final building height
                base_height = self._calculate_building_height(block_info['avg_height'], type_specs)
                roof_style = self._select_roof_style(block_type)

                building_dict = {
                    'coords': list(spoly.exterior.coords)[:-1],
                    'height': base_height,
                    'block_type': block_type,
                    'roof_style': roof_style['name'],
                    'roof_params': roof_style
                }
                processed.append(building_dict)

        return processed

    def _calculate_building_height(self, avg_height, type_specs):
        """
        Pick a final building height that respects the block's average
        but also the block-type constraints.
        """
        min_h = type_specs['min_height']
        max_h = type_specs['max_height']

        # Start around the block's average
        base = max(avg_height, min_h)
        if base < 15.0:
            base = 15.0

        # Add a little random variation (+/- 15%)
        variation = random.uniform(0.85, 1.15)
        candidate = base * variation

        # Clamp to [min_h, max_h]
        final_height = max(min_h, min(candidate, max_h))
        return final_height

    def _select_roof_style(self, block_type):
        """
        Randomly pick a roof style from the block type's style list.
        """
        styles = self.BLOCK_TYPES.get(block_type, self.BLOCK_TYPES['residential'])['roof_styles']
        choice = random.choice(styles)

        # Add minor parameter variation
        if choice['name'] == 'pitched':
            choice['height_factor'] *= random.uniform(0.8, 1.2)
        elif choice['name'] == 'tiered':
            choice['levels'] = max(1, choice['levels'] + random.randint(-1, 1))
        elif choice['name'] == 'flat':
            choice['border'] *= random.uniform(0.9, 1.1)
        # etc. for others

        return choice

```

# lib/style/building_merger.py

```py
# lib/style/building_merger.py
from shapely.geometry import LineString
from ..geometry import GeometryUtils


class BuildingMerger:
    def __init__(self, style_manager):
        self.style_manager = style_manager
        self.geometry = GeometryUtils()

    def merge_buildings(self, buildings, barrier_union=None):
        """Choose and execute merging strategy."""
        if self.style_manager.style["artistic_style"] == "block-combine":
            return self._merge_by_blocks(buildings)
        else:
            return self._merge_by_distance(buildings, barrier_union)

    def _merge_by_blocks(self, buildings):
        """Merge buildings by block."""
        from .block_combiner import BlockCombiner  # Local import

        block_combiner = BlockCombiner(self.style_manager)
        return block_combiner.combine_buildings_by_block(
            self.style_manager.current_features
        )

    def _merge_by_distance(self, buildings, barrier_union):
        """Merge buildings based on distance."""
        merge_dist = self.style_manager.style["merge_distance"]
        if merge_dist <= 0:
            return buildings

        indexed_buildings = self._index_buildings(buildings)
        visited = set()
        clusters = []

        for i, centroidA, bldgA in indexed_buildings:
            if i in visited:
                continue

            cluster = self._build_cluster(
                i, indexed_buildings, visited, barrier_union, merge_dist
            )
            merged = self._merge_cluster(cluster)
            clusters.append(merged)

        return clusters

    def _index_buildings(self, buildings):
        """Create indexed building list with centroids."""
        return [
            (idx, self.geometry.calculate_centroid(bldg["coords"]), bldg)
            for idx, bldg in enumerate(buildings)
        ]

    def _build_cluster(
        self, start_idx, indexed_buildings, visited, barrier_union, merge_dist
    ):
        """Build a cluster of buildings starting from given index."""
        stack = [start_idx]
        cluster = []
        visited.add(start_idx)

        while stack:
            current_idx = stack.pop()
            _, current_centroid, current_bldg = indexed_buildings[current_idx]
            cluster.append(current_bldg)

            for j, centroidB, bldgB in indexed_buildings:
                if j not in visited:
                    dist = self.geometry.calculate_distance(current_centroid, centroidB)
                    if dist < merge_dist:
                        if not self._is_blocked(
                            current_centroid, centroidB, barrier_union
                        ):
                            visited.add(j)
                            stack.append(j)

        return cluster

    def _is_blocked(self, ptA, ptB, barrier_union):
        """Check if line between points is blocked by barrier."""
        if barrier_union is None:
            return False
        line = LineString([ptA, ptB])
        return line.intersects(barrier_union)

    def _merge_cluster(self, cluster):
        """Merge a cluster of buildings into one shape."""
        if len(cluster) == 1:
            return cluster[0]

        total_area = 0.0
        weighted_height = 0.0
        all_coords = []

        for b in cluster:
            coords = b["coords"]
            area = self.geometry.calculate_polygon_area(coords)
            total_area += area
            weighted_height += b["height"] * area
            all_coords.extend(coords)

        avg_height = (
            weighted_height / total_area if total_area > 0 else cluster[0]["height"]
        )
        hull_coords = self.style_manager.artistic_effects.create_artistic_hull(
            all_coords
        )

        return {
            "coords": hull_coords,
            "height": avg_height,
            "is_cluster": True,
            "size": len(cluster),
        }

```

# lib/style/generate_building.py

```py
class BuildingGenerator:
    """
    Generates OpenSCAD code for buildings with clean, non-overlapping roofs
    that respect block boundaries and barriers.
    """
    
    def __init__(self, style_manager):
        self.style_manager = style_manager

    def generate_building_details(self, points_str, height, roof_style=None, roof_params=None, block_type=None):
        """Generate a building with appropriate roof style."""
        if not roof_style or not roof_params:
            return self._generate_basic_building(points_str, height)

        if roof_style == 'pitched':
            return self._generate_pitched_roof(points_str, height, roof_params)
        elif roof_style == 'tiered':
            return self._generate_tiered_roof(points_str, height, roof_params)
        elif roof_style == 'flat':
            return self._generate_flat_roof(points_str, height, roof_params)
        elif roof_style == 'sawtooth':
            return self._generate_sawtooth_roof(points_str, height, roof_params)
        elif roof_style == 'modern':
            return self._generate_modern_roof(points_str, height, roof_params)
        elif roof_style == 'complex':
            return self._generate_complex_roof(points_str, height, roof_params)
        elif roof_style == 'stepped':
            return self._generate_stepped_roof(points_str, height, roof_params)
        else:
            return self._generate_basic_building(points_str, height)

    def _generate_basic_building(self, points_str, height):
        """Generate a basic building without roof details."""
        return f"""
            linear_extrude(height={height}, convexity=2)
                polygon([{points_str}]);"""

    def _generate_pitched_roof(self, points_str, height, params):
        """Generate a pitched roof building."""
        roof_height = height * params['height_factor']
        base_height = height - roof_height
        
        return f"""
            union() {{
                // Base building
                linear_extrude(height={base_height}, convexity=2)
                    polygon([{points_str}]);
                
                // Pitched roof
                translate([0, 0, {base_height}])
                    linear_extrude(height={roof_height}, scale=0.6, convexity=2)
                        polygon([{points_str}]);
            }}"""

    def _generate_tiered_roof(self, points_str, height, params):
        """Generate a tiered roof with multiple levels."""
        num_levels = params['levels']
        level_height = height * 0.15  # Each tier is 15% of total height
        base_height = height - (level_height * num_levels)
        
        tiers = []
        for i in range(num_levels):
            offset = (i + 1) * 1.5  # Increasing inset for each tier
            tier_start = base_height + (i * level_height)
            tiers.append(f"""
                // Tier {i + 1}
                translate([0, 0, {tier_start}])
                    linear_extrude(height={level_height}, convexity=2)
                        offset(r=-{offset})
                            polygon([{points_str}]);""")
        
        return f"""
            union() {{
                // Base building
                linear_extrude(height={base_height}, convexity=2)
                    polygon([{points_str}]);
                {' '.join(tiers)}
            }}"""

    def _generate_flat_roof(self, points_str, height, params):
        """Generate a flat roof with border detail."""
        border = params['border']
        return f"""
            union() {{
                // Main building
                linear_extrude(height={height}, convexity=2)
                    polygon([{points_str}]);
                
                // Roof border
                translate([0, 0, {height}])
                    linear_extrude(height=1.0, convexity=2)
                        difference() {{
                            polygon([{points_str}]);
                            offset(r=-{border})
                                polygon([{points_str}]);
                        }}
            }}"""

    def _generate_sawtooth_roof(self, points_str, height, params):
        """Generate an industrial sawtooth roof."""
        angle = params['angle']
        tooth_height = height * 0.2
        base_height = height - tooth_height
        
        return f"""
            union() {{
                // Base building
                linear_extrude(height={base_height}, convexity=2)
                    polygon([{points_str}]);
                
                // Sawtooth roof
                translate([0, 0, {base_height}]) {{
                    intersection() {{
                        linear_extrude(height={tooth_height}, convexity=2)
                            polygon([{points_str}]);
                        
                        // Sawtooth pattern
                        rotate([{angle}, 0, 0])
                            translate([0, 0, -50])
                                linear_extrude(height=100, convexity=4)
                                    polygon([{points_str}]);
                    }}
                }}
            }}"""

    def _generate_modern_roof(self, points_str, height, params):
        """Generate a modern style roof with setback."""
        setback = params['setback']
        top_height = height * 0.2
        base_height = height - top_height
        
        return f"""
            union() {{
                // Base building
                linear_extrude(height={base_height}, convexity=2)
                    polygon([{points_str}]);
                
                // Setback top section
                translate([0, 0, {base_height}])
                    linear_extrude(height={top_height}, convexity=2)
                        offset(r=-{setback})
                            polygon([{points_str}]);
            }}"""

    def _generate_complex_roof(self, points_str, height, params):
        """Generate a complex roof with multiple variations."""
        variations = params['variations']
        section_height = height * 0.15
        base_height = height - (section_height * variations)
        
        sections = []
        for i in range(variations):
            offset = 1.0 + (i * 0.8)  # Progressive offset
            section_start = base_height + (i * section_height)
            scale = 1.0 - (i * 0.15)  # Progressive scale reduction
            
            sections.append(f"""
                // Complex section {i + 1}
                translate([0, 0, {section_start}])
                    linear_extrude(height={section_height}, scale={scale}, convexity=2)
                        offset(r=-{offset})
                            polygon([{points_str}]);""")
        
        return f"""
            union() {{
                // Base building
                linear_extrude(height={base_height}, convexity=2)
                    polygon([{points_str}]);
                {' '.join(sections)}
            }}"""

    def _generate_stepped_roof(self, points_str, height, params):
        """Generate a stepped industrial roof."""
        num_levels = params['levels']
        step_height = height * 0.12
        base_height = height - (step_height * num_levels)
        
        steps = []
        for i in range(num_levels):
            offset = 2.0 + (i * 1.5)  # Increasing step size
            step_start = base_height + (i * step_height)
            steps.append(f"""
                // Step {i + 1}
                translate([0, 0, {step_start}])
                    linear_extrude(height={step_height}, convexity=2)
                        offset(r=-{offset})
                            polygon([{points_str}]);""")
        
        return f"""
            union() {{
                // Base building
                linear_extrude(height={base_height}, convexity=2)
                    polygon([{points_str}]);
                {' '.join(steps)}
            }}"""
```

# lib/style/height_manager.py

```py
# lib/style/height_manager.py
from math import log10


class HeightManager:
    def __init__(self, style_manager):
        self.style_manager = style_manager

    def scale_height(self, properties):
        """Scale building height based on properties."""
        height_m = self._extract_height(properties)
        return self._scale_to_range(height_m)

    def _extract_height(self, properties):
        """Extract height from building properties."""
        default_height = 5.0

        if "height" in properties:
            try:
                return float(properties["height"].split()[0])
            except (ValueError, IndexError):
                pass
        elif "building:levels" in properties:
            try:
                levels = float(properties["building:levels"])
                return levels * 3  # assume 3m per level
            except ValueError:
                pass

        return default_height

    def _scale_to_range(self, height_m):
        """Scale height to target range using logarithmic scaling."""
        layer_specs = self.style_manager.get_default_layer_specs()
        min_height = layer_specs["buildings"]["min_height"]
        max_height = layer_specs["buildings"]["max_height"]

        # Log scaling from 1..100 meters -> min_height..max_height in mm
        log_min = log10(1.0)
        log_max = log10(101.0)
        log_height = log10(height_m + 1.0)  # +1 to avoid log(0)
        scaled = (log_height - log_min) / (log_max - log_min)
        final_height = min_height + scaled * (max_height - min_height)
        return round(final_height, 2)

```

# lib/style/style_manager.py

```py
# lib/style/style_manager.py
from .building_merger import BuildingMerger
from .height_manager import HeightManager
from .artistic_effects import ArtisticEffects
from .block_combiner import BlockCombiner


class StyleManager:
    def __init__(self, style_settings=None):
        # Initialize default style settings
        self.style = {
            "merge_distance": 2.0,
            "cluster_size": 3.0,
            "height_variance": 0.2,
            "detail_level": 1.0,
            "artistic_style": "modern",
            "min_building_area": 600.0,
        }

        # Override defaults with provided settings
        if style_settings:
            self.style.update(style_settings)

        # Initialize components
        self.building_merger = BuildingMerger(self)
        self.height_manager = HeightManager(self)
        self.artistic_effects = ArtisticEffects(self)
        self.block_combiner = BlockCombiner(self)
        self.current_features = {}

    def get_default_layer_specs(self):
        """Get default layer specifications."""
        return {
            "water": {"depth": 2.4},
            "roads": {"depth": 0.4, "width": 1.0},
            "railways": {"depth": 0.6, "width": 1.5},
            "parks": {
                "start_offset": 0.2,  # top of base + 0.2
                "thickness": 0.4
            },
            "buildings": {"min_height": 2, "max_height": 8},
            "base": {"height": 3},
        }

    def scale_building_height(self, properties):
        """Scale building height using HeightManager."""
        return self.height_manager.scale_height(properties)

    def merge_nearby_buildings(self, buildings, barrier_union=None):
        """Choose merging strategy based on style."""
        if self.style["artistic_style"] == "block-combine":
            # This calls our new block combiner code
            return self.block_combiner.combine_buildings_by_block(self.current_features)
        else:
            # Original distance-based approach
            return self.building_merger.merge_buildings(buildings, barrier_union)

    def set_current_features(self, features):
        """Store current features."""
        self.current_features = features

```

# package.json

```json
{
  "name": "shadow-city-frontend",
  "version": "1.0.0",
  "description": "Node frontend to interact with the Shadow City Generator command line tool",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "multer": "1.4.5-lts.1",
    "ejs": "^3.1.8",
    "uuid": "^9.0.0"
  }
}

```

# psl

This is a binary file of the type: Binary

# public/css/style.css

```css
body {
  padding-top: 20px;
  padding-bottom: 20px;
}

```

# README.md

```md
# Shadow City Generator

Create beautiful, 3D-printable city maps from OpenStreetMap data. This tool generates geometric interpretations of urban landscapes, complete with buildings, roads, and water features. The output includes a main city model and a decorative frame that can be printed separately and assembled.

## Quick Start

\`\`\`bash
python geojson_to_shadow_city.py input.geojson output.scad [options]
\`\`\`

This creates:
- `output_main.scad` - The city model
- `output_frame.scad` - A decorative frame that fits around the model

### Basic Export Example

\`\`\`bash
# Generate both preview and STL files with modern style
python geojson_to_shadow_city.py map.geojson output.scad \
    --export both \
    --style modern \
    --size 200 \
    --water-depth 3 \
    --road-width 1
\`\`\`

## Export Options

### Preview Generation
\`\`\`bash
# Generate preview images
python geojson_to_shadow_city.py map.geojson output.scad \
    --export preview \
    --preview-size 1920 1080
\`\`\`

### STL Export
\`\`\`bash
# Generate high-quality STL files
python geojson_to_shadow_city.py map.geojson output.scad \
    --export stl \
    --style classic
\`\`\`

Creates:
- `output_main.stl` - Main city model
- `output_frame.stl` - Decorative frame

The STL files are generated using OpenSCAD's Manifold backend for optimal quality and performance.

## Preprocessing Options

The Shadow City Generator includes preprocessing capabilities to help you refine your input data before generating the 3D model.

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

#### Building Size Selection
\`\`\`bash
--min-building-area 600
\`\`\`
Controls which buildings are included:
- Low values (200-400): Include small buildings like houses and shops
- Medium values (600-800): Focus on medium-sized structures
- High values (1000+): Show only larger buildings like offices and apartments

#### Artistic Building Combinations
\`\`\`bash
--merge-distance 2.0
\`\`\`
Controls how buildings are combined:
- `0`: Each building stands alone
- `1-2`: Nearby buildings gently blend together
- `3-5`: Buildings flow into each other more dramatically
- `6+`: Creates bold, abstract representations

#### Height Artistry
\`\`\`bash
--height-variance 0.2
\`\`\`
Controls building height variations:
- `0.0`: Uniform heights within groups
- `0.1-0.2`: Subtle height variations
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

## Creative Examples

### Contemporary Downtown
\`\`\`bash
python geojson_to_shadow_city.py input.geojson output.scad \
    --preprocess \
    --crop-distance 800 \
    --style modern \
    --detail 0.5 \
    --merge-distance 0 \
    --min-building-area 1000 \
    --road-width 1.5 \
    --export both
\`\`\`

### Historic District
\`\`\`bash
python geojson_to_shadow_city.py input.geojson output.scad \
    --style classic \
    --detail 1.5 \
    --merge-distance 3 \
    --min-building-area 400 \
    --height-variance 0.3 \
    --export stl
\`\`\`

### Minimalist Urban Plan
\`\`\`bash
python geojson_to_shadow_city.py input.geojson output.scad \
    --style minimal \
    --detail 0.3 \
    --merge-distance 0 \
    --road-width 1.5 \
    --water-depth 2 \
    --export both
\`\`\`

## Installation

1. Install Python dependencies:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

2. Install OpenSCAD:
   - Windows: Download from openscad.org
   - macOS: `brew install openscad`
   - Linux: `sudo apt install openscad` or equivalent

## 3D Printing Guide

### Print Settings
1. **Layer Height**: 
   - 0.2mm for good detail
   - 0.12mm for extra detail in complex areas

2. **Infill**:
   - Main model: 10-15%
   - Frame: 20% for stability

3. **Support Settings**:
   - Main model: Support on build plate only
   - Frame: Usually no supports needed

4. **Material Choice**:
   - PLA works well for both parts
   - Consider using contrasting colors for main model and frame

### Assembly Tips
1. Print the main model (`*_main.stl`) and frame (`*_frame.stl`) separately
2. The frame has a 5mm border and will be slightly larger than the main model
3. Clean any support material carefully, especially from the frame
4. The main model should fit snugly inside the frame

## Troubleshooting

### Common Issues

1. **Long Processing Times**:
   - Reduce `--detail` level
   - Increase `--min-building-area`
   - Use `--crop-distance` to limit area

2. **Memory Issues**:
   - Use `--preprocess` with smaller areas
   - Increase `--min-building-area`
   - Reduce `--detail` level

3. **Preview/STL Generation**:
   - Ensure OpenSCAD is properly installed
   - Try using `--export preview` first to check the model
   - Check available disk space

### Getting Help

If you encounter issues:
1. Enable debug output with `--debug`
2. Check the generated log file (`*.log`)
3. Verify OpenSCAD installation
4. Ensure all dependencies are installed

## Contributing

Contributions are welcome! Please feel free to submit pull requests or create issues for bugs and feature requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
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

# server.js

```js
const express = require("express");
const multer = require("multer");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");
const { v4: uuidv4 } = require("uuid");

const app = express();
const port = process.env.PORT || 3000;

// Set view engine to EJS
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));

// Serve static files
app.use(express.static(path.join(__dirname, "public")));
app.use("/uploads", express.static("uploads"));
app.use("/outputs", express.static("outputs"));

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// Ensure uploads/outputs folders exist
const uploadsDir = path.join(__dirname, "uploads");
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir);
}
const outputsDir = path.join(__dirname, "outputs");
if (!fs.existsSync(outputsDir)) {
  fs.mkdirSync(outputsDir);
}

// Configure Multer storage
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, "uploads/");
  },
  filename: function (req, file, cb) {
    const uniqueSuffix = Date.now() + "-" + uuidv4();
    cb(null, uniqueSuffix + "-" + file.originalname);
  },
});

// Only allow .geojson files
function fileFilter(req, file, cb) {
  const ext = path.extname(file.originalname).toLowerCase();
  if (ext === ".geojson") {
    cb(null, true);
  } else {
    cb(new Error("Invalid file type. Only .geojson files are allowed."));
  }
}

// Create Multer instance with storage + fileFilter
const upload = multer({ storage: storage, fileFilter: fileFilter });

// -------------------------------------
// ROUTES
// -------------------------------------

// Home route
app.get("/", (req, res) => {
  res.render("index");
});

// Endpoint to handle AJAX file upload
app.post("/uploadFile", upload.single("geojson"), (req, res) => {
  // If Multer’s fileFilter rejects the file, req.file will be undefined
  if (!req.file) {
    return res
      .status(400)
      .json({ error: "No valid .geojson file was uploaded." });
  }
  const filePath = path.join(__dirname, req.file.path);
  res.json({ filePath: filePath });
});

// Live preview endpoint
app.post("/preview", (req, res) => {
  const uploadedFile = req.body.uploadedFile;
  if (!uploadedFile) {
    return res.status(400).json({ error: "No uploaded file provided." });
  }
  const outputBase = "preview-" + Date.now() + "-" + uuidv4();
  const outputScad = path.join(outputsDir, outputBase + ".scad");

  let args = [
    path.join(__dirname, "geojson_to_shadow_city.py"),
    uploadedFile,
    outputScad,
    "--export",
    "preview",
  ];

  // Basic options
  if (req.body.size) args.push("--size", req.body.size);
  if (req.body.height) args.push("--height", req.body.height);
  if (req.body.style) args.push("--style", req.body.style);
  if (req.body.detail) args.push("--detail", req.body.detail);
  if (req.body["merge-distance"])
    args.push("--merge-distance", req.body["merge-distance"]);
  if (req.body["cluster-size"])
    args.push("--cluster-size", req.body["cluster-size"]);
  if (req.body["height-variance"])
    args.push("--height-variance", req.body["height-variance"]);
  if (req.body["road-width"]) args.push("--road-width", req.body["road-width"]);
  if (req.body["water-depth"])
    args.push("--water-depth", req.body["water-depth"]);
  if (req.body["min-building-area"])
    args.push("--min-building-area", req.body["min-building-area"]);
  if (req.body.debug === "on") args.push("--debug");

  // NEW bridging lines
  if (req.body["bridge-height"]) {
    args.push("--bridge-height", req.body["bridge-height"]);
  }
  if (req.body["bridge-thickness"]) {
    args.push("--bridge-thickness", req.body["bridge-thickness"]);
  }
  if (req.body["support-width"]) {
    args.push("--support-width", req.body["support-width"]);
  }

  // Preprocessing
  if (req.body.preprocess === "on") args.push("--preprocess");
  if (req.body["crop-distance"])
    args.push("--crop-distance", req.body["crop-distance"]);
  if (req.body["crop-bbox"]) {
    const bbox = req.body["crop-bbox"]
      .split(",")
      .map((coord) => coord.trim())
      .map(Number);
    if (bbox.length === 4 && bbox.every((num) => !isNaN(num))) {
      args.push(
        "--crop-bbox",
        bbox[0].toString(),
        bbox[1].toString(),
        bbox[2].toString(),
        bbox[3].toString()
      );
    }
  }

  // Preview integration
  if (req.body["preview-size-width"] && req.body["preview-size-height"]) {
    args.push(
      "--preview-size",
      req.body["preview-size-width"],
      req.body["preview-size-height"]
    );
  }
  if (req.body["preview-file"]) {
    args.push("--preview-file", req.body["preview-file"]);
  }
  if (req.body.watch === "on") {
    args.push("--watch");
  }
  if (req.body["openscad-path"]) {
    args.push("--openscad-path", req.body["openscad-path"]);
  }

  console.log("Live preview generation command:", args.join(" "));

  const pythonProcess = spawn("python3", args);
  let stdoutData = "";
  let stderrData = "";

  pythonProcess.stdout.on("data", (data) => {
    stdoutData += data.toString();
  });
  pythonProcess.stderr.on("data", (data) => {
    stderrData += data.toString();
  });
  pythonProcess.on("close", (code) => {
    if (code !== 0) {
      console.error("Python preview process exited with code", code);
      console.error(stderrData);
      return res.status(500).json({ error: stderrData });
    }
    const previewMain = outputBase + "_preview_main.png";
    const previewFrame = outputBase + "_preview_frame.png";

    res.json({
      previewMain: "/outputs/" + previewMain,
      previewFrame: "/outputs/" + previewFrame,
      stdout: stdoutData,
      stderr: stderrData,
    });
  });
});

// Final render endpoint
app.post("/render", (req, res) => {
  const uploadedFile = req.body.uploadedFile;
  if (!uploadedFile) {
    return res.status(400).json({ error: "No uploaded file provided." });
  }
  const outputBase = "output-" + Date.now() + "-" + uuidv4();
  const outputPath = path.join(outputsDir, outputBase + ".scad");

  let args = [
    path.join(__dirname, "geojson_to_shadow_city.py"),
    uploadedFile,
    outputPath,
  ];

  // Basic options
  if (req.body.size) args.push("--size", req.body.size);
  if (req.body.height) args.push("--height", req.body.height);
  if (req.body.style) args.push("--style", req.body.style);
  if (req.body.detail) args.push("--detail", req.body.detail);
  if (req.body["merge-distance"])
    args.push("--merge-distance", req.body["merge-distance"]);
  if (req.body["cluster-size"])
    args.push("--cluster-size", req.body["cluster-size"]);
  if (req.body["height-variance"])
    args.push("--height-variance", req.body["height-variance"]);
  if (req.body["road-width"]) args.push("--road-width", req.body["road-width"]);
  if (req.body["water-depth"])
    args.push("--water-depth", req.body["water-depth"]);
  if (req.body["min-building-area"])
    args.push("--min-building-area", req.body["min-building-area"]);
  if (req.body.debug === "on") args.push("--debug");

  // NEW bridging lines
  if (req.body["bridge-height"]) {
    args.push("--bridge-height", req.body["bridge-height"]);
  }
  if (req.body["bridge-thickness"]) {
    args.push("--bridge-thickness", req.body["bridge-thickness"]);
  }
  if (req.body["support-width"]) {
    args.push("--support-width", req.body["support-width"]);
  }

  // Preprocessing
  if (req.body.preprocess === "on") args.push("--preprocess");
  if (req.body["crop-distance"])
    args.push("--crop-distance", req.body["crop-distance"]);
  if (req.body["crop-bbox"]) {
    const bbox = req.body["crop-bbox"]
      .split(",")
      .map((coord) => coord.trim())
      .map(Number);
    if (bbox.length === 4 && bbox.every((num) => !isNaN(num))) {
      args.push(
        "--crop-bbox",
        bbox[0].toString(),
        bbox[1].toString(),
        bbox[2].toString(),
        bbox[3].toString()
      );
    }
  }

  // Export options
  if (req.body.export) args.push("--export", req.body.export);
  if (req.body["output-stl"]) args.push("--output-stl", req.body["output-stl"]);
  if (req.body["no-repair"] === "on") args.push("--no-repair");
  if (req.body.force === "on") args.push("--force");

  // Preview & integration
  if (req.body["preview-size-width"] && req.body["preview-size-height"]) {
    args.push(
      "--preview-size",
      req.body["preview-size-width"],
      req.body["preview-size-height"]
    );
  }
  if (req.body["preview-file"]) {
    args.push("--preview-file", req.body["preview-file"]);
  }
  if (req.body.watch === "on") {
    args.push("--watch");
  }
  if (req.body["openscad-path"]) {
    args.push("--openscad-path", req.body["openscad-path"]);
  }

  console.log("Final render command:", args.join(" "));

  const pythonProcess = spawn("python3", args);
  let stdoutData = "";
  let stderrData = "";

  pythonProcess.stdout.on("data", (data) => {
    stdoutData += data.toString();
  });
  pythonProcess.stderr.on("data", (data) => {
    stderrData += data.toString();
  });
  pythonProcess.on("close", (code) => {
    if (code !== 0) {
      console.error("Python final render process exited with code", code);
      console.error(stderrData);
      return res.status(500).json({ error: stderrData });
    }
    const mainScad = outputBase + "_main.scad";
    const frameScad = outputBase + "_frame.scad";
    const logFile = outputBase + ".scad.log";

    let stlFiles = {};
    if (req.body.export === "stl" || req.body.export === "both") {
      const mainStl = outputBase + "_main.stl";
      const frameStl = outputBase + "_frame.stl";
      stlFiles = {
        mainStl: "/outputs/" + mainStl,
        frameStl: "/outputs/" + frameStl,
      };
    }

    res.json({
      mainScad: "/outputs/" + mainScad,
      frameScad: "/outputs/" + frameScad,
      logFile: "/outputs/" + logFile,
      stlFiles: stlFiles,
      stdout: stdoutData,
      stderr: stderrData,
    });
  });
});

// Fallback /upload endpoint (if needed)
app.post("/upload", upload.single("geojson"), (req, res) => {
  if (!req.file) {
    return res.status(400).send("No valid .geojson file was uploaded.");
  }
  res.redirect("/");
});

// Start the server
app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});

```

# views/index.ejs

```ejs
<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <title>Shadow City Generator Frontend</title>
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <link rel="stylesheet" href="/css/style.css">
  <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
  <style>
    .preview-container {
      margin-top: 20px;
    }

    .preview-container img {
      max-width: 100%;
      border: 1px solid #ddd;
      padding: 5px;
    }

    .download-links a {
      display: block;
      margin-bottom: 5px;
    }

    .log-container {
      margin-top: 20px;
    }

    #liveLog {
      background-color: #1e1e1e;
      color: #cfcfcf;
      padding: 10px;
      border-radius: 5px;
      min-height: 100px;
      max-height: 300px;
      overflow-y: auto;
      font-family: monospace;
      white-space: pre;
    }

    .processing-indicator {
      display: none;
      color: #007bff;
      margin-bottom: 10px;
    }
  </style>
</head>

<body>
  <div class="container">
    <h1 class="mt-5">Shadow City Generator</h1>
    <p class="lead">Use the form to upload a GeoJSON file and set options. Live previews and downloadable outputs will
      appear on the right.</p>

    <!-- Hidden field to store uploaded file path -->
    <input type="hidden" id="uploadedFile" name="uploadedFile" value="">

    <div class="row">
      <!-- Left Column: Form and Options -->
      <div class="col-md-4">
        <form id="optionsForm">
          <!-- File Upload -->
          <div class="form-group">
            <label for="geojson">GeoJSON File</label>
            <input type="file" class="form-control-file" id="geojson" name="geojson" accept=".geojson" required>
          </div>

          <!-- Preprocessing Options -->
          <fieldset class="border p-3 mb-3">
            <legend class="w-auto">Preprocessing Options</legend>
            <div class="form-group form-check">
              <input type="checkbox" class="form-check-input live-preview" id="preprocess" name="preprocess">
              <label class="form-check-label" for="preprocess">Enable Preprocessing</label>
            </div>
            <div class="form-group">
              <label for="crop-distance">Crop Distance (meters)</label>
              <input type="number" step="0.1" class="form-control live-preview" id="crop-distance" name="crop-distance">
            </div>
            <div class="form-group">
              <label for="crop-bbox">Bounding Box (paste from Overpass)</label>
              <input type="text" class="form-control live-preview" id="crop-bbox" name="crop-bbox"
                placeholder="e.g. 26.942061, -80.074937, 26.94714, -80.070162">
            </div>
          </fieldset>

          <!-- Basic Options -->
          <fieldset class="border p-3 mb-3">
            <legend class="w-auto">Basic Options</legend>
            <div class="form-group">
              <label for="size">Model Size (mm)</label>
              <input type="number" class="form-control live-preview" id="size" name="size" value="200" required>
            </div>
            <div class="form-group">
              <label for="height">Maximum Height (mm)</label>
              <input type="number" class="form-control live-preview" id="height" name="height" value="20" required>
            </div>
            <div class="form-group">
              <label for="style">Artistic Style</label>
              <select class="form-control live-preview" id="style" name="style">
                <option value="modern" selected>Modern</option>
                <option value="classic">Classic</option>
                <option value="minimal">Minimal</option>
                <option value="block-combine">Block Combine</option>
              </select>
            </div>
            <div class="form-group">
              <label for="detail">Detail Level (0-2)</label>
              <input type="number" step="0.1" class="form-control live-preview" id="detail" name="detail" value="1.0"
                required>
            </div>
            <div class="form-group">
              <label for="merge-distance">Merge Distance</label>
              <input type="number" step="0.1" class="form-control live-preview" id="merge-distance"
                name="merge-distance" value="2.0">
            </div>
            <div class="form-group">
              <label for="cluster-size">Cluster Size</label>
              <input type="number" step="0.1" class="form-control live-preview" id="cluster-size" name="cluster-size"
                value="3.0">
            </div>
            <div class="form-group">
              <label for="height-variance">Height Variance</label>
              <input type="number" step="0.1" class="form-control live-preview" id="height-variance"
                name="height-variance" value="0.2">
            </div>
            <div class="form-group">
              <label for="road-width">Road Width (mm)</label>
              <input type="number" step="0.1" class="form-control live-preview" id="road-width" name="road-width"
                value="2.0">
            </div>
            <div class="form-group">
              <label for="water-depth">Water Depth (mm)</label>
              <input type="number" step="0.1" class="form-control live-preview" id="water-depth" name="water-depth"
                value="1.4">
            </div>
            <div class="form-group">
              <label for="min-building-area">Minimum Building Area (m²)</label>
              <input type="number" step="0.1" class="form-control live-preview" id="min-building-area"
                name="min-building-area" value="600.0">
            </div>
            <div class="form-group form-check">
              <input type="checkbox" class="form-check-input live-preview" id="debug" name="debug">
              <label class="form-check-label" for="debug">Enable Debug Output</label>
            </div>
          </fieldset>

          <!-- Bridge Options -->
          <fieldset class="border p-3 mb-3">
            <legend class="w-auto">Bridge Options</legend>
            <div class="form-group">
              <label for="bridge-height">Bridge Deck Height Above Base</label>
              <input type="number" step="0.1" class="form-control live-preview" id="bridge-height" name="bridge-height"
                value="2.0">
            </div>
            <div class="form-group">
              <label for="bridge-thickness">Bridge Deck Thickness</label>
              <input type="number" step="0.1" class="form-control live-preview" id="bridge-thickness"
                name="bridge-thickness" value="1.0">
            </div>
            <div class="form-group">
              <label for="support-width">Bridge Support Radius</label>
              <input type="number" step="0.1" class="form-control live-preview" id="support-width" name="support-width"
                value="2.0">
            </div>
          </fieldset>

          <!-- Export Options -->
          <fieldset class="border p-3 mb-3">
            <legend class="w-auto">Export Options</legend>
            <div class="form-group">
              <label for="export">Export Format</label>
              <select class="form-control live-preview" id="export" name="export">
                <option value="preview">Preview</option>
                <option value="stl">STL</option>
                <option value="both" selected>Both</option>
              </select>
            </div>
            <div class="form-group">
              <label for="output-stl">Output STL Filename</label>
              <input type="text" class="form-control live-preview" id="output-stl" name="output-stl"
                placeholder="Optional">
            </div>
            <div class="form-group form-check">
              <input type="checkbox" class="form-check-input live-preview" id="no-repair" name="no-repair">
              <label class="form-check-label" for="no-repair">Disable Automatic Geometry Repair</label>
            </div>
            <div class="form-group form-check">
              <input type="checkbox" class="form-check-input live-preview" id="force" name="force">
              <label class="form-check-label" for="force">Force STL Generation on Validation Failure</label>
            </div>
          </fieldset>

          <!-- Preview & Integration Options -->
          <fieldset class="border p-3 mb-3">
            <legend class="w-auto">Preview &amp; Integration Options</legend>
            <div class="form-group">
              <label>Preview Image Size (Width, Height in pixels)</label>
              <div class="form-row">
                <div class="col">
                  <input type="number" class="form-control live-preview" placeholder="Width" name="preview-size-width"
                    value="1080">
                </div>
                <div class="col">
                  <input type="number" class="form-control live-preview" placeholder="Height" name="preview-size-height"
                    value="1080">
                </div>
              </div>
            </div>
            <div class="form-group">
              <label for="preview-file">Preview Image Filename</label>
              <input type="text" class="form-control live-preview" id="preview-file" name="preview-file"
                placeholder="Optional">
            </div>
            <div class="form-group form-check">
              <input type="checkbox" class="form-check-input live-preview" id="watch" name="watch">
              <label class="form-check-label" for="watch">Watch SCAD File and Auto-Reload</label>
            </div>
            <div class="form-group">
              <label for="openscad-path">OpenSCAD Executable Path</label>
              <input type="text" class="form-control live-preview" id="openscad-path" name="openscad-path"
                placeholder="Optional">
            </div>
          </fieldset>

          <!-- Final Render Button -->
          <button type="button" id="renderBtn" class="btn btn-success mb-3">Render Final Model</button>
        </form>
      </div>

      <!-- Right Column: Live Previews and Downloadable Files -->
      <div class="col-md-8">
        <div class="processing-indicator">
          Processing changes... Preview will update in 2 seconds.
        </div>

        <div class="preview-container">
          <h3>Live Preview - Main Model</h3>
          <img id="previewMain" src="" alt="Main Model Preview" style="display: none;">
        </div>

        <div class="preview-container">
          <h3>Live Preview - Frame Model</h3>
          <img id="previewFrame" src="" alt="Frame Model Preview" style="display: none;">
        </div>

        <div class="log-container">
          <h4>Live Log</h4>
          <div id="liveLog"></div>
        </div>

        <div class="download-links mt-4">
          <h4>Download Rendered Files</h4>
          <div id="downloadLinks">
            <!-- Links will be inserted here after final render -->
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    // Debounce function to limit how often a function can be called
    function debounce(func, wait) {
      let timeout;
      return function executedFunction(...args) {
        // Show processing indicator
        $(".processing-indicator").show();

        const later = () => {
          clearTimeout(timeout);
          $(".processing-indicator").hide();
          func(...args);
        };

        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
      };
    }

    // Function to update the live preview images
    function updatePreview() {
      var uploadedFile = $("#uploadedFile").val();
      if (!uploadedFile) {
        console.log("No file uploaded yet.");
        return;
      }

      $("#liveLog").text("Generating preview...");

      var formData = $("#optionsForm").serializeArray();
      formData.push({ name: "uploadedFile", value: uploadedFile });

      $.ajax({
        url: "/preview",
        type: "POST",
        data: formData,
        success: function (data) {
          if (data.previewMain && data.previewFrame) {
            $("#previewMain").attr("src", data.previewMain + "?t=" + new Date().getTime()).show();
            $("#previewFrame").attr("src", data.previewFrame + "?t=" + new Date().getTime()).show();
          }

          var logText = "";
          if (data.stdout) {
            logText += data.stdout + "\n";
          }
          if (data.stderr) {
            logText += data.stderr + "\n";
          }
          if (logText.trim().length > 0) {
            $("#liveLog").text(logText);
          }
        },
        error: function (err) {
          console.error("Preview update error:", err);
          $("#liveLog").text("Error generating preview:\n" + JSON.stringify(err));
        }
      });
    }

    // Create debounced version of updatePreview with 2 second delay
    const debouncedUpdatePreview = debounce(updatePreview, 2000);

    // Handle file upload
    $("#geojson").on("change", function () {
      var fileInput = document.getElementById("geojson");
      if (fileInput.files.length === 0) return;

      var formData = new FormData();
      formData.append("geojson", fileInput.files[0]);

      $.ajax({
        url: "/uploadFile",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        success: function (data) {
          if (data.filePath) {
            $("#uploadedFile").val(data.filePath);
            debouncedUpdatePreview();
          }
        },
        error: function (err) {
          console.error("File upload error:", err);
          $("#liveLog").text("Error uploading file:\n" + JSON.stringify(err));
        }
      });
    });

    // Update live preview when any option changes
    $(".live-preview").on("change keyup", function () {
      debouncedUpdatePreview();
    });

    // Handle final render button click
    $("#renderBtn").on("click", function () {
      var uploadedFile = $("#uploadedFile").val();
      if (!uploadedFile) {
        alert("Please upload a GeoJSON file first.");
        return;
      }

      $("#liveLog").text("Generating final render...");
      var formData = $("#optionsForm").serializeArray();
      formData.push({ name: "uploadedFile", value: uploadedFile });

      $.ajax({
        url: "/render",
        type: "POST",
        data: formData,
        success: function (data) {
          var linksHtml = "";

          if (data.mainScad) {
            linksHtml += '<a href="' + data.mainScad + '" download>Main Model (SCAD)</a><br>';
          }
          if (data.frameScad) {
            linksHtml += '<a href="' + data.frameScad + '" download>Frame Model (SCAD)</a><br>';
          }

          if (data.stlFiles && data.stlFiles.mainStl) {
            linksHtml += '<a href="' + data.stlFiles.mainStl + '" download>Main Model (STL)</a><br>';
          }
          if (data.stlFiles && data.stlFiles.frameStl) {
            linksHtml += '<a href="' + data.stlFiles.frameStl + '" download>Frame Model (STL)</a><br>';
          }

          if (data.logFile) {
            linksHtml += '<a href="' + data.logFile + '" download>Debug Log</a><br>';
          }

          $("#downloadLinks").html(linksHtml);

          var logText = "";
          if (data.stdout) {
            logText += data.stdout + "\n";
          }
          if (data.stderr) {
            logText += data.stderr + "\n";
          }
          if (logText.trim().length > 0) {
            $("#liveLog").text(logText);
          }
        },
        error: function (err) {
          console.error("Final render error:", err);
          $("#liveLog").text("Error during final render:\n" + JSON.stringify(err));
          alert("An error occurred during final render.");
        }
      });
    });
  </script>
</body>

</html>
```

# views/result.ejs

```ejs
<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <title>Generation Result</title>
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <link rel="stylesheet" href="/css/style.css">
</head>

<body>
  <div class="container">
    <h1 class="mt-5">Generation Result</h1>
    <p class="lead">The Shadow City model has been generated. Download the output files below:</p>
    <ul class="list-group">
      <li class="list-group-item">
        <a href="<%= mainScad %>" download>Main Model (SCAD)</a>
      </li>
      <li class="list-group-item">
        <a href="<%= frameScad %>" download>Frame Model (SCAD)</a>
      </li>
      <% if (stlFiles && stlFiles.mainStl) { %>
        <li class="list-group-item">
          <a href="<%= stlFiles.mainStl %>" download>Main Model (STL)</a>
        </li>
        <li class="list-group-item">
          <a href="<%= stlFiles.frameStl %>" download>Frame Model (STL)</a>
        </li>
        <% } %>
          <li class="list-group-item">
            <a href="<%= logFile %>" download>Debug Log</a>
          </li>
    </ul>
    <hr>
    <h3>Process Output</h3>
    <div class="card">
      <div class="card-body">
        <h5>Standard Output</h5>
        <pre><%= stdout %></pre>
        <h5>Error Output</h5>
        <pre><%= stderr %></pre>
      </div>
    </div>
    <a href="/" class="btn btn-secondary mt-3">Back to Home</a>
  </div>
</body>

</html>
```

