import os
import streamlit as st

try:
    for key, env_key in [("supabase_url", "SUPABASE_URL"), ("supabase_key", "SUPABASE_KEY")]:
        if key in st.secrets and st.secrets[key]:
            os.environ[env_key] = st.secrets[key]
except Exception:
    pass

from config import SUPABASE_URL, SUPABASE_KEY
from db import load_executions, load_cases
import plotly.graph_objects as go

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Configure SUPABASE_URL e SUPABASE_KEY nos secrets.")
    st.stop()


projeto = st.session_state.get("projeto", "")
if not projeto:
    st.switch_page("pages/2_Inicio.py")


@st.cache_data(ttl=60, show_spinner="Carregando dados...")
def get_data(projeto):
    return load_executions(projeto), load_cases(projeto)


exec_df, cases_df = get_data(projeto)

st.title(f" Execuções Diárias - {projeto}")

if exec_df.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

st.sidebar.header("Filtros")

min_date = exec_df["execution_date"].min().date()
max_date = exec_df["execution_date"].max().date()

date_range = st.sidebar.date_input(
    "Período",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

suites = sorted(exec_df["suite_name"].unique())
st.sidebar.markdown("**Suites**")
selected_suites = []
for suite in suites:
    if st.sidebar.checkbox(suite, value=True):
        selected_suites.append(suite)

st.sidebar.divider()
st.sidebar.markdown("**Status**")
selected_statuses = []
for status in ["PASSED", "FAILED", "ERROR", "SKIPPED"]:
    if st.sidebar.checkbox(status, value=True):
        selected_statuses.append(status)

st.sidebar.divider()
if st.sidebar.button(" Atualizar Agora"):
    st.cache_data.clear()
    st.rerun()

exec_filtered = exec_df.copy()
if len(date_range) == 2:
    start_d, end_d = date_range
    exec_filtered = exec_filtered[
        (exec_filtered["execution_date"].dt.date >= start_d)
        & (exec_filtered["execution_date"].dt.date <= end_d)
    ]
if selected_suites:
    exec_filtered = exec_filtered[exec_filtered["suite_name"].isin(selected_suites)]

for suite in selected_suites:
    suite_df = (
        exec_filtered[exec_filtered["suite_name"] == suite]
        .copy()
        .sort_values("execution_date")
    )
    if suite_df.empty:
        continue

    suite_df["date"] = suite_df["execution_date"].dt.date
    suite_df["pass_count"] = (
        suite_df["total_tests"] - suite_df["total_failures"] - suite_df["total_errors"]
    )

    daily = (
        suite_df.groupby("date")
        .agg(
            pass_count=("pass_count", "sum"),
            fail_count=("total_failures", "sum"),
            error_count=("total_errors", "sum"),
            total=("total_tests", "sum"),
        )
        .reset_index()
        .sort_values("date")
    )
    daily["pass_pct"] = (daily["pass_count"] / daily["total"] * 100).round(1)
    daily["fail_pct"] = (daily["fail_count"] / daily["total"] * 100).round(1)
    daily["error_pct"] = (daily["error_count"] / daily["total"] * 100).round(1)

    fig = go.Figure(data=[
        go.Bar(
            name="Passados", x=daily["date"].astype(str), y=daily["pass_count"],
            text=daily["pass_pct"].apply(lambda x: f"{x}%" if x > 0 else ""),
            textposition="inside", textfont_color="white",
            marker_color="#2ecc71",
        ),
        go.Bar(
            name="Falhas", x=daily["date"].astype(str), y=daily["fail_count"],
            text=daily["fail_pct"].apply(lambda x: f"{x}%" if x > 0 else ""),
            textposition="inside", textfont_color="white",
            marker_color="#e74c3c",
        ),
        go.Bar(
            name="Erros", x=daily["date"].astype(str), y=daily["error_count"],
            text=daily["error_pct"].apply(lambda x: f"{x}%" if x > 0 else ""),
            textposition="inside", textfont_color="white",
            marker_color="#f39c12",
        ),
    ])
    fig.update_layout(
        title=suite,
        barmode="stack",
        height=350,
        xaxis_title="Data",
        yaxis_title="Quantidade",
        legend_title="Status",
    )
    fig.update_traces(textfont_size=11, textfont_color="white")
    st.plotly_chart(fig, use_container_width=True)
