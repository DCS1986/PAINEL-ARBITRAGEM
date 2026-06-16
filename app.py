import pandas as pd
import streamlit as st
import yfinance as yf
import requests

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Radar Fundamentalista", layout="wide")

# --- CONFIGURAÇÃO DO FUNDO ---
link_da_imagem = "https://raw.githubusercontent.com/DCS1986/PAINEL-ARBITRAGEM/main/1500x500.PNG"

page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("{link_da_imagem}");
    background-size: cover;
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

/* ---- ESTILOS DO GRÁFICO DE DY ---- */
.dy-bar-container {{
    display: flex;
    align-items: flex-end;
    gap: 8px;
    height: 110px;
    margin-top: 10px;
    padding: 0 4px;
}}
.dy-bar-wrap {{
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
}}
.dy-bar {{
    width: 100%;
    border-radius: 4px 4px 0 0;
    min-height: 6px;
}}
.dy-bar-label {{
    font-size: 12px;
    color: #bbb;
    margin-top: 5px;
    white-space: nowrap;
    font-weight: bold;
}}
.dy-bar-value {{
    font-size: 11px;
    color: #fff;
    margin-bottom: 4px;
    font-weight: bold;
}}

/* ---- ESTILOS DO SCORE ---- */
.score-badge {{
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: bold;
    font-size: 1.1em;
    margin-top: 4px;
}}

/* ---- CARDS DO TOPO ---- */
.top-card {{
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
}}
.top-card .label {{
    font-size: 0.78em;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
}}
.top-card .value {{
    font-size: 1.9em;
    font-weight: 800;
    color: #fff;
    line-height: 1.1;
}}
.top-card .sub {{
    font-size: 0.85em;
    color: #39FF14;
    margin-top: 4px;
    font-weight: bold;
}}

