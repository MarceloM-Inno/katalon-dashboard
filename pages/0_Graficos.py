import os
import streamlit as st
import pandas as pd

st_secrets_valid = True
try:
    for key, env_key in [("supabase_url", "SUPABASE_URL"), ("supabase_key", "SUPABASE_KEY")]:
        if key in st.secrets and st.secrets[key]:
            os.environ[env_key] = st.secrets[key]
except Exception:
    st_secrets_valid = False

from config import SUPABASE_URL, SUPABASE_KEY
from db import (
    load_executions,
    load_cases_by_exec_ids,
    load_status_overrides,
    apply_overrides_to_cases,
)
from visualizations import (
    render_kpi_cards,
    render_trend_chart,
    render_failure_trend,
    render_suite_distribution,
    render_status_pie,
    render_detail_table,
)
from datetime import datetime, timedelta

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error(
        "Configure as variáveis SUPABASE_URL e SUPABASE_KEY "
        "no arquivo .env ou nos secrets do Streamlit."
    )
    st.stop()


projeto = st.session_state.get("projeto", "")
if not projeto:
    st.switch_page("pages/2_Inicio.py")


@st.cache_data(ttl=60, show_spinner="Carregando execuções...")
def get_exec_data(projeto):
    return load_executions(projeto)


st.title(f" Dashboard de Testes - {projeto}")
st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

exec_df = get_exec_data(projeto)
overrides_df = load_status_overrides()

st.sidebar.header("Filtros")

if not exec_df.empty:
    min_date = exec_df["execution_date"].min().date()
    max_date = exec_df["execution_date"].max().date()
else:
    min_date = datetime.today().date() - timedelta(days=30)
    max_date = datetime.today().date()

hoje = datetime.today().date()
segunda = hoje - timedelta(days=hoje.weekday())
padrao_inicio = max(segunda, min_date)
padrao_fim = min(hoje, max_date)
padrao_inicio = min(padrao_inicio, padrao_fim)
padrao = (padrao_inicio, padrao_fim)

date_range = st.sidebar.date_input(
    "Período",
    value=padrao,
    min_value=min_date,
    max_value=max_date,
)

st.sidebar.markdown("**Suites**")
selected_suites = []
if not exec_df.empty:
    for suite in sorted(exec_df["suite_name"].unique()):
        if st.sidebar.checkbox(suite, value=True):
            selected_suites.append(suite)

st.sidebar.markdown("**Status**")
selected_statuses = []
for status in ["PASSED", "FAILED", "ERROR", "SKIPPED"]:
    if st.sidebar.checkbox(status, value=True):
        selected_statuses.append(status)

if st.sidebar.button(" Atualizar Agora"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.caption(
    f"Total de execuções: {len(exec_df)}"
)

if exec_df.empty:
    st.warning(
        "Nenhum dado encontrado. Execute o script parse_and_send.py "
        "para enviar os resultados dos testes ao banco de dados."
    )
    st.stop()

exec_filtered = exec_df.copy()
if len(date_range) == 2:
    start_d, end_d = date_range
    exec_filtered = exec_filtered[
        (exec_filtered["execution_date"].dt.date >= start_d)
        & (exec_filtered["execution_date"].dt.date <= end_d)
    ]
if selected_suites:
    exec_filtered = exec_filtered[exec_filtered["suite_name"].isin(selected_suites)]

exec_ids = exec_filtered["id"].tolist()
cases_filtered = pd.DataFrame()
cases_all = pd.DataFrame()
if exec_ids:
    cases_filtered = load_cases_by_exec_ids(exec_ids)
    if not overrides_df.empty:
        cases_filtered = apply_overrides_to_cases(cases_filtered, overrides_df)

cases_all = cases_filtered.copy() if not cases_filtered.empty else pd.DataFrame()

if selected_statuses and not cases_filtered.empty:
    cases_filtered = cases_filtered[
        cases_filtered["status"].isin(selected_statuses)
    ]

render_kpi_cards(exec_filtered, cases_all)

col1, col2 = st.columns(2)
with col1:
    render_trend_chart(exec_filtered, cases_all)
with col2:
    render_failure_trend(exec_filtered, cases_all)

col3, col4 = st.columns(2)
with col3:
    render_suite_distribution(cases_all, exec_filtered)
with col4:
    render_status_pie(cases_filtered)

st.subheader(" Detalhamento dos Testes")
cases_merged = cases_filtered.merge(
    exec_filtered[["id", "suite_name", "execution_date"]],
    left_on="execution_id",
    right_on="id",
    how="left",
)
if not exec_filtered.empty and not overrides_df.empty:
    exec_ids_set = set(exec_filtered["id"].tolist())
    overrides_df = overrides_df[overrides_df["execution_id"].isin(exec_ids_set)].copy()
if not overrides_df.empty:
    cases_merged = cases_merged.merge(
        overrides_df[["test_case_id", "overridden_status", "reason"]],
        left_on="id_x",
        right_on="test_case_id",
        how="left",
    )
    cases_merged["has_override"] = cases_merged["overridden_status"].notna()
    cases_merged["_override"] = cases_merged["has_override"].apply(
        lambda x: " ✅" if x else ""
    )
else:
    cases_merged["_override"] = ""
render_detail_table(cases_merged)

st.caption(
    "Desenvolvido com Streamlit  |  Dados: Supabase  |  Fonte: Katalon JUnit XML"
)
