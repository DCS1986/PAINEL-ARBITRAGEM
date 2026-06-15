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

def formatar_yield(valor):
    s = str(valor).replace('%', '').replace(',', '.').strip()
    return f"{s}%"

# ---- NOVO: Cor dinâmica da barra de progresso ----
def cor_progresso(porcentagem):
    """Retorna cor hex conforme o progresso em relação à meta."""
    if porcentagem >= 50:
        return "#39FF14"   # verde neon
    elif porcentagem >= 25:
        return "#FFD700"   # amarelo ouro
    else:
        return "#FF4444"   # vermelho

# ---- NOVO: Cálculo do Score Geral (0–10) ----
def calcular_score(dy_num, pl_num, div_ebitda_num, cagr_num, roe_num, margem_num):
    """
    Pontuação ponderada com base nos principais fundamentos.
    Cada critério gera até N pontos, totalizando 10.
    """
    score = 0.0

    # DY (até 2.5 pts): acima de 10% = máximo
    score += min(dy_num / 10.0, 1.0) * 2.5

    # P/L (até 2.0 pts): quanto menor melhor; abaixo de 8x = máximo
    if pl_num > 0:
        score += max(0, (20 - pl_num) / 20.0) * 2.0

    # Dívida/EBITDA (até 1.5 pts): abaixo de 1 = máximo; acima de 5 = 0
    score += max(0, (5 - div_ebitda_num) / 5.0) * 1.5

    # CAGR Lucros (até 2.0 pts): acima de 20% = máximo
    score += min(cagr_num / 20.0, 1.0) * 2.0

    # ROE (até 1.0 pt): acima de 20% = máximo
    score += min(roe_num / 20.0, 1.0) * 1.0

    # Margem Líq. (até 1.0 pt): acima de 30% = máximo
    score += min(margem_num / 30.0, 1.0) * 1.0

    return round(min(score, 10.0), 1)

def badge_score(score):
    """Retorna HTML do badge colorido conforme o score."""
    if score >= 7:
        cor_bg, cor_txt = "#1a3a1a", "#39FF14"
        label = "Ótimo"
    elif score >= 5:
        cor_bg, cor_txt = "#3a3a10", "#FFD700"
        label = "Bom"
    elif score >= 3:
        cor_bg, cor_txt = "#3a2010", "#FFA500"
        label = "Regular"
    else:
        cor_bg, cor_txt = "#3a1010", "#FF4444"
        label = "Fraco"
    return f"""
    <div style="display:flex; align-items:center; gap:10px; margin-top:6px;">
        <span class="score-badge" style="background:{cor_bg}; color:{cor_txt}; border: 1px solid {cor_txt};">
            ⭐ Score: {score}/10
        </span>
        <span style="color:{cor_txt}; font-size:0.9em; font-weight:bold;">{label}</span>
    </div>"""

# ---- NOVO: Mini gráfico de histórico de DY ----
def mini_grafico_dy(historico_dy):
    """
    historico_dy: dict {ano: valor_percentual}  ex: {2020: 6.2, 2021: 7.0, ...}
    Retorna HTML de um gráfico de barras verticais maior e mais legível.
    """
    if not historico_dy:
        return "<span style='color:#888; font-size:0.9em;'>Histórico indisponível</span>"

    max_val = max(historico_dy.values()) if historico_dy.values() else 1
    if max_val == 0:
        max_val = 1

    barras = ""
    for ano, val in sorted(historico_dy.items()):
        # Altura máxima de 90px para caber bem no container de 110px
        altura = max(int((val / max_val) * 90), 6)
        cor = "#39FF14" if val >= 8 else "#1E90FF"
        barras += f"""
        <div class="dy-bar-wrap">
            <span class="dy-bar-value">{val:.1f}%</span>
            <div class="dy-bar" style="height:{altura}px; background:{cor};"></div>
            <span class="dy-bar-label">{ano}</span>
        </div>"""

    return f'<div class="dy-bar-container">{barras}</div>'