/* ---- SEPARADOR ENTRE ATIVOS ---- */
.ativo-sep {{
    height: 1px;
    background: linear-gradient(to right, transparent, rgba(255,255,255,0.08), transparent);
    margin: 4px 0;
}}
.asset-card {{
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 12px;
    padding: 12px 10px 10px 10px;
    text-align: center;
    margin-bottom: 4px;
}}
.asset-card:hover {{ background: rgba(255,255,255,0.09); border-color: rgba(57,255,20,0.4); }}
.asset-card .ac-logo {{ width:44px;height:44px;border-radius:50%;object-fit:cover;background:#fff;padding:2px;margin:0 auto 7px auto;display:block; }}
.asset-card .ac-ticker {{ font-size:0.95em;font-weight:800;color:#ffffff;letter-spacing:1px; }}
.asset-card .ac-cot {{ font-size:0.9em;color:#fff;font-weight:bold;margin-top:2px; }}
.asset-card .ac-var-pos {{ color:#39FF14;font-size:0.78em;font-weight:bold; }}
.asset-card .ac-var-neg {{ color:#FF4444;font-size:0.78em;font-weight:bold; }}
.asset-card .ac-var-neu {{ color:#FFD700;font-size:0.78em;font-weight:bold; }}
.asset-card .ac-row {{ display:flex;justify-content:space-between;margin-top:6px;font-size:0.8em;color:#fff;font-weight:bold;border-top:1px solid rgba(255,255,255,0.07);padding-top:6px; }}
.asset-card .ac-val {{ color:#fff;font-weight:bold;font-size:1.0em; }}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# --- FUNÇÕES UTILITÁRIAS ---
def limpar_valor(valor):
    try:
        s = str(valor).replace('%', '').replace(',', '.').replace('R$', '').strip()
        return float(s)
    except:
        return 0.0

def limpar_valor_resultado(valor):
    if pd.isna(valor) or str(valor).strip() == '-':
        return 0.0
    s = str(valor).replace('R$', '').replace('.', '').replace(' ', '')
    s = s.replace(',', '.')
    try:
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

# ---- Cor dinâmica da barra de progresso ----
def cor_progresso(porcentagem):
    if porcentagem >= 50:
        return "#39FF14"
    elif porcentagem >= 25:
        return "#FFD700"
    else:
        return "#FF4444"

# ---- Score Geral por Setor (0–10) ----
def classificar_setor(setor):
    s = str(setor).lower()
    if any(x in s for x in ['banco', 'financeiro', 'holding']):
        return 'banco'
    if any(x in s for x in ['seguro', 'segur']):
        return 'seguradora'
    if any(x in s for x in ['elétric', 'eletric', 'energia', 'saneamento', 'utilities']):
        return 'capital_intensivo'
    if any(x in s for x in ['papel', 'celulose', 'mineração', 'minera', 'petróleo', 'petro', 'óleo', 'cíclico']):
        return 'ciclica'
    return 'geral'

def calcular_score(dy_num, pl_num, div_ebitda_num, cagr_num, roe_num, margem_num, pvp_num=0, setor=''):
    categoria = classificar_setor(setor)
    score = 0.0

    if categoria == 'banco':
        # Bancos: P/VP e ROE têm muito peso; dívida irrelevante; margem distorce
        score += min(dy_num / 10.0, 1.0) * 2.0          # DY: 2.0
        score += min(roe_num / 25.0, 1.0) * 2.5          # ROE: 2.5 (mais importante)
        if pl_num > 0:
            score += max(0, (12 - pl_num) / 12.0) * 1.5  # P/L: 1.5 (referência menor pra bancos)
        if pvp_num > 0:
            score += max(0, (2.0 - pvp_num) / 2.0) * 2.0 # P/VP: 2.0 (muito relevante)
        score += min(cagr_num / 20.0, 1.0) * 1.0         # CAGR: 1.0
        score += max(0, (5 - div_ebitda_num) / 5.0) * 1.0 # Dívida: 1.0 (baixo peso)

    elif categoria == 'seguradora':
        # Seguradoras: ROE e DY dominam; P/VP irrelevante; dívida irrelevante
        score += min(dy_num / 10.0, 1.0) * 2.5           # DY: 2.5
        score += min(roe_num / 25.0, 1.0) * 3.0          # ROE: 3.0 (mais importante)
        if pl_num > 0:
            score += max(0, (15 - pl_num) / 15.0) * 2.0  # P/L: 2.0
        score += min(cagr_num / 20.0, 1.0) * 1.5         # CAGR: 1.5
        score += max(0, (5 - div_ebitda_num) / 5.0) * 1.0 # Dívida: 1.0 (baixo)

    elif categoria == 'capital_intensivo':
        # Elétricas, saneamento: dívida pode ser alta (aceita até 4x); DY e ROE importantes
        score += min(dy_num / 10.0, 1.0) * 2.5           # DY: 2.5
        score += min(roe_num / 20.0, 1.0) * 2.0          # ROE: 2.0
        if pl_num > 0:
            score += max(0, (18 - pl_num) / 18.0) * 1.5  # P/L: 1.5
        score += max(0, (4 - div_ebitda_num) / 4.0) * 2.0 # Dívida: 2.0 (aceita até 4x)
        score += min(cagr_num / 15.0, 1.0) * 1.0         # CAGR: 1.0
        if pvp_num > 0:
            score += max(0, (2.5 - pvp_num) / 2.5) * 1.0 # P/VP: 1.0

    elif categoria == 'ciclica':
        # Cíclicas (Vale, PETR, Klabin): P/L distorce muito — menor peso; DY e ROE lideram
        score += min(dy_num / 12.0, 1.0) * 3.0           # DY: 3.0 (proventos baseados em EBITDA)
        score += min(roe_num / 20.0, 1.0) * 2.5          # ROE: 2.5
        if pl_num > 0:
            score += max(0, (15 - pl_num) / 15.0) * 0.5  # P/L: 0.5 (mínimo — distorce)
        score += max(0, (3 - div_ebitda_num) / 3.0) * 2.0 # Dívida: 2.0
        score += min(cagr_num / 20.0, 1.0) * 1.0         # CAGR: 1.0
        if pvp_num > 0:
            score += max(0, (2.0 - pvp_num) / 2.0) * 1.0 # P/VP: 1.0

    else:
        # Geral: pesos balanceados
        score += min(dy_num / 10.0, 1.0) * 2.5           # DY: 2.5
        score += min(roe_num / 20.0, 1.0) * 2.0          # ROE: 2.0 (acima do CAGR)
        if pl_num > 0:
            score += max(0, (20 - pl_num) / 20.0) * 1.5  # P/L: 1.5
        score += max(0, (5 - div_ebitda_num) / 5.0) * 1.5 # Dívida: 1.5
        score += min(cagr_num / 20.0, 1.0) * 1.5         # CAGR: 1.5
        if pvp_num > 0:
            score += max(0, (3 - pvp_num) / 3.0) * 1.0   # P/VP: 1.0

    return round(min(score, 10.0), 1)

def badge_score(score):
    if score >= 7:
        cor_bg, cor_txt, label = "#1a3a1a", "#39FF14", "Ótimo"
    elif score >= 5:
        cor_bg, cor_txt, label = "#3a3a10", "#FFD700", "Bom"
    elif score >= 3:
        cor_bg, cor_txt, label = "#3a2010", "#FFA500", "Regular"
    else:
        cor_bg, cor_txt, label = "#3a1010", "#FF4444", "Fraco"
    return f"""
    <div style="display:flex; align-items:center; gap:10px; margin-top:6px;">
        <span class="score-badge" style="background:{cor_bg}; color:{cor_txt}; border:1px solid {cor_txt};">
            ⭐ Score: {score}/10
        </span>
        <span style="color:{cor_txt}; font-size:0.9em; font-weight:bold;">{label}</span>
    </div>"""

# ---- Gráfico de barras — Histórico DY ----
def mini_grafico_dy(historico_dy):
    if not historico_dy:
        return "<span style='color:#888; font-size:0.9em;'>Histórico indisponível</span>"
    max_val = max(historico_dy.values()) or 1
    barras = ""
    for ano, val in sorted(historico_dy.items()):
        altura = max(int((val / max_val) * 90), 6)
        cor = "#39FF14" if val >= 8 else "#1E90FF"
        barras += f"""
        <div class="dy-bar-wrap">
            <span class="dy-bar-value">{val:.1f}%</span>
            <div class="dy-bar" style="height:{altura}px; background:{cor};"></div>
            <span class="dy-bar-label">{ano}</span>
        </div>"""
    return f'<div class="dy-bar-container">{barras}</div>'

# ---- Mini gráfico de linha SVG — P/L e Lucro ----
def mini_grafico_linha(dados, cor, label_suffix="", altura=95, largura=420):
    if not dados or len(dados) < 2:
        return "<span style='color:#888; font-size:0.9em;'>Dados insuficientes</span>"

    itens = sorted(dados.items())
    anos  = [str(a) for a, _ in itens]
    vals  = [v for _, v in itens]

    min_v = min(vals)
    max_v = max(vals)
    span  = max_v - min_v if max_v != min_v else 1

    pad_x, pad_y = 38, 24
    w = largura - pad_x * 2
    h = altura  - pad_y * 2
    n = len(vals)

    pts = []
    for i, v in enumerate(vals):
        x = pad_x + (i / (n - 1)) * w
        y = pad_y + h - ((v - min_v) / span) * h
        pts.append((x, y))

    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area_pts = (
        f"{pts[0][0]:.1f},{pad_y + h} "
        + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        + f" {pts[-1][0]:.1f},{pad_y + h}"
    )
    grad_id = f"grad_{cor.replace('#', '')}"

    def fmt(v):
        if abs(v) >= 1_000_000_000:
            return f"{v / 1_000_000_000:.1f}B{label_suffix}"
        if abs(v) >= 1_000_000:
            return f"{v / 1_000_000:.0f}M{label_suffix}"
        return f"{v:.1f}{label_suffix}"

    val_labels = ""
    for i, (x, y) in enumerate(pts):
        anchor = "start" if i == 0 else ("end" if i == len(pts) - 1 else "middle")
        val_labels += (
            f'<text x="{x:.1f}" y="{y - 9:.1f}" text-anchor="{anchor}" '
            f'font-size="10" fill="{cor}" font-weight="bold">{fmt(vals[i])}</text>'
        )

    labels_x = ""
    for i, (x, _) in enumerate(pts):
        labels_x += (
            f'<text x="{x:.1f}" y="{altura - 2}" text-anchor="middle" '
            f'font-size="9" fill="#aaa" font-weight="bold">{anos[i]}</text>'
        )

    circles = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{cor}" '
        f'stroke="#111" stroke-width="1.5"/>'
        for x, y in pts
    )

    svg = f"""<svg viewBox="0 0 {largura} {altura}" width="100%" xmlns="http://www.w3.org/2000/svg" style="display:block;overflow:visible;">
  <defs>
    <linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{cor}" stop-opacity="0.30"/>
      <stop offset="100%" stop-color="{cor}" stop-opacity="0.03"/>
    </linearGradient>
  </defs>
  <polygon points="{area_pts}" fill="url(#{grad_id})" />
  <polyline points="{polyline}" fill="none" stroke="{cor}" stroke-width="2.5"
            stroke-linejoin="round" stroke-linecap="round"/>
  {circles}
  {val_labels}
  {labels_x}
</svg>"""

    return f"<div style='margin-top:8px; overflow:visible;'>{svg}</div>"


ICONES_SETOR = {
    "Bancos": "🏦",
    "Seguros": "🛡️",
    "Energia": "⚡",
    "Elétrico": "⚡",
    "Petróleo": "🛢️",
    "Óleo": "🛢️",
    "Mineração": "⛏️",
    "Saúde": "🏥",
    "Varejo": "🛒",
    "Shoppings": "🏬",
    "Telecomunicações": "📡",
    "Agronegócio": "🌾",
    "Serviços Financeiros": "💹",
    "Holding": "🏛️",
    "Transportes": "🚚",
    "Logística": "🚚",
    "Bens Industriais": "⚙️",
    "Construção": "🏗️",
    "Tecnologia": "💻",
    "Automóveis": "🚗",
    "Papel": "📄",
    "Alimentos": "🍽️",
    "Bebidas": "🍺",
    "Saneamento": "💧",
    "Utilities": "💡",
}

def icone_setor(setor):
    for chave, icone in ICONES_SETOR.items():
        if chave.lower() in str(setor).lower():
            return icone
    return "📊"

# ---- Logo via brapi ----
@st.cache_data(ttl=86400)
def get_logo_url(ticker):
    try:
        url = f"https://brapi.dev/api/quote/{ticker}?token=qX942ePxQaNWzSEs9gphZi"
        r = requests.get(url, timeout=8).json()
        if r.get('results'):
            return r['results'][0].get('logourl', '') or ''
    except:
        pass
    return ''

# ---- Busca de dados no Yahoo Finance ----
@st.cache_data(ttl=86400)
def get_dados_yahoo(ticker):
    try:
        stock = yf.Ticker(f"{ticker}.SA")
        info  = stock.info

        divs     = stock.dividends
        data_ex  = divs.index[-1].strftime('%d/%m/%Y') if not divs.empty else "-"
        valor_div = f"R$ {divs.iloc[-1]:.4f}" if not divs.empty else "-"

        preco_atual_iv = info.get('currentPrice') or info.get('regularMarketPrice', 0)
        preco_anterior = info.get('previousClose', 0)
        if preco_anterior and preco_atual_iv:
            variacao_dia = ((preco_atual_iv - preco_anterior) / preco_anterior) * 100
        else:
            variacao_dia = 0.0

        iv_str = "-"
        try:
            datas_opcoes = stock.options
            if datas_opcoes:
                chain = stock.option_chain(datas_opcoes[0])
                calls_iv = chain.calls['impliedVolatility']
                calls_iv = calls_iv[calls_iv > 0]
                if not calls_iv.empty:
                    iv_val = calls_iv.median() * 100
                    iv_str = f"{iv_val:.1f}%"
        except:
            iv_str = "-"

        roe    = info.get('returnOnEquity', 0)
        margem = info.get('profitMargins', 0)
        beta   = info.get('beta', 0)
        pvp    = info.get('priceToBook', None)

        roe_num    = (roe    * 100) if roe    else 0
        margem_num = (margem * 100) if margem else 0

        roe_str    = f"{roe_num:.1f}%"    if roe    else "-"
        margem_str = f"{margem_num:.1f}%" if margem else "-"
        beta_str   = f"{beta:.2f}"        if beta   else "N/A"
        pvp_str    = f"{pvp:.2f}x"        if pvp    else "-"

        low52  = info.get('fiftyTwoWeekLow',  0)
        high52 = info.get('fiftyTwoWeekHigh', 0)
        low_str  = f"R$ {low52:.2f}"  if low52  else "-"
        high_str = f"R$ {high52:.2f}" if high52 else "-"

        historico_dy = {}
        try:
            preco_hist  = stock.history(period="5y", interval="1mo")
            divs_anuais = stock.dividends
            if not divs_anuais.empty and not preco_hist.empty:
                ano_atual = pd.Timestamp.now().year
                for ano in range(ano_atual - 4, ano_atual + 1):
                    soma_divs   = divs_anuais[divs_anuais.index.year == ano].sum()
                    preco_ano   = preco_hist[preco_hist.index.year == ano]['Close']
                    preco_medio = preco_ano.mean() if not preco_ano.empty else 0
                    if preco_medio > 0 and soma_divs > 0:
                        historico_dy[ano] = round((soma_divs / preco_medio) * 100, 2)
        except:
            historico_dy = {}

        historico_pl    = {}
        historico_lucro = {}
        try:
            financials  = stock.financials
            preco_atual = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            shares      = info.get('sharesOutstanding', 0)

            if financials is not None and not financials.empty:
                ano_atual = pd.Timestamp.now().year
                for col in financials.columns:
                    ano = col.year
                    if ano < ano_atual - 4:
                        continue
                    for chave in ['Net Income', 'Net Income Common Stockholders']:
                        if chave in financials.index:
                            lucro = financials.loc[chave, col]
                            if pd.notna(lucro) and lucro != 0:
                                historico_lucro[ano] = float(lucro)
                            break
                    if shares > 0 and ano in historico_lucro and historico_lucro[ano] > 0:
                        lpa = historico_lucro[ano] / shares
                        if lpa > 0 and preco_atual:
                            historico_pl[ano] = round(preco_atual / lpa, 1)
        except:
            historico_pl    = {}
            historico_lucro = {}

        proximo_provento_data  = "-"
        proximo_provento_valor = "-"
        try:
            calendar = stock.calendar
            if calendar is not None:
                ex_date = calendar.get('Ex-Dividend Date') or calendar.get('Dividend Date')
                if ex_date:
                    hoje  = pd.Timestamp.now().normalize()
                    ex_ts = pd.Timestamp(ex_date).normalize()
                    data_com = ex_ts - pd.offsets.BDay(1)
                    if data_com > hoje:
                        proximo_provento_data  = data_com.strftime('%d/%m/%Y')
                        proximo_provento_valor = f"R$ {divs.iloc[-1]:.4f}" if not divs.empty else "-"
        except:
            pass

        return (
            data_ex, valor_div, roe_str, margem_str, low_str, high_str,
            beta_str, pvp_str, roe_num, margem_num,
            historico_dy, historico_pl, historico_lucro,
            proximo_provento_data, proximo_provento_valor,
            variacao_dia, iv_str
        )
    except:
        return "-", "-", "-", "-", "-", "-", "N/A", "-", 0, 0, {}, {}, {}, "-", "-", 0.0, "-"


@st.cache_data(ttl=60)
def carregar_dados():
    try:
        spreadsheet_id = "1QM3xaaiZHleTJb8MEChy95LJSX3j3hLs8-ecQydMHYM"
        gid_id         = "596101825"
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid_id}"
        df  = pd.read_csv(url, header=None)

        idx = 0
        for i, row in df.iterrows():
            if "CÓDIGO" in [str(x).upper().strip() for x in row.values]:
                idx = i
                break

        df.columns = [str(c).strip() for c in df.iloc[idx]]
        df = df.iloc[idx + 1:].reset_index(drop=True)
        df = df.dropna(how='all')

        df['pl_num']      = df['P/L PROJETADO'].apply(limpar_valor)
        df['dy_num']      = df['Dividend Yield bruto estimado'].apply(limpar_valor)
        df['div_num']     = df['Dívida líquida/EBITDA'].apply(limpar_valor)
        df['cagr_num']    = df['CAGR lucros (últ. 5 anos)'].apply(limpar_valor)
        df['res_val_num'] = df['RESULTADO 2026 (1/4)'].apply(limpar_valor_resultado)

        return df
    except:
        return pd.DataFrame()

df = carregar_dados()

# --- SIDEBAR ---
st.sidebar.header("🎯 Filtros Quantitativos")
ativar_filtros    = st.sidebar.checkbox("✅ Ativar Filtros Quantitativos", value=False)
busca_ticker      = st.sidebar.text_input("🔍 Buscar por Ticker:").strip().upper()
setores_disponiveis = sorted(df['SETOR'].unique().tolist()) if not df.empty else []
filtro_setor      = st.sidebar.multiselect("🏢 Filtrar por Setor:", setores_disponiveis)

max_pl   = st.sidebar.slider("P/L abaixo de:",              0.0, 50.0, 20.0)
min_dy   = st.sidebar.slider("Dividend Yield acima de (%)", 0.0, 20.0,  6.0)
max_div  = st.sidebar.slider("Dívida Líq./EBITDA abaixo de:", 0.0, 10.0, 3.0)
min_cagr = st.sidebar.slider("CAGR Lucros acima de (%)",    0.0, 50.0, 10.0)
min_score = st.sidebar.slider("⭐ Score mínimo (0–10):",     0.0, 10.0,  0.0, step=0.5)

# --- FILTROS ---
df_f = df.copy()
if ativar_filtros:
    df_f = df_f[
        (df_f['pl_num']   <= max_pl)  &
        (df_f['dy_num']   >= min_dy)  &
        (df_f['div_num']  <= max_div) &
        (df_f['cagr_num'] >= min_cagr)
    ]
if busca_ticker:
    df_f = df_f[df_f['CÓDIGO'].str.contains(busca_ticker)]
if filtro_setor:
    df_f = df_f[df_f['SETOR'].isin(filtro_setor)]

_min_score_efetivo = min_score if ativar_filtros else 0.0

if 'ativo_selecionado' not in st.session_state:
    st.session_state.ativo_selecionado = None
if 'modo_exibicao' not in st.session_state:
    st.session_state.modo_exibicao = 'Lista'


def pagina_ativo(ticker, row, ativo_data):
    try:
        import plotly.graph_objects as go
    except ImportError:
        go = None
    if st.button("← Voltar para o Radar", key="btn_voltar"):
        st.session_state.ativo_selecionado = None
        st.rerun()

    logo_url    = ativo_data.get('logo_url', '')
    variacao_dia= ativo_data.get('variacao_dia', 0.0)
    cot         = formatar_cotacao(row.get('Cotação atual', 0))
    dy_clean    = ativo_data.get('dy_clean', '-')
    dy_num      = ativo_data.get('dy_num', 0)
    score       = ativo_data.get('score', 0)
    porcentagem = ativo_data.get('porcentagem', 0)
    cor         = cor_progresso(porcentagem)
    roe         = ativo_data.get('roe', '-')
    margem      = ativo_data.get('margem', '-')
    beta        = ativo_data.get('beta', '-')
    pvp_str     = ativo_data.get('pvp_str', '-')
    historico_dy    = ativo_data.get('historico_dy', {})
    historico_pl    = ativo_data.get('historico_pl', {})
    historico_lucro = ativo_data.get('historico_lucro', {})
    proximo_provento_data  = ativo_data.get('proximo_provento_data', '-')
    proximo_provento_valor = ativo_data.get('proximo_provento_valor', '-')
    dt  = ativo_data.get('dt', '-')
    val = ativo_data.get('val', '-')

    if variacao_dia > 0:
        var_str = "🟢 +{:.2f}%".format(variacao_dia)
    elif variacao_dia < 0:
        var_str = "🔴 {:.2f}%".format(variacao_dia)
    else:
        var_str = "🟡 {:.2f}%".format(variacao_dia)

    hcol1, hcol2 = st.columns([1, 5])
    with hcol1:
        if logo_url:
            st.markdown(
                "<img src='{}' style='height:80px;width:auto;border-radius:12px;background:#fff;padding:4px;'/>".format(logo_url),
                unsafe_allow_html=True)
    with hcol2:
        st.markdown(
            "<h1 style='margin:0;color:#FFD700;font-size:2.2em;font-weight:900;letter-spacing:2px;'>{}</h1>"
            "<span style='color:#aaa;font-size:0.95em;'>{} &nbsp;|&nbsp; {} &nbsp; {} &nbsp;|&nbsp; ⭐ Score: {}/10</span>".format(
                ticker, row.get('SETOR','-'), cot, var_str, score),
            unsafe_allow_html=True)

    st.markdown("<div style='margin:16px 0 8px 0;height:1px;background:rgba(255,255,255,0.1);'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📊 Valuation")
        st.markdown("**P/L Médio (10 anos):** {}x".format(row.get('P/L médio (últ. 10 anos)', '-')))
        st.markdown("**P/VP:** {}".format(pvp_str))
        st.markdown("**Valor de Mercado:** {}".format(row.get('VALOR DE MERCADO', '-')))
        st.markdown("**RESULTADO PROJETADO:** {}".format(row.get('LL PROJETADO', '-')))
        st.markdown("**⭐ RESULTADO ENTREGUE (1/4):** <span style='color:#39FF14;font-weight:bold;'>{}</span>".format(
            row.get('RESULTADO 2026 (1/4)', '-')), unsafe_allow_html=True)
        barra = "<div style='background:#222;border-radius:6px;height:12px;width:100%;margin:6px 0;'><div style='background:{};width:{}%;height:12px;border-radius:6px;'></div></div>".format(cor, porcentagem)
        st.markdown(barra, unsafe_allow_html=True)
        st.markdown("<span style='color:{};font-weight:bold;'>Status: {}% do resultado projetado</span>".format(cor, porcentagem), unsafe_allow_html=True)
        if historico_lucro:
            st.markdown("<span style='font-size:0.85em;color:#aaa;font-weight:bold;'>📈 Lucro Líquido (5 anos)</span>", unsafe_allow_html=True)
            st.markdown(mini_grafico_linha(historico_lucro, "#39FF14"), unsafe_allow_html=True)

    with col2:
        st.markdown("#### 💰 Dividendos")
        style_dy = "color:#39FF14;font-weight:bold;" if dy_num > 8 else ""
        st.markdown("**Dividend Yield:** <span style='{}'>{}</span>".format(style_dy, dy_clean + "%"), unsafe_allow_html=True)
        st.markdown("**Payout:** {}".format(row.get('PAYOUT', '-')))
        st.markdown("**LPA Est.:** {}".format(row.get('LPA ESTIMADO', '-')))
        st.markdown("**Div. Projetado:** {}".format(row.get('Dividendo por ação bruto projetado', '-')))
        st.markdown("**Data Ex (último):** {}".format(dt))
        st.markdown("**Valor Último Div.:** {}".format(val))
        if proximo_provento_data != "-":
            st.markdown(
                "<div style='margin-top:10px;padding:8px 12px;border-radius:8px;background:#1a3a1a;border:1px solid #39FF14;'>"
                "<span style='color:#39FF14;font-weight:bold;'>📅 Próximo Provento em Aberto</span><br>"
                "<span style='color:#fff;'>Data COM: <b>{}</b> | Valor Est.: <b>{}</b></span></div>".format(
                    proximo_provento_data, proximo_provento_valor),
                unsafe_allow_html=True)
        else:
            st.markdown(
                "<div style='margin-top:10px;padding:6px 12px;border-radius:8px;background:#2a2a2a;border:1px solid #555;color:#888;font-size:0.85em;'>📅 Nenhum provento futuro identificado</div>",
                unsafe_allow_html=True)
        st.markdown("**Histórico DY (5 anos):**")
        st.markdown(mini_grafico_dy(historico_dy), unsafe_allow_html=True)

    with col3:
        st.markdown("#### ⚙️ Operacional")
        pl_proj = row.get('P/L PROJETADO', '-')
        st.markdown("**P/L Projetado:** <span style='color:#FFD700;font-weight:bold;font-size:1.1em;'>{}x</span>".format(pl_proj), unsafe_allow_html=True)
        st.markdown("**Dívida Líq/EBITDA:** {}".format(row.get('Dívida líquida/EBITDA', '-')))
        st.markdown("**CAGR Lucros:** {}".format(row.get('CAGR lucros (últ. 5 anos)', '-')))
        st.markdown("**ROE:** {}".format(roe))
        st.markdown("**Margem Líq.:** {}".format(margem))
        st.markdown("**Beta (vs IBOV):** {}".format(beta))
        if historico_pl:
            st.markdown("<span style='font-size:0.85em;color:#aaa;font-weight:bold;'>📈 P/L Histórico (5 anos)</span>", unsafe_allow_html=True)
            st.markdown(mini_grafico_linha(historico_pl, "#1E90FF", label_suffix="x"), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📉 Preço Histórico")
    periodo_opcoes = {"1 mês": "1mo", "3 meses": "3mo", "6 meses": "6mo", "1 ano": "1y", "2 anos": "2y", "5 anos": "5y"}
    periodo_sel = st.selectbox("Período:", list(periodo_opcoes.keys()), index=3, key="periodo_{}".format(ticker))
    try:
        if go is None:
            st.warning("Instale plotly: adicione 'plotly' ao requirements.txt")
        else:
          stock = yf.Ticker("{}.SA".format(ticker))
          hist  = stock.history(period=periodo_opcoes[periodo_sel])
          if not hist.empty:
            fig = go.Figure(data=[go.Candlestick(
                x=hist.index,
                open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'],
                increasing_line_color='#39FF14', decreasing_line_color='#FF4444', name=ticker
            )])
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.3)',
                font_color='#fff',
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                margin=dict(l=0, r=0, t=10, b=0), height=420,
                xaxis_rangeslider_visible=False,
            )
            st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.warning("Não foi possível carregar o gráfico de preços.")



# --- DASHBOARD ---
st.markdown("""
<div style="position:relative; margin-bottom:20px; padding:10px 0 16px 0;
            border-bottom:1px solid rgba(255,255,255,0.08);">
    <h1 style="margin:0; font-size:2.4em; font-weight:900; letter-spacing:2px;
               text-transform:uppercase; color:#fff; line-height:1.1;
               text-shadow: 0 0 30px rgba(57,255,20,0.3);">
        Radar Fundamentalista
    </h1>
    <span style="position:absolute; top:14px; right:0; font-size:0.85em;
                 letter-spacing:3px; text-transform:uppercase; font-weight:700;
                 color:rgba(255,255,255,0.55);">Diego Castro</span>
</div>
""", unsafe_allow_html=True)

if not df_f.empty:
    idx_max_dy    = df_f['dy_num'].idxmax()
    ticker_max_dy = df_f.loc[idx_max_dy, 'CÓDIGO']
    val_max_dy    = df_f.loc[idx_max_dy, 'Dividend Yield bruto estimado']

else:
    ticker_max_dy = val_max_dy = "-"

ticket_max_score = "-"
val_max_score    = "-"

# Maior score calculado após montar ativos_com_score — placeholder por enquanto
ticker_max_score = "-"
val_max_score    = "-"

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class='top-card'>
        <div class='label'>📋 Total de Ativos</div>
        <div class='value'>{len(df)}</div>
    </div>""", unsafe_allow_html=True)
with c2:
    card_filtrados = st.empty()
with c3:
    st.markdown(f"""<div class='top-card'>
        <div class='label'>🏆 Maior DY</div>
        <div class='value'>{ticker_max_dy}</div>
        <div class='sub'>{val_max_dy}</div>
    </div>""", unsafe_allow_html=True)
with c4:
    card_maior_score = st.empty()

st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

st.markdown("""
<style>
div[data-testid="stButton"] button[kind="primary"] {
    background-color: #00BCD4 !important;
    color: #ffffff !important;
    border: none !important;
    font-weight: 700 !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
    background-color: #00ACC1 !important;
}
</style>
""", unsafe_allow_html=True)
tcol1, tcol2, tcol3 = st.columns([1, 1, 8])
with tcol1:
    if st.button("☰ Lista", use_container_width=True,
                 type="primary" if st.session_state.modo_exibicao == 'Lista' else "secondary"):
        st.session_state.modo_exibicao = 'Lista'
        st.rerun()
with tcol2:
    if st.button("⊞ Cards", use_container_width=True,
                 type="primary" if st.session_state.modo_exibicao == 'Cards' else "secondary"):
        st.session_state.modo_exibicao = 'Cards'
        st.rerun()

# --- LISTAGEM DE ATIVOS ---
if df_f.empty:
    card_filtrados.markdown("""<div class='top-card'>
        <div class='label'>🔍 Ativos Filtrados</div>
        <div class='value'>0</div>
    </div>""", unsafe_allow_html=True)
    st.warning("Nenhum ativo encontrado.")
else:
    ativos_com_score = []

    for _, row in df_f.iterrows():
        dt = val = roe = margem = low = high = beta = pvp_str = "-"
        roe_num_raw = margem_num_raw = 0
        historico_dy = historico_pl = historico_lucro = {}
        proximo_provento_data = proximo_provento_valor = "-"
        variacao_dia = 0.0
        iv_str = "-"
        progresso = 0.0

        try:
            (dt, val, roe, margem, low, high,
             beta, pvp_str, roe_num_raw, margem_num_raw,
             historico_dy, historico_pl, historico_lucro,
             proximo_provento_data, proximo_provento_valor,
             variacao_dia, iv_str) = get_dados_yahoo(row['CÓDIGO'])
        except:
            pass

        # Logo — chamada separada, não interfere nos dados acima
        logo_url = get_logo_url(row['CÓDIGO'])

        val_entregue  = limpar_valor_resultado(row.get('RESULTADO 2026 (1/4)', 0))
        val_projetado = limpar_valor_resultado(row.get('LL PROJETADO', 0))
        progresso     = float(min(val_entregue / val_projetado, 1.0)) if val_projetado > 0 else 0.0
        porcentagem   = int(progresso * 100)

        dy_raw   = str(row.get('Dividend Yield bruto estimado', '0'))
        dy_clean = dy_raw.replace('%', '').strip()
        try:
            dy_num = float(dy_clean.replace(',', '.'))
        except:
            dy_num = 0

        pl_num         = limpar_valor(row.get('P/L PROJETADO',          0))
        div_ebitda_num = limpar_valor(row.get('Dívida líquida/EBITDA',  0))
        cagr_num       = limpar_valor(row.get('CAGR lucros (últ. 5 anos)', 0))

        pvp_num_raw = limpar_valor(pvp_str.replace('x','')) if pvp_str != '-' else 0
        score = calcular_score(dy_num, pl_num, div_ebitda_num, cagr_num, roe_num_raw, margem_num_raw,
                               pvp_num=pvp_num_raw, setor=row.get('SETOR', ''))

        ativos_com_score.append({
            'row': row, 'score': score,
            'dy_num': dy_num, 'dy_clean': dy_clean, 'pl_num': pl_num,
            'progresso': progresso, 'porcentagem': porcentagem,
            'dt': dt, 'val': val, 'roe': roe, 'margem': margem,
            'beta': beta, 'pvp_str': pvp_str,
            'historico_dy': historico_dy,
            'historico_pl': historico_pl,
            'historico_lucro': historico_lucro,
            'proximo_provento_data': proximo_provento_data,
            'proximo_provento_valor': proximo_provento_valor,
            'variacao_dia': variacao_dia,
            'iv_str': iv_str,
            'logo_url': logo_url,
        })

    ativos_com_score = [a for a in ativos_com_score if a['score'] >= _min_score_efetivo]
    ativos_com_score.sort(key=lambda x: x['score'], reverse=True)

    card_filtrados.markdown(f"""<div class='top-card'>
        <div class='label'>🔍 Ativos Filtrados</div>
        <div class='value'>{len(ativos_com_score)}</div>
    </div>""", unsafe_allow_html=True)

    if ativos_com_score:
        top = ativos_com_score[0]
        card_maior_score.markdown(f"""<div class='top-card'>
            <div class='label'>🏅 Maior Score</div>
            <div class='value'>{top['row']['CÓDIGO']}</div>
            <div class='sub'>⭐ {top['score']}/10</div>
        </div>""", unsafe_allow_html=True)
    else:
        card_maior_score.markdown("""<div class='top-card'>
            <div class='label'>🏅 Maior Score</div>
            <div class='value'>-</div>
        </div>""", unsafe_allow_html=True)

    if not ativos_com_score:
        st.warning("Nenhum ativo com score suficiente encontrado.")
    else:
        # Página de detalhe
        if st.session_state.ativo_selecionado:
            ticker_sel = st.session_state.ativo_selecionado
            ativo_sel  = next((a for a in ativos_com_score if a['row']['CÓDIGO'] == ticker_sel), None)
            if ativo_sel:
                pagina_ativo(ticker_sel, ativo_sel['row'], ativo_sel)
                st.stop()
            else:
                st.session_state.ativo_selecionado = None

        # Modo Cards
        if st.session_state.modo_exibicao == 'Cards':
            cols_n = 6
            rows_c = [ativos_com_score[i:i+cols_n] for i in range(0, len(ativos_com_score), cols_n)]
            for linha in rows_c:
                cols = st.columns(cols_n)
                for idx, ativo in enumerate(linha):
                    row_c    = ativo['row']
                    ticker_c = row_c['CÓDIGO']
                    logo_c   = ativo.get('logo_url', '')
                    cot_c    = formatar_cotacao(row_c.get('Cotação atual', 0))
                    var_c    = ativo['variacao_dia']
                    dy_c     = ativo['dy_clean']
                    dy_num_c = ativo['dy_num']
                    pl_c     = row_c.get('P/L PROJETADO', '-')
                    score_c  = ativo['score']
                    ic_c     = icone_setor(row_c['SETOR'])

                    if var_c > 0:
                        var_html = "<span class='ac-var-pos'>🟢 +{:.2f}%</span>".format(var_c)
                    elif var_c < 0:
                        var_html = "<span class='ac-var-neg'>🔴 {:.2f}%</span>".format(var_c)
                    else:
                        var_html = "<span class='ac-var-neu'>🟡 {:.2f}%</span>".format(var_c)

                    dy_color = "#39FF14" if dy_num_c > 8 else "#1E90FF"
                    logo_html = "<img src='{}' class='ac-logo'/>".format(logo_c) if logo_c else "<div style='font-size:2em;margin-bottom:8px;'>{}</div>".format(ic_c)

                    with cols[idx]:
                        st.markdown(
                            "<div class='asset-card'>"
                            + logo_html
                            + "<div class='ac-ticker'>{}</div>".format(ticker_c)
                            + "<div class='ac-cot'>{}</div>".format(cot_c)
                            + "<div style='margin-top:4px;'>{}</div>".format(var_html)
                            + "<div class='ac-row'><span>DY</span><span class='ac-val' style='color:{};'>{}%</span></div>".format(dy_color, dy_c)
                            + "<div class='ac-row'><span>P/L</span><span class='ac-val'>{}x</span></div>".format(pl_c)
                            + "<div class='ac-row'><span>Score</span><span class='ac-val' style='color:#FFD700;'>⭐ {}</span></div>".format(score_c)
                            + "</div>",
                            unsafe_allow_html=True
                        )
                        if st.button("Ver detalhes", key="card_{}".format(ticker_c), use_container_width=True):
                            st.session_state.ativo_selecionado = ticker_c
                            st.rerun()
            st.stop()

        # Modo Lista
        for ativo in ativos_com_score:
            row                    = ativo['row']
            score                  = ativo['score']
            dy_num                 = ativo['dy_num']
            dy_clean               = ativo['dy_clean']
            porcentagem            = ativo['porcentagem']
            progresso              = ativo['progresso']
            dt                     = ativo['dt']
            val                    = ativo['val']
            roe                    = ativo['roe']
            margem                 = ativo['margem']
            beta                   = ativo['beta']
            pvp_str                = ativo['pvp_str']
            historico_dy           = ativo['historico_dy']
            historico_pl           = ativo['historico_pl']
            historico_lucro        = ativo['historico_lucro']
            proximo_provento_data  = ativo['proximo_provento_data']
            proximo_provento_valor = ativo['proximo_provento_valor']
            variacao_dia           = ativo['variacao_dia']
            iv_str                 = ativo['iv_str']
            logo_url               = ativo['logo_url']

            dy_icone  = "🔷" if dy_num > 8 else ""
            cot       = formatar_cotacao(row.get('Cotação atual', 0))
            pl        = f"{row.get('P/L PROJETADO', '0')}x"
            ic_setor  = icone_setor(row['SETOR'])

            if variacao_dia > 0:
                var_str = f"🟢 +{variacao_dia:.2f}%"
            elif variacao_dia < 0:
                var_str = f"🔴 {variacao_dia:.2f}%"
            else:
                var_str = f"🟡 {variacao_dia:.2f}%"

            iv_label = f"IV: {iv_str}" if iv_str != "-" else ""

            titulo = (
                f"{ic_setor} :orange[**{row['CÓDIGO']}**] | {cot} {var_str} | P/L: {pl} | "
                f"DY: {dy_icone} {dy_clean}% | {iv_label} | ⭐ Score: {score}/10 | Setor: {row['SETOR']}"
            )

            st.markdown("<div class='ativo-sep'></div>", unsafe_allow_html=True)
            with st.expander(titulo):

                # Logo no topo do card — apenas uma vez, acima das colunas
                if logo_url:
                    st.markdown(
                        f"<div style='display:flex; align-items:center; gap:12px; "
                        f"margin-bottom:14px; padding-bottom:10px; "
                        f"border-bottom:1px solid rgba(255,255,255,0.07);'>"
                        f"<img src='{logo_url}' style='height:36px; width:auto; "
                        f"border-radius:6px; background:#fff; padding:3px;'/>"
                        f"<span style='font-size:1.1em; font-weight:700; color:#FFD700; "
                        f"letter-spacing:1px;'>{row['CÓDIGO']}</span>"
                        f"<span style='font-size:0.85em; color:#888;'>{row.get('SETOR','-')}</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                col1, col2, col3 = st.columns(3)

                # ── COLUNA 1: VALUATION ──────────────────────────────────
                with col1:
                    st.markdown("#### 📊 Valuation")
                    st.markdown(f"**P/L Médio (10 anos):** {row.get('P/L médio (últ. 10 anos)', '-')}x")
                    st.markdown(f"**P/VP:** {pvp_str}")
                    st.markdown(f"**Valor de Mercado:** {row.get('VALOR DE MERCADO', '-')}")
                    st.markdown(f"**RESULTADO PROJETADO:** {row.get('LL PROJETADO', '-')}")
                    st.markdown(
                        f"**⭐ RESULTADO ENTREGUE (1/4):** "
                        f"<span style='color:#39FF14; font-weight:bold;'>"
                        f"{row.get('RESULTADO 2026 (1/4)', '-')}</span>",
                        unsafe_allow_html=True
                    )
                    cor = cor_progresso(porcentagem)
                    st.markdown(
                        f"""<div style="background:#222; border-radius:6px; height:12px;
                                        width:100%; margin:6px 0;">
                              <div style="background:{cor}; width:{porcentagem}%; height:12px;
                                          border-radius:6px;"></div>
                            </div>""",
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f"<span style='color:{cor}; font-weight:bold;'>"
                        f"Status: {porcentagem}% do resultado projetado</span>",
                        unsafe_allow_html=True
                    )
                    if historico_lucro:
                        st.markdown(
                            "<span style='font-size:0.85em; color:#aaa; font-weight:bold;'>"
                            "📈 Lucro Líquido (5 anos)</span>",
                            unsafe_allow_html=True
                        )
                        st.markdown(
                            mini_grafico_linha(historico_lucro, "#39FF14"),
                            unsafe_allow_html=True
                        )

                # ── COLUNA 2: DIVIDENDOS ─────────────────────────────────
                with col2:
                    st.markdown("#### 💰 Dividendos")
                    style_dy = "color:#39FF14; font-weight:bold;" if dy_num > 8 else ""
                    st.markdown(
                        f"**Dividend Yield:** <span style='{style_dy}'>{dy_clean}%</span>",
                        unsafe_allow_html=True
                    )
                    st.markdown(f"**Payout:** {row.get('PAYOUT', '-')}")
                    st.markdown(f"**LPA Est.:** {row.get('LPA ESTIMADO', '-')}")
                    st.markdown(f"**Div. Projetado:** {row.get('Dividendo por ação bruto projetado', '-')}")
                    st.markdown(f"**Data Ex (último):** {dt}")
                    st.markdown(f"**Valor Último Div.:** {val}")
                    if proximo_provento_data != "-":
                        st.markdown(
                            f"<div style='margin-top:10px; padding:8px 12px; border-radius:8px;"
                            f"background:#1a3a1a; border:1px solid #39FF14;'>"
                            f"<span style='color:#39FF14; font-weight:bold; font-size:0.95em;'>"
                            f"📅 Próximo Provento em Aberto</span><br>"
                            f"<span style='color:#fff;'>Data COM: <b>{proximo_provento_data}</b>"
                            f" &nbsp;|&nbsp; Valor Est.: <b>{proximo_provento_valor}</b></span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            "<div style='margin-top:10px; padding:6px 12px; border-radius:8px;"
                            "background:#2a2a2a; border:1px solid #555; color:#888; font-size:0.85em;'>"
                            "📅 Nenhum provento futuro identificado</div>",
                            unsafe_allow_html=True
                        )
                    st.markdown("**Histórico DY (5 anos):**")
                    st.markdown(mini_grafico_dy(historico_dy), unsafe_allow_html=True)

                # ── COLUNA 3: OPERACIONAL ────────────────────────────────
                with col3:
                    st.markdown("#### ⚙️ Operacional")
                    pl_proj = row.get('P/L PROJETADO', '-')
                    st.markdown(
                        f"**P/L Projetado:** <span style='color:#FFD700; font-weight:bold; font-size:1.1em;'>{pl_proj}x</span>",
                        unsafe_allow_html=True
                    )
                    st.markdown(f"**Dívida Líq/EBITDA:** {row.get('Dívida líquida/EBITDA', '-')}")
                    st.markdown(f"**CAGR Lucros:** {row.get('CAGR lucros (últ. 5 anos)', '-')}")
                    st.markdown(f"**ROE:** {roe}")
                    st.markdown(f"**Margem Líq.:** {margem}")
                    st.markdown(f"**Beta (vs IBOV):** {beta}")
                    if historico_pl:
                        st.markdown(
                            "<span style='font-size:0.85em; color:#aaa; font-weight:bold;'>"
                            "📈 P/L Histórico (5 anos)</span>",
                            unsafe_allow_html=True
                        )
                        st.markdown(
                            mini_grafico_linha(historico_pl, "#1E90FF", label_suffix="x"),
                            unsafe_allow_html=True
                        )
