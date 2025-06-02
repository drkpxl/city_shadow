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
