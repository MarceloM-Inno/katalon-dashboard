import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from typing import Optional, Dict, Any

st_secrets_valid = True
try:
    for key, env_key in [("supabase_url", "SUPABASE_URL"), ("supabase_key", "SUPABASE_KEY")]:
        if key in st.secrets and st.secrets[key]:
            os.environ[env_key] = st.secrets[key]
except Exception:
    st_secrets_valid = False

from config import SUPABASE_URL, SUPABASE_KEY
from db import (
    load_manual_registered,
    load_manual_history,
    load_manual_snapshots,
    load_manual_test_cases,
)

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error(
        "Configure as variáveis SUPABASE_URL e SUPABASE_KEY "
        "no arquivo .env ou nos secrets do Streamlit."
    )
    st.stop()


@st.cache_data(ttl=60)
def get_data():
    registered_df = load_manual_registered()
    history_df = load_manual_history()
    snapshots_df = load_manual_snapshots(limit=100)
    return registered_df, history_df, snapshots_df


def get_status_color(status: str) -> str:
    status_map = {
        "PASS": "#2ecc71",
        "FAIL": "#e74c3c",
        "ABORTED": "#f39c12",
        "BLOCKED": "#9b59b6",
        "PENDING": "#3498db",
    }
    return status_map.get(status, "#95a5a6")


st.markdown(
    "<h1 style='text-align: center; margin-bottom: 0.5rem;'>"
    " Dashboard - Testes Manuais</h1>",
    unsafe_allow_html=True,
)
st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
st.divider()

registered_df, history_df, snapshots_df = get_data()

today = date.today()

if not registered_df.empty:
    registered_df["date_start_dt"] = pd.to_datetime(registered_df["date_start"]).dt.date
    registered_df["date_end_dt"] = pd.to_datetime(registered_df["date_end"]).dt.date
    registered_df["is_active"] = (
        (registered_df["date_start_dt"] <= today) & 
        (today <= registered_df["date_end_dt"])
    )
    
    active_df = registered_df[registered_df["is_active"]].copy()
else:
    active_df = pd.DataFrame()


st.sidebar.header(" Filtros")

filter_base = st.sidebar.selectbox(
    "Projeto Base",
    ["Todos", "ONEY", "BNPL"],
    key="sidebar_base"
)

if not active_df.empty:
    project_keys = ["Todos"] + sorted(active_df["project_key"].unique().tolist())
    filter_project = st.sidebar.selectbox(
        "Project Key",
        project_keys,
        key="sidebar_project"
    )
else:
    filter_project = "Todos"

st.sidebar.divider()

if st.sidebar.button(" Atualizar Agora", use_container_width=True):
    st.cache_data.clear()
    st.rerun()


if active_df.empty:
    st.warning("Nenhum projeto ATIVO no momento.")
    st.info(
        "Para adicionar projetos, acesse a página **Cadastro de Projetos** "
        "no menu lateral."
    )
    st.stop()


if filter_base != "Todos":
    active_df = active_df[active_df["base_project"] == filter_base]

if filter_project != "Todos":
    active_df = active_df[active_df["project_key"] == filter_project]

if active_df.empty:
    st.warning("Nenhum projeto encontrado com os filtros selecionados.")
    st.stop()


tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Visão Geral", 
    "📈 Histórico", 
    "📋 Detalhes", 
    "📅 Próximos"
])


