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
