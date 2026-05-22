from supabase import create_client
import pandas as pd

from config import SUPABASE_URL, SUPABASE_KEY, TABLE_EXECUTIONS, TABLE_CASES


_client = None


def get_client():
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def load_executions(projeto: str | None = None) -> pd.DataFrame:
    client = get_client()
    query = client.table(TABLE_EXECUTIONS).select("*").order("execution_date")
    if projeto:
        query = query.eq("project", projeto)
    data = query.execute()
    df = pd.DataFrame(data.data)
    if not df.empty and "execution_date" in df.columns:
        df["execution_date"] = pd.to_datetime(df["execution_date"])
    return df


def load_cases(projeto: str | None = None) -> pd.DataFrame:
    client = get_client()
    query = client.table(TABLE_CASES).select("*").order("test_name")
    if projeto:
        query = query.eq("project", projeto)
    data = query.execute()
    df = pd.DataFrame(data.data)
    return df
