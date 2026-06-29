import os
import re
import sys
import csv
from pathlib import Path
from datetime import datetime, date
from typing import Optional, Dict, List, Any, Tuple
from collections import defaultdict

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

import json
PROJECT_MAP_DEFAULT = '{"Oney Bank": "ONEY", "BNPL": "BNPL"}'
MANUAL_PROJECT_MAP = json.loads(os.getenv("MANUAL_PROJECT_MAP", PROJECT_MAP_DEFAULT))

CSV_TYPE_TEST_LIST = "TEST_LIST"
CSV_TYPE_DEFECTS = "DEFECTS"
CSV_TYPE_FILL_AUTO_DEFECTS = "FILL_AUTO_DEFECTS"

CSV_PATTERNS = {
    CSV_TYPE_TEST_LIST: r"Lista Testes All Projects \(([^)]+)\) (\d{4}-\d{2}-\d{2}T\d{2}_\d{2}_\d{2}[+-]\d{4})\.csv",
    CSV_TYPE_DEFECTS: r"Defects All Projects \(([^)]+)\) (\d{4}-\d{2}-\d{2}T\d{2}_\d{2}_\d{2}[+-]\d{4})\.csv",
    CSV_TYPE_FILL_AUTO_DEFECTS: r"FillAutoDefects \(([^)]+)\) (\d{4}-\d{2}-\d{2}T\d{2}_\d{2}_\d{2}[+-]\d{4})\.csv",
}

CSV_TYPE_NAMES = {
    CSV_TYPE_TEST_LIST: "Lista de Testes",
    CSV_TYPE_DEFECTS: "Defeitos",
    CSV_TYPE_FILL_AUTO_DEFECTS: "Defeitos de Automação",
}

