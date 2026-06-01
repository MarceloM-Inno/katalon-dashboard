from supabase import create_client
from supabase.client import Client
import pandas as pd
from typing import Optional, Any
from datetime import datetime, date

from config import (
    SUPABASE_URL, SUPABASE_KEY, TABLE_EXECUTIONS, TABLE_CASES,
    TABLE_MANUAL_REGISTERED, TABLE_MANUAL_SNAPSHOTS,
    TABLE_MANUAL_HISTORY, TABLE_MANUAL_CASES, TABLE_MANUAL_DEFECTS
)


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
        df["execution_date"] = pd.to_datetime(df["execution_date"], format="mixed")
    return df


def load_cases(projeto: str | None = None) -> pd.DataFrame:
    client = get_client()
    query = client.table(TABLE_CASES).select("*").order("test_name")
    if projeto:
        query = query.eq("project", projeto)
    data = query.execute()
    df = pd.DataFrame(data.data)
    return df


# ========================================
# Testes Manuais
# ========================================


def load_manual_registered(
    base_project: Optional[str] = None,
    is_active: Optional[bool] = None,
    project_key: Optional[str] = None
) -> pd.DataFrame:
    client = get_client()
    query = client.table(TABLE_MANUAL_REGISTERED).select("*").order("date_start", desc=True)
    
    if base_project:
        query = query.eq("base_project", base_project)
    if project_key:
        query = query.eq("project_key", project_key)
    
    data = query.execute()
    df = pd.DataFrame(data.data)
    
    if not df.empty and is_active is not None:
        today = date.today()
        df["_date_start"] = pd.to_datetime(df["date_start"], format="mixed").dt.date
        df["_date_end"] = pd.to_datetime(df["date_end"], format="mixed").dt.date
        
        if is_active:
            df = df[(df["_date_start"] <= today) & (today <= df["_date_end"])]
        else:
            df = df[(today < df["_date_start"]) | (df["_date_end"] < today)]
        
        df = df.drop(columns=["_date_start", "_date_end"])
    
    return df


def insert_manual_registered(
    project_key: str,
    base_project: str,
    date_start: str,
    date_end: str,
    friendly_name: Optional[str] = None,
    notes: Optional[str] = None
) -> Optional[int]:
    client = get_client()
    now = datetime.utcnow().isoformat()
    
    data = {
        "project_key": project_key,
        "base_project": base_project,
        "date_start": date_start,
        "date_end": date_end,
        "created_at": now,
        "updated_at": now,
    }
    if friendly_name:
        data["friendly_name"] = friendly_name
    if notes:
        data["notes"] = notes
    
    try:
        result = client.table(TABLE_MANUAL_REGISTERED).insert([data]).execute()
        if result.data:
            return result.data[0]["id"]
    except Exception as e:
        print(f"Erro ao inserir projeto registrado: {e}")
    return None


def update_manual_registered(
    registered_id: int,
    updates: dict
) -> bool:
    client = get_client()
    updates["updated_at"] = datetime.utcnow().isoformat()
    
    try:
        result = client.table(TABLE_MANUAL_REGISTERED).update(updates).eq("id", registered_id).execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"Erro ao atualizar projeto registrado: {e}")
        return False


def delete_manual_registered(registered_id: int) -> bool:
    client = get_client()
    try:
        result = client.table(TABLE_MANUAL_REGISTERED).delete().eq("id", registered_id).execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"Erro ao excluir projeto registrado: {e}")
        return False


def load_manual_snapshots(
    base_project: Optional[str] = None,
    limit: Optional[int] = 100
) -> pd.DataFrame:
    client = get_client()
    query = client.table(TABLE_MANUAL_SNAPSHOTS).select("*").order("snapshot_date", desc=True)
    
    if base_project:
        query = query.eq("base_project", base_project)
    if limit:
        query = query.limit(limit)
    
    data = query.execute()
    df = pd.DataFrame(data.data)
    if not df.empty and "snapshot_date" in df.columns:
        df["snapshot_date"] = pd.to_datetime(df["snapshot_date"], format="mixed")
    return df


