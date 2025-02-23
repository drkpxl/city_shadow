# lib/style/block_combiner.py
from math import sqrt
import random
from shapely.geometry import Polygon, MultiPolygon, LineString, box
from shapely.ops import unary_union
from shapely.validation import make_valid
from ..geometry import GeometryUtils

class BlockCombiner:
    """
    Handles the combination of building footprints based on area thresholds and proximity.
    
    This class implements two main approaches:
    1. Area-based merging for "block-combine" style
    2. Legacy block subdivision for other styles
    
    For "block-combine" style:
    - Large footprints (area >= threshold) are preserved individually
    - Small footprints are merged with nearby unblocked footprints until reaching the threshold
    - Merged clusters get unique roof styles
    """
    
    def __init__(self, style_manager):
        """
        Initialize the BlockCombiner.
        
        Args:
            style_manager: StyleManager instance for accessing global style settings
        """
        self.style_manager = style_manager
        self.geometry = GeometryUtils()
        self.debug = False
        
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
                    {'name': 'stepped', 'levels': 2}
                ]
            },
            'commercial': {
                'min_height': 20.0,
                'max_height': 40.0,
                'roof_styles': [
                    {'name': 'modern', 'setback': 2.0},
                    {'name': 'tiered', 'levels': 2},
                    {'name': 'complex', 'variations': 5}
                ]
            }
        }
    
    def _select_random_roof(self):
        """
        Select a random roof style with randomized parameters.
        
        Returns:
            dict: Roof style parameters including name and style-specific parameters
        """
        roof_styles = [
            {
                'name': 'pitched',
                'height_factor': random.uniform(0.2, 0.4)
            },
            {
                'name': 'tiered',
                'levels': random.randint(2, 4)
            },
            {
                'name': 'flat',
                'border': random.uniform(0.8, 1.2)
            },
            {
                'name': 'sawtooth',
                'angle': random.randint(25, 35)
            },
            {
                'name': 'modern',
                'setback': random.uniform(1.8, 2.2)
            },
            {
                'name': 'stepped',
                'levels': random.randint(2, 4)
            }
        ]
        return random.choice(roof_styles)

    def combine_buildings_by_block(self, features):
        """
        Main entry point for building combination.
        
        Args:
            features: Dict containing all feature types (buildings, roads, etc.)
            
        Returns:
            list: Combined building features with appropriate roof styles
        """
        if self.style_manager.style.get("artistic_style") == "block-combine":
            return self._area_based_merge(features)
        else:
            return self._legacy_combine(features)

    def _gather_all_footprints(self, features):
        """
        Collect all building/industrial footprints into a unified list.
        
        Args:
            features: Dict containing feature collections
            
        Returns:
            list: Footprint dictionaries with polygon, height, and area information
        """
        footprints = []
        
        # Process normal building features
        for bldg in features.get('buildings', []):
            coords = bldg.get('coords')
            if coords and len(coords) >= 3:
                poly = Polygon(coords)
                if poly.is_valid and not poly.is_empty:
                    footprints.append({
                        'polygon': poly,
                        'height': bldg.get('height', 10.0),
                        'area': poly.area,
                        'original': bldg
                    })
        
        # Process industrial features
        for ind in features.get('industrial', []):
            coords = ind.get('coords')
            if coords and len(coords) >= 3:
                poly = Polygon(coords)
                if poly.is_valid and not poly.is_empty:
                    footprints.append({
                        'polygon': poly,
                        'height': ind.get('height', 15.0),
                        'area': poly.area,
                        'original': ind
                    })
        
        return footprints

    def _area_based_merge(self, features):
        """
        Implement area-based merging for block-combine style.
        
        Args:
            features: Dict containing feature collections
            
        Returns:
            list: Merged building features with appropriate roof styles
        """
        AREA_THRESHOLD = 200  # in m²
        footprints = self._gather_all_footprints(features)
        barrier_union = self._create_barrier_union(features)
        
        # Separate large and small footprints
        large = [fp for fp in footprints if fp['area'] >= AREA_THRESHOLD]
        small = [fp for fp in footprints if fp['area'] < AREA_THRESHOLD]
        
        merged_clusters = []
        visited = set()
        merge_dist = self.style_manager.style.get("merge_distance", 2.0)
        
        # Process small footprints
        for i, fp in enumerate(small):
            if i in visited:
                continue
                
            cluster = [fp]
            visited.add(i)
            cluster_union = fp['polygon']
            total_area = fp['area']
            weighted_height = fp.get('height', 10.0) * fp['area']
            
            # Grow cluster while under threshold
            growing = True
            while growing and cluster_union.area < AREA_THRESHOLD:
                growing = False
                for j, candidate in enumerate(small):
                    if j in visited:
                        continue
                    if candidate['polygon'].distance(cluster_union) < merge_dist:
                        if not self._is_blocked_by_barrier(
                            cluster_union.centroid,
                            candidate['polygon'].centroid,
                            barrier_union
                        ):
                            cluster.append(candidate)
                            visited.add(j)
                            cluster_union = unary_union([cluster_union, candidate['polygon']])
                            cluster_union = make_valid(cluster_union)
                            total_area += candidate['area']
                            weighted_height += candidate.get('height', 10.0) * candidate['area']
                            growing = True
            
            # Force merge if needed
            if cluster_union.geom_type != "Polygon":
                combined = cluster_union.buffer(merge_dist * 0.5).buffer(-merge_dist * 0.5)
                if combined.geom_type != "Polygon":
                    combined = unary_union(combined.geoms)
                    if combined.geom_type != "Polygon":
                        combined = combined.convex_hull
                cluster_union = combined

            # Extract coordinates for the merged shape
            if cluster_union.geom_type == "Polygon":
                coords = list(cluster_union.exterior.coords)[:-1]
            else:
                coords = list(cluster_union.convex_hull.exterior.coords)[:-1]
            
            avg_height = weighted_height / total_area if total_area > 0 else 4.0
            
            # Assign unique roof style to merged clusters
            if len(cluster) > 1:
                roof_style = self._select_random_roof()
                merged_clusters.append({
                    'coords': coords,
                    'height': avg_height,
                    'is_cluster': True,
                    'roof_style': roof_style['name'],
                    'roof_params': roof_style
                })
            else:
                merged_clusters.append({
                    'coords': coords,
                    'height': avg_height,
                    'is_cluster': False
                })
        
        # Process large footprints (preserve individually)
        large_buildings = []
        for fp in large:
            poly = fp['polygon']
            if poly.geom_type == "MultiPolygon":
                poly = max(poly.geoms, key=lambda g: g.area)
            large_buildings.append({
                'coords': list(poly.exterior.coords)[:-1],
                'height': fp.get('height', 10.0),
                'is_cluster': False
            })
        
        if self.debug:
            print(f"Area-based merge: {len(large_buildings)} large buildings, {len(merged_clusters)} merged clusters")
            
        return large_buildings + merged_clusters

    def _legacy_combine(self, features):
        """
        Legacy block subdivision approach for non-block-combine styles.
        
        Args:
            features: Dict containing feature collections
            
        Returns:
            list: Combined building features using legacy approach
        """
        if self.debug:
            print("\n=== Legacy Block Combiner Debug ===")
        
        building_footprints = self._gather_all_footprints(features)
        barrier_union = self._create_barrier_union(features)
        blocks = self._create_blocks_from_barriers(barrier_union)
        
        if self.debug:
            print(f"Found {len(building_footprints)} building footprints")
            print(f"Generated {len(blocks)} blocks from barrier union")
        
        combined_buildings = []
        for block in blocks:
            block_buildings = self._find_buildings_in_block(block, building_footprints)
            block_info = self._analyze_block(block_buildings)
            processed_shapes = self._process_block_buildings(
                block, block_buildings, block_info, barrier_union
            )
            combined_buildings.extend(processed_shapes)
        
        return combined_buildings

    def _create_barrier_union(self, features):
        """
        Create union of barrier geometries (roads, water).
        
        Args:
            features: Dict containing feature collections
            
        Returns:
            shapely.geometry: Union of all barrier geometries
        """
        barriers = []
        
        road_width = self.style_manager.get_default_layer_specs()["roads"]["width"]
        for road in features.get('roads', []):
            try:
                line = LineString(road["coords"])
                buffered = line.buffer(road_width * 0.2)
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

    def _is_blocked_by_barrier(self, ptA, ptB, barrier_union):
        """
        Check if line between points intersects barrier.
        
        Args:
            ptA: First point (shapely.geometry.Point)
            ptB: Second point (shapely.geometry.Point)
            barrier_union: Union of all barriers
            
        Returns:
            bool: True if line intersects barrier
        """
        if barrier_union is None:
            return False
        try:
            line = LineString([ptA.coords[0], ptB.coords[0]])
            return line.intersects(barrier_union)
        except Exception:
            return False

    def _create_blocks_from_barriers(self, barrier_union):
        """
        Create blocks by subtracting barriers from bounding box.
        
        Args:
            barrier_union: Union of all barriers
            
        Returns:
            list: Block polygons
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
        Find all footprints that intersect a given block.
        
        Args:
            block: Block polygon
            building_footprints: List of building footprints
            
        Returns:
            list: Building footprints that intersect the block
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
        Analyze a block to compute average height and predominant type.
        
        Args:
            block_buildings: List of buildings in the block
            
        Returns:
            dict: Block analysis information
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
        Process buildings within a block into final building shapes.
        
        Args:
            block: Block polygon
            block_buildings: List of buildings in the block
            block_info: Block analysis information
            barrier_union: Union of all barriers
            
        Returns:
            list: Processed building shapes with appropriate styles
        """
        from shapely.ops import unary_union
        if not block_buildings:
            return []
            
        processed = []
        block_type = block_info['type']
        type_specs = self.BLOCK_TYPES.get(block_type, self.BLOCK_TYPES['residential'])
        
        try:
            # Create union of all building footprints
            footprints_union = unary_union([b['polygon'] for b in block_buildings])
            if not footprints_union.is_valid:
                footprints_union = make_valid(footprints_union)
        except Exception:
            return []
            
        # Handle different geometry types
        polygons = []
        if footprints_union.geom_type == "MultiPolygon":
            polygons.extend(footprints_union.geoms)
        else:
            polygons.append(footprints_union)
            
        # Process each polygon shape
        for shape in polygons:
            if shape.is_empty or shape.area < 2:
                continue
                
            # Clean up the geometry
            cleaned = shape.simplify(0.1)
            if not cleaned.is_valid or cleaned.is_empty:
                continue
                
            # Buffer slightly inward to create separation
            final_poly = cleaned.buffer(-0.1)
            if final_poly.is_empty:
                continue
                
            # Handle barriers if present
            if barrier_union:
                clipped = final_poly.difference(barrier_union)
                if clipped.is_empty:
                    continue
            else:
                clipped = final_poly
                
            if clipped.is_empty or clipped.area < 1:
                continue
                
            # Process resulting geometry
            sub_polys = list(clipped.geoms) if clipped.geom_type=="MultiPolygon" else [clipped]
            for spoly in sub_polys:
                if spoly.is_empty or spoly.area < 1:
                    continue
                    
                # Calculate height and select roof style
                base_height = self._calculate_building_height(block_info['avg_height'], type_specs)
                roof_style = self._select_roof_style(block_type)
                
                # Create final building dictionary
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
        Calculate building height based on average and type constraints.
        
        Args:
            avg_height: Average height of buildings in block
            type_specs: Building type specifications
            
        Returns:
            float: Calculated building height
        """
        min_h = type_specs['min_height']
        max_h = type_specs['max_height']
        
        # Ensure minimum base height
        base = max(avg_height, min_h)
        if base < 15.0:
            base = 15.0
            
        # Add random variation
        variation = random.uniform(0.85, 1.15)
        candidate = base * variation
        
        # Constrain to min/max range
        final_height = max(min_h, min(candidate, max_h))
        return final_height

    def _select_roof_style(self, block_type):
        """
        Select a roof style for a block type, with randomized parameters.
        
        Args:
            block_type: Type of building block
            
        Returns:
            dict: Selected roof style parameters
        """
        styles = self.BLOCK_TYPES.get(block_type, self.BLOCK_TYPES['residential'])['roof_styles']
        choice = random.choice(styles)
        
        # Randomize parameters based on roof type
        if choice['name'] == 'pitched':
            choice['height_factor'] *= random.uniform(0.8, 1.2)
        elif choice['name'] == 'tiered':
            choice['levels'] = max(1, choice['levels'] + random.randint(-1, 1))
        elif choice['name'] == 'flat':
            choice['border'] *= random.uniform(0.9, 1.1)
        elif choice['name'] == 'sawtooth':
            choice['angle'] = max(10, choice['angle'] + random.randint(-5, 5))
        elif choice['name'] == 'modern':
            choice['setback'] *= random.uniform(0.9, 1.1)
        elif choice['name'] == 'stepped':
            choice['levels'] = max(2, choice['levels'] + random.randint(-1, 1))
            
        return choice