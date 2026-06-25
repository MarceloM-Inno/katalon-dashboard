import os
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

try:
    for key, env_key in [("supabase_url", "SUPABASE_URL"), ("supabase_key", "SUPABASE_KEY")]:
        if key in st.secrets and st.secrets[key]:
            os.environ[env_key] = st.secrets[key]
except Exception:
    pass

from config import SUPABASE_URL, SUPABASE_KEY
from db import (
    load_executions,
    load_cases,
    load_status_overrides,
    set_status_override,
    delete_status_override_by_test_case,
)

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Configure SUPABASE_URL e SUPABASE_KEY nos secrets.")
    st.stop()


projeto = st.session_state.get("projeto", "")
if not projeto:
    st.switch_page("pages/2_Inicio.py")


STATUS_OPTIONS = ["PASSED", "FAILED", "ERROR", "SKIPPED"]
STATUS_COLORS = {
    "PASSED": "#2ecc71",
    "FAILED": "#e74c3c",
    "ERROR": "#f39c12",
    "SKIPPED": "#95a5a6",
}


@st.cache_data(ttl=60, show_spinner="Carregando dados...")
def get_data(projeto):
    exec_df = load_executions(projeto)
    cases_df = load_cases(projeto)
    return exec_df, cases_df


st.markdown(
    "<h1 style='text-align: center; margin-bottom: 0.5rem;'>"
    " Gerenciar Overrides de Status</h1>",
    unsafe_allow_html=True,
)
st.caption(
    "Edite manualmente o status de casos de teste automatizados. "
    "Os overrides são aplicados nos gráficos e KPIs automaticamente."
)
st.divider()

exec_df, cases_df = get_data(projeto)

if exec_df.empty or cases_df.empty:
    st.warning("Nenhum dado encontrado para o projeto selecionado.")
    st.stop()


overrides_df = load_status_overrides()

st.sidebar.header(" Filtros")

min_date = exec_df["execution_date"].min().date()
max_date = exec_df["execution_date"].max().date()
hoje = date.today()
padrao_inicio = max(hoje - timedelta(days=30), min_date)
padrao_fim = min(hoje, max_date)

date_range = st.sidebar.date_input(
    "Período",
    value=(padrao_inicio, padrao_fim),
    min_value=min_date,
    max_value=max_date,
)

suites = sorted(exec_df["suite_name"].unique())
selected_suites = []
st.sidebar.markdown("**Suites**")
for suite in suites:
    if st.sidebar.checkbox(suite, value=True, key=f"suite_{suite}"):
        selected_suites.append(suite)

st.sidebar.markdown("**Status Original**")
selected_statuses = []
for status in STATUS_OPTIONS:
    if st.sidebar.checkbox(status, value=True, key=f"orig_{status}"):
        selected_statuses.append(status)

st.sidebar.markdown("**Busca**")
search_text = st.sidebar.text_input(
    "Nome do teste",
    placeholder="Digite parte do nome...",
    label_visibility="collapsed",
    help="Filtra casos de teste por nome (busca parcial, ignore case)",
)

st.sidebar.divider()
show_overrides_only = st.sidebar.checkbox(
    "Mostrar apenas com override",
    value=False,
    help="Exibe somente casos que já possuem override de status",
)

st.sidebar.divider()
if st.sidebar.button(" Atualizar Agora", use_container_width=True):
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

cases_filtered = cases_df[
    cases_df["execution_id"].isin(exec_filtered["id"])
].copy()

if not overrides_df.empty:
    cases_filtered = cases_filtered.merge(
        overrides_df[["test_case_id", "overridden_status", "reason"]],
        left_on="id",
        right_on="test_case_id",
        how="left",
    )
    cases_filtered["has_override"] = cases_filtered["overridden_status"].notna()
else:
    cases_filtered["overridden_status"] = None
    cases_filtered["reason"] = None
    cases_filtered["has_override"] = False

if show_overrides_only:
    cases_filtered = cases_filtered[cases_filtered["has_override"]]

if selected_statuses:
    cases_filtered = cases_filtered[
        cases_filtered["status"].isin(selected_statuses)
    ]

if search_text:
    cases_filtered = cases_filtered[
        cases_filtered["test_name"].str.contains(search_text, case=False, na=False)
    ]

exec_map = exec_filtered[["id", "suite_name", "execution_date"]].set_index("id")

display = cases_filtered.copy()
display["suite"] = display["execution_id"].map(exec_map["suite_name"])
display["data"] = pd.to_datetime(
    display["execution_id"].map(exec_map["execution_date"]), format="mixed"
).dt.strftime("%d/%m/%Y")

display["status_exibido"] = display.apply(
    lambda r: (
        f"{r['overridden_status']} (override)"
        if r["has_override"]
        else r["status"]
    ),
    axis=1,
)

