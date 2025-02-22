# lib/feature_processor.py
from .geometry import GeometryUtils


class FeatureProcessor:
    def __init__(self, style_manager):
        self.style_manager = style_manager
        self.geometry = GeometryUtils()
        self.debug = False

    def process_features(self, geojson_data, size):
        """Process and enhance GeoJSON features"""
        transform = self.geometry.create_coordinate_transformer(
            geojson_data["features"], size
        )

        features = {"water": [], "roads": [], "railways": [], "buildings": []}

        # Process each feature type
        for feature in geojson_data["features"]:
            self._process_single_feature(feature, features, transform)

        # Log feature counts if in debug mode
        if self.debug:
            print(f"\nProcessed feature counts:")
            print(f"Water features: {len(features['water'])}")
            print(f"Road features: {len(features['roads'])}")
            print(f"Railway features: {len(features['railways'])}")
            print(f"Building features: {len(features['buildings'])}")

        # Apply building merging/clustering
        features["buildings"] = self.style_manager.merge_nearby_buildings(
            features["buildings"]
        )

        return features

    def _process_single_feature(self, feature, features, transform):
        """Process a single GeoJSON feature"""
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        # If this is a building, check area:
        if "building" in props:
            area_m2 = self.geometry.approximate_polygon_area_m2(coords)
            min_area = self.style_manager.style.get("min_building_area", 600.0)

            if area_m2 < min_area:
                if self.debug:
                    print(f"Skipping small building with area {area_m2:.1f}m²")
                return

            # Transform coordinates and store the building
            transformed = [transform(lon, lat) for lon, lat in coords]
            height = self.style_manager.scale_building_height(props)
            features["buildings"].append({"coords": transformed, "height": height})
            if self.debug:
                print(
                    f"Added building with height {height:.1f}mm and area {area_m2:.1f}m²"
                )

        # Handle roads (excluding tunnels)
        elif "highway" in props:
            # Skip if it's a tunnel
            if props.get("tunnel") in ["yes", "true", "1"]:
                if self.debug:
                    print(f"Skipping tunnel road of type '{props.get('highway')}'")
                return

            transformed = [transform(lon, lat) for lon, lat in coords]
            if len(transformed) >= 2:  # Ensure we have enough points for a road
                road_type = props.get("highway", "unknown")
                features["roads"].append(
                    {"coords": transformed, "type": road_type, "is_parking": False}
                )
                if self.debug:
                    print(
                        f"Added road of type '{road_type}' with {len(transformed)} points"
                    )

        # Handle parking areas and service roads
        elif (
            props.get("amenity") == "parking"
            or props.get("parking") == "surface"
            or props.get("service") == "parking_aisle"
        ):
            transformed = [transform(lon, lat) for lon, lat in coords]
            if len(transformed) >= 3:  # Ensure we have enough points for a polygon
                features["roads"].append(
                    {"coords": transformed, "type": "parking", "is_parking": True}
                )
                if self.debug:
                    print(f"Added parking area with {len(transformed)} points")

        # Handle railways (excluding tunnels)
        elif "railway" in props:
            # Skip if it's a tunnel
            if props.get("tunnel") in ["yes", "true", "1"]:
                if self.debug:
                    print(f"Skipping tunnel railway of type '{props.get('railway')}'")
                return

            transformed = [transform(lon, lat) for lon, lat in coords]
            if len(transformed) >= 2:  # Ensure we have enough points
                features["railways"].append(
                    {"coords": transformed, "type": props.get("railway", "unknown")}
                )
                if self.debug:
                    print(
                        f"Added railway of type '{props.get('railway', 'unknown')}' with {len(transformed)} points"
                    )

        # Handle water features
        elif "natural" in props and props["natural"] == "water":
            transformed = [transform(lon, lat) for lon, lat in coords]
            if len(transformed) >= 3:  # Ensure we have enough points for a polygon
                features["water"].append(
                    {"coords": transformed, "type": props.get("water", "unknown")}
                )
                if self.debug:
                    print(
                        f"Added water feature of type '{props.get('water', 'unknown')}' with {len(transformed)} points"
                    )
