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
                os.path.expanduser("~/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"),
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
        """
        Generate a PNG preview of the main SCAD file (output_main.scad) using a shell command.
        
        This method assumes that the conversion process produces two SCAD files:
          - output_main.scad (the main 3D model)
          - output_frame.scad (the decorative frame)
          
        It derives the main file by replacing '.scad' with '_main.scad' in the provided output_file.
        """
        # Derive the main SCAD file from the provided output file.
        main_scad_file = output_file.replace('.scad', '_main.scad')
        main_scad_file = os.path.abspath(main_scad_file)
        output_image = os.path.abspath(output_image)
        print("SCAD file path:", main_scad_file)
        print("Output image path:", output_image)

        # Set environment variable explicitly
        env = os.environ.copy()
        env["OPENSCAD_HEADLESS"] = "1"

        # Build the command (adjust the image size if needed)
        command = [
            self.openscad_path,
            '--preview=throwntogether',
            '--imgsize', f'{size[0]},{size[1]}',
            '--autocenter',
            '--colorscheme=Nature',
            '-o', output_image,
            main_scad_file
        ]

        print("Running command:", " ".join(command))
        try:
            result = subprocess.run(
                command,
                env=env,
                cwd=os.path.dirname(main_scad_file),
                capture_output=True,
                text=True,
                check=True
            )
            print("Subprocess stdout:", result.stdout)
            print("Subprocess stderr:", result.stderr)
            print(f"Preview image generated: {output_image}")
        except subprocess.CalledProcessError as e:
            print("Error generating preview:", e)
            print("Subprocess stdout:", e.stdout)
            print("Subprocess stderr:", e.stderr)

    def watch_and_reload(self, scad_file):
        """Watch the SCAD file and trigger a reload in OpenSCAD when it changes."""
        if not self.openscad_path:
            raise RuntimeError("OpenSCAD not found")

        # First, open the file in OpenSCAD.
        subprocess.Popen([self.openscad_path, scad_file])

        # Set up file watching.
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
                                    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_F5, 0)
                            win32gui.EnumWindows(callback, None)
                        elif sys.platform == "darwin":
                            subprocess.run(["osascript", "-e", 
                                'tell application "OpenSCAD" to activate\n' +
                                'tell application "System Events"\n' +
                                'keystroke "r" using {command down}\n' +
                                'end tell'])
                        else:  # Linux
                            try:
                                subprocess.run(["xdotool", "search", "--name", "OpenSCAD", 
                                              "windowactivate", "--sync", "key", "F5"])
                            except:
                                print("Warning: xdotool not found. Auto-reload may not work on Linux.")
                        self.last_reload = current_time

        # Start watching the file.
        self.running = True
        event_handler = SCDHandler(os.path.abspath(scad_file))
        self.observer = Observer()
        self.observer.schedule(event_handler, os.path.dirname(scad_file), recursive=False)
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
