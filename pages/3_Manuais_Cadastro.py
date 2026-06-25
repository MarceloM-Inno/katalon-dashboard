import os
import streamlit as st
import pandas as pd
from datetime import datetime, date

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
    insert_manual_registered,
    update_manual_registered,
    delete_manual_registered,
)

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error(
        "Configure as variáveis SUPABASE_URL e SUPABASE_KEY "
        "no arquivo .env ou nos secrets do Streamlit."
    )
    st.stop()


def get_status_icon(row):
    today = date.today()
    if pd.isna(row.get("date_start")) or pd.isna(row.get("date_end")):
        return "❓"
    
    ds = pd.to_datetime(row["date_start"]).date()
    de = pd.to_datetime(row["date_end"]).date()
    
    if today < ds:
        return "📅"
    elif ds <= today <= de:
        return "🟢"
    else:
        return "📦"


def get_status_text(row):
    today = date.today()
    if pd.isna(row.get("date_start")) or pd.isna(row.get("date_end")):
        return "Indefinido"
    
    ds = pd.to_datetime(row["date_start"]).date()
    de = pd.to_datetime(row["date_end"]).date()
    
    if today < ds:
        return "Agendado"
    elif ds <= today <= de:
        return "Ativo"
    else:
        return "Arquivado"


st.markdown(
    "<h1 style='text-align: center; margin-bottom: 0.5rem;'>"
    " Cadastro de Projetos - Testes Manuais</h1>",
    unsafe_allow_html=True,
)
st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
st.divider()

tab1, tab2 = st.tabs(["📋 Projetos Ativos", "➕ Novo Projeto"])


with tab2:
    st.subheader("Cadastrar Novo Projeto")
    st.info(
        "Preencha os dados abaixo para cadastrar um novo projeto. "
        "Estas datas serão usadas pelo Katalon para extrair os dados do Jira."
    )
    
    with st.form("new_project_form", clear_on_submit=True):
        st.markdown("### Dados do Projeto")
        
        col1, col2 = st.columns(2)
        
        with col1:
            base_project = st.selectbox(
                "Projeto Base",
                ["ONEY", "BNPL"],
                key="new_base",
                help="Selecione o projeto base (ONEY ou BNPL)"
            )
        
        with col2:
            project_key = st.text_input(
                "Project Key",
                placeholder="Ex: PRICINGII, PR101LT2V3, etc.",
                key="new_key",
                help="Identificador único do projeto (ex: PRICINGII)"
            )
        
        st.divider()
        st.markdown("### Período de Extração")
        
        col3, col4 = st.columns(2)
        
        with col3:
            date_start = st.date_input(
                "Data Início",
                key="new_start",
                help="Data de início do período de extração"
            )
        
        with col4:
            date_end = st.date_input(
                "Data Fim",
                key="new_end",
                help="Data de fim do período de extração"
            )
        
        st.divider()
        st.markdown("### Dados Adicionais (Opcionais)")
        
        friendly_name = st.text_input(
            "Nome Amigável",
            placeholder="Ex: Certificação Pricing II - Regressão",
            key="new_friendly",
            help="Nome descritivo para facilitar a identificação"
        )
        
        notes = st.text_area(
            "Observações",
            placeholder="Informações adicionais sobre este projeto...",
            key="new_notes",
            height=100
        )
        
        st.divider()
        
        submit = st.form_submit_button("📝 Cadastrar Projeto", use_container_width=True, type="primary")
        
        if submit:
            if not project_key or not project_key.strip():
                st.error("⚠️ Project Key é obrigatório!")
            elif date_end < date_start:
                st.error("⚠️ Data Fim não pode ser anterior à Data Início!")
            else:
                proj_id = insert_manual_registered(
                    project_key=project_key.strip(),
                    base_project=base_project,
                    date_start=str(date_start),
                    date_end=str(date_end),
                    friendly_name=friendly_name.strip() if friendly_name else None,
                    notes=notes.strip() if notes else None
                )
                
                if proj_id:
                    st.success(f"✅ Projeto cadastrado com sucesso! ID: {proj_id}")
                    
                    st.balloons()
                    
                    st.info(
                        "📋 Dados para o Katalon:\n\n"
                        f"- Project Key: `{project_key.strip()}`\n"
                        f"- Data Início: `{date_start}`\n"
                        f"- Data Fim: `{date_end}`\n"
                        f"- Projeto Base: `{base_project}`"
                    )
                    
                    st.cache_data.clear()
                else:
                    st.error(
                        "❌ Erro ao cadastrar projeto. "
                        "Verifique se o Project Key já existe para este projeto base."
                    )