with tab1:
    st.subheader(" KPIs - Projetos Ativos")
    
    total_active = len(active_df)
    
    if not history_df.empty and "project_key" in history_df.columns:
        active_project_keys = active_df["project_key"].unique()
        recent_history = history_df[
            history_df["project_key"].isin(active_project_keys)
        ].copy()
        
         if not recent_history.empty:
            if "snapshot_datetime" in recent_history.columns:
                recent_history["snapshot_datetime"] = pd.to_datetime(recent_history["snapshot_datetime"])
                latest_per_project = recent_history.sort_values("snapshot_datetime").groupby("project_key").last()
            else:
                recent_history["snapshot_date"] = pd.to_datetime(recent_history["snapshot_date"])
                latest_per_project = recent_history.sort_values("snapshot_date").groupby("project_key").last()
            
            total_tests = latest_per_project["total_tests"].sum()
            total_pass = latest_per_project["total_pass"].sum()
            total_fail = latest_per_project["total_fail"].sum()
            total_aborted = latest_per_project["total_aborted"].sum()
            total_blocked = latest_per_project["total_blocked"].sum()
            total_pending = latest_per_project["total_pending"].sum()
            
            if total_tests > 0:
                pass_rate = (total_pass / total_tests) * 100
            else:
                pass_rate = 0.0
        else:
            total_tests = total_pass = total_fail = total_aborted = total_blocked = total_pending = 0
            pass_rate = 0.0
    else:
        total_tests = total_pass = total_fail = total_aborted = total_blocked = total_pending = 0
        pass_rate = 0.0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Projetos Ativos", total_active)
    
    with col2:
        st.metric("Total de Testes", f"{total_tests:,}")
    
    with col3:
        st.metric("Testes Passados", f"{total_pass:,}")
    
    with col4:
        st.metric("Taxa de Sucesso", f"{pass_rate:.1f}%")
    
    st.divider()
    
    col_pie, col_bar = st.columns(2)
    
    with col_pie:
        st.subheader("Distribuição de Status")
        
        status_data = {
            "Status": ["PASS", "FAIL", "ABORTED", "BLOCKED", "PENDING"],
            "Quantidade": [total_pass, total_fail, total_aborted, total_blocked, total_pending],
        }
        status_df = pd.DataFrame(status_data)
        status_df = status_df[status_df["Quantidade"] > 0]
        
        if not status_df.empty:
            fig_pie = px.pie(
                status_df,
                values="Quantidade",
                names="Status",
                color="Status",
                color_discrete_map={
                    "PASS": "#2ecc71",
                    "FAIL": "#e74c3c",
                    "ABORTED": "#f39c12",
                    "BLOCKED": "#9b59b6",
                    "PENDING": "#3498db",
                },
                hole=0.4
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sem dados de histórico ainda.")
    
    with col_bar:
        st.subheader("Por Prioridade")
        
        if not history_df.empty and "project_key" in history_df.columns:
            active_keys = active_df["project_key"].unique()
            hf = history_df[history_df["project_key"].isin(active_keys)].copy()
            
            if not hf.empty:
                if "snapshot_datetime" in hf.columns:
                    hf["snapshot_datetime"] = pd.to_datetime(hf["snapshot_datetime"])
                    latest = hf.sort_values("snapshot_datetime").groupby("project_key").last()
                else:
                    hf["snapshot_date"] = pd.to_datetime(hf["snapshot_date"])
                    latest = hf.sort_values("snapshot_date").groupby("project_key").last()
                
                high_total = latest["priority_high_total"].sum()
                high_pass = latest["priority_high_pass"].sum()
                med_total = latest["priority_med_total"].sum()
                med_pass = latest["priority_med_pass"].sum()
                low_total = latest["priority_low_total"].sum()
                low_pass = latest["priority_low_pass"].sum()
                
                priority_data = {
                    "Prioridade": ["High", "High", "Medium", "Medium", "Low", "Low"],
                    "Status": ["Passados", "Outros", "Passados", "Outros", "Passados", "Outros"],
                    "Quantidade": [
                        high_pass, high_total - high_pass,
                        med_pass, med_total - med_pass,
                        low_pass, low_total - low_pass
                    ]
                }
                priority_df = pd.DataFrame(priority_data)
                
                fig_bar = px.bar(
                    priority_df,
                    x="Prioridade",
                    y="Quantidade",
                    color="Status",
                    barmode="stack",
                    color_discrete_map={
                        "Passados": "#2ecc71",
                        "Outros": "#95a5a6"
                    }
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Sem dados de histórico.")
        else:
            st.info("Sem dados de histórico.")
    
    st.divider()
    
    st.subheader("Resumo por Projeto")
    
    summary_rows = []
    
    if not history_df.empty and "project_key" in history_df.columns:
        active_keys = active_df["project_key"].unique()
        hf = history_df[history_df["project_key"].isin(active_keys)].copy()
        
        if not hf.empty:
            if "snapshot_datetime" in hf.columns:
                hf["snapshot_datetime"] = pd.to_datetime(hf["snapshot_datetime"])
                for _, proj in active_df.iterrows():
                    proj_key = proj["project_key"]
                    proj_base = proj["base_project"]
                    
                    proj_history = hf[hf["project_key"] == proj_key]
                    
                    if proj_history.empty:
                        continue
                    
                    latest = proj_history.sort_values("snapshot_datetime").iloc[-1]
                    
                    total = latest["total_tests"]
                    passed = latest["total_pass"]
                    rate = (passed / total * 100) if total > 0 else 0
                    
                    days_remaining = (proj["date_end_dt"] - today).days
                    
                    summary_rows.append({
                        "Project Key": proj_key,
                        "Base": proj_base,
                        "Fim em": f"{days_remaining} dias",
                        "Total": total,
                        "Passados": passed,
                        "Taxa %": f"{rate:.1f}%",
                    })
            else:
                hf["snapshot_date"] = pd.to_datetime(hf["snapshot_date"])
                
                for _, proj in active_df.iterrows():
                    proj_key = proj["project_key"]
                    proj_base = proj["base_project"]
                    
                    proj_history = hf[hf["project_key"] == proj_key]
                    
                    if proj_history.empty:
                        continue
                    
                    latest = proj_history.sort_values("snapshot_date").iloc[-1]
                    
                    total = latest["total_tests"]
                    passed = latest["total_pass"]
                    rate = (passed / total * 100) if total > 0 else 0
                    
                    days_remaining = (proj["date_end_dt"] - today).days
                    
                    summary_rows.append({
                        "Project Key": proj_key,
                        "Base": proj_base,
                        "Fim em": f"{days_remaining} dias",
                        "Total": total,
                        "Passados": passed,
                        "Taxa %": f"{rate:.1f}%",
                    })
    
    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum projeto com dados de histórico ainda.")


with tab2:
    st.subheader(" Histórico de Execuções")
    
    if not history_df.empty and "project_key" in history_df.columns:
        active_keys = active_df["project_key"].unique()
        hf = history_df[history_df["project_key"].isin(active_keys)].copy()
        
        if not hf.empty:
            if "snapshot_datetime" in hf.columns:
                hf["snapshot_datetime"] = pd.to_datetime(hf["snapshot_datetime"])
                hf = hf.sort_values("snapshot_datetime")
            else:
                hf["snapshot_date"] = pd.to_datetime(hf["snapshot_date"])
                hf = hf.sort_values("snapshot_date")
            
            hf["Taxa Sucesso %"] = (hf["total_pass"] / hf["total_tests"] * 100).round(1)
            
            x_col = "snapshot_datetime" if "snapshot_datetime" in hf.columns else "snapshot_date"
            
            fig_trend = px.line(
                hf,
                x=x_col,
                y="Taxa Sucesso %",
                color="project_key",
                markers=True,
                title="Evolução da Taxa de Sucesso por Projeto"
            )
            st.plotly_chart(fig_trend, use_container_width=True)
            
            st.divider()
            
            fig_total = px.line(
                hf,
                x=x_col,
                y="total_tests",
                color="project_key",
                markers=True,
                title="Evolução da Quantidade de Testes"
            )
            st.plotly_chart(fig_total, use_container_width=True)
            
            st.divider()
            
            status_cols = ["total_pass", "total_fail", "total_aborted", "total_blocked", "total_pending"]
            
            for proj_key in hf["project_key"].unique():
                proj_data = hf[hf["project_key"] == proj_key].copy()
                
                with st.expander(f"📊 {proj_key} - Detalhe por Status"):
                    fig_status = go.Figure()
                    
                    fig_status.add_trace(go.Bar(
                        x=proj_data[x_col],
                        y=proj_data["total_pass"],
                        name="PASS",
                        marker_color="#2ecc71"
                    ))
                    fig_status.add_trace(go.Bar(
                        x=proj_data[x_col],
                        y=proj_data["total_fail"],
                        name="FAIL",
                        marker_color="#e74c3c"
                    ))
                    fig_status.add_trace(go.Bar(
                        x=proj_data[x_col],
                        y=proj_data["total_aborted"],
                        name="ABORTED",
                        marker_color="#f39c12"
                    ))
                    fig_status.add_trace(go.Bar(
                        x=proj_data[x_col],
                        y=proj_data["total_blocked"],
                        name="BLOCKED",
                        marker_color="#9b59b6"
                    ))
                    
                    fig_status.update_layout(
                        barmode="stack",
                        title=f"{proj_key} - Status ao Longo do Tempo",
                        xaxis_title="Data/Hora",
                        yaxis_title="Quantidade"
                    )
                    st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("Sem dados de histórico.")
    else:
        st.info("Sem dados de histórico.")


with tab3:
    st.subheader(" Detalhes dos Projetos")
    
    if not active_df.empty:
        for _, proj in active_df.iterrows():
            proj_key = proj["project_key"]
            proj_base = proj["base_project"]
            
            with st.expander(f"🔍 {proj_key} ({proj_base})"):
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.metric("Data Início", str(proj["date_start_dt"]))
                
                with col_b:
                    st.metric("Data Fim", str(proj["date_end_dt"]))
                
                with col_c:
                    days_remaining = (proj["date_end_dt"] - today).days
                    st.metric("Dias Restantes", days_remaining)
                
                friendly = proj.get("friendly_name")
                if friendly and not pd.isna(friendly):
                    st.markdown(f"**Nome:** {friendly}")
                
                notes = proj.get("notes")
                if notes and not pd.isna(notes):
                    st.markdown(f"**Observações:** {notes}")
                
                if not history_df.empty and "project_key" in history_df.columns:
                    proj_history = history_df[history_df["project_key"] == proj_key].copy()
                    
                    if not proj_history.empty:
                        if "snapshot_datetime" in proj_history.columns:
                            proj_history["snapshot_datetime"] = pd.to_datetime(proj_history["snapshot_datetime"])
                            proj_history = proj_history.sort_values("snapshot_datetime", ascending=False)
                            date_col = "snapshot_datetime"
                        else:
                            proj_history["snapshot_date"] = pd.to_datetime(proj_history["snapshot_date"])
                            proj_history = proj_history.sort_values("snapshot_date", ascending=False)
                            date_col = "snapshot_date"
                        
                        latest = proj_history.iloc[0]
                        
                        st.divider()
                        st.markdown("**Última Atualização:**")
                        
                        col_d1, col_d2, col_d3, col_d4 = st.columns(4)
                        
                        with col_d1:
                            st.metric("Total", latest["total_tests"])
                        with col_d2:
                            st.metric("PASS", latest["total_pass"])
                        with col_d3:
                            st.metric("FAIL", latest["total_fail"])
                        with col_d4:
                            rate = (latest["total_pass"] / latest["total_tests"] * 100) if latest["total_tests"] > 0 else 0
                            st.metric("Taxa %", f"{rate:.1f}%")
                        
                        display_cols = [
                            date_col, "total_tests", "total_pass", "total_fail",
                            "total_aborted", "total_blocked", "total_pending"
                        ]
                        display_df = proj_history[display_cols].copy()
                        
                        if date_col == "snapshot_datetime":
                            display_df[date_col] = display_df[date_col].dt.strftime("%d/%m/%Y %H:%M")
                        else:
                            display_df[date_col] = display_df[date_col].dt.strftime("%d/%m/%Y")
                        
                        display_df = display_df.rename(columns={
                            date_col: "Data/Hora",
                            "total_tests": "Total",
                            "total_pass": "PASS",
                            "total_fail": "FAIL",
                            "total_aborted": "ABORTED",
                            "total_blocked": "BLOCKED",
                            "total_pending": "PENDING"
                        })
                        
                        st.markdown("**Histórico:**")
                        st.dataframe(display_df, use_container_width=True, hide_index=True)
                    else:
                        st.info("Sem histórico para este projeto.")


with tab4:
    st.subheader(" Próximos a Vencer")
    
    active_df["days_remaining"] = (active_df["date_end_dt"] - today).days
    
    urgent_df = active_df[active_df["days_remaining"] <= 7].copy()
    urgent_df = urgent_df.sort_values("days_remaining")
    
    if urgent_df.empty:
        st.success("Nenhum projeto para vencer nos próximos 7 dias.")
    else:
        st.warning(f"⚠️ {len(urgent_df)} projeto(s) para vencer nos próximos 7 dias:")
        
        for _, proj in urgent_df.iterrows():
            days = proj["days_remaining"]
            
            if days <= 2:
                emoji = "🔴"
            elif days <= 4:
                emoji = "🟡"
            else:
                emoji = "🟢"
            
            st.markdown(
                f"{emoji} **{proj['project_key']}** ({proj['base_project']}) - "
                f"Faltam **{days} dias** (Fim em {proj['date_end_dt']})"
            )
    
    st.divider()
    
    st.subheader(" Todos os Projetos Ativos - Timeline")
    
    timeline_data = []
    for _, proj in active_df.iterrows():
        timeline_data.append({
            "Projeto": proj["project_key"],
            "Base": proj["base_project"],
            "Início": proj["date_start_dt"],
            "Fim": proj["date_end_dt"],
            "Dias Restantes": proj["days_remaining"]
        })
    
    if timeline_data:
        timeline_df = pd.DataFrame(timeline_data)
        timeline_df = timeline_df.sort_values("Dias Restantes")
        
        st.dataframe(
            timeline_df[["Projeto", "Base", "Início", "Fim", "Dias Restantes"]],
            use_container_width=True,
            hide_index=True
        )


st.divider()
st.caption(
    "Desenvolvido com Streamlit  |  Dados: Supabase  |  Módulo: Testes Manuais"
)
