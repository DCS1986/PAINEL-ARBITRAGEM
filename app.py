import pandas as pd
import streamlit as st
import yfinance as yf

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Screener Estratégico", layout="wide")

# --- CSS E FUNDO ---
link_da_imagem = "https://raw.githubusercontent.com/DCS1986/PAINEL-ARBITRAGEM/main/1500x500.png"
page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("{link_da_imagem}");
    background-size: contain;
    background-position: top center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}
[data-testid="stAppViewContainer"]::before {{
    content: "";
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0, 0, 0, 0.7); 
}}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# --- FUNÇÕES ---
def limpar_valor(valor):
    try:
        s = str(valor).replace('%', '').replace(',', '.').replace('R$', '').strip()
        return float(s)
    except:
        return 0.0

def formatar_cotacao(valor):
    try:
        s = str(valor).replace('R$', '').replace(',', '.').strip()
        return f"R$ {s}"
    except:
        return "R$ 0,00"

@st.cache_data(ttl=3600)
def get_info_dividendos(ticker):
    try:
        stock = yf.Ticker(f"{ticker}.SA")
        divs = stock.dividends
        if not divs.empty:
            data = divs.index[-1].strftime('%d/%m/%Y')
            valor = divs.iloc[-1]
            return data, f"R$ {valor:.2f}"
        return "-", "-"
    except:
        return "-", "-"

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
        
        # Mapeamento de colunas para cálculo
        df['pl_num'] = df['P/L PROJETADO'].apply(limpar_valor)
        df['dy_num'] = df['Dividend Yield bruto estimado'].apply(limpar_valor)
        df['div_num'] = df['Dívida líquida/EBITDA'].apply(limpar_valor)
        df['cagr_num'] = df['CAGR lucros (últ. 5 anos)'].apply(limpar_valor)
        
        return df
    except:
        return pd.DataFrame()

df = carregar_dados()

# --- SIDEBAR ---
st.sidebar.header("🎯 Filtros Quantitativos")
ativar_filtros = st.sidebar.checkbox("✅ Ativar Filtros Quantitativos", value=False)
busca_ticker = st.sidebar.text_input("🔍 Buscar por Ticker:").strip().upper()
setores_disponiveis = sorted(df['SETOR'].unique().tolist()) if not df.empty else []
filtro_setor = st.sidebar.multiselect("🏢 Filtrar por Setor:", setores_disponiveis)

max_pl = st.sidebar.slider("P/L abaixo de:", 0.0, 50.0, 20.0)
min_dy = st.sidebar.slider("Dividend Yield acima de (%)", 0.0, 20.0, 6.0)
max_div = st.sidebar.slider("Dívida Líq./EBITDA abaixo de:", 0.0, 10.0, 3.0)
min_cagr = st.sidebar.slider("CAGR Lucros acima de (%)", 0.0, 50.0, 10.0)

# --- LÓGICA DE FILTROS ---
df_f = df.copy()
if ativar_filtros:
    df_f = df_f[(df_f['pl_num'] <= max_pl) & (df_f['dy_num'] >= min_dy) & (df_f['div_num'] <= max_div) & (df_f['cagr_num'] >= min_cagr)]
if busca_ticker:
    df_f = df_f[df_f['CÓDIGO'].str.contains(busca_ticker)]
if filtro_setor:
    df_f = df_f[df_f['SETOR'].isin(filtro_setor)]

# --- DASHBOARD ---
st.title("🎯 Radar de ações")

# --- LISTAGEM DE ATIVOS ---
if df_f.empty:
    st.warning("Nenhum ativo encontrado.")
else:
    for _, row in df_f.iterrows():
        cot = formatar_cotacao(row.get('Cotação atual', '0'))
        pl = str(row.get('P/L PROJETADO', '-'))
        dy = str(row.get('Dividend Yield bruto estimado', '-'))
        setor = row.get('SETOR', '-')
        
        titulo = f"🏦 **{row.get('CÓDIGO', 'N/A')}** | {cot} | P/L: {pl} | DY: {dy} | Setor: {setor}"
        
        with st.expander(titulo):
            # Header Expander
            c1_exp, c2_exp, c3_exp = st.columns(3)
            c1_exp.metric("Cotação", cot)
            c2_exp.metric("P/L Projetado", pl)
            c3_exp.metric("Dividend Yield", dy)
            
            st.markdown("---")
            
            # Detalhes (Restaurados conforme prints)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 📊 Valuation")
                st.markdown(f"**P/L Médio (10 anos):** {row.get('P/L médio (últ. 10 anos)', '-')}")
                st.markdown(f"**LL Projetado:** {row.get('LL PROJETADO', '-')}")
                st.markdown(f"**Valor de Mercado:** {row.get('VALOR DE MERCADO', '-')}")
                # Estilização especial conforme print
                res_2026 = row.get('RESULTADO 2026 (1/4)', '-')
                st.markdown(f"**⭐ RESULTADO 2026 (1/4):** <span style='color: #39FF14; font-weight: bold;'>{res_2026}</span>", unsafe_allow_html=True)
                
            with col2:
                st.markdown("#### 💰 Dividendos")
                st.markdown(f"**Dividend Yield:** {dy}")
                st.markdown(f"**Payout:** {row.get('PAYOUT', '-')}")
                st.markdown(f"**LPA Est.:** {row.get('LPA ESTIMADO', '-')}")
                st.markdown(f"**Div. Bruto Proj.:** {row.get('Dividendo por ação bruto projetado', '-')}")
                
            with col3:
                st.markdown("#### ⚙️ Operacional")
                st.markdown(f"**Setor:** {setor}")
                st.markdown(f"**Dívida Líq/EBITDA:** {row.get('Dívida líquida/EBITDA', '-')}")
                st.markdown(f"**CAGR Lucros:** {row.get('CAGR lucros (últ. 5 anos)', '-')}")
                st.markdown(f"**Nº Ações:** {row.get('Nº AÇÕES', '-')}")
                
                # Divs via API
                st.markdown("---")
                dt, val = get_info_dividendos(row.get('CÓDIGO', ''))
                st.markdown(f"**Últ. Div. (YF):** {val}")
                st.markdown(f"**Data Ex-Div:** {dt}")
