import time
import json
import shutil
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Set, Optional

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
STATE_FILE = SCRIPT_DIR / "manual_processed_state.json"
LOG_FILE = SCRIPT_DIR / "watcher_manual.log"

from dotenv import load_dotenv
env_path = PROJECT_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)

import os
import sys
sys.path.insert(0, str(PROJECT_DIR))

MANUAL_REPORT_PATH = os.getenv("MANUAL_REPORT_PATH", r"C:\Users\mmmorais\Downloads")
MANUAL_REPORT_PATH = Path(MANUAL_REPORT_PATH)

PROCESSED_DIR = MANUAL_REPORT_PATH / "_processed"
ERROR_DIR = MANUAL_REPORT_PATH / "_error"
UNMATCHED_DIR = MANUAL_REPORT_PATH / "_unmatched"

for d in [PROCESSED_DIR, ERROR_DIR, UNMATCHED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE, level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)


def load_state() -> Set[str]:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()


def save_state(state: Set[str]):
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(state), f)


def move_file(src_path: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    dest_path = dest_dir / src_path.name
    counter = 1
    while dest_path.exists():
        dest_path = dest_dir / f"{src_path.stem}_{counter}{src_path.suffix}"
        counter += 1
    
    shutil.move(str(src_path), str(dest_path))
    return dest_path


def process_file(file_path: Path) -> Optional[bool]:
    from parse_manual_csv import process_csv as parse_csv
    
    file_name = file_path.name
    logging.info(f"Processando: {file_name}")
    
    try:
        success = parse_csv(str(file_path))
        
        if success:
            logging.info(f"  Sucesso! Movendo para _processed/")
            move_file(file_path, PROCESSED_DIR)
            return True
        else:
            logging.warning(f"  Parser rejeitou o arquivo. Movendo para _unmatched/")
            move_file(file_path, UNMATCHED_DIR)
            return False
            
    except Exception as e:
        logging.error(f"  Erro durante processamento: {e}")
        move_file(file_path, ERROR_DIR)
        return False


class ManualReportHandler(FileSystemEventHandler):
    def __init__(self, processed_state: Set[str]):
        self.processed_state = processed_state
        self.debounce_map = {}
        self.DEBOUNCE_SEC = 10
    
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".csv"):
            self.trigger(event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".csv"):
            self.trigger(event.src_path)
    
    def trigger(self, src_path: str):
        src_path = Path(src_path)
        file_name = src_path.name
        
        if str(src_path) in self.processed_state:
            return
        
        if file_name.startswith("_"):
            return
        
        now = time.time()
        last = self.debounce_map.get(str(src_path), 0)
        if now - last < self.DEBOUNCE_SEC:
            return
        self.debounce_map[str(src_path)] = now
        
        time.sleep(5)
        
        if not src_path.exists():
            return
        
        success = process_file(src_path)
        
        self.processed_state.add(str(src_path))
        save_state(self.processed_state)


def scan_existing_files(handler: ManualReportHandler, processed_state: Set[str]):
    logging.info("Verificando arquivos CSV existentes...")
    
    csv_files = list(MANUAL_REPORT_PATH.glob("*.csv"))
    
    for csv_file in csv_files:
        if csv_file.name.startswith("_"):
            continue
        if str(csv_file) in processed_state:
            continue
        
        logging.info(f"Encontrado: {csv_file.name}")
        handler.trigger(str(csv_file))


def main():
    logging.info("=" * 60)
    logging.info("WATCHER DE TESTES MANUAIS INICIADO")
    logging.info(f"Monitorando: {MANUAL_REPORT_PATH}")
    logging.info("Tipos suportados: Lista Testes, Defects, FillAutoDefects")
    logging.info("=" * 60)
    
    if not MANUAL_REPORT_PATH.exists():
        logging.error(f"ERRO: Caminho não encontrado: {MANUAL_REPORT_PATH}")
        logging.error(f"Crie a pasta ou configure MANUAL_REPORT_PATH no .env")
        exit(1)
    
    processed_state = load_state()
    logging.info(f"Arquivos já processados (estado): {len(processed_state)}")
    
    handler = ManualReportHandler(processed_state)
    
    scan_existing_files(handler, processed_state)
    
    observer = Observer()
    observer.schedule(handler, str(MANUAL_REPORT_PATH), recursive=False)
    observer.start()
    
    print(f"\nMonitorando: {MANUAL_REPORT_PATH}")
    print("Pressione Ctrl+C para parar.\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Interrompido pelo usuário")
        observer.stop()
    
    observer.join()
    logging.info("Watcher finalizado.")


if __name__ == "__main__":
    main()
