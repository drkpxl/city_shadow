# lib/preprocessor.py (updated with geometric clipping using Shapely)

from copy import deepcopy
import json
import statistics
from math import radians, cos, sin, sqrt, pi
from shapely.geometry import shape, mapping, box, Point


class GeoJSONPreprocessor:
    def __init__(self, bbox=None, distance_meters=None):
        """
        bbox: [south, west, north, east]
        distance_meters: radius (in meters) to crop from the center
        """
        self.bbox = bbox
        self.distance = distance_meters
        self.debug = True

    def create_cropping_geometry(self, features):
        """
        Create a Shapely geometry to use for cropping. Either a bounding box
        or a circular buffer (approximating the given distance in meters) is used.
        """
        if self.distance:
            # Calculate center from all features
            all_coords = []
            for feature in features:
                all_coords.extend(self.extract_coordinates(feature))
            if not all_coords:
                raise ValueError("No coordinates found in features")
            lons, lats = zip(*all_coords)
            center_lon = statistics.median(lons)
            center_lat = statistics.median(lats)
            # Convert distance in meters to degrees (approximation)
            radius_degrees = self.distance / 111320.0
            cropping_geom = Point(center_lon, center_lat).buffer(radius_degrees)
            if self.debug:
                print(
                    f"Using circular cropping geometry with center: ({center_lon:.6f}, {center_lat:.6f}) and radius (deg): {radius_degrees:.6f}"
                )
            return cropping_geom
        elif self.bbox:
            # bbox provided as [south, west, north, east]
            south, west, north, east = self.bbox
            cropping_geom = box(west, south, east, north)
            if self.debug:
                print(f"Using bounding box cropping geometry: {self.bbox}")
            return cropping_geom
        else:
            return None

    def extract_coordinates(self, feature):
        """Extract all coordinates from a feature regardless of geometry type"""
        geometry = feature["geometry"]
        coords = []

        if geometry["type"] == "Point":
            coords = [geometry["coordinates"]]
        elif geometry["type"] == "LineString":
            coords = geometry["coordinates"]
        elif geometry["type"] == "Polygon":
            for ring in geometry["coordinates"]:
                coords.extend(ring)
        elif geometry["type"] == "MultiPolygon":
            for polygon in geometry["coordinates"]:
                for ring in polygon:
                    coords.extend(ring)
        elif geometry["type"] == "MultiLineString":
            for line in geometry["coordinates"]:
                coords.extend(line)

        return coords

    def crop_feature(self, feature, cropping_geom):
        """
        Crop a feature to the cropping geometry using geometric intersection.
        Returns a new feature with the clipped geometry, or None if no intersection.
        """
        try:
            geom = shape(feature["geometry"])
        except Exception as e:
            if self.debug:
                print(f"Failed to parse geometry: {e}")
            return None

        # Compute the intersection with the cropping geometry
        clipped = geom.intersection(cropping_geom)
        if clipped.is_empty:
            return None

        # Handle GeometryCollection by selecting a valid geometry if possible
        if clipped.geom_type == "GeometryCollection":
            valid_geoms = [
                g
                for g in clipped
                if g.geom_type
                in ["Polygon", "MultiPolygon", "LineString", "MultiLineString"]
            ]
            if not valid_geoms:
                return None
            # Pick the largest polygon if available; otherwise use the first valid geometry
            polygons = [
                g for g in valid_geoms if g.geom_type in ["Polygon", "MultiPolygon"]
            ]
            clipped = (
                max(polygons, key=lambda g: g.area) if polygons else valid_geoms[0]
            )

        new_feature = deepcopy(feature)
        new_feature["geometry"] = mapping(clipped)
        return new_feature

    def process_geojson(self, input_data):
        """
        Process the GeoJSON data by clipping each feature to the defined cropping geometry.
        """
        features = input_data.get("features", [])
        cropping_geom = self.create_cropping_geometry(features)
        if cropping_geom is None:
            raise ValueError(
                "No cropping geometry defined (neither bbox nor distance provided)"
            )

        new_features = []
        for feature in features:
            cropped = self.crop_feature(feature, cropping_geom)
            if cropped:
                new_features.append(cropped)

        if self.debug:
            print(f"Original features: {len(features)}")
            print(f"Cropped features: {len(new_features)}")

        output_data = {"type": "FeatureCollection", "features": new_features}
        return output_data


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Preprocess GeoJSON for 3D city modeling"
    )
    parser.add_argument("input_file", help="Input GeoJSON file")
    parser.add_argument("output_file", help="Output GeoJSON file")
    parser.add_argument(
        "--distance", type=float, help="Distance in meters from center to crop"
    )
    parser.add_argument(
        "--bbox",
        type=float,
        nargs=4,
        metavar=("SOUTH", "WEST", "NORTH", "EAST"),
        help="Bounding box coordinates (south west north east)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    args = parser.parse_args()

    if not args.distance and not args.bbox:
        parser.error("Either --distance or --bbox must be specified")

    try:
        with open(args.input_file, "r") as f:
            input_data = json.load(f)

        processor = GeoJSONPreprocessor(
            bbox=args.bbox if args.bbox else None,
            distance_meters=args.distance if args.distance else None,
        )
        processor.debug = args.debug
        output_data = processor.process_geojson(input_data)

        with open(args.output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"Successfully processed GeoJSON data and saved to {args.output_file}")

    except Exception as e:
        print(f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
