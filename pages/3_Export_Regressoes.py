import os
import re
import streamlit as st
import pandas as pd
from datetime import date, timedelta

try:
    for key, env_key in [("supabase_url", "SUPABASE_URL"), ("supabase_key", "SUPABASE_KEY")]:
        if key in st.secrets and st.secrets[key]:
            os.environ[env_key] = st.secrets[key]
except Exception:
    pass

from config import SUPABASE_URL, SUPABASE_KEY, normalize_suite_name, build_suite_display_map
from db import (
    load_executions,
    load_cases_by_exec_ids,
    load_status_overrides,
    apply_overrides_to_cases,
)

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Configure SUPABASE_URL e SUPABASE_KEY nos secrets.")
    st.stop()


projeto = st.session_state.get("projeto", "")
if not projeto:
    st.switch_page("pages/2_Inicio.py")


@st.cache_data(ttl=60, show_spinner="Carregando execuções...")
def get_exec_data(projeto):
    return load_executions(projeto)


def extract_identifier(test_name: str) -> str:
    """Extrai o identificador do teste (tudo antes do primeiro _ no segmento final)."""
    parts = test_name.replace("\\", "/").split("/")
    last_segment = parts[-1] if parts else test_name
    match = re.match(r'^([A-Za-z0-9]+)', last_segment)
    return match.group(1) if match else last_segment


st.markdown(
    "<h1 style='text-align: center; margin-bottom: 0.5rem;'>"
    " Export Regressões Automáticas</h1>",
    unsafe_allow_html=True,
)
st.caption(
    "Selecione as suites e a data para exportar o resultado dos testes em CSV."
)
st.divider()

exec_df = get_exec_data(projeto)

if not exec_df.empty:
    exec_df["suite_name_normalized"] = exec_df["suite_name"].apply(normalize_suite_name)

if exec_df.empty:
    st.warning("Nenhum dado encontrado para o projeto selecionado.")
    st.stop()


min_date = exec_df["execution_date"].min().date()
max_date = exec_df["execution_date"].max().date()

col_date, col_suites = st.columns([1, 2])
with col_date:
    export_date = st.date_input(
        "Data",
        value=max_date,
        min_value=min_date,
        max_value=max_date,
    )
with col_suites:
    st.markdown("**Suites**")
    selected_suites = []
    suite_display_map = build_suite_display_map(exec_df["suite_name"].unique().tolist())
    cols_suites = st.columns(min(len(suite_display_map), 3))
    for i, norm_name in enumerate(suite_display_map):
        display_name = suite_display_map[norm_name]
        with cols_suites[i % len(cols_suites)]:
            if st.checkbox(display_name, value=False, key=f"export_suite_{norm_name}"):
                selected_suites.append(norm_name)

exec_filtered = exec_df.copy()
exec_filtered = exec_filtered[
    exec_filtered["execution_date"].dt.date == export_date
]

if selected_suites:
    exec_filtered = exec_filtered[exec_filtered["suite_name_normalized"].isin(selected_suites)]

exec_ids = exec_filtered["id"].tolist()
cases_df = pd.DataFrame()
if exec_ids:
    cases_df = load_cases_by_exec_ids(exec_ids)
    overrides_df = load_status_overrides()
    if not overrides_df.empty:
        cases_df = apply_overrides_to_cases(cases_df, overrides_df)

if exec_filtered.empty:
    st.info("Nenhuma execução encontrada para a data e suites selecionadas.")
    st.stop()

csv_content = ""
file_name = f"DadosRegressãoAutomática-{export_date.strftime('%d/%m')}.csv"
if not cases_df.empty:
    export_df = cases_df.copy()
    export_df["identifier"] = export_df["test_name"].apply(extract_identifier)

    def _sort_key(val):
        m = re.match(r'^([A-Za-z]+)(\d*)', str(val))
        if m:
            return (m.group(1), int(m.group(2)) if m.group(2) else 0)
        return (val, 0)

    export_df = export_df.sort_values("identifier", key=lambda s: s.map(_sort_key))
    csv_lines = ["Identifier,Status"]
    for _, row in export_df.iterrows():
        csv_status = "OK" if row["status"] == "PASSED" else "ERROR"
        csv_lines.append(f"{row['identifier']},{csv_status}")
    csv_content = "\n".join(csv_lines)

if csv_content:
    st.download_button(
        label="📥 Exportar CSV",
        data=csv_content,
        file_name=file_name,
        mime="text/csv",
        type="primary",
        use_container_width=True,
    )

st.divider()

st.subheader(" Resultados")
st.caption(
    f"Data: **{export_date.strftime('%d/%m/%Y')}** | "
    f"Suites: **{len(selected_suites)}** | "
    f"Testes: **{len(cases_df)}**"
)

if not cases_df.empty:
    exec_map = exec_filtered[["id", "suite_name"]].set_index("id")
    cases_display = cases_df.copy()
    cases_display["suite"] = cases_display["execution_id"].map(exec_map["suite_name"])
    cases_display["identifier"] = cases_display["test_name"].apply(extract_identifier)

    st.dataframe(
        cases_display[["identifier", "status", "suite", "test_name"]].rename(
            columns={
                "identifier": "Identificador",
                "status": "Status",
                "suite": "Suite",
                "test_name": "Nome do Teste",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


st.divider()
st.caption(
    "Desenvolvido com Streamlit  |  Dados: Supabase  |  Módulo: Export Regressões"
)
