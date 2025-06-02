# TerrainForge3D

This is an old project where you can take BBOX data generate 3d printable cityscapes. I am picking back up that likely needs some updating. There are many UI updates I want to make but I would like you to review, audit, and update this CLAUDE.MD with possible ways to accomplish the following:

## Critical Missing Components

Based on GIStoLaser-fresh patterns analysis: From GIStoLaser-fresh located here: /Users/stevenhubert/Code/GIStoLaser-fresh

### 1. Leaflet Maps Integration

From GIStoLaser-fresh located here: /Users/stevenhubert/Code/GIStoLaser-fresh

- Uses Leaflet.js with OpenStreetMap tiles in `webapp/views/index.ejs`
- Includes square bbox selection tool with visual feedback
- Real-time selection status and controls
- Supports multiple tile layers (OSM, Satellite, Topographic)
- Uses proj4 for coordinate transformations
- Max area validation (10x10 miles default, configurable)

**Implementation approach:**

- Add Leaflet.js to package.json dependencies
- Create map container in views/index.ejs
- Port the square selection logic from `webapp/public/js/main.js`
- Add bbox validation and coordinate display

### 2. Overpass API Integration

From GIStoLaser-fresh located here: /Users/stevenhubert/Code/GIStoLaser-fresh

- Uses `osmnx` Python library for Overpass queries
- Smart data source selection (local PBF vs Overpass)
- Configurable Overpass endpoint in `config.yaml`
- Tag-based feature fetching (buildings, roads, water, etc.)

**Implementation approach:**

- Add `osmnx` to requirements.txt
- Configure Overpass endpoint in new config.yaml
- Use `smart_features_from_bbox()` pattern for data fetching
- Implement fallback mechanism for API failures

### 3. Boundary Clipping

From GIStoLaser-fresh located here: /Users/stevenhubert/Code/GIStoLaser-fresh

- Uses `gpd.clip()` to ensure features don't exceed bbox
- Creates cutline polygon from bbox coordinates
- Clips all feature types (buildings, roads, water, etc.)

**Implementation approach:**

- Add clipping logic in feature processors
- Use GeoPandas clip function before processing
- Ensure all geometry types are properly clipped

### 4. Configuration System

From GIStoLaser-fresh `webapp/config.yaml`:

- Hierarchical YAML configuration
- Separate sections for tags, geometry, SVG, elevation
- Tooltip text and UI strings
- Default values for all parameters

**Implementation approach:**

- Create config.yaml with similar structure
- Add yaml loading in server.js
- Pass config to frontend for tooltips
- Use for default parameter values

### 5. GitHub Authentication

From GIStoLaser-fresh located here: /Users/stevenhubert/Code/GIStoLaser-fresh

- Login, marketing, FAQ, legal pages
- Uses passport.js with passport-github2 strategy
- Session management with Redis store
- User data stored in JSON files
- Credit system for usage tracking

**Implementation approach:**

- Add passport dependencies to package.json
- Configure GitHub OAuth app
- Implement session management
- Create user data directory structure

### 6. Job History/Management

From GIStoLaser-fresh located here: /Users/stevenhubert/Code/GIStoLaser-fresh

- Stores job parameters in `params.json` per job
- UUID-based job folders
- Library endpoint for listing previous jobs
- Regeneration without credit consumption

**Implementation approach:**

- Create job management system in jobManager.js
- Store bbox, parameters, and timestamps
- Add library view for job history
- Implement regeneration endpoint

### 7. Parameter Validation

From GIStoLaser-fresh located here: /Users/stevenhubert/Code/GIStoLaser-fresh

- Comprehensive parameter configuration with min/max values
- Type checking (number, integer, boolean)
- Descriptive error messages
- Frontend and backend validation

**Implementation approach:**

- Create parameter schema with validation rules
- Add validation middleware
- Return specific error messages
- Add frontend validation before submission

### 8. File Cleanup

From GIStoLaser-fresh located here: /Users/stevenhubert/Code/GIStoLaser-fresh

- Periodic cleanup of temp files
- Preserves params.json for history
- Age-based deletion (configurable)

**Implementation approach:**

- Add cleanup scheduler in server.js
- Configure retention periods
- Keep only essential metadata
- Log cleanup operations

### 9. Process Timeouts

From GIStoLaser-fresh:

- Configurable timeout for Python processes
- Graceful handling of timeouts
- Error logging and user feedback

**Implementation approach:**

- Add timeout to child process spawn
- Implement proper error handling
- Send timeout status via socket.io
- Show user-friendly error messages

## Priority Tasks

### 1. Docker Setup Fix

**Problem:** OpenSCAD compatibility across platforms

**Solution approach:**

- Use multi-stage Dockerfile with platform-specific builds
- For M-series Macs: Use `--platform linux/amd64` flag
- Consider using pre-compiled OpenSCAD binaries
- Alternative: Use OpenSCAD headless version
- Test with docker-compose for both platforms

### Lower Priority

### 1. OSM Data Caching

From GIStoLaser-fresh located here: /Users/stevenhubert/Code/GIStoLaser-fresh

- Uses local PBF files for US states
- Smart selection between local and API
- Efficient PBF parser with osmium
- Automatic fallback for large areas

**Implementation approach:**

- Port `osm_data_source.py` logic
- Add PBF download capability
- Implement area-based selection
- Cache frequently accessed regions

### 2. Project Rename

- Update all references from city_shadow to TerrainForge3D
- Update package.json, Docker files, README
- Update UI branding

### 3. Frontend Styling

From GIStoLaser-fresh located here: /Users/stevenhubert/Code/GIStoLaser-fresh

- Bootstrap-based responsive design
- Card-based layout for controls
- Real-time console output
- Progress indicators

**Implementation approach:**

- Port CSS styles from GIStoLaser-fresh
- Update layout structure to match
- Add missing UI components
- Ensure mobile responsiveness

### 4. Tooltips

From GIStoLaser-fresh:

- Bootstrap tooltips with info icons
- Contextual help text from config
- Parameter explanations

**Implementation approach:**

- Add Bootstrap tooltip initialization
- Create tooltip text in config.yaml
- Add info icons to all controls
- Include parameter ranges and effects
