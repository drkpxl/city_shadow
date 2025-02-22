# lib/converter.py
import json
from .feature_processor import FeatureProcessor
from .scad_generator import ScadGenerator
from .style_manager import StyleManager

class EnhancedCityConverter:
    def __init__(self, size_mm=200, max_height_mm=20, style_settings=None):
        self.size = size_mm
        self.max_height = max_height_mm
        self.style_manager = StyleManager(style_settings)
        self.feature_processor = FeatureProcessor(self.style_manager)
        self.scad_generator = ScadGenerator(self.style_manager)
        self.debug = True
        self.debug_log = []
        
        # Initialize layer specifications
        self.layer_specs = self.style_manager.get_default_layer_specs()

    def print_debug(self, *args):
        """Log debug messages"""
        message = " ".join(str(arg) for arg in args)
        if self.debug:
            print(message)
            self.debug_log.append(message)

    def convert(self, input_file, output_file):
        """Convert GeoJSON to OpenSCAD file"""
        try:
            # Read input file
            with open(input_file) as f:
                data = json.load(f)
            
            # Process features
            self.print_debug("\nProcessing features...")
            features = self.feature_processor.process_features(data, self.size)
            
            # Generate main model SCAD code
            self.print_debug("\nGenerating OpenSCAD code...")
            main_scad = self.scad_generator.generate_openscad(
                features, 
                self.size, 
                self.layer_specs
            )
            
            # Generate frame SCAD code using the helper method
            frame_scad = self._generate_frame(self.size, self.max_height)
            
            # Combine main model and frame in a union block
            final_scad = f"union() {{\n{main_scad}\n{frame_scad}\n}}"
            
            # Write output
            with open(output_file, 'w') as f:
                f.write(final_scad)
            
            self.print_debug(f"\nSuccessfully created {output_file}")
            self.print_debug("Style settings used:")
            for key, value in self.style_manager.style.items():
                self.print_debug(f"  {key}: {value}")
            
            # Write debug log if needed
            if self.debug:
                log_file = output_file + '.log'
                with open(log_file, 'w') as f:
                    f.write('\n'.join(self.debug_log))
                self.print_debug(f"\nDebug log written to {log_file}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            raise

    def _generate_frame(self, size, height):
        """
        Generate a frame around the entire [0,0] to [size,size] area.
        The data is already inset 5mm on each side, so the 'inner' region is [5,5] → [size-5,size-5].
        We make a difference of two cubes to produce a 5mm frame.
        """
        return f"""
    // Frame around the model
    difference() {{
        // Outer block: [0,0,0] to [size, size, height]
        cube([{size}, {size}, {height}]);
        // Subtract the inner region: shift by [5,5], then [size-10, size-10] wide
        translate([5, 5, 0])
            cube([{size-10}, {size-10}, {height}]);
    }}
    """