display = display.sort_values(["data", "suite", "test_name"])

st.subheader(" Casos de Teste")
st.caption(
    f"{len(display)} casos encontrados | "
    f"{display['has_override'].sum()} com override"
)

for idx, row in display.iterrows():
    is_overridden = row["has_override"]
    border_color = STATUS_COLORS.get(
        row["overridden_status"] if is_overridden else row["status"], "#ccc"
    )

    with st.container():
        cols = st.columns([4, 2, 1, 1, 1])
        with cols[0]:
            label = f"{row['test_name']}"
            if is_overridden:
                label += f" ️"
            st.markdown(f"**{label}**")
            st.caption(f"{row['suite']} | {row['data']}")
        with cols[1]:
            if is_overridden:
                st.markdown(
                    f"<span style='color:#888'>Original:</span> "
                    f"<span style='color:{STATUS_COLORS.get(row['status'], '#888')};text-decoration:line-through'>"
                    f"{row['status']}</span>"
                    f"<br>"
                    f"<span style='color:{STATUS_COLORS.get(row['overridden_status'], '#2ecc71')};font-weight:bold'>"
                    f"{row['overridden_status']}</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<span style='color:{STATUS_COLORS.get(row['status'], '#888')};font-weight:bold'>"
                    f"{row['status']}</span>",
                    unsafe_allow_html=True,
                )
            if is_overridden and pd.notna(row.get("reason")) and row["reason"]:
                st.caption(f" Motivo: {row['reason']}")
        with cols[2]:
            if st.button("✏️", key=f"edit_{row['id']}", help="Editar status"):
                st.session_state.edit_test_case_id = int(row["id"])
                st.session_state.edit_execution_id = int(row["execution_id"])
                st.session_state.edit_test_name = row["test_name"]
                st.session_state.edit_original_status = row["status"]
                st.session_state.edit_current_override = (
                    row["overridden_status"] if is_overridden else ""
                )
                st.session_state.edit_current_reason = (
                    row["reason"] if is_overridden and pd.notna(row["reason"]) else ""
                )
                st.rerun()
        with cols[3]:
            if is_overridden:
                if st.button("✖️", key=f"del_{row['id']}", help="Remover override"):
                    success = delete_status_override_by_test_case(int(row["id"]))
                    if success:
                        st.success("Override removido!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Erro ao remover override.")
        with cols[4]:
            pass

        st.markdown("---")


if "edit_test_case_id" in st.session_state:
    tc_id = st.session_state.edit_test_case_id
    exec_id = st.session_state.edit_execution_id
    test_name = st.session_state.edit_test_name
    orig_status = st.session_state.edit_original_status
    current_override = st.session_state.edit_current_override
    current_reason = st.session_state.edit_current_reason

    with st.sidebar:
        st.subheader("✏️ Editar Status")
        st.divider()

        st.info(f"**Teste:** {test_name}")
        st.caption(f"Status original: **{orig_status}**")

        with st.form("edit_override_form"):
            new_status = st.selectbox(
                "Novo Status",
                STATUS_OPTIONS,
                index=(
                    STATUS_OPTIONS.index(current_override)
                    if current_override in STATUS_OPTIONS
                    else STATUS_OPTIONS.index(orig_status)
                    if orig_status in STATUS_OPTIONS
                    else 0
                ),
            )

            reason = st.text_area(
                "Motivo (opcional)",
                value=current_reason,
                placeholder="Ex: Falso positivo, corrigido em outra build...",
                height=80,
            )

            st.divider()

            col_salvar, col_cancelar = st.columns(2)

            with col_salvar:
                salvar = st.form_submit_button("💾 Salvar", use_container_width=True)

            with col_cancelar:
                cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)

            if salvar:
                if new_status == orig_status and not current_override:
                    st.warning(
                        "O status selecionado é igual ao original. "
                        "Nenhum override necessário."
                    )
                else:
                    success = set_status_override(
                        test_case_id=tc_id,
                        execution_id=exec_id,
                        original_status=orig_status,
                        overridden_status=new_status,
                        reason=reason if reason else None,
                    )
                    if success:
                        st.success("✅ Override salvo com sucesso!")
                        del st.session_state.edit_test_case_id
                        del st.session_state.edit_execution_id
                        del st.session_state.edit_test_name
                        del st.session_state.edit_original_status
                        del st.session_state.edit_current_override
                        del st.session_state.edit_current_reason
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ Erro ao salvar override.")

            if cancelar:
                del st.session_state.edit_test_case_id
                del st.session_state.edit_execution_id
                del st.session_state.edit_test_name
                del st.session_state.edit_original_status
                del st.session_state.edit_current_override
                del st.session_state.edit_current_reason
                st.rerun()


st.divider()
st.caption(
    "Desenvolvido com Streamlit  |  Dados: Supabase  |  Módulo: Overrides de Status"
)