with tab1:
    st.subheader("Projetos Cadastrados")
    
    col_filter1, col_filter2 = st.columns([1, 1])
    
    with col_filter1:
        filter_base = st.selectbox(
            "Filtrar por Projeto Base",
            ["Todos", "ONEY", "BNPL"],
            key="filter_base_list"
        )
    
    with col_filter2:
        filter_status = st.selectbox(
            "Filtrar por Status",
            ["Todos", "Ativos", "Agendados", "Arquivados"],
            key="filter_status_list"
        )
    
    load_param = None if filter_base == "Todos" else filter_base
    df = load_manual_registered(base_project=load_param)
    
    if df.empty:
        st.info("📭 Nenhum projeto cadastrado ainda.")
        st.markdown(
            "Use a aba **'➕ Novo Projeto'** para cadastrar o primeiro projeto."
        )
    else:
        df["status_icon"] = df.apply(get_status_icon, axis=1)
        df["status_text"] = df.apply(get_status_text, axis=1)
        
        if filter_status == "Ativos":
            df = df[df["status_text"] == "Ativo"]
        elif filter_status == "Agendados":
            df = df[df["status_text"] == "Agendado"]
        elif filter_status == "Arquivados":
            df = df[df["status_text"] == "Arquivado"]
        
        if df.empty:
            st.info(f"📭 Nenhum projeto encontrado com o filtro: {filter_status}")
        else:
            today = date.today()
            
            for idx, row in df.iterrows():
                ds = pd.to_datetime(row["date_start"]).date()
                de = pd.to_datetime(row["date_end"]).date()
                
                is_active = row["status_text"] == "Ativo"
                
                display_name = row.get("friendly_name", "")
                if pd.isna(display_name) or not display_name:
                    display_name = row["project_key"]
                
                with st.expander(
                    f"{row['status_icon']} **{display_name}** "
                    f"({row['base_project']}) - {row['status_text']}",
                    expanded=is_active
                ):
                    col_a, col_b, col_c = st.columns([2, 2, 1])
                    
                    with col_a:
                        st.metric("Project Key", row["project_key"])
                        st.metric("Projeto Base", row["base_project"])
                    
                    with col_b:
                        st.metric(
                            "Período",
                            f"{row['date_start']} até {row['date_end']}"
                        )
                        
                        if is_active:
                            dias_restantes = (de - today).days
                            st.metric(
                                "Dias Restantes",
                                f"{dias_restantes} dias",
                                delta=f"-{dias_restantes}" if dias_restantes < 7 else None,
                                delta_color="inverse" if dias_restantes < 7 else "normal"
                            )
                        elif row["status_text"] == "Agendado":
                            dias_para = (ds - today).days
                            st.metric("Início em", f"{dias_para} dias")
                        else:
                            dias_passados = (today - de).days
                            st.metric("Concluído há", f"{dias_passados} dias")
                    
                    with col_c:
                        proj_id = row["id"]
                        if st.button(f"✏️ Editar", key=f"edit_{proj_id}", use_container_width=True):
                            st.session_state.edit_id = proj_id
                            st.rerun()
                        
                        if st.button(f"🗑️ Excluir", key=f"del_{proj_id}", use_container_width=True):
                            st.session_state.delete_id = proj_id
                            st.session_state.delete_data = row
                            st.rerun()
                    
                    if is_active:
                        st.divider()
                        st.markdown("### 📋 Dados para o Katalon")
                        
                        st.code(
                            f"Project Key: {row['project_key']}\n"
                            f"Data Início: {row['date_start']}\n"
                            f"Data Fim: {row['date_end']}\n"
                            f"Projeto Base: {row['base_project']}",
                            language="text"
                        )
                        
                        st.caption(
                            "Copie estas datas para usar no Katalon como parâmetros de extração."
                        )
                    
                    notes = row.get("notes")
                    if notes and not pd.isna(notes) and notes.strip():
                        st.divider()
                        st.markdown("📝 Observações:")
                        st.info(notes)


