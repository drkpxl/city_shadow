# lib/feature_processor/park_processor.py
from .base_processor import BaseProcessor

class ParkProcessor(BaseProcessor):
    """
    Processes OSM features for 'leisure' areas and green 'landuse' types
    (grass, forest, etc.) into a dedicated layer.
    """

    GREEN_LANDUSE_VALUES = {"grass", "forest", "meadow", "village_green", "farmland", "orchard"}
    GREEN_LEISURE_VALUES = {"park", "garden", "golf_course", "recreation_ground", "pitch", "playground"}

    def process_park(self, feature, features, transform):
        """
        Extract polygons that are either 'leisure' or 'landuse' in the 'green' family
        and store them into the `features["parks"]` bucket for later extrusion.
        """
        props = feature.get("properties", {})
        geometry_type = feature["geometry"]["type"]

        # Identify if feature is in one of our 'green' categories
        landuse = props.get("landuse", "").lower()
        leisure = props.get("leisure", "").lower()

        # If it's landuse in GREEN_LANDUSE_VALUES or leisure in GREEN_LEISURE_VALUES
        if (landuse in self.GREEN_LANDUSE_VALUES) or (leisure in self.GREEN_LEISURE_VALUES):
            # Extract raw coords
            coords = self.geometry.extract_coordinates(feature)
            if not coords:
                return

            # For polygons only: if it has at least 3 points
            # (We can skip linestring “parks” or points)
            if geometry_type in ["Polygon", "MultiPolygon"] and len(coords) >= 3:
                # Apply your standard lat/lon -> XY transform
                transformed = [transform(lon, lat) for lon, lat in coords]
                # Store them so we can extrude later in scad_generator
                features["parks"].append({"coords": transformed})
