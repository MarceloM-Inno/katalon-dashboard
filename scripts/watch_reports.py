import time
import subprocess
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
VENV_PYTHON = PROJECT_DIR / ".venv" / "Scripts" / "python.exe"
PARSE_SCRIPT = SCRIPT_DIR / "parse_and_send.py"
REPORT_PATH = r"E:\Pipeline-Report"
LOG = SCRIPT_DIR / "watcher.log"

logging.basicConfig(
    filename=LOG, level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

last_run = 0
DEBOUNCE = 30


class ReportHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith("JUnit_Report.xml"):
            self.trigger()

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith("JUnit_Report.xml"):
            self.trigger()

    def trigger(self):
        global last_run
        now = time.time()
        if now - last_run < DEBOUNCE:
            return
        last_run = now
        time.sleep(5)
        logging.info("Rodando parse_and_send.py...")
        subprocess.run([str(VENV_PYTHON), str(PARSE_SCRIPT)])
        logging.info("Concluído.")


if __name__ == "__main__":
    if not Path(REPORT_PATH).exists():
        logging.error(f"Caminho não encontrado: {REPORT_PATH}")
        exit(1)

    observer = Observer()
    handler = ReportHandler()
    observer.schedule(handler, REPORT_PATH, recursive=True)
    observer.start()
    logging.info(f"Monitorando {REPORT_PATH}...")
    print(f"Monitorando {REPORT_PATH}...")
    print("Pressione Ctrl+C para parar.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
