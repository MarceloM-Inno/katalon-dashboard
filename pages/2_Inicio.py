import streamlit as st

PROJETOS = {
    "ONEY": {"cor": "#1f77b4"},
    "BNPL": {"cor": "#ff7f0e"},
}

st.markdown(
    "<h1 style='text-align: center; margin-bottom: 2rem;'>"
    " Dashboard de Testes - Katalon</h1>",
    unsafe_allow_html=True,
)

st.markdown("### Selecione um projeto:")

cols = st.columns(2)
for i, (nome, info) in enumerate(PROJETOS.items()):
    with cols[i]:
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
                <h2 style='margin: 0.5rem 0;'>{nome}</h2>
                <p style='color: #888;'>Clique para acessar o dashboard</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Acessar {nome}", key=f"btn_{nome}", use_container_width=True):
            st.session_state.projeto = nome
            st.switch_page("pages/0_Graficos.py")
