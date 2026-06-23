"""
app_score.py - Demonstracao do Score de Confluencia do RADAR.
Suba no GitHub + Streamlit Cloud junto com cvm_insiders.py e logica_score.py.
requirements.txt: streamlit, pandas, requests
"""

import streamlit as st
import pandas as pd

from cvm_insiders import baixar_vlmo
from logica_score import score_confluencia, sinais_cvm, PESOS

st.set_page_config(page_title="Score de Confluencia | RADAR", layout="wide")
st.title("Score de Confluência")
st.caption(
    "Sinais oficiais de insiders, controladores e recompra cruzados num só número — "
    "com grau de concordância. Fonte: CVM — Dados Abertos."
)

ano = st.sidebar.number_input("Ano de referência", min_value=2021, max_value=2030, value=2026)
meses = st.sidebar.select_slider("Janela (meses)", options=[3, 6, 12], value=6)


@st.cache_data(ttl=60 * 60 * 12, show_spinner="Baixando dados da CVM...")
def carregar(ano: int) -> pd.DataFrame:
    return baixar_vlmo(ano)


try:
    df = carregar(int(ano))
except Exception as e:
    st.error(f"Não consegui baixar o arquivo da CVM: {e}")
    st.stop()

res = score_confluencia(df, meses=int(meses))


def cor_score(v):
    if v > 5:
        return "background-color: #1b5e20; color: white"
    if v < -5:
        return "background-color: #b71c1c; color: white"
    return "background-color: #424242; color: #ddd"


st.subheader(f"Ranking — janela de {meses} meses")
st.dataframe(
    res.style.map(cor_score, subset=["score"]),
    use_container_width=True, hide_index=True,
)

with st.expander("Como ler / valores brutos por papel (R$)"):
    st.write(
        "**Score**: soma ponderada dos sinais, de -100 a +100. "
        "**Concordância** X/N: quantos sinais apontam no mesmo sentido do score. "
        "4/4 = convicção robusta; 3/5 = sinais em conflito, leitura ambígua."
    )
    st.write("Pesos atuais:", PESOS)
    st.dataframe(sinais_cvm(df, meses=int(meses)), use_container_width=True, hide_index=True)

st.caption(
    "Sinais de valuation e dividend safety entram quando integrado ao RADAR "
    "(parâmetro `extras` em score_confluencia). Fonte: CVM — Dados Abertos (ODbL)."
)