def insert_manual_snapshot(
    base_project: str,
    snapshot_date: str,
    file_name: str,
    total_rows_in_csv: int = 0,
    processed_rows: int = 0
) -> Optional[int]:
    client = get_client()
    data = {
        "base_project": base_project,
        "snapshot_date": snapshot_date,
        "file_name": file_name,
        "total_rows_in_csv": total_rows_in_csv,
        "processed_rows": processed_rows,
        "created_at": datetime.utcnow().isoformat(),
    }
    
    try:
        result = client.table(TABLE_MANUAL_SNAPSHOTS).insert([data]).execute()
        if result.data:
            return result.data[0]["id"]
    except Exception as e:
        print(f"Erro ao inserir snapshot: {e}")
    return None


def load_manual_history(
    registered_project_id: Optional[int] = None,
    project_key: Optional[str] = None,
    base_project: Optional[str] = None
) -> pd.DataFrame:
    client = get_client()
    query = client.table(TABLE_MANUAL_HISTORY).select("*").order("snapshot_date", desc=True)
    
    if registered_project_id:
        query = query.eq("registered_project_id", registered_project_id)
    if project_key:
        query = query.eq("project_key", project_key)
    if base_project:
        query = query.eq("base_project", base_project)
    
    data = query.execute()
    df = pd.DataFrame(data.data)
    if not df.empty and "snapshot_date" in df.columns:
        df["snapshot_date"] = pd.to_datetime(df["snapshot_date"], format="mixed")
    return df


def insert_manual_history_batch(history_records: list[dict]) -> bool:
    if not history_records:
        return True
    
    client = get_client()
    now = datetime.utcnow().isoformat()
    
    for rec in history_records:
        rec["created_at"] = now
    
    try:
        BATCH_SIZE = 1000
        for i in range(0, len(history_records), BATCH_SIZE):
            batch = history_records[i:i + BATCH_SIZE]
            client.table(TABLE_MANUAL_HISTORY).insert(batch).execute()
        return True
    except Exception as e:
        print(f"Erro ao inserir history batch: {e}")
        return False


def load_manual_test_cases(
    snapshot_id: Optional[int] = None,
    registered_project_id: Optional[int] = None,
    issue_key: Optional[str] = None,
    limit: Optional[int] = 5000
) -> pd.DataFrame:
    client = get_client()
    query = client.table(TABLE_MANUAL_CASES).select("*").order("snapshot_date", desc=True)
    
    if snapshot_id:
        query = query.eq("snapshot_id", snapshot_id)
    if registered_project_id:
        query = query.eq("registered_project_id", registered_project_id)
    if issue_key:
        query = query.eq("issue_key", issue_key)
    if limit:
        query = query.limit(limit)
    
    data = query.execute()
    df = pd.DataFrame(data.data)
    if not df.empty and "snapshot_date" in df.columns:
        df["snapshot_date"] = pd.to_datetime(df["snapshot_date"], format="mixed")
    return df


def insert_manual_test_cases_batch(test_cases: list[dict]) -> bool:
    if not test_cases:
        return True
    
    client = get_client()
    now = datetime.utcnow().isoformat()
    
    for tc in test_cases:
        tc["created_at"] = now
    
    try:
        BATCH_SIZE = 1000
        for i in range(0, len(test_cases), BATCH_SIZE):
            batch = test_cases[i:i + BATCH_SIZE]
            client.table(TABLE_MANUAL_CASES).insert(batch).execute()
        return True
    except Exception as e:
        print(f"Erro ao inserir test cases batch: {e}")
        return False


def update_snapshot_processed_rows(snapshot_id: int, processed_rows: int) -> bool:
    client = get_client()
    try:
        result = client.table(TABLE_MANUAL_SNAPSHOTS).update({
            "processed_rows": processed_rows
        }).eq("id", snapshot_id).execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"Erro ao atualizar snapshot: {e}")
        return False


