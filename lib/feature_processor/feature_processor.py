# file: feature_processor.py

from shapely.geometry import box
from .building_processor import BuildingProcessor
from .industrial_processor import IndustrialProcessor
from .road_processor import RoadProcessor
from .railway_processor import RailwayProcessor
from .water_processor import WaterProcessor
from .barrier_processor import create_barrier_union

from ..geometry import GeometryUtils


class FeatureProcessor:
    def __init__(self, style_manager):
        self.style_manager = style_manager
        self.geometry = GeometryUtils()  # uses the same GeometryUtils
        self.debug = True  # set True for debug prints

        # Create sub-processor instances
        self.building_proc = BuildingProcessor(self.geometry, style_manager, debug=self.debug)
        self.industrial_proc = IndustrialProcessor(self.geometry, style_manager, debug=self.debug)
        self.road_proc = RoadProcessor(self.geometry, style_manager, debug=self.debug)
        self.rail_proc = RailwayProcessor(self.geometry, style_manager, debug=self.debug)
        self.water_proc = WaterProcessor(self.geometry, style_manager, debug=self.debug)

    def process_features(self, geojson_data, size):
        """
        Parse the GeoJSON and gather features by category: water, roads, railways, buildings, etc.
        Then merge buildings if needed, returning the final dictionary of feature lists.
        """

        # Create lat/lon -> model transform
        transform = self.geometry.create_coordinate_transformer(geojson_data["features"], size)

        # Initialize buckets
        features = {
            "water": [],
            "roads": [],
            "railways": [],
            "buildings": [],
            "bridges": [],
            "industrial": [],
        }

        # First pass: handle everything except industrial landuse
        for feature in geojson_data["features"]:
            props = feature.get("properties", {})

            # Coastline
            if props.get("natural") == "coastline":
                self.water_proc.process_coastline(feature, features, transform)
                continue

            # Water (e.g., rivers, lakes, ponds)
            if props.get("natural") == "water":
                self.water_proc.process_water(feature, features, transform)
                continue

            # Industrial buildings
            if props.get("building") == "industrial":
                self.industrial_proc.process_industrial_building(feature, features, transform)
                continue

            # "Regular" building
            if "building" in props:
                self.building_proc.process_building(feature, features, transform)
                continue

            # Parking vs roads vs bridges
            if self.road_proc.is_parking_area(props):
                self.road_proc.process_parking(feature, features, transform)
                continue
            if "highway" in props:
                self.road_proc.process_road_or_bridge(feature, features, transform)
                continue

            # Railways
            if "railway" in props:
                self.rail_proc.process_railway(feature, features, transform)
                continue

        # Second pass: handle industrial landuse polygons
        for feature in geojson_data["features"]:
            props = feature.get("properties", {})
            if props.get("landuse") == "industrial":
                self.industrial_proc.process_industrial_area(feature, features, transform)

        # After collecting everything, build the “ocean” polygon(s) from coastlines
        bounding_polygon = self._compute_bounding_polygon(size)
        self.water_proc.build_ocean_polygons(bounding_polygon, features)

        # Store features in style manager (so merges can see them)
        self.style_manager.set_current_features(features)

        # If debug is on, print summary
        if self.debug:
            print(f"\nProcessed feature counts:")
            for cat, items in features.items():
                print(f"  {cat}: {len(items)}")

        # Build a union of roads, rails, water to use as a barrier for building merges
        barrier_union = create_barrier_union(
            roads=features["roads"],
            railways=features["railways"],
            water=features["water"],
            road_buffer=1.0,
            railway_buffer=1.0,
        )

        # Merge all buildings + industrial into a single list
        all_buildings = features["buildings"] + features["industrial"]
        merged_bldgs = self.style_manager.merge_nearby_buildings(all_buildings, barrier_union)
        features["buildings"] = merged_bldgs

        return features

    def _compute_bounding_polygon(self, size):
        """
        Returns a Shapely Polygon from (0,0) to (size,size).
        We subtract coastline lines from this area to create
        an 'ocean' polygon, so it becomes everything outside
        the coastline but within the bounding box.
        """
        return box(0, 0, size, size)
