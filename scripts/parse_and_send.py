import os
import sys
import json
import glob
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
REPORT_PATH = os.getenv("REPORT_PATH", r"E:\Pipeline-Report")
PROJECT_NAME = os.getenv("PROJECT_NAME", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

TABLE_EXECUTIONS = "test_executions"
TABLE_CASES = "test_cases"

STATE_FILE = Path(__file__).parent / "processed_state.json"


def parse_timestamp(ts: str) -> str:
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return ts


def load_state() -> set:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return set(json.load(f))
    return set()


def save_state(state: set):
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(state), f)


def fetch_existing() -> set:
    existing = set()
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_EXECUTIONS}"
    params = {"select": "suite_name,execution_date"}
    resp = requests.get(url, headers=HEADERS, params=params)
    if resp.status_code == 200:
        for row in resp.json():
            existing.add((row["suite_name"], row["execution_date"]))
    return existing


def parse_xml(xml_path: str) -> tuple[dict, list[dict]]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    ts_root = root.find("testsuite")
    if ts_root is None:
        ts_root = root

    suite_name = root.get("name", "")
    total_tests = int(root.get("tests", 0))
    total_failures = int(root.get("failures", 0))
    total_errors = int(root.get("errors", 0))
    total_time = float(root.get("time", 0))

    timestamp = ts_root.get("timestamp", "")
    hostname = ts_root.get("hostname", "")
    skipped = int(ts_root.get("skipped", 0))

    props = {}
    props_elem = ts_root.find("properties")
    if props_elem is not None:
        for prop in props_elem.findall("property"):
            name = prop.get("name", "")
            value = prop.get("value", "")
            props[name] = value

    execution = {
        "suite_name": suite_name,
        "execution_date": parse_timestamp(timestamp),
        "project": PROJECT_NAME,
        "total_tests": total_tests,
        "total_failures": total_failures,
        "total_errors": total_errors,
        "total_skipped": skipped,
        "total_time_sec": total_time,
        "hostname": hostname,
        "os": props.get("os", ""),
        "browser": props.get("browser", ""),
        "katalon_version": props.get("katalonVersion", ""),
        "user_full_name": props.get("userFullName", ""),
        "project_name": props.get("projectName", ""),
    }

    test_cases = []
    for tc in ts_root.findall("testcase"):
        case = {
            "test_name": tc.get("name", ""),
            "duration_sec": float(tc.get("time", 0)),
            "project": PROJECT_NAME,
            "status": tc.get("status", "UNKNOWN"),
            "failure_type": None,
            "failure_message": None,
        }
        failure = tc.find("failure")
        if failure is not None:
            case["failure_type"] = failure.get("type", "")
            msg = failure.get("message", "") or ""
            reason = ""
            if "Reason:" in msg:
                after_reason = msg.split("Reason:", 1)[1].strip()
                reason = after_reason.split("\n")[0].strip()
            case["failure_message"] = reason or msg[:300]
        test_cases.append(case)

    return execution, test_cases


def send_execution(execution: dict) -> int | None:
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_EXECUTIONS}"
    headers = {**HEADERS, "Prefer": "return=representation"}
    resp = requests.post(url, headers=headers, json=[execution])
    if resp.status_code == 201:
        data = resp.json()
        if data and isinstance(data, list):
            return data[0]["id"]
        return None
    if resp.status_code == 409:
        print(f"  Duplicado: {execution['suite_name']} @ {execution['execution_date']}")
        return None
    print(f"  ERRO {resp.status_code}: {resp.text[:200]}")
    return None


def send_cases(execution_id: int, cases: list[dict]):
    if not cases:
        return
    for case in cases:
        case["execution_id"] = execution_id
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_CASES}"
    headers = {**HEADERS, "Prefer": "return=minimal"}
    resp = requests.post(url, headers=headers, json=cases)
    if resp.status_code == 201:
        print(f"  {len(cases)} casos inseridos")
    else:
        print(f"  ERRO casos {resp.status_code}: {resp.text[:200]}")


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERRO: SUPABASE_URL e SUPABASE_KEY devem estar definidos no .env")
        sys.exit(1)

    if not PROJECT_NAME:
        print("ERRO: PROJECT_NAME deve estar definido no .env (ONEY ou BNPL)")
        sys.exit(1)

    report_path = Path(REPORT_PATH)
    if not report_path.exists():
        print(f"ERRO: Caminho não encontrado: {REPORT_PATH}")
        sys.exit(1)

    xml_files = sorted(glob.glob(str(report_path / "**" / "JUnit_Report.xml"), recursive=True))
    if not xml_files:
        print(f"Nenhum JUnit_Report.xml encontrado em {REPORT_PATH}")
        sys.exit(0)

    processed_state = load_state()
    existing_db = fetch_existing()

    print(f"Encontrados {len(xml_files)} arquivos XML")
    print(f"Já processados (local): {len(processed_state)}")
    print(f"Já existentes (DB): {len(existing_db)}")

    new_count = 0
    for xml_path in xml_files:
        rel_path = os.path.relpath(xml_path, str(report_path))

        if xml_path in processed_state:
            continue

        exec_data, cases_data = parse_xml(xml_path)
        key = (exec_data["suite_name"], exec_data["execution_date"])
        if key in existing_db:
            print(f"  Já no DB: {exec_data['suite_name']}")
            processed_state.add(xml_path)
            save_state(processed_state)
            continue

        print(f"\n[+] {rel_path}")
        print(f"    Suite: {exec_data['suite_name']}")
        print(f"    Data:  {exec_data['execution_date']}")
        print(f"    Tests: {exec_data['total_tests']} | Fail: {exec_data['total_failures']} | Err: {exec_data['total_errors']}")

        exec_id = send_execution(exec_data)
        if exec_id:
            send_cases(exec_id, cases_data)
            processed_state.add(xml_path)
            save_state(processed_state)
            new_count += 1

    print(f"\nConcluído. {new_count} novas execuções enviadas ao Supabase.")


if __name__ == "__main__":
    main()
