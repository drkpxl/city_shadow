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
            self.style_manager.get_border_width(),
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
        
        # Apply building enhancements
        features['buildings'] = self.style_manager.merge_nearby_buildings(features['buildings'])
        
        return features

    def _process_single_feature(self, feature, features, transform):
        """Process a single GeoJSON feature"""
        props = feature.get('properties', {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return
            
        transformed = [transform(lon, lat) for lon, lat in coords]
        
        # Categorize and process feature
        if 'building' in props:
            height = self.style_manager.scale_building_height(props)
            features['buildings'].append({
                'coords': transformed,
                'height': height
            })
        # Handle parking features explicitly:
        elif props.get('amenity') == 'parking' or props.get('parking') == 'surface' or props.get('service') == 'parking_aisle':
            features['roads'].append({
                'coords': transformed,
                'is_parking': True
            })
        elif 'highway' in props:
            features['roads'].append({
                'coords': transformed,
                'is_parking': False
            })
        elif 'railway' in props:
            features['railways'].append(transformed)
        elif 'natural' in props and props['natural'] == 'water':
            features['water'].append(transformed)
