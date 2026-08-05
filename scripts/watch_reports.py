import os
import time
import logging
import threading
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
VENV_PYTHON = PROJECT_DIR / ".venv" / "Scripts" / "python.exe"
PARSE_SCRIPT = SCRIPT_DIR / "parse_and_send.py"
LOG = SCRIPT_DIR / "watcher.log"

env_path = PROJECT_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)

REPORT_PATH = Path(os.getenv("REPORT_PATH", r"E:\Pipeline-Report"))
DEBOUNCE_SEC = 20
STABILIZE_SEC = 5

logging.basicConfig(
    filename=LOG, level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)


class ReportHandler(FileSystemEventHandler):
    def __init__(self):
        self.debounce_map = {}
        self.lock = threading.Lock()
        self.running = False

    def on_created(self, event):
        self._handle(event)

    def on_modified(self, event):
        self._handle(event)

    def _handle(self, event):
        if event.is_directory:
            return
        if not Path(event.src_path).name == "JUnit_Report.xml":
            return

        now = time.time()
        last = self.debounce_map.get(event.src_path, 0)
        if now - last < DEBOUNCE_SEC:
            return
        self.debounce_map[event.src_path] = now

        logging.info(f"Novo report detetado: {event.src_path}")
        self.trigger()

    def trigger(self):
        with self.lock:
            if self.running:
                logging.info("Parse ja em execucao, ignorando novo disparo.")
                return
            self.running = True
        try:
            time.sleep(STABILIZE_SEC)
            self._run_parser()
        finally:
            with self.lock:
                self.running = False

    def _run_parser(self):
        logging.info("Rodando parse_and_send.py...")
        result = subprocess.run(
            [str(VENV_PYTHON), str(PARSE_SCRIPT)],
            capture_output=True, text=True,
        )
        for line in result.stdout.splitlines():
            logging.info(f"  {line}")
            print(line)
        if result.stderr:
            for line in result.stderr.splitlines():
                logging.error(f"  STDERR: {line}")
                print(f"STDERR: {line}")
        if result.returncode == 0:
            logging.info("Parse concluido com sucesso.")
        else:
            logging.error(f"Parse falhou (codigo {result.returncode})")


def main():
    logging.info("=" * 60)
    logging.info("WATCHER DE REPORTS KATALON INICIADO")
    logging.info(f"Monitorando: {REPORT_PATH}")
    logging.info("=" * 60)

    if not REPORT_PATH.exists():
        logging.error(f"ERRO: Caminho nao encontrado: {REPORT_PATH}")
        print(f"ERRO: Caminho nao encontrado: {REPORT_PATH}")
        exit(1)

    handler = ReportHandler()

    logging.info("Scan inicial (processa reports ainda nao enviados)...")
    handler.trigger()

    observer = Observer()
    observer.schedule(handler, str(REPORT_PATH), recursive=True)
    observer.start()

    print(f"\nMonitorando: {REPORT_PATH}")
    print("Pressione Ctrl+C para parar.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Interrompido pelo usuario")
        observer.stop()

    observer.join()
    logging.info("Watcher finalizado.")


if __name__ == "__main__":
    main()