if "edit_id" in st.session_state:
    edit_id = st.session_state.pop("edit_id")
    edit_df = load_manual_registered()
    
    if not edit_df.empty:
        edit_row = edit_df[edit_df["id"] == edit_id]
        
        if not edit_row.empty:
            edit_row = edit_row.iloc[0]
            
            with st.sidebar:
                st.subheader("✏️ Editar Projeto")
                st.divider()
                
                st.info(f"Editando: **{edit_row.get('project_key', 'N/A')}**")
                
                with st.form("edit_project_form"):
                    current_start = pd.to_datetime(edit_row["date_start"]).date()
                    current_end = pd.to_datetime(edit_row["date_end"]).date()
                    
                    st.markdown("### Alterar Período")
                    new_start = st.date_input("Nova Data Início", value=current_start)
                    new_end = st.date_input("Nova Data Fim", value=current_end)
                    
                    current_friendly = edit_row.get("friendly_name", "")
                    if pd.isna(current_friendly):
                        current_friendly = ""
                    
                    st.markdown("### Alterar Dados Adicionais")
                    new_friendly = st.text_input("Nome Amigável", value=current_friendly)
                    
                    current_notes = edit_row.get("notes", "")
                    if pd.isna(current_notes):
                        current_notes = ""
                    new_notes = st.text_area("Observações", value=current_notes, height=100)
                    
                    st.divider()
                    
                    col_salvar, col_cancelar = st.columns(2)
                    
                    with col_salvar:
                        salvar = st.form_submit_button("💾 Salvar", use_container_width=True)
                    
                    with col_cancelar:
                        cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
                    
                    if salvar:
                        if new_end < new_start:
                            st.error("⚠️ Data Fim não pode ser anterior à Data Início!")
                        else:
                            updates = {
                                "date_start": str(new_start),
                                "date_end": str(new_end),
                                "friendly_name": new_friendly if new_friendly else None,
                                "notes": new_notes if new_notes else None,
                            }
                            
                            if update_manual_registered(edit_id, updates):
                                st.success("✅ Projeto atualizado!")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("❌ Erro ao atualizar projeto.")
                    
                    if cancelar:
                        st.rerun()


if "delete_id" in st.session_state:
    del_id = st.session_state.pop("delete_id")
    del_data = st.session_state.pop("delete_data", {})
    
    with st.sidebar:
        st.subheader("🗑️ Confirmar Exclusão")
        st.divider()
        st.warning("Tem certeza que deseja excluir o projeto:")
        st.info(
            f"**{del_data.get('project_key', 'N/A')}**\n\n"
            f"Projeto Base: {del_data.get('base_project', 'N/A')}\n"
            f"Período: {del_data.get('date_start', 'N/A')} até {del_data.get('date_end', 'N/A')}"
        )
        
        st.divider()
        
        col_del_yes, col_del_no = st.columns(2)
        
        with col_del_yes:
            if st.button("✅ Sim, Excluir", use_container_width=True, type="primary"):
                if delete_manual_registered(del_id):
                    st.success("✅ Projeto excluído!")
                    st.cache_data.clear()
                else:
                    st.error("❌ Erro ao excluir projeto.")
                st.rerun()
        
        with col_del_no:
            if st.button("❌ Não", use_container_width=True):
                st.rerun()


st.divider()
st.caption(
    "Desenvolvido com Streamlit  |  Dados: Supabase  |  Módulo: Testes Manuais"
)
