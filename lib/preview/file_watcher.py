# lib/preview/file_watcher.py
import os
import sys
import time
import threading
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileWatcher:
    def __init__(self):
        self.observer = None
        self.watch_thread = None
        self.running = False

    def watch_and_reload(self, scad_file, openscad_path):
        """Watch SCAD file and trigger auto-reload in OpenSCAD."""
        subprocess.Popen([openscad_path, scad_file])

        class SCDHandler(FileSystemEventHandler):
            def __init__(self, scad_path):
                self.scad_path = scad_path
                self.last_reload = 0
                self.reload_cooldown = 1.0

            def on_modified(self, event):
                if event.src_path == self.scad_path:
                    current_time = time.time()
                    if current_time - self.last_reload >= self.reload_cooldown:
                        self._reload_openscad()
                        self.last_reload = current_time

            def _reload_openscad(self):
                if sys.platform == "win32":
                    self._reload_windows()
                elif sys.platform == "darwin":
                    self._reload_macos()
                else:
                    self._reload_linux()

            def _reload_windows(self):
                import win32gui
                import win32con

                def callback(hwnd, _):
                    if "OpenSCAD" in win32gui.GetWindowText(hwnd):
                        win32gui.SetForegroundWindow(hwnd)
                        win32gui.PostMessage(
                            hwnd, win32con.WM_KEYDOWN, win32con.VK_F5, 0
                        )

                win32gui.EnumWindows(callback, None)

            def _reload_macos(self):
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

            def _reload_linux(self):
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
