# Shadow City Generator - Artist's Guide

Create beautiful, 3D-printable city maps from OpenStreetMap data. This tool generates two separate files - a main city model and a decorative frame that can be printed separately and assembled.

## Quick Start

```bash
python geojson_to_shadow_city.py input.geojson output.scad [artistic options]
```

This creates:
- `output_main.scad` - The city model
- `output_frame.scad` - A decorative frame that fits around the model

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

## Creative Styles

### Contemporary Urban Center
```bash
python geojson_to_shadow_city.py input.geojson output.scad \
  --style modern \
  --detail 0.5 \
  --merge-distance 0 \
  --min-building-area 1000 \
  --road-width 1.5
```
Creates a sleek, modern cityscape with distinct buildings and clean lines.

### Historic District
```bash
python geojson_to_shadow_city.py input.geojson output.scad \
  --style classic \
  --detail 1.5 \
  --merge-distance 3 \
  --min-building-area 400 \
  --height-variance 0.3
```
Produces an organic feel with clustered buildings and traditional architectural details.

### Abstract City Plan
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