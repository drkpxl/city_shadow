# lib/preview/openscad_integration.py
import subprocess
import os
import sys
from .preview_generator import PreviewGenerator
from .export_manager import ExportManager
from .file_watcher import FileWatcher


class OpenSCADIntegration:
    def __init__(self, openscad_path=None):
        self.openscad_path = openscad_path or self._find_openscad()
        if not self.openscad_path:
            raise RuntimeError("Could not find OpenSCAD executable")

        self.preview_generator = PreviewGenerator(self.openscad_path)
        self.export_manager = ExportManager(self.openscad_path)
        self.file_watcher = FileWatcher()

    def _find_openscad(self):
        """Find the OpenSCAD executable."""
        if sys.platform == "win32":
            possible_paths = [
                r"C:\Program Files\OpenSCAD\openscad.exe",
                r"C:\Program Files (x86)\OpenSCAD\openscad.exe",
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
        elif sys.platform == "darwin":
            possible_paths = [
                "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD",
                os.path.expanduser(
                    "~/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
                ),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
        else:  # Linux
            try:
                return subprocess.check_output(["which", "openscad"]).decode().strip()
            except subprocess.CalledProcessError:
                pass
        return None

    def generate_preview(self, output_file, output_image, size=(1920, 1080)):
        """Generate preview using PreviewGenerator."""
        return self.preview_generator.generate(output_file, output_image, size)

    def generate_stl(self, scad_file, output_stl, repair=True):
        """Generate STL using ExportManager."""
        return self.export_manager.generate_stl(scad_file, output_stl, repair)

    def watch_and_reload(self, scad_file):
        """Watch SCAD file using FileWatcher."""
        return self.file_watcher.watch_and_reload(scad_file, self.openscad_path)

    def stop_watching(self):
        """Stop file watching."""
        self.file_watcher.stop_watching()
