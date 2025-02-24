# file: feature_processor.py

from shapely.geometry import box
from .building_processor import BuildingProcessor
from .industrial_processor import IndustrialProcessor
from .road_processor import RoadProcessor
from .railway_processor import RailwayProcessor
from .water_processor import WaterProcessor
from .barrier_processor import create_barrier_union
from .park_processor import ParkProcessor
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
        self.park_proc = ParkProcessor(self.geometry, style_manager, debug=self.debug)
        
    def process_features(self, geojson_data, size):
        """
        Parse the GeoJSON and gather features by category.
        Updated to better handle industrial areas.
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
            "parks": []
        }

        # First pass: process all features
        for feature in geojson_data["features"]:
            props = feature.get("properties", {})

            # Check for industrial features first
            if self.industrial_proc.should_process_as_industrial(props):
                if props.get("building"):
                    self.industrial_proc.process_industrial_building(feature, features, transform)
                else:
                    self.industrial_proc.process_industrial_area(feature, features, transform)
                continue

            # Process other feature types...
            if props.get("natural") == "water":
                self.water_proc.process_water(feature, features, transform)
            elif "building" in props:
                self.building_proc.process_building(feature, features, transform)
            elif self.road_proc.is_parking_area(props):
                self.road_proc.process_parking(feature, features, transform)
            elif "highway" in props:
                self.road_proc.process_road_or_bridge(feature, features, transform)
            elif "railway" in props:
                self.rail_proc.process_railway(feature, features, transform)
            #elif ("leisure" in props) or ("landuse" in props):
            #    self.park_proc.process_park(feature, features, transform)

        # Store features in style manager
        self.style_manager.set_current_features(features)

        # Debug summary
        if self.debug:
            print(f"\nProcessed feature counts:")
            for cat, items in features.items():
                print(f"  {cat}: {len(items)}")
                if cat == "industrial":
                    buildings = sum(1 for x in items if "building_type" in x)
                    areas = sum(1 for x in items if "landuse_type" in x)
                    print(f"    - Industrial buildings: {buildings}")
                    print(f"    - Industrial areas: {areas}")

        # Create barrier union and merge buildings
        barrier_union = create_barrier_union(
            roads=features["roads"],
            railways=features["railways"],
            water=features["water"],
            road_buffer=1.0,
            railway_buffer=1.0,
        )

        # Merge buildings + industrial
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