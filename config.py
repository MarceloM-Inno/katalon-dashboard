import os
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
