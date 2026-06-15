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

# --- FUNÇÕES AUXILIARES ---
def limpar_valor(valor):
    try:
        s = str(valor).replace('%', '').replace(',', '.').replace('R$', '').replace('x', '').strip()
        return float(s)
    except:
        return 0.0

def formatar_pl_exibir(valor):
    # Garante que apareça o 'x' no final
    val_limpo = limpar_valor(valor)
    return f"{val_limpo:.1f}x"

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
            return data, f"R$ {valor:.4f}" # 4 casas decimais conforme pedido
        return "-", "-"
    except:
        return "Erro", "-"

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

if df_f.empty:
    st.warning("Nenhum ativo encontrado.")
else:
    for _, row in df_f.iterrows():
        # Formatação básica
        cot = formatar_cotacao(row.get('Cotação atual', '0'))
        pl_exib = formatar_pl_exibir(row.get('P/L PROJETADO', '0'))
        dy_exib = str(row.get('Dividend Yield bruto estimado', '0'))
        
        # Cor condicional para o DY na lista
        if row['dy_num'] > 8:
            dy_display = f":green[{dy_exib}]"
        else:
            dy_display = dy_exib
            
        titulo = f"🏦 **{row.get('CÓDIGO', 'N/A')}** | {cot} | P/L: {pl_exib} | DY: {dy_display} | Setor: {row.get('SETOR', '-')}"
        
        with st.expander(titulo):
            c1_exp, c2_exp, c3_exp = st.columns(3)
            c1_exp.metric("Cotação", cot)
            c2_exp.metric("P/L Projetado", pl_exib)
            c3_exp.metric("Dividend Yield", dy_exib)
            
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 📊 Valuation")
                pl_med = formatar_pl_exibir(row.get('P/L médio (últ. 10 anos)', '-'))
                st.markdown(f"**P/L Médio (10 anos):** {pl_med}")
                st.markdown(f"**LL Projetado:** {row.get('LL PROJETADO', '-')}")
                st.markdown(f"**Valor de Mercado:** {row.get('VALOR DE MERCADO', '-')}")
                
            with col2:
                st.markdown("#### 💰 Dividendos")
                st.markdown(f"**Dividend Yield:** {dy_exib}")
                st.markdown(f"**Payout:** {row.get('PAYOUT', '-')}")
                st.markdown(f"**LPA Est.:** {row.get('LPA ESTIMADO', '-')}")
                st.markdown(f"**Div. Proj.:** {row.get('Dividendo por ação bruto projetado', '-')}")
                
            with col3:
                st.markdown("#### ⚙️ Operacional")
                dt, val = get_info_dividendos(row.get('CÓDIGO', ''))
                st.markdown(f"**Dívida Líq/EBITDA:** {row.get('Dívida líquida/EBITDA', '-')}")
                st.markdown(f"**CAGR Lucros:** {row.get('CAGR lucros (últ. 5 anos)', '-')}")
                st.markdown(f"**Últ. Div (YF):** {val}")
                st.markdown(f"**Data Ex-Div:** {dt}")