STATUS_PASS = ["PASS", "PASSED"]
STATUS_FAIL = ["FAIL", "FAILED"]
STATUS_ABORTED = ["ABORTED"]
STATUS_BLOCKED = ["BLOCKED"]
STATUS_PENDING = ["PENDING", "NOT_EXECUTED", "WIP", "UNEXECUTED", "TO_DO"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def parse_timestamp_from_name(ts_str: str) -> str:
    ts_str = ts_str.replace("_", ":", 2)
    ts_str = ts_str.replace("_", "", 1)
    if "+" in ts_str:
        parts = ts_str.split("+")
        if len(parts) == 2:
            tz = parts[1]
            if len(tz) == 4:
                ts_str = f"{parts[0]}+{tz[:2]}:{tz[2:]}"
    return ts_str


def extract_date_only(iso_timestamp: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.date().isoformat()
    except Exception:
        if "T" in iso_timestamp:
            return iso_timestamp.split("T")[0]
        return iso_timestamp


def identify_csv_type(file_name: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    for csv_type, pattern in CSV_PATTERNS.items():
        match = re.match(pattern, file_name)
        if match:
            project_name = match.group(1)
            ts_str = match.group(2)
            
            base_project = MANUAL_PROJECT_MAP.get(project_name)
            if not base_project:
                for key, val in MANUAL_PROJECT_MAP.items():
                    if key.lower() in project_name.lower():
                        base_project = val
                        break
            
            if base_project:
                timestamp = parse_timestamp_from_name(ts_str)
                return csv_type, base_project, timestamp
    
    return None, None, None


def load_csv_rows(file_path: str) -> Tuple[List[Dict], int]:
    rows = []
    total_rows = 0
    
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            total_rows += 1
            if row:
                rows.append(row)
    
    return rows, total_rows


def normalize_test_status(status: str) -> str:
    if not status:
        return "UNKNOWN"
    
    status_upper = status.strip().upper()
    
    if status_upper in STATUS_PASS:
        return "PASS"
    elif status_upper in STATUS_FAIL:
        return "FAIL"
    elif status_upper in STATUS_ABORTED:
        return "ABORTED"
    elif status_upper in STATUS_BLOCKED:
        return "BLOCKED"
    elif status_upper in STATUS_PENDING:
        return "PENDING"
    
    return status_upper


def parse_pt_date(date_str: str) -> Optional[str]:
    if not date_str:
        return None
    
    formats = [
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.isoformat()
        except ValueError:
            continue
    
    return None


def fetch_active_projects(base_project: str) -> List[Dict]:
    import requests
    
    today = date.today().isoformat()
    
    url = f"{SUPABASE_URL}/rest/v1/manual_registered_projects"
    params = {
        "select": "*",
        "base_project": f"eq.{base_project}",
        "date_start": f"lte.{today}",
        "date_end": f"gte.{today}",
    }
    
    resp = requests.get(url, headers=HEADERS, params=params)
    if resp.status_code == 200:
        return resp.json()
    
    print(f"Erro ao buscar projetos ativos: {resp.status_code} - {resp.text[:200]}")
    return []


def delete_snapshot(base_project: str, snapshot_datetime: str) -> bool:
    import requests
    
    url = f"{SUPABASE_URL}/rest/v1/manual_daily_snapshots"
    params = {
        "base_project": f"eq.{base_project}",
        "snapshot_datetime": f"eq.{snapshot_datetime}",
    }
    
    resp = requests.delete(url, headers=HEADERS, params=params)
    return resp.status_code in [200, 204]


def delete_test_cases(base_project: str, snapshot_datetime: str) -> bool:
    import requests
    
    url = f"{SUPABASE_URL}/rest/v1/manual_test_cases"
    params = {
        "base_project": f"eq.{base_project}",
        "snapshot_datetime": f"eq.{snapshot_datetime}",
    }
    
    resp = requests.delete(url, headers=HEADERS, params=params)
    return resp.status_code in [200, 204]


def delete_history(base_project: str, snapshot_datetime: str) -> bool:
    import requests
    
    url = f"{SUPABASE_URL}/rest/v1/manual_project_history"
    params = {
        "base_project": f"eq.{base_project}",
        "snapshot_datetime": f"eq.{snapshot_datetime}",
    }
    
    resp = requests.delete(url, headers=HEADERS, params=params)
    return resp.status_code in [200, 204]


def delete_defects(base_project: str, snapshot_datetime: str) -> bool:
    import requests
    
    url = f"{SUPABASE_URL}/rest/v1/manual_defects"
    params = {
        "base_project": f"eq.{base_project}",
        "snapshot_datetime": f"eq.{snapshot_datetime}",
    }
    
    resp = requests.delete(url, headers=HEADERS, params=params)
    return resp.status_code in [200, 204]


def insert_snapshot(
    base_project: str, 
    snapshot_date: str, 
    snapshot_datetime: str,
    file_name: str, 
    total_rows: int
) -> Optional[int]:
    import requests
    
    url = f"{SUPABASE_URL}/rest/v1/manual_daily_snapshots"
    headers = {**HEADERS, "Prefer": "return=representation"}
    
    data = {
        "base_project": base_project,
        "snapshot_date": snapshot_date,
        "snapshot_datetime": snapshot_datetime,
        "file_name": file_name,
        "total_rows_in_csv": total_rows,
        "processed_rows": 0,
    }
    
    resp = requests.post(url, headers=headers, json=[data])
    
    if resp.status_code == 201:
        result = resp.json()
        if result:
            return result[0]["id"]
    
    print(f"  Erro ao inserir snapshot: {resp.status_code} - {resp.text[:200]}")
    return None


def batch_insert(url_path: str, records: List[Dict]) -> bool:
    if not records:
        return True
    
    import requests
    
    BATCH_SIZE = 1000
    url = f"{SUPABASE_URL}/rest/v1/{url_path}"
    headers = {**HEADERS, "Prefer": "return=minimal"}
    
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        resp = requests.post(url, headers=headers, json=batch)
        
        if resp.status_code not in [201, 204]:
            print(f"  Erro no batch insert (linha {i}): {resp.status_code} - {resp.text[:300]}")
            return False
    
    return True


def update_processed_rows(snapshot_id: int, processed_count: int) -> bool:
    if processed_count <= 0:
        return True
    
    import requests
    url = f"{SUPABASE_URL}/rest/v1/manual_daily_snapshots"
    resp = requests.patch(
        url,
        headers=HEADERS,
        params={"id": f"eq.{snapshot_id}"},
        json={"processed_rows": processed_count}
    )
    return resp.status_code in [200, 204]


def process_test_list(
    file_path: str,
    base_project: str,
    snapshot_date: str,
    snapshot_datetime: str,
    snapshot_id: int,
    csv_rows: List[Dict]
) -> int:
    print(f"  Tipo: Lista de Testes")
    
    active_projects = fetch_active_projects(base_project)
    print(f"  Projetos ativos encontrados: {len(active_projects)}")
    
    project_key_map: Dict[str, Dict] = {}
    for proj in active_projects:
        project_key_map[proj["project_key"]] = proj
    
    project_metrics: Dict[str, Dict] = defaultdict(lambda: {
        "total_tests": 0,
        "total_pass": 0,
        "total_fail": 0,
        "total_aborted": 0,
        "total_blocked": 0,
        "total_pending": 0,
        "total_other": 0,
        "priority_high_total": 0,
        "priority_high_pass": 0,
        "priority_med_total": 0,
        "priority_med_pass": 0,
        "priority_low_total": 0,
        "priority_low_pass": 0,
    })
    
    test_cases_records = []
    processed_count = 0
    
    snapshot_date_only = extract_date_only(snapshot_date)
    
    for row in csv_rows:
        project_key = row.get("Project key", "").strip()
        issue_key = row.get("Issue key", "").strip()
        
        if not issue_key:
            continue
        
        project_name = row.get("Project name", "").strip()
        status_raw = row.get("Status", "").strip()
        priority = row.get("Priority", "").strip()
        
        status = normalize_test_status(status_raw)
        
        registered_proj = project_key_map.get(project_key)
        
        issue_id_str = row.get("Issue id", "").strip()
        issue_id = int(issue_id_str) if issue_id_str and issue_id_str.isdigit() else None
        
        tc_record = {
            "snapshot_id": snapshot_id,
            "registered_project_id": registered_proj["id"] if registered_proj else None,
            "base_project": base_project,
            "project_key": project_key,
            "project_name": project_name or None,
            "issue_key": issue_key,
            "issue_id": issue_id,
            "status": status,
            "priority": priority or None,
            "snapshot_date": snapshot_date_only,
            "snapshot_datetime": snapshot_datetime,
        }
        
        if registered_proj:
            metrics = project_metrics[project_key]
            metrics["total_tests"] += 1
            
            if status == "PASS":
                metrics["total_pass"] += 1
            elif status == "FAIL":
                metrics["total_fail"] += 1
            elif status == "ABORTED":
                metrics["total_aborted"] += 1
            elif status == "BLOCKED":
                metrics["total_blocked"] += 1
            elif status == "PENDING":
                metrics["total_pending"] += 1
            else:
                metrics["total_other"] += 1
            
            priority_lower = priority.lower() if priority else ""
            
            if priority_lower == "high":
                metrics["priority_high_total"] += 1
                if status == "PASS":
                    metrics["priority_high_pass"] += 1
            elif priority_lower in ["medium", "med", "normal"]:
                metrics["priority_med_total"] += 1
                if status == "PASS":
                    metrics["priority_med_pass"] += 1
            elif priority_lower == "low":
                metrics["priority_low_total"] += 1
                if status == "PASS":
                    metrics["priority_low_pass"] += 1
        
        test_cases_records.append(tc_record)
        processed_count += 1
    
    print(f"  Linhas processadas: {processed_count}")
    print(f"  Projetos com métricas: {len(project_metrics)}")
    
    if test_cases_records:
        print(f"  Inserindo {len(test_cases_records)} test cases...")
        if not batch_insert("manual_test_cases", test_cases_records):
            print("  ERRO ao inserir test cases")
    
    history_records = []
    for project_key, metrics in project_metrics.items():
        registered_proj = project_key_map.get(project_key)
        if not registered_proj:
            continue
        
        history_rec = {
            "snapshot_id": snapshot_id,
            "registered_project_id": registered_proj["id"],
            "base_project": base_project,
            "project_key": project_key,
            "snapshot_date": snapshot_date_only,
            "snapshot_datetime": snapshot_datetime,
            "total_tests": metrics["total_tests"],
            "total_pass": metrics["total_pass"],
            "total_fail": metrics["total_fail"],
            "total_aborted": metrics["total_aborted"],
            "total_blocked": metrics["total_blocked"],
            "total_pending": metrics["total_pending"],
            "total_other": metrics["total_other"],
            "priority_high_total": metrics["priority_high_total"],
            "priority_high_pass": metrics["priority_high_pass"],
            "priority_med_total": metrics["priority_med_total"],
            "priority_med_pass": metrics["priority_med_pass"],
            "priority_low_total": metrics["priority_low_total"],
            "priority_low_pass": metrics["priority_low_pass"],
        }
        history_records.append(history_rec)
    
    if history_records:
        print(f"  Inserindo {len(history_records)} registros de history...")
        if not batch_insert("manual_project_history", history_records):
            print("  ERRO ao inserir history")
    
    return processed_count


def process_defects(
    file_path: str,
    base_project: str,
    snapshot_date: str,
    snapshot_datetime: str,
    snapshot_id: int,
    csv_rows: List[Dict],
    csv_type: str
) -> int:
    type_name = CSV_TYPE_NAMES.get(csv_type, csv_type)
    print(f"  Tipo: {type_name}")
    
    defect_records = []
    processed_count = 0
    
    snapshot_date_only = extract_date_only(snapshot_date)
    
    for row in csv_rows:
        project_key = row.get("Project key", "").strip()
        issue_key = row.get("Issue key", "").strip()
        
        if not issue_key:
            continue
        
        issue_id_str = row.get("Issue id", "").strip()
        issue_id = int(issue_id_str) if issue_id_str and issue_id_str.isdigit() else None
        
        summary = row.get("Summary", "").strip()
        status = row.get("Status", "").strip()
        priority = row.get("Priority", "").strip()
        assignee = row.get("Assignee", "").strip()
        reporter = row.get("Reporter", "").strip()
        project_name = row.get("Project name", "").strip()
        
        created_raw = row.get("Created", "").strip()
        updated_raw = row.get("Updated", "").strip()
        
        created_dt = parse_pt_date(created_raw)
        updated_dt = parse_pt_date(updated_raw)
        
        fornecedor = row.get("Fornecedor", "").strip() or row.get("Custom field (Fornecedor)", "").strip()
        impact_qa = row.get("Impacto QA", "").strip() or row.get("Custom field (Impacto QA)", "").strip()
        reopen_bug = row.get("Reopen Bug", "").strip() or row.get("Custom field (Reopen Bug)", "").strip()
        
        links_blocks = row.get("Links: blocks", "").strip() or row.get("Blocks", "").strip()
        links_relates = row.get("Links: relates", "").strip() or row.get("Relates", "").strip()
        links_problem_incident = row.get("Links: problem/incident", "").strip()
        links_tests = row.get("Links: tests", "").strip()
        
        blocks_list = [s.strip() for s in links_blocks.split(",")] if links_blocks else []
        relates_list = [s.strip() for s in links_relates.split(",")] if links_relates else []
        
        defect_record = {
            "snapshot_id": snapshot_id,
            "base_project": base_project,
            "project_key": project_key,
            "project_name": project_name or None,
            "issue_key": issue_key,
            "issue_id": issue_id,
            "summary": summary or None,
            "status": status or "UNKNOWN",
            "priority": priority or None,
            "assignee": assignee or None,
            "reporter": reporter or None,
            "created_dt": created_dt,
            "updated_dt": updated_dt,
            "custom_fornecedor": fornecedor or None,
            "custom_impact_qa": impact_qa or None,
            "custom_reopen_bug": reopen_bug or None,
            "links_blocks": blocks_list if blocks_list else None,
            "links_relates": relates_list if relates_list else None,
            "links_problem_incident": links_problem_incident if links_problem_incident else None,
            "links_tests": links_tests if links_tests else None,
            "snapshot_date": snapshot_date_only,
            "snapshot_datetime": snapshot_datetime,
        }
        
        defect_records.append(defect_record)
        processed_count += 1
    
    print(f"  Linhas processadas: {processed_count}")
    
    if defect_records:
        print(f"  Inserindo {len(defect_records)} defeitos...")
        if not batch_insert("manual_defects", defect_records):
            print("  ERRO ao inserir defeitos")
    
    return processed_count


def process_csv(file_path: str) -> bool:
    file_path = Path(file_path)
    file_name = file_path.name
    
    print(f"\nProcessando: {file_name}")
    
    csv_type, base_project, snapshot_datetime = identify_csv_type(file_name)
    
    if not csv_type or not base_project or not snapshot_datetime:
        print(f"  ERRO: Não foi possível identificar o tipo de CSV")
        print(f"  Padrões esperados:")
        print(f"    - Lista Testes All Projects (Nome Projeto) data.csv")
        print(f"    - Defects All Projects (Nome Projeto) data.csv")
        print(f"    - FillAutoDefects (Nome Projeto) data.csv")
        return False
    
    type_name = CSV_TYPE_NAMES.get(csv_type, csv_type)
    print(f"  Tipo detectado: {type_name}")
    print(f"  Base Project: {base_project}")
    print(f"  Data/Hora: {snapshot_datetime}")
    
    snapshot_date = extract_date_only(snapshot_datetime)
    print(f"  Data (apenas): {snapshot_date}")
    
    csv_rows, total_rows = load_csv_rows(str(file_path))
    print(f"  Total linhas no CSV: {total_rows}")
    
    if not csv_rows:
        print(f"  AVISO: Nenhuma linha válida no CSV")
        return False
    
    print(f"  Verificando snapshot existente para {base_project} @ {snapshot_datetime}...")
    
    print(f"  Excluindo dados antigos (se existirem)...")
    delete_test_cases(base_project, snapshot_datetime)
    delete_history(base_project, snapshot_datetime)
    delete_defects(base_project, snapshot_datetime)
    delete_snapshot(base_project, snapshot_datetime)
    
    snapshot_id = insert_snapshot(
        base_project, 
        snapshot_date, 
        snapshot_datetime,
        file_name, 
        total_rows
    )
    if not snapshot_id:
        return False
    
    print(f"  Snapshot ID: {snapshot_id}")
    
    processed_count = 0
    
    if csv_type == CSV_TYPE_TEST_LIST:
        processed_count = process_test_list(
            file_path, base_project, snapshot_date, snapshot_datetime, snapshot_id, csv_rows
        )
    else:
        processed_count = process_defects(
            file_path, base_project, snapshot_date, snapshot_datetime, snapshot_id, csv_rows, csv_type
        )
    
    if processed_count > 0:
        update_processed_rows(snapshot_id, processed_count)
    
    print(f"  CONCLUÍDO!")
    return True


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERRO: SUPABASE_URL e SUPABASE_KEY devem estar definidos")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if not os.path.exists(file_path):
            print(f"ERRO: Arquivo não encontrado: {file_path}")
            sys.exit(1)
        process_csv(file_path)
    else:
        print("Uso: python parse_manual_csv.py <caminho_do_arquivo.csv>")
        print("\nTipos de CSV suportados:")
        print("  - Lista Testes All Projects (Nome Projeto) YYYY-MM-DDTHH_MM_SS+HHMM.csv")
        print("  - Defects All Projects (Nome Projeto) YYYY-MM-DDTHH_MM_SS+HHMM.csv")
        print("  - FillAutoDefects (Nome Projeto) YYYY-MM-DDTHH_MM_SS+HHMM.csv")
        sys.exit(1)


if __name__ == "__main__":
    main()
