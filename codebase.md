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
import sys
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
        # Prepare style settings; detailed logs are only enabled if --debug is passed.
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

        # Create the converter and explicitly set debug based on the flag.
        converter = EnhancedCityConverter(
            size_mm=args.size, max_height_mm=args.height, style_settings=style_settings
        )
        converter.debug = args.debug  # When --debug is not passed, debug is False.
        converter.layer_specs["roads"]["width"] = args.road_width
        converter.layer_specs["water"]["depth"] = args.water_depth

        # Process input data (with optional preprocessing)
        if args.preprocess:
            if not (args.crop_distance or args.crop_bbox):
                parser.error("When --preprocess is enabled, either --crop-distance or --crop-bbox must be specified")
            preprocessor = GeoJSONPreprocessor(
                bbox=args.crop_bbox, distance_meters=args.crop_distance
            )
            preprocessor.debug = args.debug
            converter.convert_preprocessed(args.input_json, args.output_scad, preprocessor)
        else:
            converter.convert(args.input_json, args.output_scad)

        # Print a concise summary of processed features.
        print("\nConversion complete. Processed feature counts:", flush=True)
        features = converter.style_manager.current_features
        for category, items in features.items():
            print(f"  {category}: {len(items)}", flush=True)

        # Generate preview image.
        integration = OpenSCADIntegration()
        preview_size = [1080, 1080]
        preview_file = args.output_scad.replace(".scad", "_preview.png")
        print("\nGenerating preview image...", flush=True)
        integration.generate_preview(args.output_scad, preview_file, size=preview_size)
        print(f"Preview generated successfully: {preview_file}", flush=True)

        # Generate STL files.
        print("\nGenerating STL files...", flush=True)
        stl_file = args.output_scad.replace(".scad", ".stl")
        integration.generate_stl(args.output_scad, stl_file)

    except Exception as e:
        print(f"Error: {str(e)}", flush=True)
        raise

if __name__ == "__main__":
    main()

```

# lib/__init__.py

```py

```

# lib/config.py

```py
# lib/config.py
from typing import Dict, Any, List, Set

