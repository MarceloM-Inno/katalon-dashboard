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
