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
        """Convert GeoJSON to separate OpenSCAD files for main model and frame"""
        try:
            # Read input file
            with open(input_file) as f:
                data = json.load(f)
            
            # Process features
            self.print_debug("\nProcessing features...")
            features = self.feature_processor.process_features(data, self.size)
            
            # Generate main model SCAD code
            self.print_debug("\nGenerating main model OpenSCAD code...")
            main_scad = self.scad_generator.generate_openscad(
                features, 
                self.size, 
                self.layer_specs
            )
            
            # Generate frame SCAD code
            self.print_debug("\nGenerating frame OpenSCAD code...")
            frame_scad = self._generate_frame(self.size, self.max_height)
            
            # Determine output filenames
            main_file = output_file.replace('.scad', '_main.scad')
            frame_file = output_file.replace('.scad', '_frame.scad')
            
            # Write main model
            with open(main_file, 'w') as f:
                f.write(main_scad)
            
            # Write frame
            with open(frame_file, 'w') as f:
                f.write(frame_scad)
            
            self.print_debug(f"\nSuccessfully created main model: {main_file}")
            self.print_debug(f"Successfully created frame: {frame_file}")
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

    def convert_preprocessed(self, input_file, output_file, preprocessor):
        """Convert GeoJSON to OpenSCAD with preprocessing"""
        try:
            # Read input file
            with open(input_file) as f:
                data = json.load(f)
            
            # Preprocess the data
            self.print_debug("\nPreprocessing GeoJSON data...")
            processed_data = preprocessor.process_geojson(data)
            
            # Process features
            self.print_debug("\nProcessing features...")
            features = self.feature_processor.process_features(processed_data, self.size)
            
            # Generate main model SCAD code
            self.print_debug("\nGenerating main model OpenSCAD code...")
            main_scad = self.scad_generator.generate_openscad(
                features, 
                self.size, 
                self.layer_specs
            )
            
            # Generate frame SCAD code
            self.print_debug("\nGenerating frame OpenSCAD code...")
            frame_scad = self._generate_frame(self.size, self.max_height)
            
            # Determine output filenames
            main_file = output_file.replace('.scad', '_main.scad')
            frame_file = output_file.replace('.scad', '_frame.scad')
            
            # Write main model
            with open(main_file, 'w') as f:
                f.write(main_scad)
            
            # Write frame
            with open(frame_file, 'w') as f:
                f.write(frame_scad)
            
            self.print_debug(f"\nSuccessfully created main model: {main_file}")
            self.print_debug(f"Successfully created frame: {frame_file}")
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
        Generate a frame that will fit around the main model.
        The frame's inner dimensions match the main model size exactly,
        with a 5mm border around all sides.
        """
        frame_size = size + 10  # Add 10mm to total size (5mm on each side)
        return f"""// Frame for city model
// Outer size: {frame_size}mm x {frame_size}mm x {height}mm
// Inner size: {size}mm x {size}mm x {height}mm
// Frame width: 5mm

difference() {{
    // Outer block (10mm larger than main model)
    cube([{frame_size}, {frame_size}, {height}]);
    
    // Inner cutout (sized to match main model exactly)
    translate([5, 5, 0])
        cube([{size}, {size}, {height}]);
}}"""