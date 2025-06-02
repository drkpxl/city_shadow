# GIStoLaser-fresh Deep Analysis

## 1. Leaflet Maps Integration

### Frontend Architecture (webapp/views/index.ejs & webapp/public/js/main.js)

**Map Initialization:**
- Uses Leaflet.js with multiple tile layer options (OpenStreetMap, Satellite, Topographic)
- Map initialized at coordinates [39.75, -105.01] (Denver area) with zoom level 12
- Layer control allows switching between different map styles

**Square BBOX Selection Mechanism:**
1. **First Click**: Sets anchor point with visual marker (📍 emoji icon)
2. **Mouse Movement**: Creates square selection box in real-time
3. **Mercator Projection Handling**: Uses proj4 to ensure square remains square in meters despite map projection
   - Converts lat/lng to EPSG:3857 (Web Mercator) for accurate distance calculations
   - Calculates side length as max(|dx|, |dy|) to maintain square shape
   - Converts back to EPSG:4326 for display
4. **Size Validation**: Enforces user-specific limits (default 10x10 miles)
   - Real-time size display in km and miles
   - Visual feedback when size limit is reached
5. **Second Click**: Finalizes selection
6. **Dragging**: Allows repositioning of finalized rectangle

**Key Implementation Details:**
```javascript
// Calculate square bbox maintaining aspect ratio in meters
function getLatLngBoundsFromMercatorSquare(anchor, mouse) {
    // Convert to Web Mercator for accurate distance
    let anchorMerc = proj4("EPSG:4326", "EPSG:3857", [anchor.lng, anchor.lat]);
    let mouseMerc = proj4("EPSG:4326", "EPSG:3857", [mouse.lng, mouse.lat]);
    
    // Get max dimension to ensure square
    let side = Math.max(Math.abs(dx), Math.abs(dy));
    
    // Apply size limits
    if (side > userLimits.maxSideMeters) {
        side = userLimits.maxSideMeters;
    }
}
```

**User Experience Features:**
- Real-time selection status messages
- Restart/Clear selection controls
- Copy BBOX coordinates button
- Center map by lat/lng input
- Visual feedback during all operations

## 2. Overpass API Integration

### Smart Data Source Selection (smart_osm.py & osm_data_source.py)

**Architecture:**
- Wrapper layer that intelligently chooses between local PBF files and Overpass API
- Decision based on:
  1. Geographic location (US vs international)
  2. BBOX area size (threshold: 0.05 deg² ≈ 5km²)
  3. State boundary containment
  4. PBF file availability

**Implementation Flow:**
```python
def should_use_local_pbf(bbox):
    # Check if in US
    if not is_bbox_in_us(bbox):
        return False  # Use Overpass
    
    # Check bbox size
    if bbox_area > max_bbox_area:
        return False  # Use Overpass for large areas
    
    # Check if contained in single state
    best_state = get_best_state_for_bbox(bbox)
    if best_state is None:
        return False  # Spans multiple states
    
    # Check PBF availability
    if best_state not in available_states:
        return False
    
    return True  # Use local PBF
```

**PBF Processing:**
- Uses `EfficientPBFParser` with osmium for fast extraction
- Pre-downloaded US state PBF files in cache/us_data/raw_pbf/
- Tag-based filtering matches OSMnx query format

**Overpass Fallback:**
- Uses OSMnx's `features_from_bbox()` for international queries
- Automatic retry and error handling
- Returns empty GeoDataFrame on failure

## 3. BBOX Clipping Implementation

### Cutline Polygon Creation (city_to_laser_svg.py)

**Process:**
1. **Create BBOX Polygon**: `box(west, south, east, north)` from coordinates
2. **Project to Web Mercator**: EPSG:4326 → EPSG:3857 for accurate distance calculations
3. **Apply Inset**: 20 meters inward from all edges
4. **Add Rounded Corners**: Fillet radius calculated based on DXF scale
5. **Project Back**: EPSG:3857 → EPSG:4326 for clipping operations

**Implementation:**
```python
def create_cutline_polygon(args, config_vars):
    # Create base polygon from bbox
    south, west, north, east = args.bbox
    bbox_poly = box(west, south, east, north)
    
    # Project to metric coordinate system
    projected_bbox = project_bbox_to_3857(bbox_poly)
    
    # Apply inset (20m from edges)
    cutline_poly_3857_square = create_inset_polygon(projected_bbox, 20)
    
    # Add rounded corners
    fillet_radius = config_vars['CUTLINE_FILLET_MM'] / dxf_scale
    cutline_poly_3857_filleted = add_fillet_to_polygon(cutline_poly_3857_square, fillet_radius)
    
    # Convert back for clipping
    cutline_poly_4326 = project_geometry_to_4326(cutline_poly_3857_filleted)
```

### Clipping Process

**All features are clipped using GeoPandas:**
```python
def clip_to_cutline(gdf):
    """Clip GeoDataFrame to the cutline boundary."""
    return gpd.clip(gdf, cutline_poly_4326)
```

**Applied to all feature types:**
- Buildings
- Roads
- Water polygons
- Water lines (rivers)
- Railways
- Piers
- Ski pistes (in ski mode)

**Key Points:**
- Clipping happens AFTER data fetching but BEFORE projection to Web Mercator
- Ensures NO features extend beyond the red cutline boundary
- Handles all geometry types (Polygon, LineString, MultiPolygon, MultiLineString)
- Rivers/highways that extend beyond bbox are cleanly cut at the boundary

## 4. Polygon and Line Rendering

### Geometry Processing Pipeline