@st.cache_data(ttl=86400)
def get_dados_yahoo(ticker):
    """Busca dividendos, ROE, Margem, 52 semanas, Beta, P/VP e histórico DY."""
    try:
        stock = yf.Ticker(f"{ticker}.SA")
        info = stock.info
        
        # Último dividendo
        divs = stock.dividends
        data_ex = divs.index[-1].strftime('%d/%m/%Y') if not divs.empty else "-"
        valor_div = f"R$ {divs.iloc[-1]:.4f}" if not divs.empty else "-"
        
        # Métricas Financeiras
        roe = info.get('returnOnEquity', 0)
        margem = info.get('profitMargins', 0)
        beta = info.get('beta', 0)

        # ---- NOVO: P/VP ----
        pvp = info.get('priceToBook', None)
        pvp_str = f"{pvp:.2f}x" if pvp else "-"

        roe_num = (roe * 100) if roe else 0
        margem_num = (margem * 100) if margem else 0
        
        roe_str = f"{roe_num:.1f}%" if roe else "-"
        margem_str = f"{margem_num:.1f}%" if margem else "-"
        beta_str = f"{beta:.2f}" if beta else "N/A"
        
        # Preços 52 semanas
        low52 = info.get('fiftyTwoWeekLow', 0)
        high52 = info.get('fiftyTwoWeekHigh', 0)
        low_str = f"R$ {low52:.2f}" if low52 else "-"
        high_str = f"R$ {high52:.2f}" if high52 else "-"

        # ---- NOVO: Histórico de DY dos últimos 5 anos ----
        historico_dy = {}
        try:
            preco_hist = stock.history(period="5y", interval="1mo")
            divs_anuais = stock.dividends
            
            if not divs_anuais.empty and not preco_hist.empty:
                ano_atual = pd.Timestamp.now().year
                anos = range(ano_atual - 4, ano_atual + 1)
                
                for ano in anos:
                    divs_ano = divs_anuais[divs_anuais.index.year == ano]
                    soma_divs = divs_ano.sum()
                    preco_ano = preco_hist[preco_hist.index.year == ano]['Close']
                    preco_medio = preco_ano.mean() if not preco_ano.empty else 0
                    
                    if preco_medio > 0 and soma_divs > 0:
                        dy_ano = (soma_divs / preco_medio) * 100
                        historico_dy[ano] = round(dy_ano, 2)
        except:
            historico_dy = {}

        # ---- NOVO: Próximo provento em aberto ----
        proximo_provento_data = "-"
        proximo_provento_valor = "-"
        try:
            calendar = stock.calendar
            # O Yahoo Finance retorna o campo 'Dividend Date' com a data ex futura
            if calendar is not None:
                ex_date = calendar.get('Ex-Dividend Date') or calendar.get('Dividend Date')
                if ex_date:
                    hoje = pd.Timestamp.now().normalize()
                    ex_ts = pd.Timestamp(ex_date)
                    if ex_ts >= hoje:
                        proximo_provento_data = ex_ts.strftime('%d/%m/%Y')
                        # Pega o último valor declarado como estimativa
                        if not divs.empty:
                            proximo_provento_valor = f"R$ {divs.iloc[-1]:.4f}"
        except:
            pass

        return (data_ex, valor_div, roe_str, margem_str, low_str, high_str,
                beta_str, pvp_str, roe_num, margem_num, historico_dy,
                proximo_provento_data, proximo_provento_valor)
    except:
        return "-", "-", "-", "-", "-", "-", "N/A", "-", 0, 0, {}, "-", "-"

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

# ---- NOVO: Filtro por Score mínimo ----
min_score = st.sidebar.slider("⭐ Score mínimo (0–10):", 0.0, 10.0, 0.0, step=0.5)

# --- LÓGICA ---
df_f = df.copy()
if ativar_filtros:
    df_f = df_f[
        (df_f['pl_num'] <= max_pl) &
        (df_f['dy_num'] >= min_dy) &
        (df_f['div_num'] <= max_div) &
        (df_f['cagr_num'] >= min_cagr)
    ]
if busca_ticker:
    df_f = df_f[df_f['CÓDIGO'].str.contains(busca_ticker)]
