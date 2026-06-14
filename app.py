import pandas as pd
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Screener Estratégico", layout="wide")

# --- CSS FORÇADO PARA ESTILIZAÇÃO ---
# Estamos mirando nos elementos internos do Streamlit (data-testid)
css_estilo = """
<style>
/* Fundo da página */
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

/* Estilização do cabeçalho do Expander */
[data-testid="stExpander"] div[role="button"] {
    background-color: #0e1621 !important; /* Azul muito escuro */
    border: 1px solid #3498db !important; /* Borda azul neon */
    border-radius: 10px !important;
    padding: 15px !important;
    font-size: 18px !important; /* Fonte maior */
    font-weight: bold !important;
    color: #ffffff !important;
    transition: 0.3s;
}

/* Efeito ao passar o mouse */
[data-testid="stExpander"] div[role="button"]:hover {
    background-color: #1a2a3a !important;
    border: 1px solid #ffffff !important;
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

st.markdown("---")

# --- LISTAGEM DE ATIVOS ---
if df_f.empty:
    st.warning("Nenhum ativo encontrado.")
else:
    for _, row in df_f.iterrows():
        cot = formatar_cotacao(row['Cotação atual'])
        pl = formatar_pl(row['P/L PROJETADO'])
        dy = formatar_yield(row['Dividend Yield bruto estimado'])
        setor = row['SETOR']
        
        # Título formatado
        titulo = f"🚀 {row['CÓDIGO']}    |    {cot}    |    P/L: {pl}    |    DY: {dy}    |    Setor: {setor}"
        
        with st.expander(titulo):
            c1_exp, c2_exp, c3_exp = st.columns(3)
            c1_exp.metric("Cotação", cot)
            c2_exp.metric("P/L Proj.", pl)
            c3_exp.metric("Dividend Yield", dy)
            
            st.markdown("---")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("#### 📊 Valuation")
                st.markdown(f"**P/L Médio (10a):** {row.get('P/L médio (últ. 10 anos)', '-')}")
                st.markdown(f"**LL Projetado:** {row.get('LL PROJETADO', '-')}")
                st.markdown(f"**Valor de Mercado:** {row.get('VALOR DE MERCADO', '-')}")
                st.markdown(f"**⭐ RESULTADO 2026 (1/4):** {row.get('RESULTADO 2026 (1/4)', '-')}")
                
            with col2:
                st.markdown("#### 💰 Dividendos")
                st.markdown(f"**Payout:** {row.get('PAYOUT', '-')}")
                st.markdown(f"**LPA Est.:** {row.get('LPA ESTIMADO', '-')}")
                st.markdown(f"**Div. Bruto Proj.:** {row.get('Dividendo por ação bruto projetado', '-')}")
                
            with col3:
                st.markdown("#### ⚙️ Operacional")
                st.markdown(f"**Setor:** {row.get('SETOR', '-')}")
                st.markdown(f"**Dívida
