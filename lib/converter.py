# lib/converter.py
import json
from .feature_processor.feature_processor import FeatureProcessor
from .scad_generator import ScadGenerator
from .style.style_manager import StyleManager

class EnhancedCityConverter:
    def __init__(self, size_mm=200, max_height_mm=20, style_settings=None):
        self.size = size_mm
        self.max_height = max_height_mm
        self.style_manager = StyleManager(style_settings)
        self.feature_processor = FeatureProcessor(self.style_manager)
        self.scad_generator = ScadGenerator(self.style_manager)
        self.debug = True
        self.debug_log = []
        self.layer_specs = self.style_manager.get_default_layer_specs()
        
        # Initialize bridge specs
        self.layer_specs["bridges"] = {
            "height": style_settings.get("bridge_height", 2.0),
            "thickness": style_settings.get("bridge_thickness", 1.0),
            "support_width": style_settings.get("support_width", 2.0),
        }

    def print_debug(self, *args):
        message = " ".join(str(arg) for arg in args)
        if self.debug:
            print(message)
            self.debug_log.append(message)

    def convert(self, input_file, output_file):
        """Standard conversion without preprocessing"""
        with open(input_file) as f:
            data = json.load(f)
        self._process_data(data, output_file)

    def convert_preprocessed(self, input_file, output_file, preprocessor):
        """Conversion with preprocessing"""
        with open(input_file) as f:
            data = json.load(f)
        processed_data = preprocessor.process_geojson(data)
        self._process_data(processed_data, output_file)

    def _process_data(self, data, output_file):
        """Shared processing pipeline"""
        try:
            # Process features
            self._log_processing_start()
            features = self.feature_processor.process_features(data, self.size)

            # Generate SCAD components
            main_scad, frame_scad = self._generate_scad_components(features)

            # Write outputs
            main_path, frame_path = self._write_output_files(
                output_file, main_scad, frame_scad
            )

            # Final logging
            self._log_success(main_path, frame_path)
            self._write_debug_log(output_file)

        except Exception as e:
            print(f"Error: {str(e)}")
            raise

    def _generate_scad_components(self, features):
        """Generate both main and frame SCAD code"""
        return (
            self.scad_generator.generate_openscad(features, self.size, self.layer_specs),
            self._generate_frame(self.size, self.max_height)
        )

    def _write_output_files(self, output_file, main_scad, frame_scad):
        """Handle file writing operations"""
        main_path = output_file.replace(".scad", "_main.scad")
        frame_path = output_file.replace(".scad", "_frame.scad")

        with open(main_path, "w") as f:
            f.write(main_scad)
        with open(frame_path, "w") as f:
            f.write(frame_scad)

        return main_path, frame_path

    def _log_processing_start(self):
        """Initial debug logging"""
        self.print_debug("\nProcessing features...")
        self.print_debug("\nGenerating main model OpenSCAD code...")

    def _log_success(self, main_path, frame_path):
        """Success state logging"""
        self.print_debug(f"\nSuccessfully created main model: {main_path}")
        self.print_debug(f"Successfully created frame: {frame_path}")
        self.print_debug("Style settings used:")
        for key, value in self.style_manager.style.items():
            self.print_debug(f"  {key}: {value}")

    def _write_debug_log(self, output_file):
        """Write debug log if enabled"""
        if self.debug:
            log_path = output_file + ".log"
            with open(log_path, "w") as f:
                f.write("\n".join(self.debug_log))
            self.print_debug(f"\nDebug log written to {log_path}")

    def _generate_frame(self, size, height):
        """Generate frame SCAD code (unchanged from original)"""
        frame_size = size + 10
        return f"""// Frame for city model
difference() {{
    cube([{frame_size}, {frame_size}, {height}]);
    translate([5, 5, 0])
        cube([{size}, {size}, {height}]);
}}"""