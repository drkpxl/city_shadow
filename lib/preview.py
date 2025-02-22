import subprocess
import os
import sys
import tempfile
import threading
import time
from PIL import Image, ImageEnhance
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class OpenSCADIntegration:
    def __init__(self, openscad_path=None):
        """Initialize OpenSCAD integration with an optional path to the OpenSCAD executable."""
        self.openscad_path = openscad_path or self._find_openscad()
        if not self.openscad_path:
            raise RuntimeError("Could not find OpenSCAD executable")

        # For file watching
        self.observer = None
        self.watch_thread = None
        self.running = False

        # Export quality settings
        self.export_quality = {
            "fn": 256,  # High-quality circles
            "fa": 2,  # Minimum angle (degrees)
            "fs": 0.2,  # Minimum size (mm)
        }

    def _find_openscad(self):
        """Find the OpenSCAD executable based on the current platform."""
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
        """Generate a high-quality PNG preview of the SCAD file."""
        # Get paths for main and frame files
        main_scad_file = output_file.replace(".scad", "_main.scad")
        frame_scad_file = output_file.replace(".scad", "_frame.scad")
        main_scad_file = os.path.abspath(main_scad_file)
        frame_scad_file = os.path.abspath(frame_scad_file)
        output_image = os.path.abspath(output_image)

        # Check if files exist
        if not os.path.exists(main_scad_file):
            raise FileNotFoundError(f"Main SCAD file not found: {main_scad_file}")
        if not os.path.exists(frame_scad_file):
            raise FileNotFoundError(f"Frame SCAD file not found: {frame_scad_file}")

        # Set environment variable explicitly
        env = os.environ.copy()
        env["OPENSCAD_HEADLESS"] = "1"

        # Generate preview for main model
        main_preview = output_image.replace(".png", "_main.png")
        command_main = [
            self.openscad_path,
            "--preview=throwntogether",
            "--imgsize",
            f"{size[0]},{size[1]}",
            "--autocenter",
            "--viewall",
            "--colorscheme=Nature",
            "--projection=perspective",
            "-o",
            main_preview,
            main_scad_file,
        ]

        # Generate preview for frame
        frame_preview = output_image.replace(".png", "_frame.png")
        command_frame = [
            self.openscad_path,
            "--preview=throwntogether",
            "--imgsize",
            f"{size[0]},{size[1]}",
            "--autocenter",
            "--viewall",
            "--colorscheme=Nature",
            "--projection=perspective",
            "-o",
            frame_preview,
            frame_scad_file,
        ]

        try:
            print("\nGenerating preview for main model...")
            result_main = subprocess.run(
                command_main,
                env=env,
                cwd=os.path.dirname(main_scad_file),
                capture_output=True,
                text=True,
                check=True,
            )

            print("Generating preview for frame...")
            result_frame = subprocess.run(
                command_frame,
                env=env,
                cwd=os.path.dirname(frame_scad_file),
                capture_output=True,
                text=True,
                check=True,
            )

            print(f"Preview images generated:")
            print(f"Main model: {main_preview}")
            print(f"Frame: {frame_preview}")
            return True

        except subprocess.CalledProcessError as e:
            print("Error generating preview:", e)
            print("OpenSCAD output:", e.stdout)
            print("OpenSCAD errors:", e.stderr)
            return False

    def generate_stl(self, scad_file, output_stl, repair=True):
        """
        Generate high-quality STL files for both main model and frame.

        Args:
            scad_file (str): Path to input SCAD file
            output_stl (str): Path for output STL file
            repair (bool): Not used, kept for backwards compatibility
        """
        try:
            # Get paths for main and frame files
            main_scad_file = scad_file.replace(".scad", "_main.scad")
            frame_scad_file = scad_file.replace(".scad", "_frame.scad")
            main_scad_file = os.path.abspath(main_scad_file)
            frame_scad_file = os.path.abspath(frame_scad_file)

            # Generate output STL paths
            main_stl = output_stl.replace(".stl", "_main.stl")
            frame_stl = output_stl.replace(".stl", "_frame.stl")
            main_stl = os.path.abspath(main_stl)
            frame_stl = os.path.abspath(frame_stl)

            # Check if input files exist
            if not os.path.exists(main_scad_file):
                raise FileNotFoundError(f"Main SCAD file not found: {main_scad_file}")
            if not os.path.exists(frame_scad_file):
                raise FileNotFoundError(f"Frame SCAD file not found: {frame_scad_file}")

            # Set environment variables for headless operation
            env = os.environ.copy()
            env["OPENSCAD_HEADLESS"] = "1"

            # Prepare high-quality export commands
            command_main = [
                self.openscad_path,
                "--backend=Manifold",
                "--export-format=binstl",
                "-o",
                main_stl,
                "-D",
                f'$fn={self.export_quality["fn"]}',
                "-D",
                f'$fa={self.export_quality["fa"]}',
                "-D",
                f'$fs={self.export_quality["fs"]}',
                main_scad_file,
            ]

            command_frame = [
                self.openscad_path,
                "--backend=Manifold",
                "--export-format=binstl",
                "-o",
                frame_stl,
                "-D",
                f'$fn={self.export_quality["fn"]}',
                "-D",
                f'$fa={self.export_quality["fa"]}',
                "-D",
                f'$fs={self.export_quality["fs"]}',
                frame_scad_file,
            ]

            print("\nGenerating high-quality STL files")
            print("Using quality settings:")
            print(f"  $fn: {self.export_quality['fn']}")
            print(f"  $fa: {self.export_quality['fa']}")
            print(f"  $fs: {self.export_quality['fs']}")

            # Generate main model STL
            print("\nGenerating main model STL...")
            result_main = subprocess.run(
                command_main,
                env=env,
                cwd=os.path.dirname(main_scad_file),
                capture_output=True,
                text=True,
                check=True,
            )

            # Generate frame STL
            print("Generating frame STL...")
            result_frame = subprocess.run(
                command_frame,
                env=env,
                cwd=os.path.dirname(frame_scad_file),
                capture_output=True,
                text=True,
                check=True,
            )

            # Verify the exports
            if not os.path.exists(main_stl):
                raise RuntimeError(f"Main STL file was not created: {main_stl}")
            if not os.path.exists(frame_stl):
                raise RuntimeError(f"Frame STL file was not created: {frame_stl}")

            main_size = os.path.getsize(main_stl)
            frame_size = os.path.getsize(frame_stl)

            print(f"\nSuccessfully generated STL files:")
            print(f"Main model: {main_stl} ({main_size/1024/1024:.1f} MB)")
            print(f"Frame: {frame_stl} ({frame_size/1024/1024:.1f} MB)")
            return True

        except subprocess.CalledProcessError as e:
            print("Error generating STL:", e)
            print("OpenSCAD output:", e.stdout if e.stdout else "No output")
            print("OpenSCAD errors:", e.stderr if e.stderr else "No errors")
            raise
        except Exception as e:
            print(f"Error generating STL: {str(e)}")
            raise

    def watch_and_reload(self, scad_file):
        """Watch the SCAD file and trigger auto-reload in OpenSCAD."""
        if not self.openscad_path:
            raise RuntimeError("OpenSCAD not found")

        # First, open the file in OpenSCAD
        subprocess.Popen([self.openscad_path, scad_file])

        class SCDHandler(FileSystemEventHandler):
            def __init__(self, scad_path):
                self.scad_path = scad_path
                self.last_reload = 0
                self.reload_cooldown = 1.0  # seconds

            def on_modified(self, event):
                if event.src_path == self.scad_path:
                    current_time = time.time()
                    if current_time - self.last_reload >= self.reload_cooldown:
                        if sys.platform == "win32":
                            import win32gui
                            import win32con

                            def callback(hwnd, _):
                                if "OpenSCAD" in win32gui.GetWindowText(hwnd):
                                    win32gui.SetForegroundWindow(hwnd)
                                    win32gui.PostMessage(
                                        hwnd, win32con.WM_KEYDOWN, win32con.VK_F5, 0
                                    )

                            win32gui.EnumWindows(callback, None)
                        elif sys.platform == "darwin":
                            subprocess.run(
                                [
                                    "osascript",
                                    "-e",
                                    'tell application "OpenSCAD" to activate\n'
                                    + 'tell application "System Events"\n'
                                    + 'keystroke "r" using {command down}\n'
                                    + "end tell",
                                ]
                            )
                        else:  # Linux
                            try:
                                subprocess.run(
                                    [
                                        "xdotool",
                                        "search",
                                        "--name",
                                        "OpenSCAD",
                                        "windowactivate",
                                        "--sync",
                                        "key",
                                        "F5",
                                    ]
                                )
                            except:
                                print(
                                    "Warning: xdotool not found. Auto-reload may not work on Linux."
                                )
                        self.last_reload = current_time

        self.running = True
        event_handler = SCDHandler(os.path.abspath(scad_file))
        self.observer = Observer()
        self.observer.schedule(
            event_handler, os.path.dirname(scad_file), recursive=False
        )
        self.observer.start()

        def watch_thread():
            while self.running:
                time.sleep(1)
            self.observer.stop()
            self.observer.join()

        self.watch_thread = threading.Thread(target=watch_thread)
        self.watch_thread.start()

    def stop_watching(self):
        """Stop watching the SCAD file."""
        if self.running:
            self.running = False
            if self.watch_thread:
                self.watch_thread.join()
                self.watch_thread = None
