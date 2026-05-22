import streamlit as st

st.set_page_config(
    page_title="Dashboard de Testes - Katalon",
    page_icon="",
    layout="wide",
)

graficos = st.Page(
    "Graficos.py",
    title="Gráficos",
)

execucoes = st.Page(
    "pages/1_Execucoes_Diarias.py",
    title="Execuções Diárias",
)

pg = st.navigation([graficos, execucoes])
pg.run()
