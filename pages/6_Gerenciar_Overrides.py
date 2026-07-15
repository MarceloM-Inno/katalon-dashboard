import os
import math
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

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
ITEMS_PER_PAGE = 20
STATUS_COLORS = {
    "PASSED": "#2ecc71",
    "FAILED": "#e74c3c",
    "ERROR": "#f39c12",
    "SKIPPED": "#95a5a6",
}


@st.cache_data(ttl=60, show_spinner="Carregando dados...")
def get_execs(projeto):
    return load_executions(projeto)


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

if "override_flash" in st.session_state:
    msg, msg_type = st.session_state.pop("override_flash")
    if msg_type == "success":
        st.success(msg)
    elif msg_type == "error":
        st.error(msg)
    elif msg_type == "warning":
        st.warning(msg)

exec_df = get_execs(projeto)

if not exec_df.empty:
    exec_df["suite_name_normalized"] = exec_df["suite_name"].apply(normalize_suite_name)

if exec_df.empty:
    st.warning("Nenhum dado encontrado para o projeto selecionado.")
    st.stop()


overrides_df = load_status_overrides()

st.sidebar.header(" Filtros")

min_date = exec_df["execution_date"].min().date()
max_date = exec_df["execution_date"].max().date()
hoje = date.today()
segunda = hoje - timedelta(days=hoje.weekday())
padrao_inicio = max(segunda, min_date)
padrao_fim = min(hoje, max_date)
if padrao_inicio > padrao_fim:
    padrao_inicio = padrao_fim

date_range = st.sidebar.date_input(
    "Período",
    value=(padrao_inicio, padrao_fim),
    min_value=min_date,
    max_value=max_date,
)

suites = sorted(exec_df["suite_name"].unique())
selected_suites = []
st.sidebar.markdown("**Suites**")
suite_display_map = build_suite_display_map(exec_df["suite_name"].unique().tolist())
for norm_name in suite_display_map:
    display_name = suite_display_map[norm_name]
    if st.sidebar.checkbox(display_name, value=True, key=f"suite_{norm_name}"):
        selected_suites.append(norm_name)

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
    exec_filtered = exec_filtered[exec_filtered["suite_name_normalized"].isin(selected_suites)]

exec_ids = exec_filtered["id"].tolist()
cases_filtered = load_cases_by_exec_ids(exec_ids)

if cases_filtered.empty:
    st.warning("Nenhum caso de teste encontrado para os filtros selecionados.")
    st.stop()

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


@st.dialog("Editar Status do Teste", width="medium", icon="✏️")
def edit_override_dialog(tc_id, exec_id, test_name, orig_status, current_override, current_reason):
    st.info(f"**Teste:** {test_name}")
    st.caption(f"Status original: {orig_status}")

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
                st.session_state.override_flash = ("Nenhum override necessário.", "warning")
                st.rerun()
            else:
                success = set_status_override(
                    test_case_id=tc_id,
                    execution_id=exec_id,
                    original_status=orig_status,
                    overridden_status=new_status,
                    reason=reason if reason else None,
                )
                if success:
                    st.session_state.override_flash = ("Override salvo com sucesso!", "success")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.session_state.override_flash = ("Erro ao salvar override.", "error")
                    st.rerun()

        if cancelar:
            st.rerun()

st.subheader(" Casos de Teste")
st.caption(
    f"{len(display)} casos encontrados | "
    f"{display['has_override'].sum()} com override"
)

total_items = len(display)
total_pages = max(1, math.ceil(total_items / ITEMS_PER_PAGE))

if "page_overrides" not in st.session_state:
    st.session_state.page_overrides = 1
if st.session_state.page_overrides > total_pages:
    st.session_state.page_overrides = total_pages

page = st.session_state.page_overrides
start_idx = (page - 1) * ITEMS_PER_PAGE
end_idx = start_idx + ITEMS_PER_PAGE
display_page = display.iloc[start_idx:end_idx]

col_prev, col_info, col_next = st.columns([1, 2, 1])
with col_prev:
    if page > 1:
        if st.button("← Anterior", use_container_width=True):
            st.session_state.page_overrides = page - 1
            st.rerun()
with col_info:
    start_item = start_idx + 1
    end_item = min(end_idx, total_items)
    st.markdown(f"<p style='text-align:center;margin-top:0.5rem'>A mostrar {start_item}-{end_item} de {total_items} testes</p>", unsafe_allow_html=True)
with col_next:
    if page < total_pages:
        if st.button("Próximo →", use_container_width=True):
            st.session_state.page_overrides = page + 1
            st.rerun()

for idx, row in display_page.iterrows():
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
                edit_override_dialog(
                    tc_id=int(row["id"]),
                    exec_id=int(row["execution_id"]),
                    test_name=row["test_name"],
                    orig_status=row["status"],
                    current_override=row["overridden_status"] if is_overridden else "",
                    current_reason=row["reason"] if is_overridden and pd.notna(row["reason"]) else "",
                )
        with cols[3]:
            if is_overridden:
                if st.button("✖️", key=f"del_{row['id']}", help="Remover override"):
                    success = delete_status_override_by_test_case(int(row["id"]))
                    if success:
                        st.session_state.override_flash = ("Override removido!", "success")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.session_state.override_flash = ("Erro ao remover override.", "error")
                        st.rerun()
        with cols[4]:
            pass

        st.markdown("---")

if total_pages > 1:
    col_prev2, col_info2, col_next2 = st.columns([1, 2, 1])
    with col_prev2:
        if page > 1:
            if st.button("← Anterior", use_container_width=True, key="page_prev_bottom"):
                st.session_state.page_overrides = page - 1
                st.rerun()
    with col_info2:
        start_item = start_idx + 1
        end_item = min(end_idx, total_items)
        st.markdown(f"<p style='text-align:center;margin-top:0.5rem'>A mostrar {start_item}-{end_item} de {total_items} testes</p>", unsafe_allow_html=True)
    with col_next2:
        if page < total_pages:
            if st.button("Próximo →", use_container_width=True, key="page_next_bottom"):
                st.session_state.page_overrides = page + 1
                st.rerun()


st.divider()
st.caption(
    "Desenvolvido com Streamlit  |  Dados: Supabase  |  Módulo: Overrides de Status"
)
