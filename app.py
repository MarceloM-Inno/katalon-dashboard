import os

os.environ.setdefault("SUPABASE_URL", "")
os.environ.setdefault("SUPABASE_KEY", "")

import streamlit as st

st_secrets_valid = True
try:
    for key, env_key in [("supabase_url", "SUPABASE_URL"), ("supabase_key", "SUPABASE_KEY")]:
        if key in st.secrets and st.secrets[key]:
            os.environ[env_key] = st.secrets[key]
except Exception:
    st_secrets_valid = False

from config import SUPABASE_URL, SUPABASE_KEY
from db import load_executions, load_cases
from visualizations import (
    render_kpi_cards,
    render_trend_chart,
    render_failure_trend,
    render_suite_distribution,
    render_status_pie,
    render_detail_table,
)
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Dashboard de Testes - Katalon",
    page_icon="",
    layout="wide",
)

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error(
        "Configure as variáveis SUPABASE_URL e SUPABASE_KEY "
        "no arquivo .env ou nos secrets do Streamlit."
    )
    st.stop()


@st.cache_data(ttl=60, show_spinner="Carregando dados...")
def get_data():
    exec_df = load_executions()
    cases_df = load_cases()
    return exec_df, cases_df


st.title(" Dashboard de Testes - Katalon")
st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

exec_df, cases_df = get_data()

st.sidebar.header("Filtros")

if not exec_df.empty:
    min_date = exec_df["execution_date"].min().date()
    max_date = exec_df["execution_date"].max().date()
else:
    min_date = datetime.today().date() - timedelta(days=30)
    max_date = datetime.today().date()

date_range = st.sidebar.date_input(
    "Período",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

suites = sorted(exec_df["suite_name"].unique()) if not exec_df.empty else []
selected_suites = st.sidebar.multiselect(
    "Suites",
    options=suites,
    default=suites,
)

statuses = ["PASSED", "FAILED", "ERROR", "SKIPPED"]
selected_statuses = st.sidebar.multiselect(
    "Status",
    options=statuses,
    default=statuses,
)

if st.sidebar.button(" Atualizar Agora"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.caption(
    f"Total de execuções: {len(exec_df)}\n"
    f"Total de casos: {len(cases_df)}"
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

cases_filtered = cases_df[
    cases_df["execution_id"].isin(exec_filtered["id"])
]
if selected_statuses:
    cases_filtered = cases_filtered[
        cases_filtered["status"].isin(selected_statuses)
    ]

render_kpi_cards(exec_filtered, cases_filtered)

col1, col2 = st.columns(2)
with col1:
    render_trend_chart(exec_filtered)
with col2:
    render_failure_trend(exec_filtered)

col3, col4 = st.columns(2)
with col3:
    render_suite_distribution(exec_filtered)
with col4:
    render_status_pie(cases_filtered)

st.subheader(" Detalhamento dos Testes")
cases_merged = cases_filtered.merge(
    exec_filtered[["id", "suite_name", "execution_date"]],
    left_on="execution_id",
    right_on="id",
    how="left",
)
render_detail_table(cases_merged)

st.caption(
    "Desenvolvido com Streamlit  |  Dados: Supabase  |  Fonte: Katalon JUnit XML"
)