**1. Filtering:**
- Buildings: Only Polygon/MultiPolygon geometries
- Roads: Only LineString/MultiLineString, excludes tunnels/alleys by default
- Water: Separated into polygons (lakes) and lines (rivers)
- Railways: Excludes tunnels

**2. Projection:**
- All geometries projected from EPSG:4326 to EPSG:3857 (Web Mercator)
- Ensures accurate distance calculations and simplification

**3. Simplification:**
- Buildings/Water polygons: Simplified with tolerance (default 1m)
- Roads/Railways/Water lines: No simplification (tolerance = 0)
- Preserves important details while reducing complexity

**4. Special Processing:**

**Water Lines → Polygons:**
```python
def convert_water_line_to_polygon(line, width, minx, miny, maxx, maxy):
    # Buffer line by half width on each side
    buffered = line.buffer(width / 2, cap_style=2, join_style=2)
    
    # Clip to extended boundary to handle edge cases
    if buffered.intersects(box(minx, miny, maxx, maxy)):
        extended_box = box(minx - width, miny - width, maxx + width, maxy + width)
        return buffered.intersection(extended_box)
```

**Hole/Island Filtering:**
- Remove holes in water bodies smaller than threshold
- Filter out ponds smaller than minimum area
- Subtract buildings and piers from water polygons

**5. Flattening (Optional):**
- Unions all features of same type into single geometry
- Improves performance for laser cutting
- Reduces file complexity

### SVG Rendering

**Coordinate Transformation:**
```python
def transform_coords_to_dxf(coords, minx, miny, maxy):
    """Flip Y-axis for SVG/DXF coordinate system."""
    return [(x, maxy - (y - miny)) for x, y in coords]
```

**Rendering Approach:**

**1. Polygons (Buildings, Water):**
- Exterior ring rendered as closed path
- Holes rendered as separate paths with white fill
- Supports both individual and flattened modes

**2. Lines (Roads, Railways):**
- Rendered as polylines with stroke width
- No fill, only stroke
- Water lines converted to polygons for consistent appearance

**3. Path Generation:**
```python
# Polygon to SVG path
def poly_to_path(poly):
    coords = transform_coords_to_dxf(poly.exterior.coords, minx, miny, maxy)
    path = "M " + " ".join(f"{x},{y}" for x, y in coords) + " Z"
    # Add holes
    for hole in poly.interiors:
        hole_coords = transform_coords_to_dxf(hole.coords, minx, miny, maxy)
        path += " M " + " ".join(f"{x},{y}" for x, y in hole_coords) + " Z"
    return path
```

**4. Layer Organization:**
- Each feature type in separate SVG group
- Consistent layer naming and styling
- Z-order: water → roads → railways → buildings

## 5. Edge Case Handling

### Features Extending Beyond BBOX

**Problem:** Rivers, highways, and other linear features often extend beyond the selected area.

**Solution:**
1. **Fetch with Buffer**: OSM queries include features that intersect the bbox
2. **Clip to Cutline**: GeoPandas clips all geometries to exact boundary
3. **Clean Cuts**: Features are cleanly cut at the boundary, not excluded

### Large Water Bodies

**Problem:** Lakes/oceans partially in bbox need proper handling.

**Solution:**
1. Water polygons clipped to exact boundary
2. Holes (islands) preserved if larger than threshold
3. Small artifacts removed by area filtering

### Road Spacing

**Problem:** Roads too close to water or each other.

**Solution:**
```python
def filter_close_roads(roads, water_lines, water_polys, min_distance):
    # Uses STRtree for efficient spatial queries
    # Preserves roads that cross/touch features
    # Only removes truly parallel close roads
```

### Coordinate System Accuracy

**Problem:** Map projections distort distances.

**Solution:**
1. All distance calculations in EPSG:3857 (meters)
2. Square selection maintained in projected coordinates
3. Final rendering uses consistent coordinate transformation

## 6. Configuration and API Structure

### Configuration System (webapp/config.yaml)

**Structure:**
```yaml
tags:
  building: ["building", true]
  road: ["highway", ["primary", "secondary", "residential", ...]]
  water_poly: ["natural", "water", "waterway", ["riverbank", "dock"]]
  
geometry:
  simplify_tolerance: 1.0
  min_building_size: 150
  min_island_size: 0
  
svg:
  width_in: 7
  height_in: 7
  scale: 1.0
  line_width_mm: 8
  
elevation:
  dem_product: "SRTM3"
  num_contour_lines: 10
```

### API Endpoints (webapp/server/index.js)

**Key Routes:**
- `POST /generate`: Main generation endpoint
- `GET /api/user`: User limits and credits
- `GET /library`: Job history
- `POST /regenerate/:jobId`: Re-run previous job
- `WebSocket /`: Real-time progress updates

**Process Flow:**
1. Validate parameters
2. Create job directory with UUID
3. Spawn Python process with timeout
4. Stream logs via WebSocket
5. Return download links on completion

## Summary

The GIStoLaser-fresh implementation provides a robust solution for:

1. **Interactive bbox selection** with proper projection handling
2. **Smart data sourcing** between local PBF and Overpass API
3. **Precise clipping** ensuring no features extend beyond boundaries
4. **Sophisticated rendering** with proper handling of all geometry types
5. **Edge case management** for real-world geographic data

The key insight is the multi-stage pipeline:
1. Select square area in Web Mercator projection
2. Fetch data with appropriate source
3. Clip all features to exact boundary with inset
4. Process geometries (simplify, filter, convert)
5. Render with proper coordinate transformation

This ensures clean, laser-cuttable output regardless of the complexity of the geographic data.