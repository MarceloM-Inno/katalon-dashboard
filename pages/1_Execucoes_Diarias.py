import os
import streamlit as st

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
import plotly.graph_objects as go
from datetime import date, timedelta

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Configure SUPABASE_URL e SUPABASE_KEY nos secrets.")
    st.stop()


projeto = st.session_state.get("projeto", "")
if not projeto:
    st.switch_page("pages/2_Inicio.py")


@st.cache_data(ttl=60, show_spinner="Carregando execuções...")
def get_exec_data(projeto):
    return load_executions(projeto)


exec_df = get_exec_data(projeto)
overrides_df = load_status_overrides()

if not exec_df.empty:
    exec_df["suite_name_normalized"] = exec_df["suite_name"].apply(normalize_suite_name)

st.title(f" Execuções Diárias - {projeto}")

if exec_df.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

st.sidebar.header("Filtros")

min_date = exec_df["execution_date"].min().date()
max_date = exec_df["execution_date"].max().date()

hoje = date.today()
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
suite_display_map = build_suite_display_map(exec_df["suite_name"].unique().tolist())
for norm_name in sorted(suite_display_map.keys()):
    display_name = suite_display_map[norm_name]
    if st.sidebar.checkbox(display_name, value=True):
        selected_suites.append(norm_name)

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
    exec_filtered = exec_filtered[exec_filtered["suite_name_normalized"].isin(selected_suites)]

exec_ids = exec_filtered["id"].tolist()
if exec_ids and not overrides_df.empty:
    cases_df = load_cases_by_exec_ids(exec_ids)
    cases_df = apply_overrides_to_cases(cases_df, overrides_df)
    per_exec = cases_df.groupby("execution_id").agg(
        total_tests=("id", "count"),
        total_failures=("status", lambda s: (s == "FAILED").sum()),
        total_errors=("status", lambda s: (s == "ERROR").sum()),
    ).reset_index()
    exec_filtered = exec_filtered.drop(
        columns=["total_tests", "total_failures", "total_errors", "total_skipped"],
        errors="ignore",
    )
    exec_filtered = exec_filtered.merge(per_exec, left_on="id", right_on="execution_id", how="left")
    for col in ["total_tests", "total_failures", "total_errors"]:
        exec_filtered[col] = exec_filtered[col].fillna(0).astype(int)

for norm_suite in selected_suites:
    suite_df = (
        exec_filtered[exec_filtered["suite_name_normalized"] == norm_suite]
        .copy()
        .sort_values("execution_date")
    )
    if suite_df.empty:
        continue

    display_name = suite_display_map.get(norm_suite, norm_suite)

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
        title=display_name,
        barmode="stack",
        height=350,
        xaxis_title="Data",
        yaxis_title="Quantidade",
        legend_title="Status",
    )
    fig.update_traces(textfont_size=11, textfont_color="white")
    st.plotly_chart(fig, use_container_width=True)
