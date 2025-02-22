import subprocess
import os
import sys
import tempfile
from PIL import Image, ImageEnhance
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class OpenSCADIntegration:
    def __init__(self, openscad_path=None):
        """Initialize OpenSCAD integration with optional path to OpenSCAD executable"""
        self.openscad_path = openscad_path or self._find_openscad()
        if not self.openscad_path:
            raise RuntimeError("Could not find OpenSCAD executable")
            
        # For file watching
        self.observer = None
        self.watch_thread = None
        self.running = False

    def _find_openscad(self):
        """Find OpenSCAD executable based on platform"""
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

    def generate_preview(self, scad_file, output_image, size=(1920, 1080)):
        """Generate a PNG preview of the SCAD file"""
        if not self.openscad_path:
            raise RuntimeError("OpenSCAD not found")

        # Create a temporary file for the preview script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as temp:
            # Read original content
            with open(scad_file, 'r') as original:
                content = original.read()
            
            # Add preview settings to the content with exact camera values
            preview_content = f"""
// Preview configuration with exact camera settings
$vpr = [55, 0, 25];    // Camera rotation
$vpt = [0, 0, 0];      // Camera translation
$vpd = 140;            // Camera distance
$vpf = 22.5;           // Field of view

{content}
"""
            temp.write(preview_content)
            temp_path = temp.name

        try:
            print("Generating preview image...")
            
            # Create process with settings
            process = subprocess.Popen([
                self.openscad_path,
                '-o', output_image,
                '--imgsize', f'{size[0]},{size[1]}',
                '--preview=throwntogether',
                '--view=axes,edges,scales',
                '--projection=perspective',
                '--camera=0,0,0,30,0,25,140',  # Exact camera settings from output
                '--colorscheme=Nature',
                temp_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            try:
                stdout, stderr = process.communicate(timeout=60)
                
                if stdout:
                    print("OpenSCAD stdout:")
                    print(stdout.decode())
                    
                if stderr:
                    print("OpenSCAD stderr:")
                    print(stderr.decode())
                
                # Check if file was created
                if not os.path.exists(output_image):
                    print("Error: Preview generation failed - no image created")
                    return
                
                # Process the image
                with Image.open(output_image) as img:
                    img = img.convert('RGBA')
                    
                    # Basic enhancements
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(1.2)
                    
                    enhancer = ImageEnhance.Sharpness(img)
                    img = enhancer.enhance(1.3)
                    
                    # Save with optimization
                    img.save(output_image, 'PNG', optimize=True, quality=95)
                    
                print(f"Preview generated: {output_image}")
                
            except subprocess.TimeoutExpired:
                print("Preview generation timed out, terminating process...")
                process.kill()
                process.communicate()
                print("Process terminated")
                
        except Exception as e:
            print(f"Error during preview generation: {e}")
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except:
                pass

    def watch_and_reload(self, scad_file):
        """Watch the SCAD file and reload it in OpenSCAD when it changes"""
        if not self.openscad_path:
            raise RuntimeError("OpenSCAD not found")

        # First, open the file in OpenSCAD
        subprocess.Popen([self.openscad_path, scad_file])

        # Set up file watching
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

        # Start watching the file
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
        """Stop watching the SCAD file"""
        if self.running:
            self.running = False
            if self.watch_thread:
                self.watch_thread.join()
                self.watch_thread = None