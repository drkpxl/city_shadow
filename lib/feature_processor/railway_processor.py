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
