# lib/preview/export_manager.py
import os
import subprocess


class ExportManager:
    def __init__(self, openscad_path):
        self.openscad_path = openscad_path
        self.export_quality = {
            "fn": 256,
            "fa": 2,
            "fs": 0.2,
        }

    def generate_stl(self, scad_file, output_stl, repair=True):
        """Generate STL files for both main model and frame."""
        try:
            main_scad_file = scad_file.replace(".scad", "_main.scad")
            frame_scad_file = scad_file.replace(".scad", "_frame.scad")

            if not all(os.path.exists(f) for f in [main_scad_file, frame_scad_file]):
                raise FileNotFoundError("Required SCAD files not found")

            main_stl = output_stl.replace(".stl", "_main.stl")
            frame_stl = output_stl.replace(".stl", "_frame.stl")

            env = os.environ.copy()
            env["OPENSCAD_HEADLESS"] = "1"

            # Generate main model STL
            self._generate_single_stl(main_scad_file, main_stl, env)

            # Generate frame STL
            self._generate_single_stl(frame_scad_file, frame_stl, env)

            return True

        except Exception as e:
            print(f"Error generating STL: {str(e)}")
            raise

    def _generate_single_stl(self, input_file, output_file, env):
        """Generate STL for a single model."""
        command = [
            self.openscad_path,
            "--backend=Manifold",
            "--render",
            "--export-format=binstl",
            "-o",
            output_file,
        ]

        # Add quality settings
        for param, value in self.export_quality.items():
            command.extend(["-D", f"${param}={value}"])

        command.append(input_file)

        subprocess.run(command, env=env, capture_output=True, text=True, check=True)
