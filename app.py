import pandas as pd
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Screener Estratégico", layout="wide")

# --- CSS PARA DESTAQUE ---
# Mantendo o estilo escuro que você gosta
css = """
<style>
[data-testid="stAppViewContainer"] {
    background-image: url("https://raw.githubusercontent.com/DCS1986/PAINEL-ARBITRAGEM/main/1500x500.png");
    background-size: contain;
    background-position: top center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0, 0, 0, 0.7); 
}
[data-testid="stExpander"] div[role="button"] {
    background-color: #0e1621 !important;
    border: 1px solid #3498db !important;
    border-radius: 10px !important;
    color: #ffffff !important;
    font-weight: bold !important;
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# --- FUNÇÕES ---
def formatar_valor(valor):
    try:
        s = str(valor).replace('%', '').replace(',', '.').replace('R$', '').strip()
        return float(s)
    except:
        return 0.0

@st.cache_data(ttl=600)
def carregar_dados():
    try:
        spreadsheet_id = "1QM3xaaiZHleTJb8MEChy95LJSX3j3hLs8-ecQydMHYM"
        gid_id = "596101825"
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid_id}"
        df = pd.read_csv(url, header=None)
        
        idx = 0
        for i, row in df.iterrows():
            if "CÓDIGO" in [str(x).upper().strip() for x in row.values]:
                idx = i
                break
        
        df.columns = [str(c).strip() for c in df.iloc[idx]]
        df = df.iloc[idx + 1:].reset_index(drop=True)
        df = df.dropna(how='all')
        
        # Criação das colunas numéricas para filtro
        df['pl_num'] = df['P/L PROJETADO'].apply(formatar_valor)
        df['dy_num'] = df['Dividend Yield bruto estimado'].apply(formatar_valor)
        df['div_num'] = df['Dívida líquida/EBITDA'].apply(formatar_valor)
        df['cagr_num'] = df['CAGR lucros (últ. 5 anos)'].apply(formatar_valor)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

df = carregar_dados()

# --- SIDEBAR ---
st.sidebar.header("Filtros")
ativar_filtros = st.sidebar.checkbox("Ativar Filtros Quantitativos")
busca_ticker = st.sidebar.text_input("Buscar Ticker").upper()
setores = sorted(df['SETOR'].unique().tolist()) if not df.empty else []
filtro_setor = st.sidebar.multiselect("Setor", setores)

max_pl = st.sidebar.slider("P/L abaixo de", 0.0, 50.0, 20.0)
min_dy = st.sidebar.slider("DY acima de (%)", 0.0, 20.0, 6.0)
max_div = st.sidebar.slider("Dívida Líq/EBITDA abaixo de", 0.0, 10.0, 3.0)
min_cagr = st.sidebar.slider("CAGR Lucros acima de (%)", 0.0, 50.0, 10.0)

# --- LÓGICA DE FILTRAGEM ---
df_f = df.copy()
