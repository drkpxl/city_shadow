# lib/preview/preview_generator.py
import os
import subprocess


class PreviewGenerator:
    def __init__(self, openscad_path):
        self.openscad_path = openscad_path

    def generate(self, output_file, output_image, size=(1080, 1080)):
        """Generate preview images for both main model and frame."""
        main_scad_file = output_file.replace(".scad", "_main.scad")
        frame_scad_file = output_file.replace(".scad", "_frame.scad")

        if not all(os.path.exists(f) for f in [main_scad_file, frame_scad_file]):
            raise FileNotFoundError("Required SCAD files not found")

        env = os.environ.copy()
        env["OPENSCAD_HEADLESS"] = "1"

        # Generate previews for main and frame
        return self._generate_model_preview(
            main_scad_file, frame_scad_file, output_image, size, env
        )

    def _generate_model_preview(self, main_file, frame_file, output_image, size, env):
        """Generate preview for a specific model file."""
        try:
            # Generate main preview
            main_preview = output_image.replace(".png", "_main.png")
            self._run_preview_command(main_file, main_preview, size, env)

            # Generate frame preview
            frame_preview = output_image.replace(".png", "_frame.png")
            self._run_preview_command(
                frame_file, frame_preview, size, env, is_frame=True
            )

            return True
        except subprocess.CalledProcessError as e:
            print("Error generating preview:", e)
            print("OpenSCAD output:", e.stdout)
            print("OpenSCAD errors:", e.stderr)
            return False

    def _run_preview_command(self, input_file, output_file, size, env, is_frame=False):
        """Run OpenSCAD command to generate preview."""
        command = [
            self.openscad_path,
            "--backend=Manifold",
            "--render",
            "--imgsize",
            f"{size[0]},{size[1]}",
            "--autocenter",
            "--colorscheme=DeepOcean",
        ]

        if is_frame:
            command.extend(["--viewall", "--projection=perspective"])

        command.extend(["-o", output_file, input_file])

        subprocess.run(command, env=env, capture_output=True, text=True, check=True)
