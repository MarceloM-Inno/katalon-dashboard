import subprocess
import logging
from pathlib import Path

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


if __name__ == "__main__":
    if not Path(REPORT_PATH).exists():
        msg = f"Caminho nao encontrado: {REPORT_PATH}"
        logging.error(msg)
        print(msg)
        exit(1)

    logging.info("Iniciando processamento diario dos reports...")
    print("Processando reports diarios...")

    result = subprocess.run([str(VENV_PYTHON), str(PARSE_SCRIPT)], capture_output=True, text=True)

    for line in result.stdout.splitlines():
        print(line)
    if result.stderr:
        for line in result.stderr.splitlines():
            print(f"STDERR: {line}")

    if result.returncode == 0:
        logging.info("Processamento diario concluido com sucesso.")
        print("Concluido.")
    else:
        logging.error(f"Processamento falhou (codigo {result.returncode})")
        print(f"ERRO: codigo {result.returncode}")
        exit(result.returncode)
