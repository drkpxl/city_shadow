# Shadow City Generator

Create beautiful, 3D-printable city maps from OpenStreetMap data. This tool generates geometric interpretations of urban landscapes, complete with buildings, roads, and water features. The output includes a main city model and a decorative frame that can be printed separately and assembled.

## Quick Start

```bash
python geojson_to_shadow_city.py input.geojson output.scad [options]
```

This creates:
- `output_main.scad` - The city model
- `output_frame.scad` - A decorative frame that fits around the model

### Basic Export Example

```bash
# Generate both preview and STL files with modern style
python geojson_to_shadow_city.py map.geojson output.scad \
    --export both \
    --style modern \
    --size 200 \
    --water-depth 3 \
    --road-width 1
```

## Export Options

### Preview Generation
```bash
# Generate preview images
python geojson_to_shadow_city.py map.geojson output.scad \
    --export preview \
    --preview-size 1920 1080
```

### STL Export
```bash
# Generate high-quality STL files
python geojson_to_shadow_city.py map.geojson output.scad \
    --export stl \
    --style classic
```

Creates:
- `output_main.stl` - Main city model
- `output_frame.stl` - Decorative frame

The STL files are generated using OpenSCAD's Manifold backend for optimal quality and performance.

## Preprocessing Options

The Shadow City Generator includes preprocessing capabilities to help you refine your input data before generating the 3D model.

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

#### Building Size Selection
```bash
--min-building-area 600
```
Controls which buildings are included:
- Low values (200-400): Include small buildings like houses and shops
- Medium values (600-800): Focus on medium-sized structures
- High values (1000+): Show only larger buildings like offices and apartments

#### Artistic Building Combinations
```bash
--merge-distance 2.0
```
Controls how buildings are combined:
- `0`: Each building stands alone
- `1-2`: Nearby buildings gently blend together
- `3-5`: Buildings flow into each other more dramatically
- `6+`: Creates bold, abstract representations

#### Height Artistry
```bash
--height-variance 0.2
```
Controls building height variations:
- `0.0`: Uniform heights within groups
- `0.1-0.2`: Subtle height variations
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

## Creative Examples

### Contemporary Downtown
```bash
python geojson_to_shadow_city.py input.geojson output.scad \
    --preprocess \
    --crop-distance 800 \
    --style modern \
    --detail 0.5 \
    --merge-distance 0 \
    --min-building-area 1000 \
    --road-width 1.5 \
    --export both
```

### Historic District
```bash
python geojson_to_shadow_city.py input.geojson output.scad \
    --style classic \
    --detail 1.5 \
    --merge-distance 3 \
    --min-building-area 400 \
    --height-variance 0.3 \
    --export stl
```

### Minimalist Urban Plan
```bash
python geojson_to_shadow_city.py input.geojson output.scad \
    --style minimal \
    --detail 0.3 \
    --merge-distance 0 \
    --road-width 1.5 \
    --water-depth 2 \
    --export both
```

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install OpenSCAD:
   - Windows: Download from openscad.org
   - macOS: `brew install openscad`
   - Linux: `sudo apt install openscad` or equivalent

## 3D Printing Guide

### Print Settings
1. **Layer Height**: 
   - 0.2mm for good detail
   - 0.12mm for extra detail in complex areas

2. **Infill**:
   - Main model: 10-15%
   - Frame: 20% for stability

3. **Support Settings**:
   - Main model: Support on build plate only
   - Frame: Usually no supports needed

4. **Material Choice**:
   - PLA works well for both parts
   - Consider using contrasting colors for main model and frame

### Assembly Tips
1. Print the main model (`*_main.stl`) and frame (`*_frame.stl`) separately
2. The frame has a 5mm border and will be slightly larger than the main model
3. Clean any support material carefully, especially from the frame
4. The main model should fit snugly inside the frame

## Troubleshooting

### Common Issues

1. **Long Processing Times**:
   - Reduce `--detail` level
   - Increase `--min-building-area`
   - Use `--crop-distance` to limit area

2. **Memory Issues**:
   - Use `--preprocess` with smaller areas
   - Increase `--min-building-area`
   - Reduce `--detail` level

3. **Preview/STL Generation**:
   - Ensure OpenSCAD is properly installed
   - Try using `--export preview` first to check the model
   - Check available disk space

### Getting Help

If you encounter issues:
1. Enable debug output with `--debug`
2. Check the generated log file (`*.log`)
3. Verify OpenSCAD installation
4. Ensure all dependencies are installed

## Contributing

Contributions are welcome! Please feel free to submit pull requests or create issues for bugs and feature requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.