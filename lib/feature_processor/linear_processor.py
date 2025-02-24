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
