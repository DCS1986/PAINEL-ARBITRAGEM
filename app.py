import pandas as pd
import streamlit as st
import yfinance as yf

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Screener Estratégico", layout="wide")

# --- CONFIGURAÇÃO DO FUNDO ---
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

def limpar_valor_resultado(valor):
    """Converte 'R$ 1,5 bi' ou 'R$ 500 mi' para número real"""
    s = str(valor).lower().replace('r$', '').replace(',', '.').strip()
    mult = 1
    if 'bi' in s: mult = 1_000_000_000
    elif 'mi' in s: mult = 1_000_000
    s_clean = s.replace('bi', '').replace('mi', '').strip()
    try: return float(s_clean) * mult
    except: return 0.0

def formatar_cotacao(valor):
    try:
        s = str(valor).replace('R$', '').replace(',', '.').strip()
        return f"R$ {s}"
    except:
        return "R$ 0,00"

def formatar_pl(valor):
    s = str(valor).replace('x', '').replace(',', '.').strip()
    return f"{s}x"

def formatar_yield(valor):
    s = str(valor).replace('%', '').replace(',', '.').strip()
    return f"{s}%"

@st.cache_data(ttl=86400)
def get_dados_yahoo(ticker):
    """Busca dividendos, ROE, Margem, 52 semanas e Beta do Yahoo Finance"""
    try:
        stock = yf.Ticker(f"{ticker}.SA")
        info = stock.info
        
        # Dividendos
        divs = stock.dividends
        data_ex = divs.index[-1].strftime('%d/%m/%Y') if not divs.empty else "-"
        valor_div = f"R$ {divs.iloc[-1]:.4f}" if not divs.empty else "-"
        
        # Métricas Financeiras
        roe = info.get('returnOnEquity', 0)
        margem = info.get('profitMargins', 0)
        beta = info.get('beta', 0)
        
        roe_str = f"{roe*100:.1f}%" if roe else "-"
        margem_str = f"{margem*100:.1f}%" if margem else "-"
        beta_str = f"{beta:.2f}" if beta else "N/A"
        
        # Preços 52 semanas
        low52 = info.get('fiftyTwoWeekLow', 0)
        high52 = info.get('fiftyTwoWeekHigh', 0)
        low_str = f"R$ {low52:.2f}" if low52 else "-"
        high_str = f"R$ {high52:.2f}" if high52 else "-"
        
        return data_ex, valor_div, roe_str, margem_str, low_str, high_str, beta_str
    except:
        return "-", "-", "-", "-", "-", "-", "N/A"

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
        # Conversão para cálculo da barra de progresso
        df['res_val_num'] = df['RESULTADO 2026 (1/4)'].apply(limpar_valor_resultado)
        
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

c1, c2 = st.columns(2)
c1.metric("Total de Ativos", len(df))
c2.metric("Ativos Filtrados", len(df_f))

# LÓGICA DE DESTAQUES
if not df_f.empty:
    idx_max_dy = df_f['dy_num'].idxmax()
    ticker_max_dy = df_f.loc[idx_max_dy, 'CÓDIGO']
    val_max_dy = df_f.loc[idx_max_dy, 'Dividend Yield bruto estimado']
    
    df_pl_valido = df_f[df_f['pl_num'] > 0]
    if not df_pl_valido.empty:
        idx_min_pl = df_pl_valido['pl_num'].idxmin()
        ticker_min_pl = df_pl_valido.loc[idx_min_pl, 'CÓDIGO']
        val_min_pl = formatar_pl(df_pl_valido.loc[idx_min_pl, 'P/L PROJETADO'])
    else:
        ticker_min_pl, val_min_pl = "-", "-"

    c3, c4 = st.columns(2)
    c3.metric("🏆 Maior DY", ticker_max_dy, val_max_dy)
    c4.metric("📉 Menor P/L", ticker_min_pl, val_min_pl)

st.markdown("---")

# --- LISTAGEM DE ATIVOS ---
if df_f.empty:
    st.warning("Nenhum ativo encontrado.")
