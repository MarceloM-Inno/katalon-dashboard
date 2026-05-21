from supabase import create_client
import pandas as pd

from config import SUPABASE_URL, SUPABASE_KEY, TABLE_EXECUTIONS, TABLE_CASES


_client = None


def get_client():
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def load_executions() -> pd.DataFrame:
    client = get_client()
    data = client.table(TABLE_EXECUTIONS).select("*").order("execution_date").execute()
    df = pd.DataFrame(data.data)
    if not df.empty and "execution_date" in df.columns:
        df["execution_date"] = pd.to_datetime(df["execution_date"])
    return df


def load_cases() -> pd.DataFrame:
    client = get_client()
    data = client.table(TABLE_CASES).select("*").order("test_name").execute()
    df = pd.DataFrame(data.data)
    return df
