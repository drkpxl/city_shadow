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
        if props.get("bridge") in ["yes", "true", "1"]:
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
