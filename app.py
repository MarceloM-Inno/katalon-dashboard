import streamlit as st

st.set_page_config(
    page_title="Dashboard de Testes - Katalon",
    page_icon="",
    layout="wide",
)

inicio = st.Page("pages/2_Inicio.py", title="Início")
graficos = st.Page("pages/0_Graficos.py", title="Gráficos")
execucoes = st.Page("pages/1_Execucoes_Diarias.py", title="Execuções Diárias")
cadastro = st.Page("pages/3_Manuais_Cadastro.py", title="Cadastro de Projetos")
overrides = st.Page("pages/6_Gerenciar_Overrides.py", title="Overrides de Status")

pg = st.navigation([inicio, graficos, execucoes, cadastro, overrides])
pg.run()
