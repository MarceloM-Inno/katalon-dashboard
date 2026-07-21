import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

SUITE_COLORS = px.colors.qualitative.Set2


def render_kpi_cards(exec_df: pd.DataFrame, cases_df: pd.DataFrame):
    total_exec = len(exec_df)
    total_tests = len(cases_df) if not cases_df.empty else 0
    total_pass = int((cases_df["status"] == "PASSED").sum()) if not cases_df.empty else 0
    total_fail = int((cases_df["status"] == "FAILED").sum()) if not cases_df.empty else 0
    total_err = int((cases_df["status"] == "ERROR").sum()) if not cases_df.empty else 0
    pass_rate = round((total_pass / total_tests * 100), 1) if total_tests > 0 else 0

    cols = st.columns(5)
    cols[0].metric("Execuções", total_exec)
    cols[1].metric("Total de Testes", total_tests)
    cols[2].metric("Passados", total_pass, delta=None)
    cols[3].metric("Falhas", total_fail, delta=None)
    cols[4].metric("Taxa de Sucesso", f"{pass_rate}%")


def render_trend_chart(exec_df: pd.DataFrame, cases_df: pd.DataFrame):
    if cases_df.empty:
        st.info("Sem dados para exibir.")
        return

    per_exec = cases_df.groupby("execution_id").agg(
        total_tests=("id", "count"),
        total_failures=("status", lambda s: (s == "FAILED").sum()),
        total_errors=("status", lambda s: (s == "ERROR").sum()),
    ).reset_index()

    df = per_exec.merge(
        exec_df[["id", "suite_name", "suite_name_normalized", "execution_date"]],
        left_on="execution_id",
        right_on="id",
        how="left",
    )
    df["date"] = df["execution_date"].dt.date
    df["pass_count"] = df["total_tests"] - df["total_failures"] - df["total_errors"]

    suite_col = "suite_name_normalized" if "suite_name_normalized" in df.columns else "suite_name"

    fig = go.Figure()
    for i, suite in enumerate(sorted(df[suite_col].unique())):
        suite_df = df[df[suite_col] == suite].sort_values("date")
        fig.add_trace(go.Scatter(
            x=suite_df["date"],
            y=suite_df["pass_count"],
            mode="lines+markers",
            name=suite,
            stackgroup=None,
            marker_color=SUITE_COLORS[i % len(SUITE_COLORS)],
        ))

    fig.update_layout(
        title="Testes Passados por Suite ao Longo do Tempo",
        xaxis_title="Data",
        yaxis_title="Testes Passados",
        hovermode="x unified",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_failure_trend(exec_df: pd.DataFrame, cases_df: pd.DataFrame):
    if cases_df.empty:
        return

    per_exec = cases_df.groupby("execution_id").agg(
        total_failures=("status", lambda s: (s == "FAILED").sum()),
    ).reset_index()

    df = per_exec.merge(
        exec_df[["id", "suite_name", "suite_name_normalized", "execution_date"]],
        left_on="execution_id",
        right_on="id",
        how="left",
    )
    df["date"] = df["execution_date"].dt.date

    suite_col = "suite_name_normalized" if "suite_name_normalized" in df.columns else "suite_name"

    fig = go.Figure()
    for i, suite in enumerate(sorted(df[suite_col].unique())):
        suite_df = df[df[suite_col] == suite].sort_values("date")
        fig.add_trace(go.Scatter(
            x=suite_df["date"],
            y=suite_df["total_failures"],
            mode="lines+markers",
            name=suite,
            marker_color=SUITE_COLORS[i % len(SUITE_COLORS)],
        ))

    fig.update_layout(
        title="Falhas por Suite ao Longo do Tempo",
        xaxis_title="Data",
        yaxis_title="Falhas",
        hovermode="x unified",
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_suite_distribution(cases_df: pd.DataFrame, exec_df: pd.DataFrame):
    if cases_df.empty or exec_df.empty:
        return

    latest = (
        exec_df.sort_values("execution_date")
        .groupby("suite_name_normalized" if "suite_name_normalized" in exec_df.columns else "suite_name")
        .last()[["id"]]
        .reset_index()
    )

    suite_col_norm = "suite_name_normalized" if "suite_name_normalized" in exec_df.columns else "suite_name"
    suite_col_display = latest.columns[0]

    cases_latest = cases_df[cases_df["execution_id"].isin(latest["id"])]
    if cases_latest.empty:
        return

    cases_latest = cases_latest.merge(
        latest[["id", suite_col_display]],
        left_on="execution_id",
        right_on="id",
        how="left",
    )

    stats = cases_latest.groupby(suite_col_display).agg(
        total_tests=("id_x", "count"),
        total_failures=("status", lambda s: (s == "FAILED").sum()),
        total_errors=("status", lambda s: (s == "ERROR").sum()),
    ).reset_index()

    stats["pass_count"] = stats["total_tests"] - stats["total_failures"] - stats["total_errors"]
    stats["total"] = stats["total_tests"]
    stats["pass_pct"] = (stats["pass_count"] / stats["total"] * 100).round(1)
    stats["fail_pct"] = (stats["total_failures"] / stats["total"] * 100).round(1)
    stats["error_pct"] = (stats["total_errors"] / stats["total"] * 100).round(1)

    fig = go.Figure(data=[
        go.Bar(
            name="Passados", x=stats[suite_col_display], y=stats["pass_count"],
            text=stats["pass_pct"].apply(lambda x: f"{x}%" if x > 0 else ""),
            textposition="inside", textfont_color="white",
            marker_color="#2ecc71",
        ),
        go.Bar(
            name="Falhas", x=stats[suite_col_display], y=stats["total_failures"],
            text=stats["fail_pct"].apply(lambda x: f"{x}%" if x > 0 else ""),
            textposition="inside", textfont_color="white",
            marker_color="#e74c3c",
        ),
        go.Bar(
            name="Erros", x=stats[suite_col_display], y=stats["total_errors"],
            text=stats["error_pct"].apply(lambda x: f"{x}%" if x > 0 else ""),
            textposition="inside", textfont_color="white",
            marker_color="#f39c12",
        ),
    ])
    fig.update_layout(
        title="Última Execução por Suite",
        barmode="group",
        height=350,
        xaxis_title="Suite",
        yaxis_title="Quantidade",
        legend_title="Status",
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
        "_override": "Override",
        "duration_sec": "Duração (s)",
        "failure_type": "Tipo Falha",
        "failure_message": "Mensagem",
    }
    available = [c for c in cols if c in merged_df.columns]
    display = merged_df[available].copy()
    display.columns = [cols[c] for c in available]

    if "Data" in display.columns:
        display["Data"] = pd.to_datetime(display["Data"], format="mixed").dt.strftime("%d/%m/%Y %H:%M")

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )
