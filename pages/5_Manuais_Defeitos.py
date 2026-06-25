import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from typing import Optional

st_secrets_valid = True
try:
    for key, env_key in [("supabase_url", "SUPABASE_URL"), ("supabase_key", "SUPABASE_KEY")]:
        if key in st.secrets and st.secrets[key]:
            os.environ[env_key] = st.secrets[key]
except Exception:
    st_secrets_valid = False

from config import SUPABASE_URL, SUPABASE_KEY
from db import load_manual_defects, load_manual_snapshots

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error(
        "Configure as variáveis SUPABASE_URL e SUPABASE_KEY "
        "no arquivo .env ou nos secrets do Streamlit."
    )
    st.stop()


@st.cache_data(ttl=60)
def get_defects_data():
    defects_df = load_manual_defects(limit=10000)
    snapshots_df = load_manual_snapshots(limit=100)
    return defects_df, snapshots_df


st.markdown(
    "<h1 style='text-align: center; margin-bottom: 0.5rem;'>"
    " Dashboard - Defeitos</h1>",
    unsafe_allow_html=True,
)
st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
st.divider()

defects_df, snapshots_df = get_defects_data()

st.sidebar.header(" Filtros")

filter_base = st.sidebar.selectbox(
    "Projeto Base",
    ["Todos", "ONEY", "BNPL"],
    key="sidebar_defects_base"
)

open_statuses = ["Open", "In Progress", "Reaberto", "Reaberto", "Em Verificação", "Reteste", "Informação Adcional", "Em Andamento"]

filter_status = st.sidebar.multiselect(
    "Status",
    [] if defects_df.empty else sorted(defects_df["status"].unique().tolist()),
    default=[],
    key="sidebar_defects_status"
)

filter_priority = st.sidebar.multiselect(
    "Prioridade",
    [] if defects_df.empty else sorted(defects_df["priority"].dropna().unique().tolist()),
    default=[],
    key="sidebar_defects_priority"
)

if not defects_df.empty:
    project_keys = sorted(defects_df["project_key"].unique().tolist())
    filter_project = st.sidebar.multiselect(
        "Project Key",
        project_keys,
        default=[],
        key="sidebar_defects_project"
    )
else:
    filter_project = []

st.sidebar.divider()

if st.sidebar.button(" Atualizar Agora", use_container_width=True, key="btn_defects_refresh"):
    st.cache_data.clear()
    st.rerun()

if defects_df.empty:
    st.warning("Nenhum defeito encontrado no banco de dados.")
    st.info(
        "Os defeitos são extraídos dos CSVs 'Defects All Projects' e 'FillAutoDefects'. "
        "Execute o watcher ou o parser manual para importar os dados."
    )
    st.stop()

filtered = defects_df.copy()

if filter_base != "Todos":
    filtered = filtered[filtered["base_project"] == filter_base]

if filter_status:
    filtered = filtered[filtered["status"].isin(filter_status)]

if filter_priority:
    filtered = filtered[filtered["priority"].isin(filter_priority)]

if filter_project:
    filtered = filtered[filtered["project_key"].isin(filter_project)]

if filtered.empty:
    st.warning("Nenhum defeito encontrado com os filtros selecionados.")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Visão Geral",
    "📈 Histórico",
    "📋 Tabela Detalhada",
    "🔍 Pesquisa"
])

with tab1:
    st.subheader(" KPIs - Defeitos")
    
    total_defects = len(filtered)
    
    is_open_mask = filtered["status"].str.strip().str.lower().isin([
        s.lower() for s in open_statuses
    ], na=False)
    
    open_defects = is_open_mask.sum()
    closed_defects = total_defects - open_defects
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Defeitos", f"{total_defects:,}")
    
    with col2:
        st.metric("Abertos", f"{open_defects:,}")
    
    with col3:
        st.metric("Fechados/Concluídos", f"{closed_defects:,}")
    
    with col4:
        if total_defects > 0:
            open_rate = (open_defects / total_defects) * 100
            st.metric("Taxa Abertos", f"{open_rate:.1f}%")
        else:
            st.metric("Taxa Abertos", "0%")
    
    st.divider()
    
    col_pie, col_bar = st.columns(2)
    
    with col_pie:
        st.subheader("Distribuição por Status")
        
        status_counts = filtered["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Quantidade"]
        
        fig_pie = px.pie(
            status_counts,
            values="Quantidade",
            names="Status",
            title="Status dos Defeitos",
            hole=0.4
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_bar:
        st.subheader("Distribuição por Prioridade")
        
        priority_counts = filtered["priority"].value_counts().reset_index()
        priority_counts.columns = ["Prioridade", "Quantidade"]
        
        fig_bar = px.bar(
            priority_counts,
            x="Prioridade",
            y="Quantidade",
            color="Prioridade",
            title="Defeitos por Prioridade"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.divider()
    
    st.subheader("Por Project Key")
    
    project_counts = filtered["project_key"].value_counts().reset_index()
    project_counts.columns = ["Project Key", "Quantidade"]
    project_counts = project_counts.head(15)
    
    fig_project = px.bar(
        project_counts,
        x="Project Key",
        y="Quantidade",
        color="Project Key",
        title="Top 15 Project Keys com Mais Defeitos"
    )
    st.plotly_chart(fig_project, use_container_width=True)
    
    st.divider()
    
    fornecedor_col = filtered.get("custom_fornecedor")
    if fornecedor_col is not None and fornecedor_col.notna().any():
        st.subheader("Por Fornecedor")
        
        fornecedor_counts = filtered["custom_fornecedor"].value_counts().reset_index()
        fornecedor_counts.columns = ["Fornecedor", "Quantidade"]
        
        fig_fornecedor = px.bar(
            fornecedor_counts,
            x="Fornecedor",
            y="Quantidade",
            color="Fornecedor",
            title="Defeitos por Fornecedor"
        )
        st.plotly_chart(fig_fornecedor, use_container_width=True)

with tab2:
    st.subheader(" Histórico de Extrações")
    
    if not snapshots_df.empty:
        snapshots_sorted = snapshots_df.sort_values("snapshot_date", ascending=False).head(20)
        
        st.dataframe(
            snapshots_sorted[["file_name", "base_project", "snapshot_date", "total_rows_in_csv", "processed_rows"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhum snapshot encontrado.")
    
    st.divider()
    
    st.subheader("Evolução de Defeitos Abertos por Extração")
    
    if "snapshot_date" in filtered.columns and not filtered.empty:
        filtered_copy = filtered.copy()
        filtered_copy["snapshot_date_only"] = pd.to_datetime(filtered_copy["snapshot_date"]).dt.date
        
        snapshot_groups = filtered_copy.groupby(["snapshot_date_only", "status"]).size().reset_index(name="count")
        
        fig_trend = px.bar(
            snapshot_groups,
            x="snapshot_date_only",
            y="count",
            color="status",
            barmode="stack",
            title="Defeitos por Data de Extração"
        )
        st.plotly_chart(fig_trend, use_container_width=True)

with tab3:
    st.subheader(" Tabela Detalhada")
    
    display_cols = [
        "issue_key", "status", "priority", "project_key",
        "assignee", "reporter", "summary", "snapshot_date"
    ]
    
    available_cols = [c for c in display_cols if c in filtered.columns]
    display_df = filtered[available_cols].copy()
    
    if "summary" in display_df.columns:
        display_df["summary"] = display_df["summary"].str[:100] + "..."
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    st.caption(f"Total de registros: {len(filtered):,}")

with tab4:
    st.subheader(" Pesquisa de Defeito")
    
    search_issue = st.text_input(
        "Buscar por Issue Key",
        placeholder="Ex: NEXTCPOREL-65, MODPCE-90, etc."
    )
    
    if search_issue:
        search_mask = filtered["issue_key"].str.contains(
            search_issue.strip(), case=False, na=False
        )
        search_results = filtered[search_mask]
        
        if search_results.empty:
            st.warning(f"Nenhum defeito encontrado para '{search_issue}'")
        else:
            st.success(f"Encontrado(s) {len(search_results)} defeito(s)")
            
            for idx, row in search_results.iterrows():
                with st.expander(f"🔍 {row.get('issue_key', 'N/A')} - {row.get('status', 'N/A')}"):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.metric("Issue Key", row.get("issue_key", "N/A"))
                        st.metric("Status", row.get("status", "N/A"))
                        st.metric("Prioridade", row.get("priority", "N/A"))
                    
                    with col_b:
                        st.metric("Project Key", row.get("project_key", "N/A"))
                        st.metric("Assignee", row.get("assignee", "N/A") or "—")
                        st.metric("Reporter", row.get("reporter", "N/A") or "—")
                    
                    summary = row.get("summary")
                    if summary:
                        st.markdown("**Descrição:**")
                        st.info(summary)
                    
                    fornecedor = row.get("custom_fornecedor")
                    if fornecedor:
                        st.metric("Fornecedor", fornecedor)
                    
                    impact_qa = row.get("custom_impact_qa")
                    if impact_qa:
                        st.metric("Impacto QA", impact_qa)
                    
                    created = row.get("created_dt")
                    updated = row.get("updated_dt")
                    if created:
                        st.metric("Criado em", str(created))
                    if updated:
                        st.metric("Atualizado em", str(updated))


st.divider()
st.caption(
    "Desenvolvido com Streamlit  |  Dados: Supabase  |  Fonte: Defects All Projects / FillAutoDefects"
)
