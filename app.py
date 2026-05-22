import streamlit as st

st.set_page_config(
    page_title="Dashboard de Testes - Katalon",
    page_icon="",
    layout="wide",
)

graficos = st.Page(
    "pages/0_Graficos.py",
    title="Gráficos",
    icon="",
)

execucoes = st.Page(
    "pages/1_Execucoes_Diarias.py",
    title="Execuções Diárias",
    icon="",
)

pg = st.navigation([graficos, execucoes])
pg.run()
