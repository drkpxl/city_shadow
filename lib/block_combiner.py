# lib/block_combiner.py
from shapely.geometry import Polygon, MultiPolygon, box, LineString, mapping
from shapely.ops import unary_union, polygonize
from shapely.validation import make_valid
from .geometry import GeometryUtils


class BlockCombiner:
    def __init__(self, style_manager):
        self.style_manager = style_manager
        self.geometry = GeometryUtils()
        self.debug = False

    def combine_buildings_by_block(self, features):
        """
        Fill each block that has any building coverage.
        """
        if self.debug:
            print("\nStarting block combination process...")
            print(f"Number of input buildings: {len(features.get('buildings', []))}")

        # Create blocks from road network
        blocks = self._create_blocks_from_roads(features.get("roads", []))
        if self.debug:
            print(f"Created {len(blocks)} blocks from road network")

        # Convert all buildings, no minimum size filtering
        building_polygons = []
        for building in features.get("buildings", []):
            try:
                # Always try to create polygon, regardless of size
                poly = Polygon(building["coords"])
                height = building.get("height", 5.0)  # Default height if not specified

                if poly.is_valid:
                    building_polygons.append((poly, height))
                else:
                    fixed_poly = make_valid(poly)
                    if isinstance(fixed_poly, MultiPolygon):
                        for p in fixed_poly.geoms:
                            if p.is_valid:
                                building_polygons.append((p, height))
                    elif fixed_poly.is_valid:
                        building_polygons.append((fixed_poly, height))
            except Exception as e:
                if self.debug:
                    print(f"Error processing building: {e}")
                continue

        if self.debug:
            print(f"Processed {len(building_polygons)} valid building polygons")

        # Create a union of all buildings for coverage checking
        all_buildings = unary_union([poly for poly, _ in building_polygons])
        if not all_buildings.is_valid:
            all_buildings = make_valid(all_buildings)

        combined_buildings = []
        default_height = 5.0

        # Process each block
        for block_idx, block in enumerate(blocks):
            try:
                # Check for any building intersection, no matter how small
                if block.intersects(all_buildings):
                    # Find all buildings in this block
                    block_heights = []
                    for building_poly, height in building_polygons:
                        if block.intersects(building_poly):
                            intersection = block.intersection(building_poly)
                            if intersection.area > 0:
                                block_heights.append((height, intersection.area))

                    # Get block height
                    if block_heights:
                        # Use height of largest building
                        block_height = max(block_heights, key=lambda x: x[1])[0]
                    else:
                        block_height = default_height

                    # Create slightly smaller block footprint
                    block_shape = block.buffer(-0.1)
                    if block_shape.is_valid:
                        coords = list(block_shape.exterior.coords)[:-1]
                        combined_buildings.append(
                            {"coords": coords, "height": block_height, "is_block": True}
                        )
                        if self.debug:
                            print(f"Added block {block_idx} with height {block_height}")

            except Exception as e:
                if self.debug:
                    print(f"Error processing block {block_idx}: {e}")
                continue

        if self.debug:
            print(f"\nFinal combined buildings count: {len(combined_buildings)}")

        return combined_buildings

    def _create_blocks_from_roads(self, roads):
        """
        Create blocks from road network.
        """
        try:
            road_polys = []
            road_width = self.style_manager.get_default_layer_specs()["roads"]["width"]

            for road in roads:
                try:
                    line = LineString(road["coords"])
                    buffered = line.buffer(road_width / 2)
                    if buffered.is_valid:
                        road_polys.append(buffered)
                except Exception as e:
                    if self.debug:
                        print(f"Error processing road: {e}")
                    continue

            if not road_polys:
                return []

            road_union = unary_union(road_polys)
            if not road_union.is_valid:
                road_union = make_valid(road_union)

            bounds = road_union.bounds
            area = box(*bounds)
            blocks_area = area.difference(road_union)

            if isinstance(blocks_area, MultiPolygon):
                blocks = [poly for poly in blocks_area.geoms if poly.is_valid]
            else:
                blocks = [blocks_area] if blocks_area.is_valid else []

            # No minimum block size filtering
            if self.debug:
                print(f"Created {len(blocks)} blocks")

            return blocks

        except Exception as e:
            if self.debug:
                print(f"Error creating blocks from roads: {e}")
            return []