class Config:
    """Central configuration management for Shadow City Generator

    This class defines all the key constants and default settings that control:
      • How features are recognized (buildings, water, roads, etc.)
      • Default artistic style settings (merging, detail, height variance, etc.)
      • Layer-specific parameters (depths, widths, minimum areas)
      • Industrial, green space, and building cluster behavior

    Changing these values will directly affect the generated 3D model. For example:
      - Increasing 'merge_distance' in DEFAULT_STYLE will make nearby buildings merge more aggressively.
      - Adjusting 'min_building_area' will filter out smaller structures from being included.
      - Altering water or road dimensions in DEFAULT_LAYER_SPECS changes the physical proportions in the model.
    """

    # -----------------------------------------------------------------------------
    # Feature Types and Tags
    # -----------------------------------------------------------------------------
    # These keys map common OpenStreetMap (OSM) tags to internal identifiers.
    # Changing these values would change how the generator categorizes input features.
    FEATURE_TYPES = {
        'BUILDING': 'building',
        'WATER': 'water',
        'HIGHWAY': 'highway',
        'RAILWAY': 'railway',
        'INDUSTRIAL': 'industrial',
        'LEISURE': 'leisure',
        'LANDUSE': 'landuse',
        'AMENITY': 'amenity',
        'NATURAL': 'natural',
        'BRIDGE': 'bridge'
    }

    # -----------------------------------------------------------------------------
    # Industrial Feature Recognition
    # -----------------------------------------------------------------------------
    # These sets determine which landuse or building tags are treated as "industrial."
    # Modifying these lists affects which features are processed with industrial rules,
    # including using different height multipliers and merging strategies.
    INDUSTRIAL_LANDUSE: Set[str] = {
        'industrial',
        'construction',
        'depot',
        'logistics',
        'port',
        'warehouse'
    }
    
    INDUSTRIAL_BUILDINGS: Set[str] = {
        'industrial',
        'warehouse',
        'factory',
        'manufacturing',
        'hangar'
    }

    # -----------------------------------------------------------------------------
    # Default Style Settings
    # -----------------------------------------------------------------------------
    # These settings are used if the user does not override them via command-line options.
    # They affect building merging, cluster formation, artistic height variation, and overall style.
    # • merge_distance: How close buildings must be to merge. Increasing this makes clusters larger.
    # • cluster_size: Threshold for grouping buildings. Higher values result in fewer, larger clusters.
    # • height_variance: Degree of variation in building heights. Higher values yield more dramatic differences.
    # • detail_level: Controls architectural detail; higher levels add more intricate shapes.
    # • artistic_style: Determines the overall look ('modern', 'classic', 'minimal', or 'block-combine').
    # • min_building_area: Minimum footprint (in m²) to include a building. Raising this ignores small structures.
    DEFAULT_STYLE: Dict[str, Any] = {
        'merge_distance': 2.0,
        'cluster_size': 3.0,
        'height_variance': 0.2,
        'detail_level': 1.0,
        'artistic_style': 'modern',
        'min_building_area': 200.0
    }

    # List of allowed artistic styles.
    # To add a new style, include it here and update related style generators.
    ARTISTIC_STYLES: List[str] = ['modern', 'classic', 'minimal', 'block-combine']

    # -----------------------------------------------------------------------------
    # Default Layer Specifications
    # -----------------------------------------------------------------------------
    # These settings define the geometry (depths, widths, etc.) for different layers in the model.
    # Adjust these to modify the physical proportions:
    #   • water: Depth and minimum area to be recognized as water.
    #   • roads: Base width, depth, and multipliers for different road types.
    #   • railways: Depth and width for railway features.
    #   • parks: Vertical offset and thickness for parks/green spaces.
    #   • buildings: Default building height range and per-level height.
    #   • base: The thickness of the supporting base.
    #   • bridges: Dimensions for bridge decks and supports.
    DEFAULT_LAYER_SPECS: Dict[str, Dict[str, Any]] = {
        'water': {
            'depth': 1.12,          # Changing this makes water features appear deeper or shallower.
            'min_area': 10.0       # Only water features with area above this (in m²) are rendered.
        },
        'roads': {
            'depth': 0.28,          # The vertical "cut" into the base for roads.
            'width': 1.0,          # Base road width; multiplied by road type factors.
            'types': {
                'motorway': 2.0,   # Motorways appear wider (2× the base width).
                'trunk': 1.8,
                'primary': 1.5,
                'secondary': 1.2,
                'residential': 1.0,
                'service': 0.8
            }
        },
        'railways': {
            'depth': 0.56,
            'width': 1.5         # Wider railways yield thicker lines in the model.
        },
        'parks': {
            'start_offset': 0,  # Vertical offset from the base at which parks start.
            'thickness': 0.42,     # Extrusion height for park areas.
            'min_area': 100.0     # Parks smaller than this (in m²) are ignored.
        },
        'buildings': {
            'min_height': 2,         # Minimum height for buildings in mm.
            'max_height': 8,         # Maximum height for buildings in mm.
            'default_height': 4,     # Default height used if no specific value is provided.
            'levels_height': 3.0     # Height per building level; used when calculating from 'building:levels'.
        },
        'base': {
            'height': 3            # The thickness of the base block; increasing this raises the entire model.
        },
        'bridges': {
            'height': 2.0,         # How high above the base the bridge deck is placed.
            'thickness': 0.6,      # Thickness of the bridge deck.
            'support_width':  {
                'road': 2.0, # Diameter of the bridge support columns.
                'rail': 2.0
            },
            'min_size': 10.0,     # Minimum area (in m²) for a bridge to be recognized.
            'assumed_width': {
                'road': 3.0, # Assumed width for bridges without explicit width data.
                'rail': 2.0
            }
        }
    }


    # -----------------------------------------------------------------------------
    # Industrial Area Settings
    # -----------------------------------------------------------------------------
    # These settings modify how industrial features are processed:
    #   • height_multipliers: Factors by which base heights are multiplied for different industrial types.
    #   • min_area: Minimum area (in m²) for an industrial feature to be processed.
    #   • default_height: Fallback height if no other info is provided.
    # Changing multipliers will make certain industrial buildings appear taller or shorter relative to others.
    INDUSTRIAL_SETTINGS: Dict[str, Any] = {
        'height_multipliers': {
            'industrial': 1.0,
            'construction': 1.5,
            'depot': 1.5,
            'logistics': 1.8,
            'port': 2.0,
            'warehouse': 1.2,
            'factory': 2.0,
            'manufacturing': 1.8,
            'hangar': 1.6
        },
        'min_area': 400.0,           # Industrial features smaller than 400 m² are typically ignored.
        'default_height': 5.0       # Default industrial building height in mm if no specific info exists.
    }

    # -----------------------------------------------------------------------------
    # Park and Green Space Types
    # -----------------------------------------------------------------------------
    # These sets determine which OSM tags are recognized as green spaces.
    # Changing these values can include or exclude features based on their landuse or leisure tag.
    GREEN_LANDUSE: Set[str] = {
        'grass',
        'forest',
        'meadow',
        'village_green',
        'farmland',
        'orchard'
    }

    GREEN_LEISURE: Set[str] = {
        'park',
        'garden',
        'golf_course',
        'recreation_ground',
        'pitch',
        'playground'
    }

    # -----------------------------------------------------------------------------
    # Block Types and Settings
    # -----------------------------------------------------------------------------
    # Block types are used when combining buildings into clusters (especially in "block-combine" style).
    # They include minimum/maximum heights and preset roof style options.
    # Adjusting these values changes the overall proportions and roof details of clusters.
    BLOCK_TYPES: Dict[str, Dict[str, Any]] = {
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
            'max_height': 20.0,
            'roof_styles': [
                {'name': 'sawtooth', 'angle': 30},
                {'name': 'flat', 'border': 2.0},
                {'name': 'stepped', 'levels': 2}
            ]
        },
        'commercial': {
            'min_height': 20.0,
            'max_height': 40.0,
            'roof_styles': [
                {'name': 'modern', 'setback': 2.0},
                {'name': 'tiered', 'levels': 2},
                {'name': 'complex', 'variations': 5}
            ]
        }
    }

    # -----------------------------------------------------------------------------
    # Roof Style Configurations
    # -----------------------------------------------------------------------------
    # These configurations define the ranges and default values for various roof styles.
    # Modifying these ranges affects how roofs are generated—for instance, a higher 'default_angle'
    # in the 'sawtooth' style will produce steeper roof slopes.
    ROOF_STYLES: Dict[str, Dict[str, Any]] = {
        'pitched': {
            'height_factor_range': (0.2, 0.4),
            'default_factor': 0.3
        },
        'tiered': {
            'levels_range': (2, 4),
            'default_levels': 2
        },
        'flat': {
            'border_range': (0.8, 1.2),
            'default_border': 1.0
        },
        'sawtooth': {
            'angle_range': (25, 35),
            'default_angle': 30
        },
        'modern': {
            'setback_range': (1.8, 2.2),
            'default_setback': 2.0
        },
        'stepped': {
            'levels_range': (2, 4),
            'default_levels': 2
        }
    }

    # -----------------------------------------------------------------------------
    # Geometry Processing Settings
    # -----------------------------------------------------------------------------
    # These parameters affect how raw geometry from GeoJSON is processed:
    #   • simplification_tolerance: Higher values simplify geometry more aggressively (may lose detail).
    #   • min_points_polygon / min_points_linestring: Minimum required points for valid geometry.
    #   • buffer_distance: Controls extra padding for buffering linear features.
    #   • merge_threshold: Minimum distance for considering points distinct.
    GEOMETRY_SETTINGS: Dict[str, Any] = {
        'simplification_tolerance': 0.1,
        'min_points_polygon': 3,
        'min_points_linestring': 2,
        'buffer_distance': {
            'roads': 1.0,
            'railways': 1.0,
            'water': 1.5
        },
        'merge_threshold': 0.001  # If set too high, nearby distinct points may merge unexpectedly.
    }

    # -----------------------------------------------------------------------------
    # Processing Settings
    # -----------------------------------------------------------------------------
    # These settings control overall processing behavior during feature combination:
    #   • area_threshold: Minimum area (in m²) for merging buildings in "block-combine" style.
    #   • min_cluster_size / max_cluster_size: Limits for cluster formation.
    #   • barrier_buffer: Extra spacing around barriers (e.g., roads or water) used during merging.
    # Tuning these values alters how aggressively small features merge into clusters.
    PROCESSING_SETTINGS: Dict[str, Any] = {
        'area_threshold': 1000,  # Increasing this value causes more buildings to merge into clusters.
        'min_cluster_size': 2,  # Fewer clusters will form if this number is raised.
        'max_cluster_size': 7,  # Was 10, Prevents clusters from becoming excessively large.
        'barrier_buffer': 0.5,  # Was 1 A larger buffer prevents merging across barriers.
    }

    # -----------------------------------------------------------------------------
    # Class Methods for Helper Operations
    # -----------------------------------------------------------------------------
    @classmethod
    def get_road_width(cls, road_type: str) -> float:
        """Get road width multiplier for a specific road type.
        
        The returned multiplier is used to scale the base road width.
        """
        return cls.DEFAULT_LAYER_SPECS['roads']['types'].get(road_type, 1.0)

    @classmethod
    def get_industrial_height_multiplier(cls, building_type: str) -> float:
        """Get height multiplier for a specific industrial building type.
        
        This multiplier influences how much taller an industrial building appears.
        """
        return cls.INDUSTRIAL_SETTINGS['height_multipliers'].get(
            building_type, 
            cls.INDUSTRIAL_SETTINGS['height_multipliers']['industrial']
        )

    @classmethod
    def is_industrial_feature(cls, properties: Dict[str, Any]) -> bool:
        """Determine whether a feature should be processed as industrial.
        
        Checks both the 'building' and 'landuse' properties against known industrial tags.
        """
        if not properties:
            return False
            
        building = properties.get('building', '').lower()
        if building in cls.INDUSTRIAL_BUILDINGS:
            return True
            
        landuse = properties.get('landuse', '').lower()
        if landuse in cls.INDUSTRIAL_LANDUSE:
            return True
            
        return False

    @classmethod
    def is_green_space(cls, properties: Dict[str, Any]) -> bool:
        """Determine whether a feature should be processed as green space.
        
        Considers both 'landuse' and 'leisure' tags. Adjusting GREEN_LANDUSE or GREEN_LEISURE
        alters which features are rendered as parks or gardens.
        """
        landuse = properties.get('landuse', '').lower()
        leisure = properties.get('leisure', '').lower()
        return landuse in cls.GREEN_LANDUSE or leisure in cls.GREEN_LEISURE

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
        self.layer_specs = self.style_manager.get_default_layer_specs()
        
        # Initialize bridge specs
        self.layer_specs["bridges"] = {
            "height": style_settings.get("bridge_height", 2.0),
            "thickness": style_settings.get("bridge_thickness", 1.0),
            "support_width": style_settings.get("support_width", 2.0),
        }

    def print_debug(self, *args):
        message = " ".join(str(arg) for arg in args)
        if self.debug:
            print(message)
            self.debug_log.append(message)

    def convert(self, input_file, output_file):
        """Standard conversion without preprocessing"""
        with open(input_file) as f:
            data = json.load(f)
        self._process_data(data, output_file)

    def convert_preprocessed(self, input_file, output_file, preprocessor):
        """Conversion with preprocessing"""
        with open(input_file) as f:
            data = json.load(f)
        processed_data = preprocessor.process_geojson(data)
        self._process_data(processed_data, output_file)

    def _process_data(self, data, output_file):
        """Shared processing pipeline"""
        try:
            # Process features
            self._log_processing_start()
            features = self.feature_processor.process_features(data, self.size)

            # Generate SCAD components
            main_scad, frame_scad = self._generate_scad_components(features)

            # Write outputs
            main_path, frame_path = self._write_output_files(
                output_file, main_scad, frame_scad
            )

            # Final logging
            self._log_success(main_path, frame_path)
            self._write_debug_log(output_file)

        except Exception as e:
            print(f"Error: {str(e)}")
            raise

    def _generate_scad_components(self, features):
        """Generate both main and frame SCAD code"""
        return (
            self.scad_generator.generate_openscad(features, self.size, self.layer_specs),
            self._generate_frame(self.size, self.max_height)
        )

    def _write_output_files(self, output_file, main_scad, frame_scad):
        """Handle file writing operations"""
        main_path = output_file.replace(".scad", "_main.scad")
        frame_path = output_file.replace(".scad", "_frame.scad")

        with open(main_path, "w") as f:
            f.write(main_scad)
        with open(frame_path, "w") as f:
            f.write(frame_scad)

        return main_path, frame_path

    def _log_processing_start(self):
        """Initial debug logging"""
        self.print_debug("\nProcessing features...")
        self.print_debug("\nGenerating main model OpenSCAD code...")

    def _log_success(self, main_path, frame_path):
        """Success state logging"""
        self.print_debug(f"\nSuccessfully created main model: {main_path}")
        self.print_debug(f"Successfully created frame: {frame_path}")
        self.print_debug("Style settings used:")
        for key, value in self.style_manager.style.items():
            self.print_debug(f"  {key}: {value}")

    def _write_debug_log(self, output_file):
        """Write debug log if enabled"""
        if self.debug:
            log_path = output_file + ".log"
            with open(log_path, "w") as f:
                f.write("\n".join(self.debug_log))
            self.print_debug(f"\nDebug log written to {log_path}")

    def _generate_frame(self, size, height):
        """Generate frame SCAD code (unchanged from original)"""
        frame_size = size + 10
        return f"""// Frame for city model
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

        # Only skip small buildings if not using block-combine style.
        #if (self.style_manager.style.get("artistic_style") != "block-combine") and (area_m2 < min_area):
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
from typing import Dict, Any, Optional, List, Tuple
from shapely.geometry import Polygon
from .base_processor import BaseProcessor
from ..config import Config

class IndustrialProcessor(BaseProcessor):
    """
    Handles processing of industrial buildings and areas, using centralized configuration
    for consistent handling of industrial features.
    """
    
    def process_industrial_building(self, feature: Dict[str, Any], features: Dict[str, list], transform) -> None:
        """
        Process an industrial building with specific industrial characteristics.
        
        Args:
            feature: GeoJSON feature to process
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
        """
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return
            
        area_m2 = self.geometry.approximate_polygon_area_m2(coords)
        min_area = Config.INDUSTRIAL_SETTINGS['min_area']
        
        # Skip small buildings unless using block-combine style
        if (self.style_manager.style.get("artistic_style") != "block-combine") and (area_m2 < min_area):
            self._log_debug(f"Skipping small industrial building with area {area_m2:.1f}m²")
            return
            
        transformed = [transform(lon, lat) for lon, lat in coords]
        height = self._calculate_industrial_height(props)
        
        features["industrial"].append({
            "coords": transformed,
            "height": height,
            "is_industrial": True,
            "building_type": props.get("building", "industrial")
        })
        
        self._log_debug(f"Added industrial building, height {height:.1f}mm, area {area_m2:.1f}m²")

    def process_industrial_area(self, feature: Dict[str, Any], features: Dict[str, list], transform) -> None:
        """
        Process industrial landuse areas as specialized building features.
        
        Args:
            feature: GeoJSON feature to process
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
        """
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return
            
        # Verify industrial landuse type
        landuse = props.get("landuse", "").lower()
        if landuse not in Config.INDUSTRIAL_LANDUSE:
            return
            
        transformed = [transform(lon, lat) for lon, lat in coords]
        area_m2 = self.geometry.approximate_polygon_area_m2(coords)
        
        # Skip small areas unless using block-combine style
        if (self.style_manager.style.get("artistic_style") != "block-combine") and (area_m2 < Config.INDUSTRIAL_SETTINGS['min_area']):
            self._log_debug(f"Skipping small industrial area with area {area_m2:.1f}m²")
            return
            
        height = self._calculate_industrial_area_height(landuse)
        
        features["industrial"].append({
            "coords": transformed,
            "height": height,
            "is_industrial": True,
            "landuse_type": landuse
        })
        
        self._log_debug(f"Added industrial area type '{landuse}' with height {height:.1f}mm")

    def should_process_as_industrial(self, properties: Dict[str, Any]) -> bool:
        """
        Check if a feature should be processed as industrial using Config helper.
        
        Args:
            properties: Feature properties to check
            
        Returns:
            bool: True if feature should be processed as industrial
        """
        return Config.is_industrial_feature(properties)

    def _calculate_industrial_height(self, properties: Dict[str, Any]) -> float:
        """
        Calculate height for industrial building using explicit height or type-based multiplier.
        
        Args:
            properties: Building properties
            
        Returns:
            float: Calculated height in mm
        """
        explicit_height = self._get_explicit_height(properties)
        if explicit_height is not None:
            # Apply industrial multiplier to explicit height
            base_height = self.style_manager.scale_building_height({
                "height": str(explicit_height)
            })
            return base_height * 1.1  # Bonus for industrial buildings
            
        # Use type-based height calculation
        building_type = properties.get("building", "industrial")
        multiplier = Config.get_industrial_height_multiplier(building_type)
        
        layer_specs = self.style_manager.get_default_layer_specs()
        min_height = layer_specs["buildings"]["min_height"]
        max_height = layer_specs["buildings"]["max_height"]
        
        return min(max_height, min_height * multiplier)

    def _calculate_industrial_area_height(self, landuse_type: str) -> float:
        """
        Calculate height for industrial landuse area.
        
        Args:
            landuse_type: Type of industrial landuse
            
        Returns:
            float: Calculated height in mm
        """
        multiplier = Config.get_industrial_height_multiplier(landuse_type)
        
        layer_specs = self.style_manager.get_default_layer_specs()
        min_height = layer_specs["buildings"]["min_height"]
        max_height = layer_specs["buildings"]["max_height"]
        
        return min(max_height, min_height * multiplier)

    def _get_explicit_height(self, properties: Dict[str, Any]) -> Optional[float]:
        """
        Extract explicit height from properties if available.
        
        Args:
            properties: Feature properties
            
        Returns:
            Optional[float]: Explicit height in meters if available
        """
        if "height" in properties:
            try:
                height_str = properties["height"].split()[0]  # Handle "10 m" format
                return float(height_str)
            except (ValueError, IndexError):
                pass
                
        if "building:levels" in properties:
            try:
                levels = float(properties["building:levels"])
                return levels * Config.DEFAULT_LAYER_SPECS["buildings"]["levels_height"]
            except ValueError:
                pass
                
        return None

    def _log_debug(self, message: str) -> None:
        """
        Wrapper for debug logging.
        
        Args:
            message: Debug message to log
        """
        if self.debug:
            print(message)
```

# lib/feature_processor/linear_processor.py

```py
# lib/feature_processor/linear_processor.py
from .base_processor import BaseProcessor

class LinearFeatureProcessor(BaseProcessor):
    """
    Base class for processing linear features like roads and railways.
    Handles common tunnel checks and coordinate transformations.
    """
    
    FEATURE_TYPE = None  # Must be set by subclasses
    
    def process_linear_feature(self, feature, features, transform, additional_tags=None):
        """
        Shared processing logic for linear features.
        Args:
            additional_tags: Extra properties to preserve (e.g., bridge status)
        """
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        # Skip tunnels
        if self._is_tunnel(props):
            if self.debug:
                print(f"Skipping tunnel {self.FEATURE_TYPE}: {props.get(self.FEATURE_TYPE)}")
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) < 2:
            return

        # Create feature dictionary
        feature_data = {
            "coords": transformed,
            "type": props.get(self.FEATURE_TYPE, "unknown"),
            "is_parking": False,
        }

        # Preserve additional properties if specified
        if additional_tags:
            for tag in additional_tags:
                if tag in props:
                    feature_data[tag] = props[tag]

        features[self.feature_category].append(feature_data)
        
        if self.debug:
            print(f"Added {self.FEATURE_TYPE} '{feature_data['type']}', {len(transformed)} points")

    def _is_tunnel(self, props):
        """Check if the feature is a tunnel (common for roads/railways)"""
        return props.get("tunnel") in ["yes", "true", "1"]

# lib/feature_processor/road_processor.py
from .linear_processor import LinearFeatureProcessor

class RoadProcessor(LinearFeatureProcessor):
    """Handles road and bridge features, inheriting core linear processing"""
    
    FEATURE_TYPE = "highway"
    feature_category = "roads"

    def process_road_or_bridge(self, feature, features, transform):
        """Special handling for bridges"""
        props = feature.get("properties", {})
        
        # First do common processing
        super().process_linear_feature(
            feature, 
            features, 
            transform,
            additional_tags=["bridge"]  # Preserve bridge status
        )
        
        # Special bridge handling
        if props.get("bridge"):
            coords = self.geometry.extract_coordinates(feature)
            transformed = [transform(lon, lat) for lon, lat in coords]
            features["bridges"].append({
                "coords": transformed,
                "type": props.get("highway", "bridge")
            })

    def process_parking(self, feature, features, transform):
        """Parking-specific logic remains here"""
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) >= 3:
            features[self.feature_category].append({
                "coords": transformed,
                "type": "parking",
                "is_parking": True
            })

    def is_parking_area(self, props):
        """Parking-specific check remains here"""
        return (
            props.get("amenity") == "parking"
            or props.get("parking") == "surface"
            or props.get("service") == "parking_aisle"
        )

```

# lib/feature_processor/park_processor.py

```py
# lib/feature_processor/park_processor.py
from typing import Dict, Any, Optional
from shapely.geometry import Polygon
from .base_processor import BaseProcessor
from ..config import Config

class ParkProcessor(BaseProcessor):
    """
    Processes OSM features for green spaces and parks.
    Uses centralized configuration for consistent handling of leisure and landuse features.
    """

    def process_park(self, feature: Dict[str, Any], features: Dict[str, list], transform) -> None:
        """
        Process a park or green space feature, applying appropriate settings and transformations.
        
        Args:
            feature: GeoJSON feature to process
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
        """
        props = feature.get("properties", {})
        geometry_type = feature["geometry"]["type"]

        # Skip if not a recognized green space type
        if not self._is_valid_green_space(props):
            return

        # Extract and validate coordinates
        coords = self.geometry.extract_coordinates(feature)
        if not coords or len(coords) < 3:
            return

        # Check minimum area requirement
        area_m2 = self.geometry.approximate_polygon_area_m2(coords)
        min_area = Config.DEFAULT_LAYER_SPECS["parks"]["min_area"]
        
        if area_m2 < min_area:
            self._log_debug(f"Skipping small green space with area {area_m2:.1f}m²")
            return

        # Process valid polygon geometries
        if geometry_type in ["Polygon", "MultiPolygon"]:
            self._process_green_space_polygon(coords, features, transform, props)

    def _process_green_space_polygon(
        self, 
        coords: list, 
        features: Dict[str, list], 
        transform,
        props: Dict[str, Any]
    ) -> None:
        """
        Process a valid green space polygon with appropriate styling.
        
        Args:
            coords: List of coordinate pairs
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
            props: Feature properties
        """
        transformed = [transform(lon, lat) for lon, lat in coords]
        
        # Get park specifications from config
        park_specs = self.style_manager.get_default_layer_specs()["parks"]
        
        feature_data = {
            "coords": transformed,
            "type": self._determine_green_space_type(props),
            "height": park_specs["thickness"],
            "offset": park_specs["start_offset"]
        }
        
        features["parks"].append(feature_data)
        
        self._log_debug(
            f"Added {feature_data['type']} green space with {len(transformed)} points"
        )

    def _is_valid_green_space(self, props: Dict[str, Any]) -> bool:
        """
        Check if properties indicate a valid green space using Config settings.
        
        Args:
            props: Feature properties
            
        Returns:
            bool: True if feature is a valid green space
        """
        return Config.is_green_space(props)

    def _determine_green_space_type(self, props: Dict[str, Any]) -> str:
        """
        Determine the specific type of green space for styling purposes.
        
        Args:
            props: Feature properties
            
        Returns:
            str: Specific type of green space
        """
        # Check landuse first
        landuse = props.get("landuse", "").lower()
        if landuse in Config.GREEN_LANDUSE:
            return landuse

        # Check leisure second
        leisure = props.get("leisure", "").lower()
        if leisure in Config.GREEN_LEISURE:
            return leisure

        # Default fallback
        return "park"

    def _get_height_for_type(self, green_space_type: str) -> float:
        """
        Get appropriate height for specific type of green space.
        
        Args:
            green_space_type: Type of green space
            
        Returns:
            float: Height in mm for the green space
        """
        park_specs = self.style_manager.get_default_layer_specs()["parks"]
        
        # Could extend this with type-specific heights in the future
        return park_specs["thickness"]

    def _should_add_features(self, green_space_type: str) -> bool:
        """
        Determine if additional features should be added based on type.
        
        Args:
            green_space_type: Type of green space
            
        Returns:
            bool: True if additional features should be added
        """
        # Could be extended to add trees, benches, etc. based on type
        return green_space_type in {"park", "garden", "recreation_ground"}

    def _log_debug(self, message: str) -> None:
        """
        Wrapper for debug logging.
        
        Args:
            message: Debug message to log
        """
        if self.debug:
            print(message)
```

# lib/feature_processor/railway_processor.py

```py
# lib/feature_processor/railway_processor.py
from typing import Dict, Any, List, Optional
from .linear_processor import LinearFeatureProcessor
from ..config import Config
from ..geometry import GeometryUtils



class RailwayProcessor(LinearFeatureProcessor):
    """
    Processes railway features with bridge handling capabilities.
    Inherits core linear processing from LinearFeatureProcessor.
    """
    
    FEATURE_TYPE = Config.FEATURE_TYPES['RAILWAY']
    feature_category = 'railways'

    def process_railway(self, feature: Dict[str, Any], features: Dict[str, list], transform) -> None:
        """
        Main processing method for railway features with bridge detection.
        """
        props = feature.get("properties", {})
        
        if self._is_bridge(props):
            self._process_railway_bridge(feature, features, transform)
        else:
            self._process_regular_railway(feature, features, transform)

    def _process_regular_railway(self, feature: Dict[str, Any], features: Dict[str, list], transform) -> None:
        """Process non-bridge railways using parent class logic"""
        railway_specs = self.style_manager.get_default_layer_specs()['railways']
        super()._process_linear_feature(
            feature,
            features,
            transform,
            width_override=railway_specs['width']
        )

    def _process_railway_bridge(self, feature: Dict[str, Any], features: Dict[str, list], transform) -> None:
        """Special handling for railway bridges"""
        coords = self.geometry.extract_coordinates(feature)
        if not coords or len(coords) < 2:
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        bridge_specs = self.style_manager.get_default_layer_specs()['bridges']
        railway_specs = self.style_manager.get_default_layer_specs()['railways']

        # Calculate bridge metrics
        bridge_width = railway_specs['width']
        bridge_area = self._calculate_bridge_area(transformed, bridge_width)

        if bridge_area >= bridge_specs['min_size']:
            features["bridges"].append({
                "coords": transformed,
                "type": "rail_bridge",
                "height": bridge_specs['height'],
                "thickness": bridge_specs['thickness'],
                "support_width": bridge_specs['support_width']['rail'],
                "width": bridge_width,
                "span_type": "rail"
            })
        else:
            self._process_regular_railway(feature, features, transform)

    def _is_bridge(self, props: Dict[str, Any]) -> bool:
        """Determine if the railway feature is a bridge"""
        return props.get("bridge") in ["yes", "true", "1"]

    def _calculate_bridge_area(self, coords: List[List[float]], width: float) -> float:
        """Calculate bridge area using railway geometry"""
        if len(coords) < 2:
            return 0.0
        start_point = coords[0]
        end_point = coords[-1]
        length = GeometryUtils.calculate_distance(start_point, end_point)
        return length * width
```

# lib/feature_processor/road_processor.py

```py
# lib/feature_processor/road_processor.py
from typing import Dict, Any, List, Optional
from shapely.geometry import LineString, Polygon
from .linear_processor import LinearFeatureProcessor
from ..config import Config
from ..geometry import GeometryUtils

class RoadProcessor(LinearFeatureProcessor):
    """
    Handles road and bridge features, using centralized configuration.
    Inherits core linear processing functionality from LinearFeatureProcessor.
    """
    
    FEATURE_TYPE = Config.FEATURE_TYPES['HIGHWAY']
    feature_category = 'roads'

    def process_road_or_bridge(self, feature: Dict[str, Any], features: Dict[str, list], transform) -> None:
        """
        Process roads and bridges with specialized handling.
        
        Args:
            feature: GeoJSON feature to process
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
        """
        props = feature.get("properties", {})
        road_type = props.get(self.FEATURE_TYPE)
        
        # Calculate actual road width based on road type
        base_width = self.style_manager.get_default_layer_specs()['roads']['width']
        type_multiplier = Config.get_road_width(road_type)
        actual_width = base_width * type_multiplier
        
        # Process common road features with calculated width
        self._process_linear_feature(
            feature, 
            features, 
            transform,
            width_override=actual_width,
            additional_tags=["bridge"]  # Preserve bridge status
        )
        
        # Special bridge handling if needed
        if props.get(Config.FEATURE_TYPES['BRIDGE']):
            self._process_bridge(feature, features, transform, props)

    def _process_linear_feature(
        self, 
        feature: Dict[str, Any], 
        features: Dict[str, list],
        transform,
        width_override: Optional[float] = None,
        additional_tags: Optional[List[str]] = None
    ) -> None:
        """
        Enhanced linear feature processing with width override capability.
        
        Args:
            feature: GeoJSON feature to process
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
            width_override: Optional specific width to use
            additional_tags: Optional additional properties to preserve
        """
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        # Skip tunnels
        if self._is_tunnel(props):
            self._log_debug(f"Skipping tunnel {self.FEATURE_TYPE}: {props.get(self.FEATURE_TYPE)}")
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) < 2:
            return

        # Create feature dictionary
        feature_data = {
            "coords": transformed,
            "type": props.get(self.FEATURE_TYPE, "unknown"),
            "is_parking": False,
            "width": width_override or self.style_manager.get_default_layer_specs()['roads']['width']
        }

        # Preserve additional properties if specified
        if additional_tags:
            for tag in additional_tags:
                if tag in props:
                    feature_data[tag] = props[tag]

        features[self.feature_category].append(feature_data)
        
        self._log_debug(
            f"Added {self.FEATURE_TYPE} '{feature_data['type']}' with width {feature_data['width']:.1f}mm, {len(transformed)} points"
        )

    def _process_bridge(
        self, 
        feature: Dict[str, Any], 
        features: Dict[str, list], 
        transform,
        props: Dict[str, Any]
    ) -> None:
        """
        Handle bridge-specific processing with bridge settings from config.
        
        Args:
            feature: GeoJSON feature to process
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
            props: Feature properties
        """
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) >= 2:
            # Calculate bridge area
            bridge_area = self._calculate_bridge_area(transformed)
            min_bridge_size = self.style_manager.get_default_layer_specs()['bridges']['min_size']

            # Only process as a bridge if it meets the minimum size requirement
            if bridge_area >= min_bridge_size:
                # Get bridge settings from config
                bridge_specs = self.style_manager.get_default_layer_specs()['bridges']
                
                features["bridges"].append({
                    "coords": transformed,
                    "type": props.get(self.FEATURE_TYPE, "bridge"),
                    "height": bridge_specs['height'],
                    "thickness": bridge_specs['thickness'],
                    "support_width": bridge_specs['support_width']
                })
                
                self._log_debug(f"Added bridge of type '{props.get(self.FEATURE_TYPE, 'bridge')}' with area {bridge_area:.1f}m²")
            else:
                # Process as a regular road if the bridge is too small
                self._log_debug(f"Skipping small bridge with area {bridge_area:.1f}m² (min size: {min_bridge_size}m²)")
                self._process_linear_feature(
                    feature, 
                    features, 
                    transform,
                    width_override=self.style_manager.get_default_layer_specs()['roads']['width'],
                    additional_tags=[]
                )

    def _calculate_bridge_area(self, coords: List[List[float]]) -> float:
        """
        Calculate the approximate area of a bridge based on its coordinates.
        
        Args:
            coords: List of coordinate pairs
            
        Returns:
            float: Approximate area in square meters
        """
        if len(coords) < 3:
            return 0.0

        # Calculate the length of the bridge (distance between first and last point)
        start_point = coords[0]
        end_point = coords[-1]
        length = GeometryUtils().calculate_distance(start_point, end_point)

        # Calculate the width using the road width from config
        width = self.style_manager.get_default_layer_specs()['roads']['width']

        # Approximate area as length * width
        return length * width

    def process_parking(self, feature: Dict[str, Any], features: Dict[str, list], transform) -> None:
        """
        Process parking areas as special road features.
        
        Args:
            feature: GeoJSON feature to process
            features: Dictionary of feature collections to update
            transform: Coordinate transformation function
        """
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) >= 3:  # Minimum points for a polygon
            features[self.feature_category].append({
                "coords": transformed,
                "type": "parking",
                "is_parking": True,
                "width": self.style_manager.get_default_layer_specs()['roads']['width']
            })
            
            self._log_debug(f"Added parking area with {len(transformed)} points")

    def is_parking_area(self, props: Dict[str, Any]) -> bool:
        """
        Check if feature represents a parking area.
        
        Args:
            props: Feature properties
            
        Returns:
            bool: True if the feature is a parking area
        """
        return any(
            props.get(key) in ["parking", "surface", "parking_aisle"]
            for key in [Config.FEATURE_TYPES['AMENITY'], "parking", "service"]
        )

    def _is_tunnel(self, props: Dict[str, Any]) -> bool:
        """
        Check if the feature is a tunnel.
        
        Args:
            props: Feature properties
            
        Returns:
            bool: True if the feature is a tunnel
        """
        return props.get("tunnel") in ["yes", "true", "1"]

    def _log_debug(self, message: str) -> None:
        """
        Wrapper for debug logging.
        
        Args:
            message: Debug message to log
        """
        if self.debug:
            print(message)
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
            "fa": 4,
            "fs": 0.2,
        }

    def generate_stl(self, scad_file, output_stl):
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
            command.extend(["-D", f"{param}={value}"])

        command.append(input_file)

        subprocess.run(command, env=env, capture_output=True, text=True, check=True)
```

# lib/preview/openscad_integration.py

```py
# lib/preview/openscad_integration.py
import subprocess
import os
import sys
from .preview_generator import PreviewGenerator
from .export_manager import ExportManager

class OpenSCADIntegration:
    def __init__(self, openscad_path=None):
        self.openscad_path = openscad_path or self._find_openscad()
        if not self.openscad_path:
            raise RuntimeError("Could not find OpenSCAD executable")

        self.preview_generator = PreviewGenerator(self.openscad_path)
        self.export_manager = ExportManager(self.openscad_path)

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

    def generate_preview(self, output_file, output_image, size=(1080, 1080)):
        """Generate preview images using PreviewGenerator."""
        return self.preview_generator.generate(output_file, output_image, size)

    def generate_stl(self, scad_file, output_stl):
        """Generate STL files using ExportManager."""
        return self.export_manager.generate_stl(scad_file, output_stl)
```

# lib/preview/preview_generator.py

```py
# lib/preview/preview_generator.py
import os
import subprocess


class PreviewGenerator:
    def __init__(self, openscad_path):
        self.openscad_path = openscad_path

    def generate(self, output_file, output_image, size=(1080, 1080)):
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
# lib/scad_generator.py
from typing import Dict, Optional, List
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
            roof_style = building.get("roof_style")
            roof_params = building.get("roof_params")
            is_cluster = building.get("is_cluster", False)

            if is_cluster and roof_style and roof_params:
                details = self.building_generator.generate_building_details(
                    points_str=points_str,
                    height=building_height,
                    roof_style=roof_style,
                    roof_params=roof_params
                )
            else:
                details = self.building_generator.generate_building_details(
                    points_str=points_str,
                    height=building_height
                )

            scad.append(f"""
            // Building {i+1} {'(Merged Cluster)' if is_cluster else ''}
            translate([0, 0, {base_height}]) {{
                color("white")
                {{
                    {details}
                }}
            }}""")

        return "\n".join(scad)

    def _generate_water_features(self, water_features, layer_specs):
        """Generate OpenSCAD code for water features (subtractive)."""
        scad = []
        base_height = layer_specs["base"]["height"]
        water_depth = layer_specs["water"]["depth"]
        park_specs = layer_specs["parks"]
        park_offset = park_specs.get("start_offset", 0.2)
        park_thickness = park_specs.get("thickness", 0.4)
        water_extrude_height = water_depth + park_offset + park_thickness + 0.1

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
                linear_extrude(height={water_extrude_height}, convexity=2)
                    polygon([{points_str}]);
            }}"""
                )

        return "\n".join(scad)
    
    def _generate_road_features(self, road_features, layer_specs):
        """Generate OpenSCAD code for road features (subtractive)."""
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
        """Generate OpenSCAD code for railways (subtractive)."""
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
        """Generate OpenSCAD code for bridges with rail/road differentiation."""
        scad = []
        base_height = layer_specs["base"]["height"]
        
        for i, bridge in enumerate(bridge_features):
            coords = bridge.get("coords", [])
            if len(coords) < 2:
                continue

            bridge_type = bridge.get("type", "road_bridge")
            is_rail = bridge.get("span_type") == "rail"
            
            # Get type-specific parameters
            style_config = self._get_bridge_style_config(bridge_type, layer_specs)
            points_str = self.geometry.generate_buffered_polygon(
                coords, 
                bridge.get("width", layer_specs['roads']['width'])
            )

            scad.append(f"""
        // {style_config['name']} {i+1}
        union() {{
            color("{style_config['color']}") {{
                translate([0, 0, {base_height + bridge['height']}])
                    linear_extrude(height={bridge['thickness']}, convexity=2)
                        polygon([{points_str}]);
            }}
            {self._generate_bridge_supports(coords, base_height, bridge['height'], bridge['support_width'])}
        }}""")

        return "\n".join(scad)

    def _get_bridge_style_config(self, bridge_type: str, layer_specs: Dict) -> Dict:
        """Return style parameters for different bridge types."""
        return {
            "road_bridge": {
                "name": "Road Bridge",
                "color": "orange",
                "support_width": layer_specs['bridges']['support_width']['road']
            },
            "rail_bridge": {
                "name": "Rail Bridge",
                "color": "steelblue",
                "support_width": layer_specs['bridges']['support_width']['rail']
            }
        }.get(bridge_type, {})

    def _generate_bridge_supports(self, coords: List[List[float]], 
                                base_height: float, 
                                bridge_height: float,
                                support_radius: float) -> str:
        """Generate support structures for bridges."""
        supports = []
        support_interval = 50  # mm between supports
        
        # Always include end supports
        supports.extend([
            self._generate_support(coords[0], base_height, bridge_height, support_radius),
            self._generate_support(coords[-1], base_height, bridge_height, support_radius)
        ])

        # Calculate intermediate supports
        total_length = sum(
            self.geometry.calculate_distance(coords[i], coords[i+1])
            for i in range(len(coords)-1)
        )
        
        if total_length > support_interval:
            num_supports = int(total_length // support_interval)
            step = total_length / (num_supports + 1)
            current_dist = step
            
            for _ in range(num_supports):
                point = self._get_point_along_path(coords, current_dist)
                if point:
                    supports.append(
                        self._generate_support(point, base_height, bridge_height, support_radius)
                    )
                current_dist += step

        return "\n".join(supports)

    def _generate_support(self, point: List[float], 
                        base_height: float, 
                        bridge_height: float,
                        radius: float) -> str:
        """Generate individual support cylinder."""
        return f"""
            translate([{point[0]}, {point[1]}, {base_height}])
                cylinder(h={bridge_height}, r={radius}, $fn=16);"""

    def _get_point_along_path(self, coords: List[List[float]], target_dist: float) -> Optional[List[float]]:
        """Find point at specified distance along the path."""
        accumulated = 0.0
        for i in range(len(coords)-1):
            start = coords[i]
            end = coords[i+1]
            segment_length = self.geometry.calculate_distance(start, end)
            
            if accumulated + segment_length >= target_dist:
                ratio = (target_dist - accumulated) / segment_length
                return [
                    start[0] + ratio * (end[0] - start[0]),
                    start[1] + ratio * (end[1] - start[1])
                ]
            accumulated += segment_length
        return None

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
# lib/style/block_combiner.py
from math import sqrt
import random
from shapely.geometry import Polygon, MultiPolygon, LineString, box
from shapely.ops import unary_union
from shapely.validation import make_valid
from ..geometry import GeometryUtils

class BlockCombiner:
    """
    Handles the combination of building footprints based on area thresholds and proximity.
    
    This class implements two main approaches:
    1. Area-based merging for "block-combine" style
    2. Legacy block subdivision for other styles
    
    For "block-combine" style:
    - Large footprints (area >= threshold) are preserved individually
    - Small footprints are merged with nearby unblocked footprints until reaching the threshold
    - Merged clusters get unique roof styles
    """
    
    def __init__(self, style_manager):
        """
        Initialize the BlockCombiner.
        
        Args:
            style_manager: StyleManager instance for accessing global style settings
        """
        self.style_manager = style_manager
        self.geometry = GeometryUtils()
        self.debug = False
        
        # Legacy block types for non-"block-combine" styles
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
                    {'name': 'stepped', 'levels': 2}
                ]
            },
            'commercial': {
                'min_height': 20.0,
                'max_height': 40.0,
                'roof_styles': [
                    {'name': 'modern', 'setback': 2.0},
                    {'name': 'tiered', 'levels': 2},
                    {'name': 'complex', 'variations': 5}
                ]
            }
        }
    
    def _select_random_roof(self):
        """
        Select a random roof style with randomized parameters.
        
        Returns:
            dict: Roof style parameters including name and style-specific parameters
        """
        roof_styles = [
            {
                'name': 'pitched',
                'height_factor': random.uniform(0.2, 0.4)
            },
            {
                'name': 'tiered',
                'levels': random.randint(2, 4)
            },
            {
                'name': 'flat',
                'border': random.uniform(0.8, 1.2)
            },
            {
                'name': 'sawtooth',
                'angle': random.randint(25, 35)
            },
            {
                'name': 'modern',
                'setback': random.uniform(1.8, 2.2)
            },
            {
                'name': 'stepped',
                'levels': random.randint(2, 4)
            }
        ]
        return random.choice(roof_styles)

    def combine_buildings_by_block(self, features):
        """
        Main entry point for building combination.
        
        Args:
            features: Dict containing all feature types (buildings, roads, etc.)
            
        Returns:
            list: Combined building features with appropriate roof styles
        """
        if self.style_manager.style.get("artistic_style") == "block-combine":
            return self._area_based_merge(features)
        else:
            return self._legacy_combine(features)

    def _gather_all_footprints(self, features):
        """
        Collect all building/industrial footprints into a unified list.
        
        Args:
            features: Dict containing feature collections
            
        Returns:
            list: Footprint dictionaries with polygon, height, and area information
        """
        footprints = []
        
        # Process normal building features
        for bldg in features.get('buildings', []):
            coords = bldg.get('coords')
            if coords and len(coords) >= 3:
                poly = Polygon(coords)
                if poly.is_valid and not poly.is_empty:
                    footprints.append({
                        'polygon': poly,
                        'height': bldg.get('height', 10.0),
                        'area': poly.area,
                        'original': bldg
                    })
        
        # Process industrial features
        for ind in features.get('industrial', []):
            coords = ind.get('coords')
            if coords and len(coords) >= 3:
                poly = Polygon(coords)
                if poly.is_valid and not poly.is_empty:
                    footprints.append({
                        'polygon': poly,
                        'height': ind.get('height', 15.0),
                        'area': poly.area,
                        'original': ind
                    })
        
        return footprints

    def _area_based_merge(self, features):
        """
        Implement area-based merging for block-combine style.
        
        Args:
            features: Dict containing feature collections
            
        Returns:
            list: Merged building features with appropriate roof styles
        """
        AREA_THRESHOLD = 200  # in m²
        footprints = self._gather_all_footprints(features)
        barrier_union = self._create_barrier_union(features)
        
        # Separate large and small footprints
        large = [fp for fp in footprints if fp['area'] >= AREA_THRESHOLD]
        small = [fp for fp in footprints if fp['area'] < AREA_THRESHOLD]
        
        merged_clusters = []
        visited = set()
        merge_dist = self.style_manager.style.get("merge_distance", 2.0)
        
        # Process small footprints
        for i, fp in enumerate(small):
            if i in visited:
                continue
                
            cluster = [fp]
            visited.add(i)
            cluster_union = fp['polygon']
            total_area = fp['area']
            weighted_height = fp.get('height', 10.0) * fp['area']
            
            # Grow cluster while under threshold
            growing = True
            while growing and cluster_union.area < AREA_THRESHOLD:
                growing = False
                for j, candidate in enumerate(small):
                    if j in visited:
                        continue
                    if candidate['polygon'].distance(cluster_union) < merge_dist:
                        if not self._is_blocked_by_barrier(
                            cluster_union.centroid,
                            candidate['polygon'].centroid,
                            barrier_union
                        ):
                            cluster.append(candidate)
                            visited.add(j)
                            cluster_union = unary_union([cluster_union, candidate['polygon']])
                            cluster_union = make_valid(cluster_union)
                            total_area += candidate['area']
                            weighted_height += candidate.get('height', 10.0) * candidate['area']
                            growing = True
            
            # Force merge if needed
            if cluster_union.geom_type != "Polygon":
                combined = cluster_union.buffer(merge_dist * 0.5).buffer(-merge_dist * 0.5)
                if combined.geom_type != "Polygon":
                    combined = unary_union(combined.geoms)
                    if combined.geom_type != "Polygon":
                        combined = combined.convex_hull
                cluster_union = combined

            # Extract coordinates for the merged shape
            if cluster_union.geom_type == "Polygon":
                coords = list(cluster_union.exterior.coords)[:-1]
            else:
                coords = list(cluster_union.convex_hull.exterior.coords)[:-1]
            
            avg_height = weighted_height / total_area if total_area > 0 else 4.0
            
            # Assign unique roof style to merged clusters
            if len(cluster) > 1:
                roof_style = self._select_random_roof()
                merged_clusters.append({
                    'coords': coords,
                    'height': avg_height,
                    'is_cluster': True,
                    'roof_style': roof_style['name'],
                    'roof_params': roof_style
                })
            else:
                merged_clusters.append({
                    'coords': coords,
                    'height': avg_height,
                    'is_cluster': False
                })
        
        # Process large footprints (preserve individually)
        large_buildings = []
        for fp in large:
            poly = fp['polygon']
            if poly.geom_type == "MultiPolygon":
                poly = max(poly.geoms, key=lambda g: g.area)
            large_buildings.append({
                'coords': list(poly.exterior.coords)[:-1],
                'height': fp.get('height', 10.0),
                'is_cluster': False
            })
        
        if self.debug:
            print(f"Area-based merge: {len(large_buildings)} large buildings, {len(merged_clusters)} merged clusters")
            
        return large_buildings + merged_clusters

    def _legacy_combine(self, features):
        """
        Legacy block subdivision approach for non-block-combine styles.
        
        Args:
            features: Dict containing feature collections
            
        Returns:
            list: Combined building features using legacy approach
        """
        if self.debug:
            print("\n=== Legacy Block Combiner Debug ===")
        
        building_footprints = self._gather_all_footprints(features)
        barrier_union = self._create_barrier_union(features)
        blocks = self._create_blocks_from_barriers(barrier_union)
        
        if self.debug:
            print(f"Found {len(building_footprints)} building footprints")
            print(f"Generated {len(blocks)} blocks from barrier union")
        
        combined_buildings = []
        for block in blocks:
            block_buildings = self._find_buildings_in_block(block, building_footprints)
            block_info = self._analyze_block(block_buildings)
            processed_shapes = self._process_block_buildings(
                block, block_buildings, block_info, barrier_union
            )
            combined_buildings.extend(processed_shapes)
        
        return combined_buildings

    def _create_barrier_union(self, features):
        """
        Create union of barrier geometries (roads, water).
        
        Args:
            features: Dict containing feature collections
            
        Returns:
            shapely.geometry: Union of all barrier geometries
        """
        barriers = []
        
        road_width = self.style_manager.get_default_layer_specs()["roads"]["width"]
        for road in features.get('roads', []):
            try:
                line = LineString(road["coords"])
                buffered = line.buffer(road_width * 0.2)
                if buffered.is_valid and not buffered.is_empty:
                    barriers.append(buffered)
            except Exception:
                continue
        
        for water in features.get('water', []):
            try:
                poly = Polygon(water["coords"])
                if poly.is_valid and not poly.is_empty:
                    barriers.append(poly.buffer(1.5))
            except Exception:
                continue
        
        if not barriers:
            return None
        
        unioned = unary_union(barriers)
        if not unioned.is_valid:
            unioned = make_valid(unioned)
        return unioned

    def _is_blocked_by_barrier(self, ptA, ptB, barrier_union):
        """
        Check if line between points intersects barrier.
        
        Args:
            ptA: First point (shapely.geometry.Point)
            ptB: Second point (shapely.geometry.Point)
            barrier_union: Union of all barriers
            
        Returns:
            bool: True if line intersects barrier
        """
        if barrier_union is None:
            return False
        try:
            line = LineString([ptA.coords[0], ptB.coords[0]])
            return line.intersects(barrier_union)
        except Exception:
            return False

    def _create_blocks_from_barriers(self, barrier_union):
        """
        Create blocks by subtracting barriers from bounding box.
        
        Args:
            barrier_union: Union of all barriers
            
        Returns:
            list: Block polygons
        """
        if not barrier_union or barrier_union.is_empty:
            return []
            
        try:
            minx, miny, maxx, maxy = barrier_union.bounds
            bounding_area = box(minx, miny, maxx, maxy)
            blocks_area = bounding_area.difference(barrier_union)
            
            if blocks_area.is_empty:
                return []
                
            blocks = []
            if blocks_area.geom_type == "MultiPolygon":
                for b in blocks_area.geoms:
                    if b.area > 5:
                        simplified = b.simplify(0.1)
                        if simplified.is_valid and not simplified.is_empty:
                            blocks.append(simplified)
            else:
                if blocks_area.area > 5:
                    simplified = blocks_area.simplify(0.1)
                    if simplified.is_valid and not simplified.is_empty:
                        blocks.append(simplified)
                        
            return blocks
            
        except Exception as e:
            if self.debug:
                print(f"Error creating blocks: {e}")
            return []

    def _find_buildings_in_block(self, block, building_footprints):
        """
        Find all footprints that intersect a given block.
        
        Args:
            block: Block polygon
            building_footprints: List of building footprints
            
        Returns:
            list: Building footprints that intersect the block
        """
        block_buildings = []
        for fp in building_footprints:
            try:
                poly = fp['polygon']
                if block.intersects(poly):
                    intersection = block.intersection(poly)
                    if not intersection.is_empty and intersection.area > 1:
                        fp_copy = dict(fp)
                        fp_copy['polygon'] = intersection
                        block_buildings.append(fp_copy)
            except Exception:
                continue
        return block_buildings

    def _analyze_block(self, block_buildings):
        """
        Analyze a block to compute average height and predominant type.
        
        Args:
            block_buildings: List of buildings in the block
            
        Returns:
            dict: Block analysis information
        """
        if not block_buildings:
            return {'type': 'residential', 'avg_height': 15.0}
            
        type_counts = {'residential': 0, 'industrial': 0, 'commercial': 0}
        total_area = 0.0
        weighted_height = 0.0
        
        for b in block_buildings:
            area = b['polygon'].area
            total_area += area
            weighted_height += b['height'] * area
            typ = b.get('type', 'residential')
            if typ in type_counts:
                type_counts[typ] += 1
            else:
                type_counts['residential'] += 1
        
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
        Process buildings within a block into final building shapes.
        
        Args:
            block: Block polygon
            block_buildings: List of buildings in the block
            block_info: Block analysis information
            barrier_union: Union of all barriers
            
        Returns:
            list: Processed building shapes with appropriate styles
        """
        from shapely.ops import unary_union
        if not block_buildings:
            return []
            
        processed = []
        block_type = block_info['type']
        type_specs = self.BLOCK_TYPES.get(block_type, self.BLOCK_TYPES['residential'])
        
        try:
            # Create union of all building footprints
            footprints_union = unary_union([b['polygon'] for b in block_buildings])
            if not footprints_union.is_valid:
                footprints_union = make_valid(footprints_union)
        except Exception:
            return []
            
        # Handle different geometry types
        polygons = []
        if footprints_union.geom_type == "MultiPolygon":
            polygons.extend(footprints_union.geoms)
        else:
            polygons.append(footprints_union)
            
        # Process each polygon shape
        for shape in polygons:
            if shape.is_empty or shape.area < 2:
                continue
                
            # Clean up the geometry
            cleaned = shape.simplify(0.1)
            if not cleaned.is_valid or cleaned.is_empty:
                continue
                
            # Buffer slightly inward to create separation
            final_poly = cleaned.buffer(-0.1)
            if final_poly.is_empty:
                continue
                
            # Handle barriers if present
            if barrier_union:
                clipped = final_poly.difference(barrier_union)
                if clipped.is_empty:
                    continue
            else:
                clipped = final_poly
                
            if clipped.is_empty or clipped.area < 1:
                continue
                
            # Process resulting geometry
            sub_polys = list(clipped.geoms) if clipped.geom_type=="MultiPolygon" else [clipped]
            for spoly in sub_polys:
                if spoly.is_empty or spoly.area < 1:
                    continue
                    
                # Calculate height and select roof style
                base_height = self._calculate_building_height(block_info['avg_height'], type_specs)
                roof_style = self._select_roof_style(block_type)
                
                # Create final building dictionary
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
        Calculate building height based on average and type constraints.
        
        Args:
            avg_height: Average height of buildings in block
            type_specs: Building type specifications
            
        Returns:
            float: Calculated building height
        """
        min_h = type_specs['min_height']
        max_h = type_specs['max_height']
        
        # Ensure minimum base height
        base = max(avg_height, min_h)
        if base < 15.0:
            base = 15.0
            
        # Add random variation
        variation = random.uniform(0.85, 1.15)
        candidate = base * variation
        
        # Constrain to min/max range
        final_height = max(min_h, min(candidate, max_h))
        return final_height

    def _select_roof_style(self, block_type):
        """
        Select a roof style for a block type, with randomized parameters.
        
        Args:
            block_type: Type of building block
            
        Returns:
            dict: Selected roof style parameters
        """
        styles = self.BLOCK_TYPES.get(block_type, self.BLOCK_TYPES['residential'])['roof_styles']
        choice = random.choice(styles)
        
        # Randomize parameters based on roof type
        if choice['name'] == 'pitched':
            choice['height_factor'] *= random.uniform(0.8, 1.2)
        elif choice['name'] == 'tiered':
            choice['levels'] = max(1, choice['levels'] + random.randint(-1, 1))
        elif choice['name'] == 'flat':
            choice['border'] *= random.uniform(0.9, 1.1)
        elif choice['name'] == 'sawtooth':
            choice['angle'] = max(10, choice['angle'] + random.randint(-5, 5))
        elif choice['name'] == 'modern':
            choice['setback'] *= random.uniform(0.9, 1.1)
        elif choice['name'] == 'stepped':
            choice['levels'] = max(2, choice['levels'] + random.randint(-1, 1))
            
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
    Generates OpenSCAD code for buildings with various roof styles.
    Maintains all original architectural features while removing redundancy.
    """
    
    def __init__(self, style_manager):
        self.style_manager = style_manager

    def generate_building_details(self, points_str, height, roof_style=None, roof_params=None):
        """Generate OpenSCAD code for a building with optional roof style."""
        if not roof_style or not roof_params:
            return self._basic_building(points_str, height)
            
        # Dispatch to specific roof generators
        if roof_style == 'pitched':
            return self._pitched_roof(points_str, height, roof_params)
        elif roof_style == 'tiered':
            return self._tiered_roof(points_str, height, roof_params)
        elif roof_style == 'flat':
            return self._flat_roof(points_str, height, roof_params)
        elif roof_style == 'sawtooth':
            return self._sawtooth_roof(points_str, height, roof_params)
        elif roof_style == 'modern':
            return self._modern_roof(points_str, height, roof_params)
        elif roof_style == 'stepped':
            return self._stepped_roof(points_str, height, roof_params)
            
        return self._basic_building(points_str, height)

    def _basic_building(self, points_str, height):
        return f"linear_extrude(height={height}, convexity=2) polygon([{points_str}]);"

    def _pitched_roof(self, points_str, height, params):
        roof_height = height * params.get('height_factor', 0.3)
        base_height = height - roof_height
        return f"""union() {{
            linear_extrude(height={base_height}, convexity=2) polygon([{points_str}]);
            translate([0, 0, {base_height}]) {{
                intersection() {{
                    linear_extrude(height={roof_height}, scale=0.6, convexity=2)
                        polygon([{points_str}]);
                    linear_extrude(height={roof_height}, convexity=2)
                        polygon([{points_str}]);
                }}
            }}
        }}"""

    def _tiered_roof(self, points_str, height, params):
        levels = params.get('levels', 2)
        level_height = height / (levels + 1)
        return f"""union() {{
            linear_extrude(height={level_height}, convexity=2) polygon([{points_str}]);
            {" ".join(self._tier_sections(points_str, level_height, levels))}
        }}"""

    def _tier_sections(self, points_str, level_height, levels):
        return [f"""
            translate([0, 0, {level_height * (i + 1)}])
                linear_extrude(height={level_height}, convexity=2)
                    offset(r=-{(i + 1) * 1.0})
                        polygon([{points_str}]);""" 
            for i in range(levels)]

    def _flat_roof(self, points_str, height, params):
        border = params.get('border', 1.0)
        return f"""union() {{
            linear_extrude(height={height}, convexity=2) polygon([{points_str}]);
            translate([0, 0, {height}])
                linear_extrude(height=1.0, convexity=2)
                    difference() {{
                        polygon([{points_str}]);
                        offset(r=-{border}) polygon([{points_str}]);
                    }}
        }}"""

    def _sawtooth_roof(self, points_str, height, params):
        angle = params.get('angle', 30)
        roof_height = height * 0.2
        return f"""union() {{
            linear_extrude(height={height - roof_height}, convexity=2) polygon([{points_str}]);
            translate([0, 0, {height - roof_height}])
                intersection() {{
                    linear_extrude(height={roof_height}, convexity=2) polygon([{points_str}]);
                    rotate([{angle}, 0, 0]) translate([0, 0, -50])
                        linear_extrude(height=100, convexity=4) polygon([{points_str}]);
                }}
        }}"""

    def _modern_roof(self, points_str, height, params):
        setback = params.get('setback', 2.0)
        roof_height = height * 0.2
        return f"""union() {{
            linear_extrude(height={height - roof_height}, convexity=2) polygon([{points_str}]);
            translate([0, 0, {height - roof_height}])
                linear_extrude(height={roof_height}, convexity=2)
                    offset(r=-{setback}) polygon([{points_str}]);
        }}"""

    def _stepped_roof(self, points_str, height, params):
        levels = params.get('levels', 2)
        step_height = height / (levels + 1)
        return f"""union() {{
            linear_extrude(height={step_height}, convexity=2) polygon([{points_str}]);
            {" ".join(self._step_sections(points_str, step_height, levels))}
        }}"""

    def _step_sections(self, points_str, step_height, levels):
        return [f"""
            translate([0, 0, {step_height * (i + 1)}])
                linear_extrude(height={step_height}, convexity=2)
                    offset(r=-{2.0 + (i * 1.5)}) polygon([{points_str}]);"""
            for i in range(levels)]
```

# lib/style/height_manager.py

```py
# lib/style/height_manager.py
from typing import Dict, Any, Optional
from math import log10
from ..config import Config

class HeightManager:
    """
    Manages height calculations and scaling for buildings.
    Uses centralized configuration for consistent height handling.
    """
    
    def __init__(self, style_manager):
        """
        Initialize height manager with style manager reference.
        
        Args:
            style_manager: StyleManager instance for accessing style settings
        """
        self.style_manager = style_manager

    def scale_height(self, properties: Dict[str, Any]) -> float:
        """
        Scale building height based on properties and current style settings.
        
        Args:
            properties: Building properties including height information
            
        Returns:
            float: Scaled height in millimeters
        """
        height_m = self._extract_height(properties)
        base_height = self._scale_to_range(height_m)
        
        # Apply any style-specific modifiers
        return self._apply_style_modifiers(base_height, properties)

    def _extract_height(self, properties: Dict[str, Any]) -> float:
        """
        Extract height from building properties using various OSM tags.
        
        Args:
            properties: Building properties
            
        Returns:
            float: Extracted height in meters
        """
        # Try explicit height tag first
        if "height" in properties:
            try:
                # Handle formats like "25 m", "25m", "25"
                height_str = properties["height"].split()[0].strip('m')
                return float(height_str)
            except (ValueError, IndexError):
                pass

        # Try building:levels tag
        if "building:levels" in properties:
            try:
                levels = float(properties["building:levels"])
                return levels * Config.DEFAULT_LAYER_SPECS["buildings"]["levels_height"]
            except ValueError:
                pass

        # Try min_height tag
        if "min_height" in properties:
            try:
                min_height_str = properties["min_height"].split()[0].strip('m')
                return float(min_height_str)
            except (ValueError, IndexError):
                pass

        # Use default height based on building type
        building_type = properties.get("building", "").lower()
        if building_type in Config.INDUSTRIAL_BUILDINGS:
            return Config.INDUSTRIAL_SETTINGS["default_height"]
            
        return Config.DEFAULT_LAYER_SPECS["buildings"]["default_height"]

    def _scale_to_range(self, height_m: float) -> float:
        """
        Scale height to target range using logarithmic scaling.
        
        Args:
            height_m: Height in meters
            
        Returns:
            float: Scaled height in millimeters
        """
        specs = Config.DEFAULT_LAYER_SPECS["buildings"]
        min_height = specs["min_height"]
        max_height = specs["max_height"]

        # Log scaling from 1..100 meters -> min_height..max_height mm
        log_min = log10(1.0)
        log_max = log10(101.0)
        log_height = log10(height_m + 1.0)  # +1 to avoid log(0)
        
        # Calculate scaled height
        scale_factor = (log_height - log_min) / (log_max - log_min)
        scaled_height = min_height + scale_factor * (max_height - min_height)
        
        # Ensure height stays within bounds
        return max(min_height, min(scaled_height, max_height))

    def _apply_style_modifiers(self, base_height: float, properties: Dict[str, Any]) -> float:
        """
        Apply style-specific height modifications.
        
        Args:
            base_height: Base calculated height
            properties: Building properties
            
        Returns:
            float: Modified height in millimeters
        """
        style = self.style_manager.style.get("artistic_style")
        
        # Apply style-specific modifiers
        if style == "modern":
            # Modern style: Taller buildings with more variation
            height_variance = self.style_manager.style.get("height_variance", 0.2)
            variance_factor = 1.0 + (height_variance * 0.5)  # Up to 50% taller
            return base_height * variance_factor
            
        elif style == "classic":
            # Classic style: More consistent heights
            return base_height
            
        elif style == "minimal":
            # Minimal style: Slightly reduced heights
            return base_height * 0.8
            
        elif style == "block-combine":
            # Block combine: Heights based on cluster characteristics
            if properties.get("is_cluster", False):
                # Clustered buildings get a slight height bonus
                return base_height * 1.2
            
        return base_height

    def get_height_range(self, building_type: str) -> tuple[float, float]:
        """
        Get valid height range for a building type.
        
        Args:
            building_type: Type of building
            
        Returns:
            tuple[float, float]: Minimum and maximum heights in millimeters
        """
        if building_type in Config.INDUSTRIAL_BUILDINGS:
            specs = Config.BLOCK_TYPES["industrial"]
        else:
            specs = Config.BLOCK_TYPES["residential"]
            
        return specs["min_height"], specs["max_height"]

    def calculate_relative_height(
        self, 
        base_height: float, 
        importance_factor: float = 1.0
    ) -> float:
        """
        Calculate height relative to base height with importance scaling.
        
        Args:
            base_height: Base height to scale from
            importance_factor: Factor to scale height (1.0 = no change)
            
        Returns:
            float: Calculated relative height
        """
        specs = Config.DEFAULT_LAYER_SPECS["buildings"]
        min_height = specs["min_height"]
        max_height = specs["max_height"]
        
        # Scale height by importance while keeping within bounds
        scaled_height = base_height * importance_factor
        return max(min_height, min(scaled_height, max_height))
```

# lib/style/style_manager.py

```py
# lib/style/style_manager.py
from typing import Dict, Any, Optional
from ..config import Config
from .building_merger import BuildingMerger
from .height_manager import HeightManager
from .artistic_effects import ArtisticEffects
from .block_combiner import BlockCombiner

class StyleManager:
    """
    Manages style settings and coordinates style-related components for the city model.
    Uses centralized configuration for consistent styling across the application.
    """
    
    def __init__(self, style_settings: Optional[Dict[str, Any]] = None):
        """
        Initialize style manager with optional custom settings.
        
        Args:
            style_settings: Optional dictionary of style settings to override defaults
        """
        # Initialize with default style settings
        self.style = dict(Config.DEFAULT_STYLE)
        
        # Override defaults with provided settings
        if style_settings:
            self._validate_and_update_style(style_settings)
            
        # Initialize style components
        self.building_merger = BuildingMerger(self)
        self.height_manager = HeightManager(self)
        self.artistic_effects = ArtisticEffects(self)
        self.block_combiner = BlockCombiner(self)
        self.current_features = {}

    def _validate_and_update_style(self, settings: Dict[str, Any]) -> None:
        """
        Validate and update style settings.
        
        Args:
            settings: Dictionary of style settings to validate and apply
        """
        for key, value in settings.items():
            if key in Config.DEFAULT_STYLE:
                if key == 'artistic_style' and value not in Config.ARTISTIC_STYLES:
                    raise ValueError(f"Invalid artistic style: {value}. Must be one of {Config.ARTISTIC_STYLES}")
                self.style[key] = value

    def get_default_layer_specs(self) -> Dict[str, Any]:
        """
        Get default layer specifications from config.
        
        Returns:
            Dictionary containing layer specifications
        """
        return dict(Config.DEFAULT_LAYER_SPECS)

    def scale_building_height(self, properties: Dict[str, Any]) -> float:
        """
        Scale building height using HeightManager.
        
        Args:
            properties: Dictionary of building properties
            
        Returns:
            Scaled height value
        """
        return self.height_manager.scale_height(properties)

    def merge_nearby_buildings(self, buildings: list, barrier_union=None) -> list:
        """
        Choose and execute building merging strategy based on style.
        
        Args:
            buildings: List of building features
            barrier_union: Optional union of barrier geometries
            
        Returns:
            List of processed building features
        """
        if self.style["artistic_style"] == "block-combine":
            return self.block_combiner.combine_buildings_by_block(self.current_features)
        else:
            return self.building_merger.merge_buildings(buildings, barrier_union)

    def set_current_features(self, features: Dict[str, list]) -> None:
        """
        Store current features for reference by style components.
        
        Args:
            features: Dictionary of feature collections by type
        """
        self.current_features = features

    def get_industrial_height_multiplier(self, building_type: str) -> float:
        """
        Get height multiplier for industrial building type.
        
        Args:
            building_type: Type of industrial building
            
        Returns:
            Height multiplier value
        """
        return Config.get_industrial_height_multiplier(building_type)

    def get_road_width(self, road_type: str) -> float:
        """
        Get width multiplier for road type.
        
        Args:
            road_type: Type of road
            
        Returns:
            Road width multiplier
        """
        return Config.get_road_width(road_type)

    def get_roof_style_params(self, style_name: str) -> Dict[str, Any]:
        """
        Get parameters for a specific roof style.
        
        Args:
            style_name: Name of the roof style
            
        Returns:
            Dictionary of roof style parameters
        """
        return Config.ROOF_STYLES.get(style_name, {})

    def get_processing_settings(self) -> Dict[str, Any]:
        """
        Get current processing settings based on style.
        
        Returns:
            Dictionary of processing settings
        """
        settings = dict(Config.PROCESSING_SETTINGS)
        # Adjust settings based on current style
        if self.style["artistic_style"] == "block-combine":
            settings["area_threshold"] = max(
                settings["area_threshold"],
                self.style.get("min_building_area", 600.0)
            )
        return settings
```

# public/css/style.css

```css
body {
  padding-top: 20px;
  padding-bottom: 20px;
}

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
  max-height: 600px;
  overflow-y: scroll;
  font-family: monospace;
  white-space: pre;
}

.processing-indicator {
  display: none;
  color: #007bff;
  margin-bottom: 10px;
}

/* Enhanced log styling */
.log-window {
  background: #1e1e1e;
  border-radius: 4px;
  padding: 15px;
  max-height: 400px;
  overflow-y: auto;
  font-family: 'Fira Code', monospace;
  font-size: 0.9em;
}

.log-entry {
  margin: 2px 0;
  padding: 4px;
  border-left: 3px solid transparent;
}

.log-info { color: #cfcfcf; border-color: #4a90e2; }
.log-warning { color: #ffd700; border-color: #ffd700; }
.log-error { color: #ff4444; border-color: #ff4444; }

.stat-card {
  background: #f8f9fa;
  border-radius: 4px;
  padding: 10px;
  margin: 5px;
  min-width: 120px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stat-value {
  font-size: 1.4em;
  font-weight: bold;
  color: #2c3e50;
}

.stat-label {
  font-size: 0.8em;
  color: #7f8c8d;
  text-transform: uppercase;
}

/* Add to public/css/style.css */
.log-container {
  margin-top: 20px;
  background-color: #1e1e1e;
  border-radius: 4px;
  padding: 15px;
  max-height: 400px;
  overflow-y: auto;
  font-family: 'Fira Code', monospace;
  font-size: 0.9em;
}

.log-entry {
  margin: 2px 0;
  padding: 4px;
  border-left: 3px solid transparent;
  white-space: pre-wrap; /* Ensure text wraps */
  word-break: break-word; /* Break long words */
}

.log-info { color: #cfcfcf; border-color: #4a90e2; }
.log-warning { color: #ffd700; border-color: #ffd700; }
.log-error { color: #ff4444; border-color: #ff4444; }
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

// Configuration setup
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.static(path.join(__dirname, "public")));
app.use("/uploads", express.static("uploads"));
app.use("/outputs", express.static("outputs"));
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// File upload configuration
const upload = multer({
  storage: multer.diskStorage({
    destination: "uploads/",
    filename: (req, file, cb) => {
      const uniqueSuffix = `${Date.now()}-${uuidv4()}`;
      cb(null, `${uniqueSuffix}-${file.originalname}`);
    },
  }),
  fileFilter: (req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    ext === ".geojson" ? cb(null, true) : cb(new Error("Invalid file type"));
  },
});

// Argument configuration
const OPTION_CONFIG = [
  { bodyKey: "size", cliFlag: "--size" },
  { bodyKey: "height", cliFlag: "--height" },
  { bodyKey: "style", cliFlag: "--style" },
  { bodyKey: "detail", cliFlag: "--detail" },
  { bodyKey: "merge-distance", cliFlag: "--merge-distance" },
  { bodyKey: "cluster-size", cliFlag: "--cluster-size" },
  { bodyKey: "height-variance", cliFlag: "--height-variance" },
  { bodyKey: "road-width", cliFlag: "--road-width" },
  { bodyKey: "water-depth", cliFlag: "--water-depth" },
  { bodyKey: "min-building-area", cliFlag: "--min-building-area" },
  { bodyKey: "bridge-height", cliFlag: "--bridge-height" },
  { bodyKey: "bridge-thickness", cliFlag: "--bridge-thickness" },
  { bodyKey: "support-width", cliFlag: "--support-width" },
  { bodyKey: "preprocess", cliFlag: "--preprocess", isFlag: true },
  { bodyKey: "crop-distance", cliFlag: "--crop-distance" },
  {
    bodyKey: "crop-bbox",
    process: (value) => {
      const bbox = value.split(",").map((coord) => Number(coord.trim()));
      return bbox.length === 4 && bbox.every((num) => !isNaN(num))
        ? ["--crop-bbox", ...bbox.map(String)]
        : [];
    },
  },
  { bodyKey: "debug", cliFlag: "--debug", isFlag: true },
];

const buildPythonArgs = (inputFile, outputFile, body) => {
  const args = [
    path.join(__dirname, "geojson_to_shadow_city.py"),
    inputFile,
    outputFile,
  ];

  OPTION_CONFIG.forEach((config) => {
    const value = body[config.bodyKey];
    if (value === undefined || value === "") return;
    if (config.process) {
      args.push(...config.process(value));
    } else if (config.isFlag) {
      if (value === "on") args.push(config.cliFlag);
    } else {
      args.push(config.cliFlag, value);
    }
  });

  return args;
};

// Run Python process in unbuffered mode and capture logs.
const runPythonProcess = (args) => {
  return new Promise((resolve, reject) => {
    // Use "-u" flag to force unbuffered output.
    const pythonProcess = spawn("python3", ["-u", ...args]);
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
        reject(stderrData);
      } else {
        resolve({ stdout: stdoutData, stderr: stderrData });
      }
    });
  });
};

app.get("/", (req, res) => res.render("index"));

app.post("/uploadFile", upload.single("geojson"), (req, res) => {
  if (!req.file) return res.status(400).json({ error: "No file uploaded" });
  res.json({ filePath: req.file.path });
});

app.post("/preview", async (req, res) => {
  try {
    const outputBase = `preview-${Date.now()}-${uuidv4()}`;
    const outputScad = path.join("outputs", `${outputBase}.scad`);

    const args = buildPythonArgs(req.body.uploadedFile, outputScad, req.body);

    // Run Python process and capture logs.
    const result = await runPythonProcess(args);

    res.json({
      previewMain: `/outputs/${outputBase}_preview_main.png`,
      previewFrame: `/outputs/${outputBase}_preview_frame.png`,
      stdout: result.stdout,
      stderr: result.stderr,
    });
  } catch (error) {
    res.status(500).json({ error: error.toString() });
  }
});

app.post("/render", async (req, res) => {
  try {
    const outputBase = `output-${Date.now()}-${uuidv4()}`;
    const outputPath = path.join("outputs", `${outputBase}.scad`);

    const args = buildPythonArgs(req.body.uploadedFile, outputPath, req.body);

    const result = await runPythonProcess(args);

    res.json({
      mainScad: `/outputs/${outputBase}_main.scad`,
      frameScad: `/outputs/${outputBase}_frame.scad`,
      stlFiles: {
        mainStl: `/outputs/${outputBase}_main.stl`,
        frameStl: `/outputs/${outputBase}_frame.stl`,
      },
      stdout: result.stdout,
      stderr: result.stderr,
    });
  } catch (error) {
    res.status(500).json({ error: error.toString() });
  }
});

// Server startup
app.listen(port, () =>
  console.log(`Server running on port ${port}\nhttp://localhost:${port}`)
);

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
                <option value="modern">Modern</option>
                <option value="classic">Classic</option>
                <option value="minimal">Minimal</option>
                <option value="block-combine" selected>Block Combine</option>
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
                value="1.2">
            </div>
            <div class="form-group">
              <label for="water-depth">Water Depth (mm)</label>
              <input type="number" step="0.1" class="form-control live-preview" id="water-depth" name="water-depth"
                value="2">
            </div>
            <div class="form-group">
              <label for="min-building-area">Minimum Building Area (m²)</label>
              <input type="number" step="0.1" class="form-control live-preview" id="min-building-area"
                name="min-building-area" value="200.0">
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
                name="bridge-thickness" value="0.6">
            </div>
            <div class="form-group">
              <label for="support-width">Bridge Support Radius</label>
              <input type="number" step="0.1" class="form-control live-preview" id="support-width" name="support-width"
                value="2.0">
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

        <!--      <div class="preview-container">
          <h3>Live Preview - Frame Model</h3>
          <img id="previewFrame" src="" alt="Frame Model Preview" style="display: none;">
        </div>
      -->
        <!-- Add to views/index.ejs, inside the log-container div -->
        <div class="log-container">
          <h4>Live Log <button id="clearLogBtn" class="btn btn-sm btn-secondary float-right">Clear Log</button></h4>
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
    // Clear log button
    $("#clearLogBtn").on("click", function () {
      $("#liveLog").empty();
    });
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

      updateLog("Generating preview...");

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
            updateLog(logText);
          }
        },
        error: function (err) {
          console.error("Error:", err);
          let errorMessage = "An error occurred: ";
          if (err.responseJSON && err.responseJSON.error) {
            errorMessage += err.responseJSON.error;
          } else {
            errorMessage += err.statusText || "Unknown error";
          }
          updateLog(errorMessage, "error");
        }
      });
    }

    // Function to auto-scroll log to the newest entry
    function scrollToBottom() {
      var logContainer = $("#liveLog");
      logContainer.scrollTop(logContainer[0].scrollHeight);
    }

    // Update the updateLog function
    function updateLog(message, level = 'info') {
      const logContainer = $("#liveLog");
      const timestamp = new Date().toLocaleTimeString();
      const logEntry = $("<div>").addClass(`log-entry log-${level}`)
        .text(`[${timestamp}] ${message}`);
      logContainer.append(logEntry);
      scrollToBottom();
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
          updateLog("Error uploading file:\n" + JSON.stringify(err));
        }
      });
    });

    // Update live preview when any option changes
    $(".live-preview").on("change keyup", function () {
      debouncedUpdatePreview();
    });

    // Scroll to bottom
    function scrollToBottom() {
      const logContainer = $("#liveLog");
      logContainer.scrollTop(logContainer[0].scrollHeight);
    }

    // Handle final render button click
    $("#renderBtn").on("click", function () {
      var uploadedFile = $("#uploadedFile").val();
      if (!uploadedFile) {
        alert("Please upload a GeoJSON file first.");
        return;
      }

      updateLog("Generating final render...");
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
            updateLog(logText);
          }
        },
        error: function (err) {
          console.error("Final render error:", err);
          updateLog("Error during final render:\n" + JSON.stringify(err));
          alert("An error occurred during final render.");
        }
      });
    });

  </script>
</body>

</html>
```

