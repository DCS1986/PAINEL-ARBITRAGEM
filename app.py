import pandas as pd
import streamlit as st

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Screener Estratégico", layout="wide")

# --- CSS PERSONALIZADO ---
css_estilo = """
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
    font-weight: bold !important;
    color: #ffffff !important;
}
</style>
"""
st.markdown(css_estilo, unsafe_allow_html=True)

# --- FUNÇÕES ---
def limpar_valor(valor):
    try:
        s = str(valor).replace('%', '').replace(',', '.').replace('R$', '').strip()
        return float(s)
    except:
        return 0.0

@st.cache_data(ttl=60)
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
        
        df['pl_num'] = df['P/L PROJETADO'].apply(limpar_valor)
        df['dy_num'] = df['Dividend Yield bruto estimado'].apply(limpar_valor)
        df['div_num'] = df['Dívida líquida/EBITDA'].apply(limpar_valor)
        df['cagr_num'] = df['CAGR lucros (últ. 5 anos)'].apply(limpar_valor)
        return df
    except:
        return pd.DataFrame()

df = carregar_dados()

# --- SIDEBAR ---
st.sidebar.header("🎯 Filtros")
if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

ativar_filtros = st.sidebar.checkbox("✅ Ativar Filtros", value=False)
busca_ticker = st.sidebar.text_input("🔍 Buscar por Ticker:").strip().upper()
setores_disponiveis = sorted(df['SETOR'].unique().tolist()) if not df.empty else []
filtro_setor = st.sidebar.multiselect("🏢 Filtrar por Setor:", setores_disponiveis)

max_pl = st.sidebar.slider("P/L abaixo de:", 0.0, 50.0, 20.0)
min_dy = st.sidebar.slider("DY acima de (%)", 0.0, 20.0, 6.0)
max_div = st.sidebar.slider("Dívida Líq./EBITDA abaixo de:", 0.0, 10.0, 3.0)
min_cagr = st.sidebar.slider("CAGR Lucros acima de (%)", 0.0, 50.0, 10.0)

# --- LÓGICA ---
df_f = df.copy()
if ativar_filtros:
    df_f = df_f[(df_f['pl_num'] <= max_pl) & (df_f['dy_num'] >= min_dy) & (df_f['div_num'] <= max_div) & (df_f['cagr_num'] >= min_cagr)]
if busca_ticker:
    df_f = df_f[df_f['CÓDIGO'].str.contains(busca_ticker)]
if filtro_setor:
    df_f = df_f[df_f['SETOR'].isin(filtro_setor)]

# --- DASHBOARD ---
st.title("🎯 Radar de ações")

# Linha 1: Métricas de Volume
c1, c2 = st.columns(2)
c1.metric("Total de Ativos", len(df))
c2.metric("Ativos Filtrados", len(df_f))

# Linha 2: Métricas de Destaque
if not df_f.empty:
    # Lógica de destaque
    idx_max_dy = df_f['dy_num'].idxmax()
    ticker_max_dy = df_f.loc[idx_max_dy, 'CÓDIGO']
    val_max_dy = df_f.loc[idx_max_dy, 'Dividend Yield bruto estimado']
    
    # Lógica de menor P/L (ignorando valores zero/nulos)
    df_pl_valido = df_f[df_f['pl_num'] > 0]
    if not df_pl_valido.empty:
        idx_min_pl = df_pl_valido['pl_num'].idxmin()
        ticker_min_pl = df_pl_valido.loc[idx_min_pl, 'CÓDIGO']
        val_min_pl = df_pl_valido.loc[idx_min_pl, 'P/L PROJETADO']
    else:
        ticker_min_pl, val_min_pl = "-", "-"

    c3, c4 = st.columns(2)
    c3.metric("🏆 Maior DY", ticker_max_dy, val_max_dy)
    c4.metric("📉 Menor P/L", ticker_min_pl, val_min_pl)

st.markdown("---")

# --- LISTAGEM ---
if df_f.empty:
    st.warning("Nenhum ativo encontrado.")
else:
    for _, row in df_f.iterrows():
        titulo = f"🚀 {row['CÓDIGO']} | R$ {row['Cotação atual']} | P/L: {row['P/L PROJETADO']} | DY: {row['Dividend Yield bruto estimado']}"
        with st.expander(titulo):
            c1_e, c2_e, c3_e = st.columns(3)
            c1_e.metric("Cotação", row['Cotação atual'])
            c2_e.metric("P/L", row['P/L PROJETADO'])
            c3_e.metric("DY", row['Dividend Yield bruto estimado'])