else:
    for _, row in df_f.iterrows():
        cot = formatar_cotacao(row['Cotação atual'])
        pl = formatar_pl(row['P/L PROJETADO'])
        dy_str = formatar_yield(row['Dividend Yield bruto estimado'])
        setor = row['SETOR']
        
        dy_display = f":green[{dy_str}]" if row['dy_num'] > 8 else dy_str
        
        titulo = f"🏦 **{row['CÓDIGO']}** | {cot} | P/L: {pl} | DY: {dy_display} | Setor: {setor}"
        
        with st.expander(titulo):
            c1_exp, c2_exp, c3_exp = st.columns(3)
            c1_exp.metric("Cotação", cot)
            c2_exp.metric("P/L Projetado", pl)
            c3_exp.metric("Dividend Yield", dy_str)
            
            st.markdown("---")
            
            # --- Busca dados do Yahoo ---
            dt, val, roe, margem, low, high, beta = get_dados_yahoo(row['CÓDIGO'])
            
            col1, col2, col3 = st.columns(3)
            
            # --- Coluna 1: Valuation ---
            with col1:
                st.markdown("#### 📊 Valuation")
                pl_medio = row.get('P/L médio (últ. 10 anos)', '-')
                pl_medio_formatado = f"{pl_medio}x" if pl_medio != '-' else "-"
                st.markdown(f"**P/L Médio (10 anos):** {pl_medio_formatado}")
                st.markdown(f"**LL Projetado:** {row.get('LL PROJETADO', '-')}")
                st.markdown(f"**Valor de Mercado:** {row.get('VALOR DE MERCADO', '-')}")
                
                # --- Barra de Progresso do Resultado ---
                valor_resultado_str = row.get('RESULTADO 2026 (1/4)', '-')
                val_num = row.get('res_val_num', 0)
                meta = 7_800_000_000
                progresso = min(val_num / meta, 1.0)
                porcentagem = int(progresso * 100)
                
                st.markdown(f"**⭐ RESULTADO 2026 (1/4):** <span style='color: #39FF14; font-weight: bold;'>{valor_resultado_str}</span>", unsafe_allow_html=True)
                st.progress(progresso)
                st.caption(f"Meta de R$ 7,8 bi: **{porcentagem}% alcançado**")
                
                st.markdown("---")
                st.markdown(f"**📉 Mínima (52 sem):** {low}")
                st.markdown(f"**📈 Máxima (52 sem):** {high}")
            
            # --- Coluna 2: Dividendos ---
            with col2:
                st.markdown("#### 💰 Dividendos")
                dy_valor_display = row.get('Dividend Yield bruto estimado', '-')
                dy_num = row.get('dy_num', 0)
                style_dy = "color: #39FF14; font-weight: bold;" if dy_num > 8 else ""
                st.markdown(f"**Dividend Yield:** <span style='{style_dy}'>{dy_valor_display}</span>", unsafe_allow_html=True)
                st.markdown(f"**Payout:** {row.get('PAYOUT', '-')}")
                st.markdown(f"**LPA Est.:** {row.get('LPA ESTIMADO', '-')}")
                st.markdown(f"**Div. Projetado:** {row.get('Dividendo por ação bruto projetado', '-')}")
                
                st.markdown("---")
                st.markdown(f"**📅 Data Ex:** {dt}")
                st.markdown(f"**💰 Valor Atual:** {val}")
                
            # --- Coluna 3: Operacional ---
            with col3:
                st.markdown("#### ⚙️ Operacional")
                st.markdown(f"**Setor:** {row.get('SETOR', '-')}")
                st.markdown(f"**Dívida Líq/EBITDA:** {row.get('Dívida líquida/EBITDA', '-')}")
                st.markdown(f"**CAGR Lucros:** {row.get('CAGR lucros (últ. 5 anos)', '-')}")
                
                st.markdown("---")
                st.markdown(f"**📊 Beta (vs IBOV):** {beta}")
                st.markdown(f"**📈 ROE:** {roe}")
                st.markdown(f"**📋 Margem Líq.:** {margem}")