def delete_manual_snapshot_by_keys(
    project_key: str,
    base_project: str,
    snapshot_datetime_iso: str
) -> bool:
    client = get_client()
    try:
        result = client.table(TABLE_MANUAL_SNAPSHOTS).delete() \
            .eq("project_key", project_key) \
            .eq("base_project", base_project) \
            .eq("snapshot_datetime", snapshot_datetime_iso) \
            .execute()
        return True
    except Exception as e:
        print(f"Erro ao deletar snapshot por chaves: {e}")
        return False


def delete_manual_test_cases_by_project_and_datetime(
    project_key: str,
    base_project: str,
    snapshot_datetime_iso: str
) -> bool:
    client = get_client()
    try:
        result = client.table(TABLE_MANUAL_CASES).delete() \
            .eq("project_key", project_key) \
            .eq("base_project", base_project) \
            .eq("snapshot_datetime", snapshot_datetime_iso) \
            .execute()
        return True
    except Exception as e:
        print(f"Erro ao deletar test cases por chaves: {e}")
        return False


def delete_manual_history_by_project_and_datetime(
    project_key: str,
    base_project: str,
    snapshot_datetime_iso: str
) -> bool:
    client = get_client()
    try:
        result = client.table(TABLE_MANUAL_HISTORY).delete() \
            .eq("project_key", project_key) \
            .eq("base_project", base_project) \
            .eq("snapshot_datetime", snapshot_datetime_iso) \
            .execute()
        return True
    except Exception as e:
        print(f"Erro ao deletar history por chaves: {e}")
        return False


def delete_manual_defects_by_project_and_datetime(
    project_key: str,
    base_project: str,
    snapshot_datetime_iso: str
) -> bool:
    client = get_client()
    try:
        result = client.table(TABLE_MANUAL_DEFECTS).delete() \
            .eq("project_key", project_key) \
            .eq("base_project", base_project) \
            .eq("snapshot_datetime", snapshot_datetime_iso) \
            .execute()
        return True
    except Exception as e:
        print(f"Erro ao deletar defects por chaves: {e}")
        return False


# ========================================
# Defeitos (Defects All Projects e FillAutoDefects)
# ========================================


def load_manual_defects(
    snapshot_id: Optional[int] = None,
    project_key: Optional[str] = None,
    base_project: Optional[str] = None,
    status: Optional[str] = None,
    limit: Optional[int] = 5000
) -> pd.DataFrame:
    client = get_client()
    query = client.table(TABLE_MANUAL_DEFECTS).select("*").order("snapshot_date", desc=True)
    
    if snapshot_id:
        query = query.eq("snapshot_id", snapshot_id)
    if project_key:
        query = query.eq("project_key", project_key)
    if base_project:
        query = query.eq("base_project", base_project)
    if status:
        query = query.eq("status", status)
    if limit:
        query = query.limit(limit)
    
    data = query.execute()
    df = pd.DataFrame(data.data)
    if not df.empty:
        if "snapshot_date" in df.columns:
            df["snapshot_date"] = pd.to_datetime(df["snapshot_date"], format="mixed")
        if "created_dt" in df.columns:
            df["created_dt"] = pd.to_datetime(df["created_dt"], format="mixed")
        if "updated_dt" in df.columns:
            df["updated_dt"] = pd.to_datetime(df["updated_dt"], format="mixed")
    return df


def insert_manual_defects_batch(defect_records: list[dict]) -> bool:
    if not defect_records:
        return True
    
    client = get_client()
    now = datetime.utcnow().isoformat()
    
    for rec in defect_records:
        rec["created_at"] = now
    
    try:
        BATCH_SIZE = 1000
        for i in range(0, len(defect_records), BATCH_SIZE):
            batch = defect_records[i:i + BATCH_SIZE]
            client.table(TABLE_MANUAL_DEFECTS).insert(batch).execute()
        return True
    except Exception as e:
        print(f"Erro ao inserir defects batch: {e}")
        return False
