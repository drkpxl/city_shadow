# lib/config.py
from typing import Dict, Any, List, Set

class Config:
    """Central configuration management for Shadow City Generator"""

    # Feature Types and Tags
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

    # Industrial Feature Recognition
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

    # Default Style Settings
    DEFAULT_STYLE: Dict[str, Any] = {
        'merge_distance': 2.0,
        'cluster_size': 3.0,
        'height_variance': 0.2,
        'detail_level': 1.0,
        'artistic_style': 'modern',
        'min_building_area': 600.0
    }

    # Available Artistic Styles
    ARTISTIC_STYLES: List[str] = ['modern', 'classic', 'minimal', 'block-combine']

    # Default Layer Specifications
    DEFAULT_LAYER_SPECS: Dict[str, Dict[str, Any]] = {
        'water': {
            'depth': 2.4,
            'min_area': 10.0  # Minimum area in m² to consider as water
        },
        'roads': {
            'depth': 0.4,
            'width': 1.0,
            'types': {
                'motorway': 2.0,
                'trunk': 1.8,
                'primary': 1.5,
                'secondary': 1.2,
                'residential': 1.0,
                'service': 0.8
            }
        },
        'railways': {
            'depth': 0.6,
            'width': 1.5
        },
        'parks': {
            'start_offset': 0.2,
            'thickness': 0.4,
            'min_area': 100.0  # Minimum area in m² to consider as park
        },
        'buildings': {
            'min_height': 2,
            'max_height': 8,
            'default_height': 4,
            'levels_height': 3.0  # meters per level for building:levels
        },
        'base': {
            'height': 3
        },
        'bridges': {
            'height': 2.0,
            'thickness': 0.6,
            'support_width': 2.0
        }
    }

    # Industrial Area Settings
    INDUSTRIAL_SETTINGS: Dict[str, Any] = {
        'height_multipliers': {
            'industrial': 2.0,
            'construction': 1.5,
            'depot': 1.5,
            'logistics': 1.8,
            'port': 2.0,
            'warehouse': 1.7,
            'factory': 2.0,
            'manufacturing': 1.8,
            'hangar': 1.6
        },
        'min_area': 400.0,  # Minimum area in m² for industrial buildings
        'default_height': 15.0  # Default height if no other height info available
    }

    # Park and Green Space Types
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

    # Block Types and Settings
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

    # Roof Style Configurations
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

    # Geometry Processing Settings
    GEOMETRY_SETTINGS: Dict[str, Any] = {
        'simplification_tolerance': 0.1,
        'min_points_polygon': 3,
        'min_points_linestring': 2,
        'buffer_distance': {
            'roads': 1.0,
            'railways': 1.0,
            'water': 1.5
        },
        'merge_threshold': 0.001  # Minimum distance to consider points different
    }

    # Processing Settings
    PROCESSING_SETTINGS: Dict[str, Any] = {
        'area_threshold': 200,  # m² threshold for block-combine style
        'min_cluster_size': 2,  # Minimum number of buildings to form a cluster
        'max_cluster_size': 10,  # Maximum number of buildings in a cluster
        'barrier_buffer': 1.0,  # Buffer distance for barriers in meters
    }

    @classmethod
    def get_road_width(cls, road_type: str) -> float:
        """Get road width multiplier for specific road type"""
        return cls.DEFAULT_LAYER_SPECS['roads']['types'].get(road_type, 1.0)

    @classmethod
    def get_industrial_height_multiplier(cls, building_type: str) -> float:
        """Get height multiplier for specific industrial building type"""
        return cls.INDUSTRIAL_SETTINGS['height_multipliers'].get(
            building_type, 
            cls.INDUSTRIAL_SETTINGS['height_multipliers']['industrial']
        )

    @classmethod
    def is_industrial_feature(cls, properties: Dict[str, Any]) -> bool:
        """Check if a feature should be processed as industrial"""
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
        """Check if a feature should be processed as a green space"""
        landuse = properties.get('landuse', '').lower()
        leisure = properties.get('leisure', '').lower()
        return landuse in cls.GREEN_LANDUSE or leisure in cls.GREEN_LEISURE