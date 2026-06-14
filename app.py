import pandas as pd
import streamlit as st

# Configuração da página
st.set_page_config(page_title="Screener Estratégico", layout="wide")

# --- CONFIGURAÇÃO DO FUNDO PERSONALIZADO (SEM CORTAR O NOME) ---
# Usamos a URL direta da imagem que você já tem no seu repositório
link_da_imagem = "https://raw.githubusercontent.com/DCS1986/PAINEL-ARBITRAGEM/main/1500x500.jpg"

page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("{link_da_imagem}");
    background-size: contain; /* Tenta encaixar a imagem inteira */
    background-position: top center; /* Centraliza horizontalmente e fixa no topo */
    background-repeat: no-repeat; /* Não repete a imagem */
    background-attachment: fixed; /* O fundo não rola com a página */
}}
[data-testid="stAppViewContainer"]::before {{
    content: "";
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0, 0, 0, 0.4); /* Uma névoa mais leve (0.4) para a imagem ficar mais nítida */
}}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# --- FUNÇÕES DE UTILIDADE ---
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
        
        # Criação das colunas numéricas para filtro
        df['pl_num'] = df['P/L PROJETADO'].apply(limpar_valor)
        df['dy_num'] = df['Dividend Yield bruto estimado'].apply(limpar_valor)
        df['div_num'] = df['Dívida líquida/EBITDA'].apply(limpar_valor)
        df['cagr_num'] = df['CAGR lucros (últ. 5 anos)'].apply(limpar_valor)
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")
        return pd.DataFrame()

df = carregar_dados()

# --- SIDEBAR (FILTROS) ---
st.sidebar.header("🎯 Filtros Quantitativos")

# Chave para ativar ou desativar os filtros numéricos
ativar_filtros = st.sidebar.checkbox("✅ Ativar Filtros Quantitativos", value=False)

busca_ticker = st.sidebar.text_input("🔍 Buscar por Ticker:").strip().upper()
setores_disponiveis = sorted(df['SETOR'].unique().tolist())
filtro_setor = st.sidebar.multiselect("🏢 Filtrar por Setor:", setores_disponiveis)

# Os sliders ficam aqui, mas só serão usados se o checkbox estiver marcado
max_pl = st.sidebar.slider("P/L abaixo de:", 0.0, 50.0, 20.0)
min_dy = st.sidebar.slider("Dividend Yield acima de (%)", 0.0, 20.0, 6.0)
max_div = st.sidebar.slider("Dívida Líq./EBITDA abaixo de:", 0.0, 10.0, 3.0)
min_cagr = st.sidebar.slider("CAGR Lucros acima de (%)", 0.0, 50.0, 10.0)

# --- LÓGICA DE FILTRAGEM ---
# Começamos com a lista completa
df_f = df.copy()

# Aplica filtros numéricos SOMENTE se o checkbox estiver marcado
if ativar_filtros:
    df_f = df_f[
        (df_f['pl_num'] <= max_pl) & 
        (df_f['dy_num'] >= min_dy) &
        (df_f['div_num'] <= max_div) &
        (df_f['cagr_num'] >= min_cagr)
    ]

# Aplica filtros de texto e setor (estes funcionam sempre)
if busca_ticker:
    df_f = df_f[df_f['CÓDIGO'].str.contains(busca_ticker)]
if filtro_setor:
    df_f = df_f[df_f['SETOR'].isin(filtro_setor)]

# --- CABEÇALHO DO DASHBOARD ---
# Vamos dar um "pulo" no topo para o título não esconder o seu nome
st.markdown("<br><br>", unsafe_allow_html=True)
st.title("🎯 Painel de Arbitragem Profissional")
c1, c2, c3 = st.columns(3)
c1.metric("Total de Ativos", len(df))
c2.metric("Ativos Filtrados", len(df_f))
c3.metric("Média DY Filtrado", f"{df_f['dy_num'].mean():.2f}%" if not df_f.empty else "0%")

st.markdown("---")

# --- LISTAGEM ---
if df_f.empty:
    st.warning("Nenhum ativo encontrado com os critérios atuais.")
else:
    for _, row in df_f.iterrows():
        cot = formatar_cotacao(row['Cotação atual'])
        pl = formatar_pl(row['P/L PROJETADO'])
        dy = formatar_yield(row['Dividend Yield bruto estimado'])
        
        titulo = f"🏦 **{row['CÓDIGO']}** | {cot} | P/L: {pl} | DY: {dy}"
        
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
                st.markdown(f"**Dívida Líq/EBITDA:** {row.get('Dívida líquida/EBITDA', '-')}")
                st.markdown(f"**CAGR Lucros:** {row.get('CAGR lucros (últ. 5 anos)', '-')}")
                st.markdown(f"**Nº Ações:** {row.get('Nº AÇÕES', '-')}")
