import os
import re
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    env_path_scripts = Path(__file__).parent / "scripts" / ".env"
    if env_path_scripts.exists():
        load_dotenv(env_path_scripts)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

TABLE_EXECUTIONS = "test_executions"
TABLE_CASES = "test_cases"

TABLE_MANUAL_REGISTERED = "manual_registered_projects"
TABLE_MANUAL_SNAPSHOTS = "manual_daily_snapshots"
TABLE_MANUAL_HISTORY = "manual_project_history"
TABLE_MANUAL_CASES = "manual_test_cases"
TABLE_MANUAL_DEFECTS = "manual_defects"
TABLE_OVERRIDES = "test_status_overrides"


def normalize_suite_name(name: str) -> str:
    """Remove prefixos numéricos e sufixo (Monday) dos nomes de suite."""
    name = re.sub(r'^\d+\.?\s*', '', name).strip()
    name = re.sub(r'\s*\(Monday\)\s*$', '', name).strip()
    return name


def build_suite_display_map(suite_names: list[str]) -> dict[str, str]:
    """Agrupa suites normalizadas e devolve o display name (com prefixo numérico) para cada grupo.
    Ordena por prefixo numérico; nomes sem prefixo ficam no final."""
    groups: dict[str, list[str]] = {}
    for name in suite_names:
        norm = normalize_suite_name(name)
        groups.setdefault(norm, []).append(name)

    def _sort_key(item: tuple[str, list[str]]) -> tuple[int, str, str]:
        norm, originals = item
        display = sorted(originals)[0]
        match = re.match(r'^(\d+)', display)
        if match:
            return (0, f"{int(match.group(1)):010d}", norm)
        return (1, "", norm)

    sorted_groups = sorted(groups.items(), key=_sort_key)
    return {norm: sorted(originals)[0] for norm, originals in sorted_groups}

import json
PROJECT_MAP_DEFAULT = '{"Oney Bank": "ONEY", "BNPL": "BNPL"}'
MANUAL_PROJECT_MAP = json.loads(os.getenv("MANUAL_PROJECT_MAP", PROJECT_MAP_DEFAULT))

MANUAL_REPORT_PATH = os.getenv("MANUAL_REPORT_PATH", r"C:\Users\mmmorais\Downloads")

CSV_TYPE_TEST_LIST = "TEST_LIST"
CSV_TYPE_DEFECTS = "DEFECTS"
CSV_TYPE_FILL_AUTO_DEFECTS = "FILL_AUTO_DEFECTS"

CSV_PATTERNS = {
    CSV_TYPE_TEST_LIST: r"Lista Testes All Projects \(([^)]+)\) (\d{4}-\d{2}-\d{2}T\d{2}_\d{2}_\d{2}[+-]\d{4})\.csv",
    CSV_TYPE_DEFECTS: r"Defects All Projects \(([^)]+)\) (\d{4}-\d{2}-\d{2}T\d{2}_\d{2}_\d{2}[+-]\d{4})\.csv",
    CSV_TYPE_FILL_AUTO_DEFECTS: r"FillAutoDefects \(([^)]+)\) (\d{4}-\d{2}-\d{2}T\d{2}_\d{2}_\d{2}[+-]\d{4})\.csv",
}
