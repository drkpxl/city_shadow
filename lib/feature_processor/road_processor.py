# lib/feature_processor/road_processor.py
from .linear_processor import LinearFeatureProcessor

class RoadProcessor(LinearFeatureProcessor):
    """Handles road and bridge features, inheriting core linear processing"""
    
    FEATURE_TYPE = "highway"
    feature_category = "roads"

    def process_road_or_bridge(self, feature, features, transform):
        """Handle roads and bridges with specialized processing"""
        props = feature.get("properties", {})
        
        # Process common road features
        super().process_linear_feature(
            feature, 
            features, 
            transform,
            additional_tags=["bridge"]  # Preserve bridge status
        )
        
        # Special bridge handling
        if props.get("bridge"):
            self._process_bridge(feature, features, transform, props)

    def _process_bridge(self, feature, features, transform, props):
        """Handle bridge-specific processing"""
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) >= 2:
            features["bridges"].append({
                "coords": transformed,
                "type": props.get("highway", "bridge")
            })
            if self.debug:
                print(f"Added bridge of type '{props.get('highway', 'bridge')}'")

    def process_parking(self, feature, features, transform):
        """Process parking areas as special road features"""
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) >= 3:  # Polygon check
            features[self.feature_category].append({
                "coords": transformed,
                "type": "parking",
                "is_parking": True
            })
            if self.debug:
                print(f"Added parking area with {len(transformed)} points")

    def is_parking_area(self, props):
        """Check if feature represents a parking area"""
        return any(
            props.get(key) in ["parking", "surface", "parking_aisle"]
            for key in ["amenity", "parking", "service"]
        )