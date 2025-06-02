# TerrainForge

This is an old project where you can take BBOX data generate 3d printable cityscapes. I am picking back up that likely needs some updating. There are many UI updates I want to make but I would like you to review, audit, and update this CLAUDE.MD with possible ways to accomplish the following:

## Critical Missing Components

Based on GIStoLaser-fresh patterns:

- Nodemon for development
- Leaflet Maps to define bounds - ref /Users/stevenhubert/Code/GIStoLaser-fresh/
- Overpass API to fetch bounds - ref /Users/stevenhubert/Code/GIStoLaser-fresh/
- Config.yaml where I can set defaults, text for tooltips, etc
- Verifying proper clipping of roads, water etc that may exceed the boundries. Reference GIStoLaser-new
- Authentication system via Github auth
- Job history/management for regenerating previous models
- Parameter validation with proper error messages
- File cleanup to prevent disk space issues - Erase STL, 3MF, Openscad models every 3 days. Keep BBOX coordinations in History
- Process timeouts and graceful error handling

4. OSM Data Caching (Lower Priority #1)

GIStoLaser-fresh has an excellent caching pattern that would benefit TerrainForge3D:

- Local PBF file storage for frequently accessed regions
- Intelligent fallback between cache and API
- Reduced API calls and faster generation

5. 3MF Export Capability (Outstanding Question #1)

Yes, 3MF export with colors is possible and would be valuable:

- Python lib3mf library supports color preservation
- Better than STL for multi-material printing
- Maintains assembly information

## Priority

2. The docker setup does not work. How could we have it work on both a Linux Digital Ocean Production Server and may M series Mac? Concern mainly being with the OPENSCAD
3. Remove the idea of "Artisic Style" from the code base and instead replace with select boxes to select the type of roof styles the user wants. Add tooltip explaining the styles

### Lower Priority

1. Use local cache for OSM data, reference project here: /Users/stevenhubert/Code/GIStoLaser-fresh
2. Rename Project TerrainForge3D
3. Mimic front end styles of /Users/stevenhubert/Code/GIStoLaser-fresh/webapp should look largely identical
4. Add tooltips outlining what each feature does