if filtro_setor:
    df_f = df_f[df_f['SETOR'].isin(filtro_setor)]

# --- DASHBOARD ---
st.title("🎯 Radar de Ações")

c1, c2 = st.columns(2)
c1.metric("Total de Ativos", len(df))
c2.metric("Ativos Filtrados", len(df_f))

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
    ativos_com_score = []

    for _, row in df_f.iterrows():
        dt, val, roe, margem, low, high, beta = "-", "-", "-", "-", "-", "-", "-"
        pvp_str = "-"
        roe_num_raw = 0
        margem_num_raw = 0
        historico_dy = {}
        proximo_provento_data = "-"
        proximo_provento_valor = "-"
        progresso = 0.0

        try:
            (dt, val, roe, margem, low, high, beta, pvp_str,
             roe_num_raw, margem_num_raw, historico_dy,
             proximo_provento_data, proximo_provento_valor) = get_dados_yahoo(row['CÓDIGO'])
        except:
            pass

        val_entregue = limpar_valor_resultado(row.get('RESULTADO 2026 (1/4)', 0))
        val_projetado = limpar_valor_resultado(row.get('LL PROJETADO', 0))

        progresso = float(min(val_entregue / val_projetado, 1.0)) if val_projetado > 0 else 0.0
        porcentagem = int(progresso * 100)

        dy_raw = str(row.get('Dividend Yield bruto estimado', '0'))
        dy_clean = dy_raw.replace('%', '').strip()
        try:
            dy_num = float(dy_clean.replace(',', '.'))
        except:
            dy_num = 0

        pl_num = limpar_valor(row.get('P/L PROJETADO', 0))
        div_ebitda_num = limpar_valor(row.get('Dívida líquida/EBITDA', 0))
        cagr_num = limpar_valor(row.get('CAGR lucros (últ. 5 anos)', 0))

        score = calcular_score(dy_num, pl_num, div_ebitda_num, cagr_num, roe_num_raw, margem_num_raw)

        ativos_com_score.append({
            'row': row,
            'score': score,
            'dy_num': dy_num,
            'dy_clean': dy_clean,
            'pl_num': pl_num,
            'progresso': progresso,
            'porcentagem': porcentagem,
            'dt': dt,
            'val': val,
            'roe': roe,
            'margem': margem,
            'beta': beta,
            'pvp_str': pvp_str,
            'historico_dy': historico_dy,
            'proximo_provento_data': proximo_provento_data,
            'proximo_provento_valor': proximo_provento_valor,
        })

    # Filtro por score mínimo
    ativos_com_score = [a for a in ativos_com_score if a['score'] >= min_score]

    # Ordenar por score decrescente
    ativos_com_score.sort(key=lambda x: x['score'], reverse=True)

    if not ativos_com_score:
        st.warning("Nenhum ativo com score suficiente encontrado.")
    else:
        for ativo in ativos_com_score:
            row = ativo['row']
            score = ativo['score']
            dy_num = ativo['dy_num']
            dy_clean = ativo['dy_clean']
            progresso = ativo['progresso']
            porcentagem = ativo['porcentagem']
            dt = ativo['dt']
            val = ativo['val']
            roe = ativo['roe']
            margem = ativo['margem']
            beta = ativo['beta']
            pvp_str = ativo['pvp_str']
            historico_dy = ativo['historico_dy']
            proximo_provento_data = ativo['proximo_provento_data']
            proximo_provento_valor = ativo['proximo_provento_valor']

            dy_icone = "🟢" if dy_num > 8 else ""
            cot = formatar_cotacao(row.get('Cotação atual', 0))
            pl = f"{row.get('P/L PROJETADO', '0')}x"

            titulo = f"🏦 **{row['CÓDIGO']}** | {cot} | P/L: {pl} | DY: {dy_icone} {dy_clean}% | ⭐ Score: {score}/10 | Setor: {row['SETOR']}"

            with st.expander(titulo):
                col1, col2, col3 = st.columns(3)

                # --- COLUNA 1: VALUATION ---
                with col1:
                    st.markdown("#### 📊 Valuation")
                    st.markdown(f"**P/L Médio (10 anos):** {row.get('P/L médio (últ. 10 anos)', '-')}x")
                    # ---- NOVO: P/VP ----
                    st.markdown(f"**P/VP:** {pvp_str}")
                    st.markdown(f"**Valor de Mercado:** {row.get('VALOR DE MERCADO', '-')}")
                    st.markdown(f"**RESULTADO PROJETADO:** {row.get('LL PROJETADO', '-')}")
                    st.markdown(
                        f"**⭐ RESULTADO ENTREGUE (1/4):** "
                        f"<span style='color:#39FF14; font-weight:bold;'>{row.get('RESULTADO 2026 (1/4)', '-')}</span>",
                        unsafe_allow_html=True
                    )

                    # ---- NOVO: Barra com cor dinâmica ----
                    cor = cor_progresso(porcentagem)
                    st.markdown(
                        f"""
                        <div style="background:#222; border-radius:6px; height:12px; width:100%; margin:6px 0;">
                            <div style="background:{cor}; width:{porcentagem}%; height:12px; border-radius:6px; transition: width 0.4s;"></div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f"<span style='color:{cor}; font-weight:bold;'>Status: {porcentagem}% da meta projetada</span>",
                        unsafe_allow_html=True
                    )

                    # ---- NOVO: Score badge ----
                    st.markdown(badge_score(score), unsafe_allow_html=True)

                # --- COLUNA 2: DIVIDENDOS ---
                with col2:
                    st.markdown("#### 💰 Dividendos")
                    style_dy = "color: #39FF14; font-weight: bold;" if dy_num > 8 else ""
                    st.markdown(
                        f"**Dividend Yield:** <span style='{style_dy}'>{dy_clean}%</span>",
                        unsafe_allow_html=True
                    )
                    st.markdown(f"**Payout:** {row.get('PAYOUT', '-')}")
                    st.markdown(f"**LPA Est.:** {row.get('LPA ESTIMADO', '-')}")
                    st.markdown(f"**Div. Projetado:** {row.get('Dividendo por ação bruto projetado', '-')}")
                    st.markdown(f"**Data Ex:** {dt}")
                    st.markdown(f"**Valor Atual:** {val}")

                    # ---- Próximo provento em aberto ----
                    if proximo_provento_data != "-":
                        st.markdown(
                            f"<div style='margin-top:10px; padding:8px 12px; border-radius:8px; "
                            f"background:#1a3a1a; border:1px solid #39FF14;'>"
                            f"<span style='color:#39FF14; font-weight:bold; font-size:0.95em;'>"
                            f"📅 Próximo Provento em Aberto</span><br>"
                            f"<span style='color:#fff;'>Data Ex: <b>{proximo_provento_data}</b> &nbsp;|&nbsp; "
                            f"Valor Est.: <b>{proximo_provento_valor}</b></span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            "<div style='margin-top:10px; padding:6px 12px; border-radius:8px; "
                            "background:#2a2a2a; border:1px solid #555; color:#888; font-size:0.85em;'>"
                            "📅 Nenhum provento futuro identificado</div>",
                            unsafe_allow_html=True
                        )

                    # ---- Histórico de DY (gráfico) ----
                    st.markdown("**Histórico DY (5 anos):**")
                    st.markdown(mini_grafico_dy(historico_dy), unsafe_allow_html=True)

                # --- COLUNA 3: OPERACIONAL ---
                with col3:
                    st.markdown("#### ⚙️ Operacional")
                    st.markdown(f"**Setor:** {row.get('SETOR', '-')}")
                    st.markdown(f"**Dívida Líq/EBITDA:** {row.get('Dívida líquida/EBITDA', '-')}")
                    st.markdown(f"**CAGR Lucros:** {row.get('CAGR lucros (últ. 5 anos)', '-')}")
                    st.markdown(f"**ROE:** {roe}")
                    st.markdown(f"**Margem Líq.:** {margem}")
                    st.markdown(f"**Beta (vs IBOV):** {beta}")
