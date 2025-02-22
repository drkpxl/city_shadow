# lib/feature_processor.py
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from .geometry import GeometryUtils
from .style.style_manager import StyleManager


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
            "industrial": [],  # New category for industrial areas
        }

        # First pass: Process everything except industrial landuse
        for feature in geojson_data["features"]:
            if feature.get("properties", {}).get("landuse") != "industrial":
                self._process_single_feature(feature, features, transform)

        # Second pass: Process industrial landuse
        for feature in geojson_data["features"]:
            if feature.get("properties", {}).get("landuse") == "industrial":
                self._process_industrial_area(feature, features, transform)

        # Store features in style manager before any merging
        self.style_manager.set_current_features(features)

        # If debug is on, print counts
        if self.debug:
            print(f"\nProcessed feature counts:")
            for category, items in features.items():
                print(f"{category.capitalize()}: {len(items)}")

        # Build one combined geometry for roads, railways, and water
        barrier_union = self.create_barrier_union(
            roads=features["roads"],
            railways=features["railways"],
            water=features["water"],
            road_buffer=1.0,
            railway_buffer=1.0,
        )

        # Merge buildings using the selected style
        all_buildings = features["buildings"] + features["industrial"]
        features["buildings"] = self.style_manager.merge_nearby_buildings(
            all_buildings, barrier_union=barrier_union
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

        # Industrial Buildings (specific handling)
        if props.get("building") == "industrial":
            self._process_industrial_building(props, coords, features, transform)
            return

        # Regular Buildings
        if "building" in props:
            self._process_building(props, coords, features, transform)
            return

        # Roads / Bridges
        if "highway" in props:
            self._process_road_or_bridge(props, coords, features, transform)
            return

        # Parking areas
        if self._is_parking_area(props):
            self._process_parking(coords, features, transform)
            return

        # Railways
        if "railway" in props and not props.get("tunnel") in ["yes", "true", "1"]:
            self._process_railway(props, coords, features, transform)
            return

        # Water features
        if props.get("natural") == "water":
            self._process_water(props, coords, features, transform)
            return

    def _process_industrial_area(self, feature, features, transform):
        """Process industrial landuse areas as potential buildings."""
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        # Transform coordinates
        transformed = [transform(lon, lat) for lon, lat in coords]

        # Use a minimum height for industrial areas
        min_height = self.style_manager.get_default_layer_specs()["buildings"][
            "min_height"
        ]

        # Check if this area should be treated as a building
        if self.style_manager.style["artistic_style"] == "block-combine":
            features["industrial"].append(
                {"coords": transformed, "height": min_height, "is_industrial": True}
            )
            if self.debug:
                print(f"Added industrial area with height {min_height}mm")

    def _process_industrial_building(self, props, coords, features, transform):
        """Process an industrial building with specific handling."""
        area_m2 = self.geometry.approximate_polygon_area_m2(coords)
        min_area = self.style_manager.style.get("min_building_area", 600.0)

        if area_m2 < min_area:
            if self.debug:
                print(f"Skipping small industrial building with area {area_m2:.1f}m²")
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        height = self.style_manager.scale_building_height(props)

        # Ensure minimum height for industrial buildings
        min_height = self.style_manager.get_default_layer_specs()["buildings"][
            "min_height"
        ]
        height = max(height, min_height)

        features["industrial"].append(
            {"coords": transformed, "height": height, "is_industrial": True}
        )
        if self.debug:
            print(
                f"Added industrial building with height {height:.1f}mm and area {area_m2:.1f}m²"
            )

    def _process_building(self, props, coords, features, transform):
        """Process a regular building."""
        area_m2 = self.geometry.approximate_polygon_area_m2(coords)
        min_area = self.style_manager.style.get("min_building_area", 600.0)

        if area_m2 < min_area:
            if self.debug:
                print(f"Skipping small building with area {area_m2:.1f}m²")
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        height = self.style_manager.scale_building_height(props)
        features["buildings"].append({"coords": transformed, "height": height})
        if self.debug:
            print(f"Added building with height {height:.1f}mm and area {area_m2:.1f}m²")

    def _is_parking_area(self, props):
        """Check if feature is a parking area."""
        return (
            props.get("amenity") == "parking"
            or props.get("parking") == "surface"
            or props.get("service") == "parking_aisle"
        )

    def _process_parking(self, coords, features, transform):
        """Process a parking area."""
        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) >= 3:  # polygon
            features["roads"].append(
                {"coords": transformed, "type": "parking", "is_parking": True}
            )
            if self.debug:
                print(f"Added parking area with {len(transformed)} points")

    def _process_road_or_bridge(self, props, coords, features, transform):
        """Process a road or bridge feature."""
        # Skip tunnels
        if props.get("tunnel") in ["yes", "true", "1"]:
            if self.debug:
                print(f"Skipping tunnel road of type '{props.get('highway')}'")
            return

        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) < 2:
            return

        if props.get("bridge") in ["yes", "true", "1"]:
            bridge_type = props.get("highway", "bridge")
            features["bridges"].append({"coords": transformed, "type": bridge_type})
            if self.debug:
                print(
                    f"Added bridge of type '{bridge_type}' with {len(transformed)} points"
                )
        else:
            road_type = props.get("highway", "unknown")
            features["roads"].append(
                {"coords": transformed, "type": road_type, "is_parking": False}
            )
            if self.debug:
                print(
                    f"Added road of type '{road_type}' with {len(transformed)} points"
                )

    def _process_railway(self, props, coords, features, transform):
        """Process a railway feature."""
        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) >= 2:
            features["railways"].append(
                {"coords": transformed, "type": props.get("railway", "unknown")}
            )
            if self.debug:
                print(
                    f"Added railway '{props.get('railway', 'unknown')}' with {len(transformed)} points"
                )

    def _process_water(self, props, coords, features, transform):
        """Process a water feature."""
        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) >= 3:
            features["water"].append(
                {"coords": transformed, "type": props.get("water", "unknown")}
            )
            if self.debug:
                print(f"Added water feature with {len(transformed)} points")

    def create_barrier_union(
        self, roads, railways, water, road_buffer=2.0, railway_buffer=2.0
    ):
        """Combine roads, railways, and water into one shapely geometry."""
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
