"""
GeoJSON to OpenSCAD converter for Shadow City Generator.

This module handles the conversion of GeoJSON data to OpenSCAD models,
coordinating between different processing stages and managing the overall
conversion pipeline.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Union

from .feature_processor import FeatureProcessor
from .scad_generator import ScadGenerator
from .style_manager import StyleManager
from .logging_manager import LoggingManager
from .preprocessor import GeoJSONPreprocessor


class EnhancedCityConverter:
    """
    Converts GeoJSON data into OpenSCAD city models with artistic styling.

    This class coordinates the conversion process between different components:
    - Feature processing
    - Style management
    - SCAD code generation
    """

    def __init__(
        self,
        size_mm: float = 200,
        max_height_mm: float = 20,
        style_settings: Optional[Dict[str, Any]] = None,
        debug: bool = False,
    ):
        """
        Initialize the city converter with specified settings.

        Args:
            size_mm: Size of the model in millimeters
            max_height_mm: Maximum height of the model in millimeters
            style_settings: Dictionary of style parameters
            debug: Enable debug logging
        """
        self.size = size_mm
        self.max_height = max_height_mm
        self.style_manager = StyleManager(style_settings)
        self.feature_processor = FeatureProcessor(self.style_manager)
        self.scad_generator = ScadGenerator(self.style_manager)
        self.logger = LoggingManager(debug=debug, module_name="converter")

        # Initialize layer specifications
        self.layer_specs = self.style_manager.get_default_layer_specs()

    def convert(
        self, input_file: Union[str, Path], output_file: Union[str, Path]
    ) -> None:
        """
        Convert GeoJSON to separate OpenSCAD files for main model and frame.

        Args:
            input_file: Path to input GeoJSON file
            output_file: Base path for output SCAD files

        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If GeoJSON data is invalid
            IOError: If unable to write output files
        """
        input_path = Path(input_file)
        output_path = Path(output_file)

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        try:
            # Read input file
            self.logger.debug(f"Reading input file: {input_path}")
            with open(input_path) as f:
                data = json.load(f)

            # Process features
            self.logger.info("Processing features...")
            features = self.feature_processor.process_features(data, self.size)

            # Generate main model SCAD code
            self.logger.info("Generating main model OpenSCAD code...")
            main_scad = self.scad_generator.generate_openscad(
                features, self.size, self.layer_specs
            )

            # Generate frame SCAD code
            self.logger.info("Generating frame OpenSCAD code...")
            frame_scad = self._generate_frame(self.size, self.max_height)

            # Determine output filenames
            main_file = output_path.with_name(f"{output_path.stem}_main.scad")
            frame_file = output_path.with_name(f"{output_path.stem}_frame.scad")

            # Write output files
            self._write_scad_file(main_file, main_scad)
            self._write_scad_file(frame_file, frame_scad)

            self.logger.info(f"Successfully created main model: {main_file}")
            self.logger.info(f"Successfully created frame: {frame_file}")

            # Write debug log if needed
            if self.logger.debug:
                log_file = output_path.with_suffix(".log")
                self.logger.write_debug_log(log_file)
                self.logger.debug(f"Debug log written to {log_file}")

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid GeoJSON data in {input_path}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Conversion failed: {str(e)}")
            raise

    def convert_preprocessed(
        self,
        input_file: Union[str, Path],
        output_file: Union[str, Path],
        preprocessor: GeoJSONPreprocessor,
    ) -> None:
        """
        Convert GeoJSON to OpenSCAD with preprocessing step.

        Args:
            input_file: Path to input GeoJSON file
            output_file: Base path for output SCAD files
            preprocessor: Configured GeoJSONPreprocessor instance

        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If GeoJSON data is invalid
            IOError: If unable to write output files
        """
        input_path = Path(input_file)
        output_path = Path(output_file)

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        try:
            # Read input file
            self.logger.debug(f"Reading input file: {input_path}")
            with open(input_path) as f:
                data = json.load(f)

            # Preprocess the data
            self.logger.info("Preprocessing GeoJSON data...")
            processed_data = preprocessor.process_geojson(data)

            # Process features
            self.logger.info("Processing features...")
            features = self.feature_processor.process_features(
                processed_data, self.size
            )

            # Generate main model SCAD code
            self.logger.info("Generating main model OpenSCAD code...")
            main_scad = self.scad_generator.generate_openscad(
                features, self.size, self.layer_specs
            )

            # Generate frame SCAD code
            self.logger.info("Generating frame OpenSCAD code...")
            frame_scad = self._generate_frame(self.size, self.max_height)

            # Determine output filenames
            main_file = output_path.with_name(f"{output_path.stem}_main.scad")
            frame_file = output_path.with_name(f"{output_path.stem}_frame.scad")

            # Write output files
            self._write_scad_file(main_file, main_scad)
            self._write_scad_file(frame_file, frame_scad)

            self.logger.info(f"Successfully created main model: {main_file}")
            self.logger.info(f"Successfully created frame: {frame_file}")

            # Write debug log if needed
            if self.logger.debug:
                log_file = output_path.with_suffix(".log")
                self.logger.write_debug_log(log_file)
                self.logger.debug(f"Debug log written to {log_file}")

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid GeoJSON data in {input_path}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Conversion failed: {str(e)}")
            raise

    def _write_scad_file(self, filepath: Path, content: str) -> None:
        """
        Write SCAD content to file with error handling.

        Args:
            filepath: Path to write the SCAD file
            content: SCAD code content to write

        Raises:
            IOError: If unable to write the file
        """
        try:
            with open(filepath, "w") as f:
                f.write(content)
        except IOError as e:
            raise IOError(f"Failed to write SCAD file {filepath}: {str(e)}")

    def _generate_frame(self, size: float, height: float) -> str:
        """
        Generate a frame that will fit around the main model.

        The frame's inner dimensions match the main model size exactly,
        with a 5mm border around all sides.

        Args:
            size: Size of the main model in mm
            height: Height of the frame in mm

        Returns:
            OpenSCAD code for the frame
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
