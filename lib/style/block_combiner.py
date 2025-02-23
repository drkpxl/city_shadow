# lib/style/block_combiner.py

import random
from shapely.geometry import Polygon, MultiPolygon, box, LineString
from shapely.ops import unary_union
from shapely.validation import make_valid
from ..geometry import GeometryUtils


class BlockCombiner:
    def __init__(self, style_manager):
        self.style_manager = style_manager
        self.geometry = GeometryUtils()
        self.debug = False

    def combine_buildings_by_block(self, features):
        """
        Fill each block that has any building coverage. For each block:
          1) Compute a block-wide height based on the largest building in that block.
          2) Slightly randomize the final height to avoid uniform extrusions.
          3) Randomly pick a 'roof_style' so block roofs vary (flat, sawtooth, etc.).
        """
        if self.debug:
            print("\nStarting block combination process...")
            print(f"Number of input buildings: {len(features.get('buildings', []))}")

        # 1) Create blocks from road network
        blocks = self._create_blocks_from_roads(features.get("roads", []))
        if self.debug:
            print(f"Created {len(blocks)} blocks from road network")

        # 2) Gather building polygons (no minimum area filter here)
        building_polygons = []
        for building in features.get("buildings", []):
            try:
                poly = Polygon(building["coords"])
                height = building.get("height", 5.0)  # Default if missing
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

        # 3) Create a union of all buildings for intersection checks
        if building_polygons:
            all_buildings = unary_union([poly for (poly, _) in building_polygons])
            if not all_buildings.is_valid:
                all_buildings = make_valid(all_buildings)
        else:
            all_buildings = None

        combined_buildings = []
        default_height = 5.0

        # 4) Process each block
        for block_idx, block_geom in enumerate(blocks):
            try:
                # If there are no buildings at all, or block doesn't intersect them, skip
                if not all_buildings or not block_geom.intersects(all_buildings):
                    continue

                # Find the largest building (by intersection area) that touches this block
                block_heights = []
                for (building_poly, bldg_height) in building_polygons:
                    if block_geom.intersects(building_poly):
                        intersection = block_geom.intersection(building_poly)
                        if intersection.area > 0:
                            block_heights.append((bldg_height, intersection.area))

                # If at least one building intersects, pick the largest intersection’s height
                if block_heights:
                    block_height = max(block_heights, key=lambda x: x[1])[0]
                else:
                    block_height = default_height

                # [Add a slight buffer shrink, so roads remain visible]
                block_shape = block_geom.buffer(-0.1)
                if not block_shape.is_valid:
                    block_shape = make_valid(block_shape)

                if block_shape.is_valid and not block_shape.is_empty:
                    coords = list(block_shape.exterior.coords)[:-1]

                    # -----------------------------------------
                    # [ADDED RANDOMIZATION SECTION]
                    # Slight random factor for final block height
                    rand_factor = random.uniform(0.85, 1.15)
                    final_height = block_height * rand_factor

                    # Randomly pick a style for the block's roof
                    roof_style = random.choice(["flat", "sawtooth", "modern", "step"])
                    # -----------------------------------------

                    combined_buildings.append({
                        "coords": coords,
                        "height": final_height,
                        "roof_style": roof_style,  # stored for SCAD generator
                        "is_block": True
                    })

                    if self.debug:
                        print(f"Block {block_idx} height ~ {final_height:.2f}, style={roof_style}")

            except Exception as e:
                if self.debug:
                    print(f"Error processing block {block_idx}: {e}")
                continue

        if self.debug:
            print(f"\nFinal combined buildings count: {len(combined_buildings)}")

        return combined_buildings

    def _create_blocks_from_roads(self, roads):
        """
        Use the road network to produce 'blocks' as polygons. We take each road,
        buffer it by half its width, then subtract from the bounding area to get blocks.
        """
        try:
            road_polys = []
            road_width = self.style_manager.get_default_layer_specs()["roads"]["width"]

            for road in roads:
                try:
                    line = LineString(road["coords"])
                    # Buffer by half the road width
                    buffered = line.buffer(road_width * 0.5)
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

            # bounding rectangle for union
            minx, miny, maxx, maxy = road_union.bounds
            area = box(minx, miny, maxx, maxy)

            blocks_area = area.difference(road_union)

            # May be multiple polygons if the bounding area was large
            if blocks_area.is_empty:
                return []
            elif isinstance(blocks_area, MultiPolygon):
                blocks = [poly for poly in blocks_area.geoms if poly.is_valid]
            else:
                blocks = [blocks_area] if blocks_area.is_valid else []

            return blocks

        except Exception as e:
            if self.debug:
                print(f"Error creating blocks from roads: {e}")
            return []
