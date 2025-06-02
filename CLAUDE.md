# TerrainForge

This is an old project where you can take BBOX data generate 3d printable cityscapes. I am picking back up that likely needs some updating. There are many UI updates I want to make but I would like you to review, audit, and update this CLAUDE.MD with possible ways to accomplish the following:

## Priority

1. Is the way we interact between the website and the python service generating the files the best way or is there a better approach that will make this more foolproof. The intention is the webapp is the only way users interact with this app.
2. The docker setup does not work. How could we have it work on both a Linux Digital Ocean Production Server and may M series Mac? Concern mainly being with the OPENSCAD
3. Remove the idea of "Artisic Style" from the code base and instead replace with select boxes to select the type of roof styles the user wants. Add tooltip explaining the styles

### Lower Priority

1. Use local cache for OSM data, reference project here: /Users/stevenhubert/Code/GIStoLaser-fresh
2. Rename Project TerrainForge3D
3. Mimic front end styles of /Users/stevenhubert/Code/GIStoLaser-fresh/webapp should look largely identical
4. Add tooltips outlining what each feature does

### Tech Idea

1. The main build should be in python as it has the most support for the 3d work we are doing
2. I know Node and EJS pretty well, plus its also in the reference project here: /Users/stevenhubert/Code/GIStoLaser-fresh/webapp do we want to mimic
3. Open to other suggestions.

### Outstanding Questions

1. Rather than export STLs can we Export 3MFs maintaining the color information into a 3D printing slicer

# Architectural Improvements for Robustness

1. Web-Python Communication (Priority #1)

The current child process spawning is fragile. I recommend adopting GIStoLaser-fresh's
pattern:

- Job-based architecture with UUID tracking
- Structured directory organization: /temp/{username}/{jobId}/
- Real-time progress updates via Socket.io
- Comprehensive logging for debugging
- Process isolation to handle concurrent requests

2. Roof Style Selection (Priority #3)

The codebase already supports 6 roof types but they're hidden in the artistic style
system:

- Extract roof types: pitched, tiered, flat, sawtooth, modern, stepped
- Create individual dropdowns with tooltips
- Remove the abstract "artistic style" concept
- Make building generation more predictable for users

3. Critical Missing Components

Based on GIStoLaser-fresh patterns:

- Authentication system (even basic auth prevents abuse)
- Job history/management for regenerating previous models
- Parameter validation with proper error messages
- File cleanup to prevent disk space issues
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

Recommended Implementation Order

1. First: Fix the web-Python communication with job management
2. Second: Extract and expose roof styles
3. Third: Add authentication and user isolation
4. Fourth: Implement Docker properly with cross-platform OpenSCAD support
5. Fifth: UI redesign matching GIStoLaser-fresh
6. Finally: Add caching and 3MF export

The most critical improvement is replacing the fragile process spawning with a proper
job queue system. This will make the application production-ready and able to handle
multiple users reliably.
