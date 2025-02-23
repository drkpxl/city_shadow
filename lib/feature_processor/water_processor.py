# lib/feature_processor/water_processor.py
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from .base_processor import BaseProcessor

class WaterProcessor(BaseProcessor):
    def __init__(self, geometry_utils, style_manager, debug=False):
        super().__init__(geometry_utils, style_manager, debug)
        self.coastline_segments = []  # store coastline lines here

    def process_water(self, feature, features, transform):
        """Process a natural water feature (lakes, rivers, ponds, etc.)."""
        props = feature.get("properties", {})
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        # The existing "natural=water" logic remains unchanged.
        if props.get("natural") == "water":
            transformed = [transform(lon, lat) for lon, lat in coords]
            if len(transformed) >= 3:
                features["water"].append(
                    {"coords": transformed, "type": props.get("water", "unknown")}
                )
                if self.debug:
                    print(f"Added water feature, {len(transformed)} points")

    def process_coastline(self, feature, features, transform):
        """
        Capture coastline segments (LineStrings).
        We'll build ocean polygons later in a separate step.
        """
        coords = self.geometry.extract_coordinates(feature)
        if not coords:
            return

        # Coastlines in OSM are usually stored as LineString(s)
        transformed = [transform(lon, lat) for lon, lat in coords]
        if len(transformed) < 2:
            return

        self.coastline_segments.append(transformed)
        if self.debug:
            print(f"Captured coastline segment with {len(transformed)} points")

    def build_ocean_polygons(self, bounding_polygon, features):
        """
        After all features have been processed, call this to create an
        'ocean' polygon that fills everything outside the coastline but
        within the bounding_polygon.
        """
        if not self.coastline_segments:
            return  # No coastlines to process

        # 1) Turn each coastline segment into a Shapely LineString
        lines = [LineString(seg) for seg in self.coastline_segments]

        # 2) Merge them all into one unified geometry
        coastline_union = unary_union(lines)

        # If the coastlines are broken or have gaps (due to inlets, parks, bridges, etc.),
        # a larger buffer is needed to “close” the coastline.
        # 3) Buffer the coastline union with an increased buffer value to bridge gaps.
        coastline_poly = coastline_union.buffer(1.0)  # Updated buffer value (from 0.0001 to 1.0)
        ocean_polygon = bounding_polygon.difference(coastline_poly)
        print("Coastline union is valid?", coastline_union.is_valid)
        print("Coastline union geometry type:", coastline_union.geom_type)

        if ocean_polygon.is_empty:
            if self.debug:
                print("Ocean polygon ended up empty—coastline might be incomplete.")
            return

        # 4) Save the final polygon(s) to features["water"].
        if ocean_polygon.geom_type == "Polygon":
            poly_coords = list(ocean_polygon.exterior.coords)
            features["water"].append({"coords": poly_coords, "type": "ocean"})
            if self.debug:
                print(f"Built ocean polygon with {len(poly_coords)} points")
        elif ocean_polygon.geom_type == "MultiPolygon":
            for geom in ocean_polygon.geoms:
                if geom.geom_type == "Polygon":
                    poly_coords = list(geom.exterior.coords)
                    features["water"].append({"coords": poly_coords, "type": "ocean"})
                    if self.debug:
                        print(f"Built ocean sub-polygon with {len(poly_coords)} points")
