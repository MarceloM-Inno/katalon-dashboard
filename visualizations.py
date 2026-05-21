import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def render_kpi_cards(exec_df: pd.DataFrame, cases_df: pd.DataFrame):
    total_exec = len(exec_df)
    total_tests = int(exec_df["total_tests"].sum()) if not exec_df.empty else 0
    total_fail = int(exec_df["total_failures"].sum()) if not exec_df.empty else 0
    total_err = int(exec_df["total_errors"].sum()) if not exec_df.empty else 0
    total_pass = total_tests - total_fail - total_err
    pass_rate = round((total_pass / total_tests * 100), 1) if total_tests > 0 else 0

    cols = st.columns(5)
    cols[0].metric("Execuções", total_exec)
    cols[1].metric("Total de Testes", total_tests)
    cols[2].metric("Passados", total_pass, delta=None)
    cols[3].metric("Falhas", total_fail, delta=None)
    cols[4].metric("Taxa de Sucesso", f"{pass_rate}%")


def render_trend_chart(exec_df: pd.DataFrame):
    if exec_df.empty:
        st.info("Sem dados para exibir.")
        return

    df = exec_df.copy()
    df["date"] = df["execution_date"].dt.date
    df["pass_count"] = df["total_tests"] - df["total_failures"] - df["total_errors"]

    fig = go.Figure()
    for suite in sorted(df["suite_name"].unique()):
        suite_df = df[df["suite_name"] == suite].sort_values("date")
        fig.add_trace(go.Scatter(
            x=suite_df["date"],
            y=suite_df["pass_count"],
            mode="lines+markers",
            name=suite,
            stackgroup=None,
        ))

    fig.update_layout(
        title="Testes Passados por Suite ao Longo do Tempo",
        xaxis_title="Data",
        yaxis_title="Testes Passados",
        hovermode="x unified",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_failure_trend(exec_df: pd.DataFrame):
    if exec_df.empty:
        return

    df = exec_df.copy()
    df["date"] = df["execution_date"].dt.date

    fig = go.Figure()
    for suite in sorted(df["suite_name"].unique()):
        suite_df = df[df["suite_name"] == suite].sort_values("date")
        fig.add_trace(go.Scatter(
            x=suite_df["date"],
            y=suite_df["total_failures"],
            mode="lines+markers",
            name=suite,
        ))

    fig.update_layout(
        title="Falhas por Suite ao Longo do Tempo",
        xaxis_title="Data",
        yaxis_title="Falhas",
        hovermode="x unified",
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_suite_distribution(exec_df: pd.DataFrame):
    if exec_df.empty:
        return

    latest = (
        exec_df.sort_values("execution_date")
        .groupby("suite_name")
        .last()
        .reset_index()
    )
    latest["pass_count"] = latest["total_tests"] - latest["total_failures"] - latest["total_errors"]

    fig = go.Figure(data=[
        go.Bar(name="Passados", y=latest["suite_name"], x=latest["pass_count"], orientation="h"),
        go.Bar(name="Falhas", y=latest["suite_name"], x=latest["total_failures"], orientation="h"),
        go.Bar(name="Erros", y=latest["suite_name"], x=latest["total_errors"], orientation="h"),
    ])
    fig.update_layout(
        title="Última Execução por Suite",
        barmode="stack",
        height=350,
        xaxis_title="Quantidade",
        yaxis_title="",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_status_pie(cases_df: pd.DataFrame):
    if cases_df.empty:
        return

    status_counts = cases_df["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]

    colors = {"PASSED": "#2ecc71", "FAILED": "#e74c3c", "ERROR": "#f39c12", "SKIPPED": "#95a5a6"}

    fig = px.pie(
        status_counts,
        values="count",
        names="status",
        title="Distribuição por Status",
        color="status",
        color_discrete_map=colors,
    )
    fig.update_traces(textinfo="label+percent")
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)


def render_detail_table(merged_df: pd.DataFrame):
    if merged_df.empty:
        st.info("Nenhum caso de teste encontrado.")
        return

    cols = {
        "execution_date": "Data",
        "suite_name": "Suite",
        "test_name": "Test Case",
        "status": "Status",
        "duration_sec": "Duração (s)",
        "failure_type": "Tipo Falha",
        "failure_message": "Mensagem",
    }
    display = merged_df[[c for c in cols if c in merged_df.columns]].copy()
    display.columns = [cols[c] for c in display.columns]

    if "Data" in display.columns:
        display["Data"] = pd.to_datetime(display["Data"]).dt.strftime("%d/%m/%Y %H:%M")

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Mensagem": st.column_config.TextColumn(width="large"),
        },
    )
