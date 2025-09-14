import sys
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from subprocess import Popen

class ReloadHandler(FileSystemEventHandler):
    def __init__(self, app_process):
        self.app_process = app_process

    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            print(f"🔄 Python file changed: {event.src_path}, restarting app...")
            self.app_process.terminate()
            time.sleep(1)
            self.app_process = Popen([sys.executable, "main.py"])
        elif event.src_path.endswith(".qss"):
            print(f"🎨 QSS file changed: {event.src_path}, reloading stylesheet...")
            os.system("python -c 'from main import window; window.reload_qss()'")

if __name__ == "__main__":
    process = Popen([sys.executable, "main.py"])
    observer = Observer()
    event_handler = ReloadHandler(process)
    observer.schedule(event_handler, ".", recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        process.terminate()

    observer.join()
