# lib/style/block_combiner.py
import random
from shapely.geometry import Polygon, MultiPolygon, LineString, box
from shapely.ops import unary_union
from shapely.validation import make_valid
from ..geometry import GeometryUtils

class BlockCombiner:
    """
    This class handles the combination of building footprints.
    
    For styles other than "block-combine", it uses the legacy block subdivision logic.
    For "block-combine" style, it performs area-based merging:
      1. If a footprint’s area is >= 1000 m², it is left unmerged.
      2. If it is smaller, it is merged with nearby unblocked footprints until the
         unioned polygon’s area is at least 1000 m².
      3. If the merged union is a MultiPolygon, the largest polygon is used.
      4. A random roof style is assigned to merged clusters.
    """
    def __init__(self, style_manager):
        self.style_manager = style_manager
        self.geometry = GeometryUtils()
        self.debug = False  # Enable to print debug messages
        
        # Legacy block types for non-"block-combine" styles
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
        Main entry point.
        If artistic_style is "block-combine", use area-based merging.
        Otherwise, use the legacy block subdivision approach.
        """
        if self.style_manager.style.get("artistic_style") == "block-combine":
            return self._area_based_merge(features)
        else:
            return self._legacy_combine(features)
    
    def _area_based_merge(self, features):
        """
        Implements area-based merging.
        Gather footprints from buildings and industrial features.
        Any footprint with area >= 1000 m² is left alone.
        Otherwise, small footprints (area < 1000) are merged iteratively
        (if within merge_distance and not blocked) until the unioned area reaches 1000 m².
        """
        AREA_THRESHOLD = 1000  # in m²
        footprints = self._gather_all_footprints(features)
        barrier_union = self._create_barrier_union(features)
        
        # Separate into "large" (>= AREA_THRESHOLD) and "small" (< AREA_THRESHOLD)
        large = [fp for fp in footprints if fp['area'] >= AREA_THRESHOLD]
        small = [fp for fp in footprints if fp['area'] < AREA_THRESHOLD]
        
        merged_clusters = []
        visited = set()
        merge_dist = self.style_manager.style.get("merge_distance", 2.0)
        
        for i, fp in enumerate(small):
            if i in visited:
                continue
            cluster = [fp]
            visited.add(i)
            cluster_union = fp['polygon']
            total_area = fp['area']
            weighted_height = fp.get('height', 10.0) * fp['area']
            
            growing = True
            while growing and cluster_union.area < AREA_THRESHOLD:
                growing = False
                for j, candidate in enumerate(small):
                    if j in visited:
                        continue
                    if candidate['polygon'].distance(cluster_union) < merge_dist:
                        centroid_cluster = cluster_union.centroid
                        centroid_candidate = candidate['polygon'].centroid
                        if not self._is_blocked((centroid_cluster.x, centroid_cluster.y),
                                                (centroid_candidate.x, centroid_candidate.y),
                                                barrier_union):
                            cluster.append(candidate)
                            visited.add(j)
                            cluster_union = unary_union([cluster_union, candidate['polygon']])
                            cluster_union = make_valid(cluster_union)  # Ensure valid polygon
                            total_area += candidate['area']
                            weighted_height += candidate.get('height', 10.0) * candidate['area']
                            growing = True
                # End for
            # End while
            
            # If the union is a MultiPolygon, select the largest polygon.
            if cluster_union.geom_type == "MultiPolygon":
                largest_poly = max(cluster_union.geoms, key=lambda g: g.area)
                cluster_union = largest_poly
            
            avg_height = weighted_height / total_area if total_area > 0 else 4.0
            merged_clusters.append({
                'coords': list(cluster_union.exterior.coords)[:-1],
                'height': avg_height,
                'is_cluster': len(cluster) > 1,
                'roof_style': self._select_random_roof() if len(cluster) > 1 else None
            })
        
        # Process large footprints: leave them unmerged.
        large_buildings = []
        for fp in large:
            poly = fp['polygon']
            if poly.geom_type == "MultiPolygon":
                poly = max(poly.geoms, key=lambda g: g.area)
            large_buildings.append({
                'coords': list(poly.exterior.coords)[:-1],
                'height': fp.get('height', 10.0),
                'is_cluster': False,
                'roof_style': None
            })
        
        if self.debug:
            print(f"Area-based merge: {len(large_buildings)} large buildings, {len(merged_clusters)} merged clusters.")
        return large_buildings + merged_clusters
    def _legacy_combine(self, features):
        """
        Legacy block subdivision approach.
        (This is the original method that divides the map into blocks,
        finds footprints in each block, and processes them.)
        """
        if self.debug:
            print("\n=== Legacy Block Combiner Debug ===")
        building_footprints = self._gather_all_footprints(features)
        if self.debug:
            print(f"Found {len(building_footprints)} building footprints.")
        barrier_union = self._create_barrier_union(features)
        blocks = self._create_blocks_from_barriers(barrier_union)
        if self.debug:
            print(f"Generated {len(blocks)} blocks from barrier union.")
        combined_buildings = []
        for block in blocks:
            block_buildings = self._find_buildings_in_block(block, building_footprints)
            block_info = self._analyze_block(block_buildings)
            processed_shapes = self._process_block_buildings(block, block_buildings, block_info, barrier_union)
            combined_buildings.extend(processed_shapes)
        return combined_buildings

    def _gather_all_footprints(self, features):
        """
        Collect all building/industrial footprints into a unified list.
        Each entry is a dict with keys:
        - 'polygon': a valid shapely Polygon,
        - 'height': building height (default 10.0 for buildings, 15.0 for industrial),
        - 'area': computed area of the polygon.
        """
        from shapely.geometry import Polygon
        from shapely.validation import make_valid
        
        footprints = []
        
        # Process normal building features.
        for bldg in features.get('buildings', []):
            coords = bldg.get('coords')
            if not coords or len(coords) < 3:
                continue
            poly = Polygon(coords)
            if not poly.is_valid:
                poly = make_valid(poly)
            if poly.is_valid and not poly.is_empty:
                footprints.append({
                    'polygon': poly,
                    'height': bldg.get('height', 10.0),
                    'area': poly.area,
                    'original': bldg
                })
        
        # Process industrial features.
        for ind in features.get('industrial', []):
            coords = ind.get('coords')
            if not coords or len(coords) < 3:
                continue
            poly = Polygon(coords)
            if not poly.is_valid:
                poly = make_valid(poly)
            if poly.is_empty or not poly.is_valid:
                continue
            footprints.append({
                'polygon': poly,
                'height': ind.get('height', 15.0),
                'area': poly.area,
                'original': ind
            })
        return footprints

    def _create_barrier_union(self, features):
        """
        Create a union of barrier geometries (roads, water).
        """
        from shapely.ops import unary_union
        barriers = []
        
        road_width = self.style_manager.get_default_layer_specs()["roads"]["width"]
        for road in features.get('roads', []):
            try:
                line = LineString(road["coords"])
                buffered = line.buffer(road_width * 0.6)
                if buffered.is_valid and not buffered.is_empty:
                    barriers.append(buffered)
            except Exception:
                continue
        
        for water in features.get('water', []):
            try:
                poly = Polygon(water["coords"])
                if poly.is_valid and not poly.is_empty:
                    barriers.append(poly.buffer(1.5))
            except Exception:
                continue
        
        if not barriers:
            return None
        
        unioned = unary_union(barriers)
        if not unioned.is_valid:
            unioned = make_valid(unioned)
        return unioned

    def _is_blocked(self, ptA, ptB, barrier_union):
        """
        Return True if the straight-line between ptA and ptB (each a (x,y) tuple)
        intersects the barrier union.
        """
        if barrier_union is None:
            return False
        line = LineString([ptA, ptB])
        return line.intersects(barrier_union)
    
    def _create_blocks_from_barriers(self, barrier_union):
        """
        Legacy method: subtract the barrier union from its bounding box to create blocks.
        """
        if not barrier_union or barrier_union.is_empty:
            return []
        try:
            minx, miny, maxx, maxy = barrier_union.bounds
            bounding_area = box(minx, miny, maxx, maxy)
            blocks_area = bounding_area.difference(barrier_union)
            if blocks_area.is_empty:
                return []
            blocks = []
            if blocks_area.geom_type == "MultiPolygon":
                for b in blocks_area.geoms:
                    if b.area > 5:
                        simplified = b.simplify(0.1)
                        if simplified.is_valid and not simplified.is_empty:
                            blocks.append(simplified)
            else:
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
        Legacy method: find all footprints that intersect a given block.
        """
        block_buildings = []
        for fp in building_footprints:
            try:
                poly = fp['polygon']
                if block.intersects(poly):
                    intersection = block.intersection(poly)
                    if not intersection.is_empty and intersection.area > 1:
                        fp_copy = dict(fp)
                        fp_copy['polygon'] = intersection
                        block_buildings.append(fp_copy)
            except Exception:
                continue
        return block_buildings
    
    def _analyze_block(self, block_buildings):
        """
        Legacy method: analyze a block to compute average height and predominant type.
        """
        if not block_buildings:
            return {'type': 'residential', 'avg_height': 15.0}
        type_counts = {'residential': 0, 'industrial': 0, 'commercial': 0}
        total_area = 0.0
        weighted_height = 0.0
        for b in block_buildings:
            area = b['polygon'].area
            total_area += area
            weighted_height += b['height'] * area
            typ = b.get('type', 'residential')
            if typ in type_counts:
                type_counts[typ] += 1
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
        Legacy method: process footprints within a block into final building shapes.
        """
        from shapely.ops import unary_union
        if not block_buildings:
            return []
        processed = []
        block_type = block_info['type']
        type_specs = self.BLOCK_TYPES.get(block_type, self.BLOCK_TYPES['residential'])
        try:
            footprints_union = unary_union([b['polygon'] for b in block_buildings])
            if not footprints_union.is_valid:
                footprints_union = make_valid(footprints_union)
        except Exception:
            return []
        polygons = []
        if footprints_union.geom_type == "MultiPolygon":
            polygons.extend(footprints_union.geoms)
        else:
            polygons.append(footprints_union)
        for shape in polygons:
            if shape.is_empty or shape.area < 2:
                continue
            cleaned = shape.simplify(0.1)
            if not cleaned.is_valid or cleaned.is_empty:
                continue
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
            sub_polys = list(clipped.geoms) if clipped.geom_type=="MultiPolygon" else [clipped]
            for spoly in sub_polys:
                if spoly.is_empty or spoly.area < 1:
                    continue
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
        Legacy method: calculate building height based on average and type constraints.
        """
        min_h = type_specs['min_height']
        max_h = type_specs['max_height']
        base = max(avg_height, min_h)
        if base < 15.0:
            base = 15.0
        variation = random.uniform(0.85, 1.15)
        candidate = base * variation
        final_height = max(min_h, min(candidate, max_h))
        return final_height
    
    def _select_roof_style(self, block_type):
        """
        Legacy method: randomly select a roof style from the block type's list.
        """
        styles = self.BLOCK_TYPES.get(block_type, self.BLOCK_TYPES['residential'])['roof_styles']
        choice = random.choice(styles)
        if choice['name'] == 'pitched':
            choice['height_factor'] *= random.uniform(0.8, 1.2)
        elif choice['name'] == 'tiered':
            choice['levels'] = max(1, choice['levels'] + random.randint(-1, 1))
        elif choice['name'] == 'flat':
            choice['border'] *= random.uniform(0.9, 1.1)
        elif choice['name'] == 'sawtooth':
            choice['angle'] = max(10, choice['angle'] + random.randint(-5, 5))
        return choice

    def _select_random_roof(self):
        """
        New helper for area-based merging: randomly select a roof style.
        Returns a dictionary similar to legacy roof style definitions.
        """
        roof_styles = [
            {'name': 'pitched', 'height_factor': 0.3},
            {'name': 'tiered', 'levels': 2},
            {'name': 'flat', 'border': 1.0},
            {'name': 'sawtooth', 'angle': 30},
            {'name': 'modern', 'setback': 2.0},
            {'name': 'stepped', 'levels': 3}
        ]
        return random.choice(roof_styles)
