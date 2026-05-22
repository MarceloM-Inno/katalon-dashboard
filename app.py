import streamlit as st

st.set_page_config(
    page_title="Dashboard de Testes - Katalon",
    page_icon="",
    layout="wide",
)

PROJETOS = {
    "ONEY": {"cor": "#1f77b4", "icone": ""},
    "BNPL": {"cor": "#ff7f0e", "icone": ""},
}


def show_sidebar_projeto():
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Projeto ativo:** {st.session_state.projeto}")
    if st.sidebar.button(" Trocar Projeto"):
        del st.session_state.projeto
        st.rerun()


if "projeto" not in st.session_state:
    st.markdown(
        "<h1 style='text-align: center; margin-bottom: 2rem;'>"
        " Dashboard de Testes - Katalon</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; font-size: 1.2rem; color: #888;'>"
        "Selecione um projeto para visualizar os dados</p>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    for i, (nome, info) in enumerate(PROJETOS.items()):
        col = col1 if i == 0 else col2
        with col:
            st.markdown(
                f"""
                <div style='
                    background: {info['cor']}15;
                    border: 2px solid {info['cor']};
                    border-radius: 16px;
                    padding: 2rem;
                    text-align: center;
                    margin: 0.5rem;
                '>
                    <div style='font-size: 4rem;'>{info['icone']}</div>
                    <h2 style='margin: 0.5rem 0;'>{nome}</h2>
                    <p style='color: #888;'>Clique para acessar o dashboard</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Acessar {nome}", key=f"btn_{nome}", use_container_width=True):
                st.session_state.projeto = nome
                st.rerun()

else:
    graficos = st.Page(
        "pages/0_Graficos.py",
        title="Gráficos",
    )
    execucoes = st.Page(
        "pages/1_Execucoes_Diarias.py",
        title="Execuções Diárias",
    )

    show_sidebar_projeto()

    pg = st.navigation([graficos, execucoes])
    pg.run()
