import random
from shapely.geometry import Polygon, MultiPolygon, box, LineString
from shapely.ops import unary_union
from shapely.validation import make_valid
from ..geometry import GeometryUtils

class BlockCombiner:
    """
    A refined block combiner that creates clean, printable 3D building blocks with:
    - Clear separation between blocks based on roads/water
    - Proper handling of industrial vs residential areas
    - Clean, non-overlapping roof structures
    - Building heights that make sense within blocks
    """

    def __init__(self, style_manager):
        self.style_manager = style_manager
        self.geometry = GeometryUtils()
        self.debug = False  # Enable/disable debug prints

        # Define block types and their characteristics
        self.BLOCK_TYPES = {
            'residential': {
                'min_height': 10.0,
                'max_height': 25.0,
                'roof_styles': [
                    {'name': 'pitched', 'height_factor': 0.3},
                    {'name': 'tiered', 'levels': 2},
                    {'name': 'flat', 'border': 1.0}
                ]
            },
            'industrial': {
                'min_height': 15.0,
                'max_height': 35.0,
                'roof_styles': [
                    {'name': 'sawtooth', 'angle': 30},
                    {'name': 'flat', 'border': 2.0},
                    {'name': 'stepped', 'levels': 3}
                ]
            },
            'commercial': {
                'min_height': 20.0,
                'max_height': 40.0,
                'roof_styles': [
                    {'name': 'modern', 'setback': 2.0},
                    {'name': 'tiered', 'levels': 3},
                    {'name': 'complex', 'variations': 4}
                ]
            }
        }

    def combine_buildings_by_block(self, features):
        """
        Main entry point that:
          1) Gathers all building footprints,
          2) Creates barrier geometry,
          3) Divides the map into blocks,
          4) Finds which footprints fall into each block,
          5) Processes them into final building shapes.
        """
        if self.debug:
            print("\n=== Block Combiner Debug ===")

        # 1. Gather footprints (buildings + industrial)
        building_footprints = self._gather_all_footprints(features)
        if self.debug:
            print(f"Found {len(building_footprints)} building footprints.")

        # 2. Create barrier geometry from roads/water
        barrier_union = self._create_barrier_union(features)

        # 3. Generate blocks by subtracting barriers from bounding area
        blocks = self._create_blocks_from_barriers(barrier_union)
        if self.debug:
            print(f"Generated {len(blocks)} blocks from barrier union.")

        # 4 & 5. For each block, find footprints, analyze, and process
        combined_buildings = []
        for block in blocks:
            block_buildings = self._find_buildings_in_block(block, building_footprints)
            block_info = self._analyze_block(block_buildings)
            processed_shapes = self._process_block_buildings(
                block, block_buildings, block_info, barrier_union
            )
            combined_buildings.extend(processed_shapes)

        # If you have footprints outside the bounding box, handle them here if desired.
        return combined_buildings

    def _gather_all_footprints(self, features):
        """
        Collect all building/industrial footprints into a unified list.
        """
        from shapely.geometry import Polygon
        from shapely.validation import make_valid

        footprints = []

        # Process "normal" building features
        for bldg in features.get('buildings', []):
            coords = bldg.get('coords')
            if not coords or len(coords) < 3:
                continue

            # Default building type
            bldg_type = 'residential'
            props = bldg.get('properties', {})
            if props.get('building') in ['commercial', 'retail', 'office']:
                bldg_type = 'commercial'
            elif props.get('building') in ['industrial', 'warehouse', 'factory']:
                bldg_type = 'industrial'

            poly = Polygon(coords)
            if not poly.is_valid:
                poly = make_valid(poly)
            if poly.is_valid and not poly.is_empty:
                footprints.append({
                    'polygon': poly,
                    'type': bldg_type,
                    'height': bldg.get('height', 10.0),
                    'original': bldg
                })

        # Process industrial features (both buildings and landuse areas)
        for ind in features.get('industrial', []):
            coords = ind.get('coords')
            if not coords or len(coords) < 3:
                continue

            poly = Polygon(coords)
            if not poly.is_valid:
                poly = make_valid(poly)
            if poly.is_empty or not poly.is_valid:
                continue

            if ind.get('landuse_type'):
                # If it's a large industrial area, optionally subdivide
                area = poly.area
                if area > 1000:
                    # Example: buffer inward to break it up
                    buffered = poly.buffer(-2.0)
                    if buffered.is_valid and not buffered.is_empty:
                        footprints.append({
                            'polygon': buffered,
                            'type': 'industrial',
                            'height': ind.get('height', 15.0),
                            'original': ind
                        })
                else:
                    footprints.append({
                        'polygon': poly,
                        'type': 'industrial',
                        'height': ind.get('height', 15.0),
                        'original': ind
                    })
            else:
                # It's an industrial building
                footprints.append({
                    'polygon': poly,
                    'type': 'industrial',
                    'height': ind.get('height', 15.0),
                    'original': ind
                })

        return footprints

    def _create_barrier_union(self, features):
        """
        Create a unified geometry of all barriers (roads, water, etc.).
        The result is used to subdivide the bounding box into 'blocks'.
        """
        from shapely.ops import unary_union

        barriers = []

        # Road buffer
        road_width = self.style_manager.get_default_layer_specs()["roads"]["width"]
        for road in features.get('roads', []):
            try:
                line = LineString(road["coords"])
                # Buffer roads by ~60% of the width to create a barrier
                buffered = line.buffer(road_width * 0.6)
                if buffered.is_valid and not buffered.is_empty:
                    barriers.append(buffered)
            except Exception:
                continue

        # Water buffer
        for water in features.get('water', []):
            try:
                poly = Polygon(water["coords"])
                if poly.is_valid and not poly.is_empty:
                    # Give water a 1.5m buffer for the barrier
                    barriers.append(poly.buffer(1.5))
            except Exception:
                continue

        if not barriers:
            return None

        unioned = unary_union(barriers)
        if not unioned.is_valid:
            unioned = make_valid(unioned)
        return unioned

    def _create_blocks_from_barriers(self, barrier_union):
        """
        Subtract the barrier geometry from its bounding box to get
        'blocks' (MultiPolygon) that remain between roads, water, etc.
        """
        if not barrier_union or barrier_union.is_empty:
            return []

        try:
            # Create bounding box around all barrier geometry
            minx, miny, maxx, maxy = barrier_union.bounds
            bounding_area = box(minx, miny, maxx, maxy)

            # Subtract barriers to form blocks
            blocks_area = bounding_area.difference(barrier_union)
            if blocks_area.is_empty:
                return []

            # Gather final blocks
            blocks = []
            if isinstance(blocks_area, MultiPolygon):
                for b in blocks_area.geoms:
                    if b.area > 5:  # was 100; lowered so small blocks are kept
                        simplified = b.simplify(0.1)  # was 0.5; less aggressive
                        if simplified.is_valid and not simplified.is_empty:
                            blocks.append(simplified)
            else:
                # Single polygon
                if blocks_area.area > 5:
                    simplified = blocks_area.simplify(0.1)
                    if simplified.is_valid and not simplified.is_empty:
                        blocks.append(simplified)

            return blocks

        except Exception as e:
            if self.debug:
                print(f"Error creating blocks: {e}")
            return []

    def _find_buildings_in_block(self, block, building_footprints):
        """
        Find all building footprints that intersect a given block polygon.
        """
        block_buildings = []
        for fp in building_footprints:
            try:
                shape = fp['polygon']
                if block.intersects(shape):
                    intersection = block.intersection(shape)
                    # Lower area cutoff from 10 down to 1
                    if not intersection.is_empty and intersection.area > 1:
                        fp_copy = dict(fp)
                        fp_copy['polygon'] = intersection
                        block_buildings.append(fp_copy)
            except Exception:
                continue
        return block_buildings

    def _analyze_block(self, block_buildings):
        """
        Inspect the buildings in this block to figure out a suitable block type
        or average height. 
        """
        if not block_buildings:
            return {'type': 'residential', 'avg_height': 15.0}

        # Tally up building types & compute weighted average height
        type_counts = {'residential': 0, 'industrial': 0, 'commercial': 0}
        total_area = 0.0
        weighted_height = 0.0

        for b in block_buildings:
            area = b['polygon'].area
            total_area += area
            weighted_height += b['height'] * area
            if b['type'] in type_counts:
                type_counts[b['type']] += 1
            else:
                type_counts['residential'] += 1

        block_type = max(type_counts, key=type_counts.get)
        avg_height = weighted_height / total_area if total_area > 0 else 15.0

        return {
            'type': block_type,
            'avg_height': avg_height,
            'building_count': len(block_buildings),
            'total_area': total_area
        }

    def _process_block_buildings(self, block, block_buildings, block_info, barrier_union):
        """
        Convert all footprints in this block into final 3D shapes,
        applying style rules, merging footprints, etc.
        """
        from shapely.ops import unary_union

        if not block_buildings:
            return []

        processed = []
        block_type = block_info['type']
        type_specs = self.BLOCK_TYPES.get(block_type, self.BLOCK_TYPES['residential'])

        # Union all footprints in this block
        try:
            footprints_union = unary_union([b['polygon'] for b in block_buildings])
            if not footprints_union.is_valid:
                footprints_union = make_valid(footprints_union)
        except Exception:
            return []

        # Possibly break a MultiPolygon into individual polygons
        polygons = []
        if isinstance(footprints_union, MultiPolygon):
            polygons.extend(footprints_union.geoms)
        else:
            polygons.append(footprints_union)

        for shape in polygons:
            if shape.is_empty or shape.area < 2:  # was 50; keep smaller shapes
                continue

            # Reduce simplification & negative buffering
            cleaned = shape.simplify(0.1)  # was 0.5
            if not cleaned.is_valid or cleaned.is_empty:
                continue

            # We can reduce the inward buffer from -0.3 to -0.1 or remove it entirely
            final_poly = cleaned.buffer(-0.1)
            if final_poly.is_empty:
                continue

            if barrier_union:
                clipped = final_poly.difference(barrier_union)
                if clipped.is_empty:
                    continue
            else:
                clipped = final_poly

            if clipped.is_empty or clipped.area < 1:
                continue

            # Convert to single polygons if it's still a MultiPolygon
            if isinstance(clipped, MultiPolygon):
                sub_polys = list(clipped.geoms)
            else:
                sub_polys = [clipped]

            for spoly in sub_polys:
                if spoly.is_empty or spoly.area < 1:
                    continue

                # Determine final building height
                base_height = self._calculate_building_height(block_info['avg_height'], type_specs)
                roof_style = self._select_roof_style(block_type)

                building_dict = {
                    'coords': list(spoly.exterior.coords)[:-1],
                    'height': base_height,
                    'block_type': block_type,
                    'roof_style': roof_style['name'],
                    'roof_params': roof_style
                }
                processed.append(building_dict)

        return processed

    def _calculate_building_height(self, avg_height, type_specs):
        """
        Pick a final building height that respects the block's average
        but also the block-type constraints.
        """
        min_h = type_specs['min_height']
        max_h = type_specs['max_height']

        base = max(avg_height, min_h)
        if base < 15.0:
            base = 15.0

        # Add a little random variation (+/- 15%)
        variation = random.uniform(0.85, 1.15)
        candidate = base * variation

        # Clamp to [min_h, max_h]
        final_height = max(min_h, min(candidate, max_h))
        return final_height

    def _select_roof_style(self, block_type):
        """
        Randomly pick a roof style from the block type's style list.
        """
        styles = self.BLOCK_TYPES.get(block_type, self.BLOCK_TYPES['residential'])['roof_styles']
        choice = random.choice(styles)

        # Add minor parameter variation
        if choice['name'] == 'pitched':
            choice['height_factor'] *= random.uniform(0.8, 1.2)
        elif choice['name'] == 'tiered':
            choice['levels'] = max(1, choice['levels'] + random.randint(-1, 1))
        elif choice['name'] == 'flat':
            choice['border'] *= random.uniform(0.9, 1.1)
        elif choice['name'] == 'sawtooth':
            choice['angle'] = max(10, choice['angle'] + random.randint(-5, 5))
        # etc. for others

        return choice
