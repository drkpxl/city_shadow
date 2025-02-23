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
