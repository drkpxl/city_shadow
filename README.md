# Shadow City Generator - Artist's Guide

Create beautiful, 3D-printable city maps from OpenStreetMap data. This tool generates two separate files - a main city model and a decorative frame that can be printed separately and assembled.

## Quick Start

```bash
python geojson_to_shadow_city.py input.geojson output.scad [artistic options]
```

This creates:
- `output_main.scad` - The city model
- `output_frame.scad` - A decorative frame that fits around the model

## Preprocessing Options

The Shadow City Generator includes preprocessing capabilities to help you refine your input data before generating the 3D model. This is particularly useful when working with large OpenStreetMap exports or when you want to focus on a specific area.

### Basic Preprocessing
```bash
python geojson_to_shadow_city.py input.geojson output.scad --preprocess [options]
```

### Distance-Based Cropping
Crop features to a specific radius from the center point:
```bash
python geojson_to_shadow_city.py input.geojson output.scad \
  --preprocess \
  --crop-distance 1000  # Crop to 1000 meters from center
```

### Bounding Box Cropping
Crop features to a specific geographic area:
```bash
python geojson_to_shadow_city.py input.geojson output.scad \
  --preprocess \
  --crop-bbox 51.5074 -0.1278 51.5174 -0.1178  # south west north east
```

## Artistic Options

### Overall Style
```bash
--style [modern|classic|minimal]
```
- `modern`: Sharp, angular designs with contemporary architectural details
- `classic`: Softer edges with traditional architectural elements
- `minimal`: Clean, simplified shapes without additional ornamentation

### Size and Scale
```bash
--size 200        # Size of the model in millimeters (default: 200)
--height 20       # Maximum height of buildings in millimeters (default: 20)
```

### Detail and Complexity
```bash
--detail 1.0      # Detail level from 0-2 (default: 1.0)
```
Higher values add more intricate architectural details and smoother transitions between elements.

### Building Features

#### Shaping Your City's Style

The Shadow City Generator gives you powerful creative control over how buildings appear in your model. You can create everything from precise architectural reproductions to artistic interpretations of urban spaces.

#### Building Size Selection
```bash
--min-building-area 600
```
Think of this like adjusting the level of detail in your city:
- Low values (200-400): Include small buildings like houses and shops
- Medium values (600-800): Focus on medium-sized structures
- High values (1000+): Show only larger buildings like offices and apartments

#### Artistic Building Combinations
```bash
--merge-distance 2.0
```
This is where the real artistic magic happens. This setting determines how buildings flow together:
- `--merge-distance 0`: Each building stands alone - perfect for architectural studies or precise city representations
- `--merge-distance 1-2`: Nearby buildings gently blend together, creating small architectural groupings
- `--merge-distance 3-5`: Buildings flow into each other more dramatically, forming artistic interpretations of city blocks
- `--merge-distance 6+`: Creates bold, abstract representations where buildings merge into sculptural forms

Think of it like adjusting the "softness" of your city's appearance:
- Sharp and distinct: Use 0
- Gentle grouping: Use 1-2
- Flowing forms: Use 3-5
- Abstract sculpture: Use 6+

#### Height Artistry
```bash
--height-variance 0.2
```
This adds personality to your buildings' heights:
- `0.0`: All buildings in a group stay the same height
- `0.1-0.2`: Subtle height variations for natural feel
- `0.3-0.5`: More dramatic height differences
- `0.6+`: Bold, artistic height variations

### Road and Water Features
```bash
--road-width 2.0          # Width of roads in millimeters (default: 2.0)
--water-depth 1.4         # Depth of water features in millimeters (default: 1.4)
```

### Building Clusters
```bash
--cluster-size 3.0        # Size threshold for building clusters (default: 3.0)
```
Controls how building clusters are formed when merging nearby structures.

## Creative Examples

### Contemporary Downtown with Focused Area
```bash
python geojson_to_shadow_city.py input.geojson output.scad \
  --preprocess \
  --crop-distance 800 \
  --style modern \
  --detail 0.5 \
  --merge-distance 0 \
  --min-building-area 1000 \
  --road-width 1.5
```
Creates a sleek, modern cityscape focusing on an 800-meter radius from the center.

### Historic District Section
```bash
python geojson_to_shadow_city.py input.geojson output.scad \
  --preprocess \
  --crop-bbox 51.5074 -0.1278 51.5174 -0.1178 \
  --style classic \
  --detail 1.5 \
  --merge-distance 3 \
  --min-building-area 400 \
  --height-variance 0.3
```
Produces an organic feel with clustered buildings and traditional architectural details within a specific area.

