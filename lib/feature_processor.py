# lib/feature_processor.py
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from .geometry import GeometryUtils


class FeatureProcessor:
    def __init__(self, style_manager):
        self.style_manager = style_manager
        self.geometry = GeometryUtils()
        self.debug = False

    def process_features(self, geojson_data, size):
        """
        Process and enhance GeoJSON features.
        """
        # Create a transform function from lat/lon to model coordinates
        transform = self.geometry.create_coordinate_transformer(
            geojson_data["features"], size
        )

        # Initialize our feature buckets
        features = {
            "water": [],
            "roads": [],
            "railways": [],
            "buildings": [],
            "bridges": [],
        }

        # Loop through each GeoJSON feature and categorize
        for feature in geojson_data["features"]:
            self._process_single_feature(feature, features, transform)

        # Store features in style manager before any merging
        self.style_manager.set_current_features(features)

        # If debug is on, print counts
        if self.debug:
            print(f"\nProcessed feature counts:")
            print(f"Water features: {len(features['water'])}")
            print(f"Road features: {len(features['roads'])}")
            print(f"Railway features: {len(features['railways'])}")
            print(f"Building features: {len(features['buildings'])}")
            print(f"Bridge features: {len(features['bridges'])}")

        # Build one combined geometry for roads, railways, and water
        barrier_union = self.create_barrier_union(
            roads=features["roads"],
            railways=features["railways"],
            water=features["water"],
            road_buffer=1.0,
            railway_buffer=1.0,
        )

        # Merge buildings using the selected style
        features["buildings"] = self.style_manager.merge_nearby_buildings(
            features["buildings"], barrier_union=barrier_union
        )

        return features

    def _process_single_feature(self, feature, features, transform):
        """
        Examine each GeoJSON feature and decide whether it's a building,
        water feature, road, railway, or bridge, etc., storing it accordingly.
        """
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        # Buildings
        if "building" in props:
            area_m2 = self.geometry.approximate_polygon_area_m2(coords)
            min_area = self.style_manager.style.get("min_building_area", 600.0)

            if area_m2 < min_area:
                if self.debug:
                    print(f"Skipping small building with area {area_m2:.1f}m²")
                return

            # Transform coordinates
            transformed = [transform(lon, lat) for lon, lat in coords]
            height = self.style_manager.scale_building_height(props)
            features["buildings"].append({"coords": transformed, "height": height})
            if self.debug:
                print(
                    f"Added building with height {height:.1f}mm and area {area_m2:.1f}m²"
                )

        # Roads / Bridges
        elif "highway" in props:
            # Skip tunnels
            if props.get("tunnel") in ["yes", "true", "1"]:
                if self.debug:
                    print(f"Skipping tunnel road of type '{props.get('highway')}'")
                return

            transformed = [transform(lon, lat) for lon, lat in coords]
            if len(transformed) < 2:
                return

            if props.get("bridge") in ["yes", "true", "1"]:
                # Mark as a bridge
                bridge_type = props.get("highway", "bridge")
                features["bridges"].append({"coords": transformed, "type": bridge_type})
                if self.debug:
                    print(
                        f"Added bridge of type '{bridge_type}' with {len(transformed)} points"
                    )
            else:
                # Normal road
                road_type = props.get("highway", "unknown")
                features["roads"].append(
                    {"coords": transformed, "type": road_type, "is_parking": False}
                )
                if self.debug:
                    print(
                        f"Added road of type '{road_type}' with {len(transformed)} points"
                    )

        # Parking areas
        elif (
            props.get("amenity") == "parking"
            or props.get("parking") == "surface"
            or props.get("service") == "parking_aisle"
        ):
            transformed = [transform(lon, lat) for lon, lat in coords]
            if len(transformed) >= 3:  # polygon
                features["roads"].append(
                    {"coords": transformed, "type": "parking", "is_parking": True}
                )
                if self.debug:
                    print(f"Added parking area with {len(transformed)} points")

        # Railways (excluding tunnels)
        elif "railway" in props:
            if props.get("tunnel") in ["yes", "true", "1"]:
                if self.debug:
                    print(f"Skipping tunnel railway of type '{props.get('railway')}'")
                return

            transformed = [transform(lon, lat) for lon, lat in coords]
            if len(transformed) >= 2:
                features["railways"].append(
                    {"coords": transformed, "type": props.get("railway", "unknown")}
                )
                if self.debug:
                    print(
                        f"Added railway '{props.get('railway', 'unknown')}' with {len(transformed)} points"
                    )

        # Water features
        elif props.get("natural") == "water":
            transformed = [transform(lon, lat) for lon, lat in coords]
            if len(transformed) >= 3:
                features["water"].append(
                    {"coords": transformed, "type": props.get("water", "unknown")}
                )
                if self.debug:
                    print(f"Added water feature with {len(transformed)} points")

        # (Add more elif blocks for parks, forests, etc., if needed)

    def create_barrier_union(
        self, roads, railways, water, road_buffer=2.0, railway_buffer=2.0
    ):
        """
        Combine roads, railways, and water into one shapely geometry (unary_union).
        """
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