### Minimalist Urban Plan
```bash
python geojson_to_shadow_city.py input.geojson output.scad \
  --style minimal \
  --detail 0.3 \
  --merge-distance 0 \
  --road-width 1.5 \
  --water-depth 2
```
Creates a stark, minimalist view emphasizing urban layout and form.

## Printing Guide

1. Print the main model (`output_main.scad`) and frame (`output_frame.scad`) separately
2. The frame has a 5mm border and will be slightly larger than the main model
3. Suggested print settings:
   - Layer height: 0.2mm for good detail
   - Consider different colors for frame and city
   - Frame often looks best in white or a contrasting color

## Workflow Tips

### For Large City Areas
1. Export your area from OpenStreetMap using Overpass Turbo
2. Use preprocessing to focus on your area of interest:
   ```bash
   python geojson_to_shadow_city.py input.geojson output.scad \
     --preprocess --crop-distance 1000
   ```
3. Adjust artistic settings and preview in OpenSCAD
4. Iterate until you achieve the desired look
5. Slice and print

### For Specific Districts
1. Export a larger area from OpenStreetMap
2. Use bounding box preprocessing to isolate your district:
   ```bash
   python geojson_to_shadow_city.py input.geojson output.scad \
     --preprocess --crop-bbox SOUTH WEST NORTH EAST
   ```
3. Fine-tune artistic settings
4. Preview and adjust as needed
5. Slice and print

## Artistic Adjustments

### For a Cleaner Look
- Increase `--min-building-area`
- Decrease `--detail`
- Use `--style minimal`
- Set `--merge-distance` to 0

### For a More Artistic Interpretation
- Increase `--merge-distance`
- Increase `--height-variance`
- Use `--style classic`
- Increase `--detail`

### For Emphasizing Urban Features
- Adjust `--road-width` to highlight street patterns
- Increase `--water-depth` to emphasize waterways
- Lower `--min-building-area` to include more architectural detail

### For a Simplified View
- Use `--style minimal`
- Set `--detail` to 0.3 or lower
- Increase `--min-building-area`
- Set `--merge-distance` to 0

## Preview and OpenSCAD Integration

The Shadow City Generator now includes features to streamline your workflow with OpenSCAD integration and preview generation.

### Quick Preview
Generate a PNG preview of your model without opening OpenSCAD:
```bash
python geojson_to_shadow_city.py input.geojson output.scad --preview
```

Customize preview size:
```bash
python geojson_to_shadow_city.py input.geojson output.scad --preview --preview-size 1024 768
```

### Auto-Reload Integration
Watch for changes and automatically reload in OpenSCAD:
```bash
python geojson_to_shadow_city.py input.geojson output.scad --watch
```

### Combined Workflow
Generate preview and enable auto-reload:
```bash
python geojson_to_shadow_city.py input.geojson output.scad --preview --watch
```

### Installation Requirements

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Platform-specific requirements:

#### Windows
No additional requirements (uses pywin32, installed via requirements.txt)

#### Linux
Install xdotool for auto-reload functionality:
```bash
sudo apt-get install xdotool  # Ubuntu/Debian
sudo dnf install xdotool      # Fedora
sudo pacman -S xdotool        # Arch Linux
```

#### macOS
No additional requirements (uses built-in osascript)

### Custom OpenSCAD Path
If OpenSCAD isn't found automatically, specify its path:
```bash
python geojson_to_shadow_city.py input.geojson output.scad --openscad-path "/path/to/openscad"
```

### Workflow Tips

1. **Development Workflow**
   ```bash
   python geojson_to_shadow_city.py input.geojson output.scad --watch
   ```
   - Make changes to parameters
   - See updates automatically in OpenSCAD
   - Press Ctrl+C when done

2. **Quick Iterations**
   ```bash
   python geojson_to_shadow_city.py input.geojson output.scad --preview
   ```
   - Quickly preview changes without opening OpenSCAD
   - Great for rapid parameter testing

3. **Production Workflow**
   ```bash
   python geojson_to_shadow_city.py input.geojson output.scad --preview --preview-size 1920 1080
   ```
   - Generate high-resolution previews
   - Perfect for documentation or sharing designs
```

### 5. Installation Steps

1. Install the new Python requirements:
```bash
pip install -r requirements.txt
```

2. Create the new `lib/preview.py` file with the content shown above

3. Update `geojson_to_shadow_city.py` with the new content

4. Update README.md with the new section

5. Platform-specific setup:
   - Windows: No additional steps needed
   - Linux: Install xdotool using package manager
   - macOS: No additional steps needed

The integration now provides:
- Automatic preview generation
- Auto-reload functionality
- Cross-platform support
- High-resolution preview options
- Streamlined development workflow