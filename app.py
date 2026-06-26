import io
import re
import pandas as pd
import streamlit as st
import yfinance as yf
import requests

from ui_confluencia import render_confluencia, render_confluencia_card
from cvm_insiders import (
    baixar_mapa_tickers, baixar_programa_recompra, programa_recompra_ativo,
)

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Radar Fundamentalista", layout="wide")

# ---- Controle de acesso ----
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# --- CONFIGURAÇÃO DO FUNDO ---
# Paleta "sóbria" (substitui o tema futurista neon anterior):
#   fundo        #0B1929 (azul-marinho)
#   card         #132238
#   destaque     #D4AF37 (dourado discreto)
#   texto        #F1EFE8 (creme)
#   texto 2ario  #94A3B8
#   positivo     #4CAF6D (verde seco)
#   negativo     #D9534F (vermelho seco)
#   info/neutro  #5B8DB8 (azul-aço)

page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] {{
    background: linear-gradient(160deg, #0B1929 0%, #0E2236 55%, #0B1929 100%);
}}

/* Topo limpo mantendo botões visíveis */
[data-testid="stHeader"] {{
    background: rgba(11, 25, 41, 0.55) !important;
}}
.block-container {{
    padding-top: 28px !important;
    padding-bottom: 0px !important;
}}
[data-testid="stSidebar"] {{
    background: rgba(11, 25, 41, 0.97) !important;
    border-right: 1px solid rgba(255,255,255,0.08) !important;
}}

/* ---- Altura fixa em todos os botões -- evita que um label mais longo
   quebre linha e fique mais alto que os vizinhos na mesma fileira ---- */
div[data-testid="stButton"] button {{
    min-height: 42px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
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
    color: #F1EFE8;
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
    height: 110px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-sizing: border-box;
}}
.top-card .label {{
    font-size: 0.78em;
    color: #ccc;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
}}
.top-card .value {{
    font-size: 1.9em;
    font-weight: 800;
    color: #F1EFE8;
    line-height: 1.1;
}}

.top-card .sub {{
    font-size: 0.85em;
    color: #4CAF6D;
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
    border-radius: 10px;
    padding: 9px 7px 7px 7px;
    text-align: center;
    margin-bottom: 4px;
    min-height: 230px;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}}
.asset-card:hover {{ background: rgba(255,255,255,0.09); border-color: rgba(212,175,55,0.4); }}
.asset-card .ac-logo-area {{ height:44px;display:flex;align-items:center;justify-content:center;margin-bottom:4px; }}
.asset-card .ac-logo {{ width:34px;height:34px;border-radius:50%;object-fit:cover;background:#F1EFE8;padding:2px;display:block; }}
.asset-card .ac-ticker {{ font-size:1.05em;font-weight:800;color:#F1EFE8;letter-spacing:0.5px; }}
.asset-card .ac-cot {{ font-size:0.95em;color:#F1EFE8;font-weight:bold;margin-top:2px; }}
.asset-card .ac-var-pos {{ color:#4CAF6D;font-size:0.68em;font-weight:bold; }}
.asset-card .ac-var-neg {{ color:#D9534F;font-size:0.68em;font-weight:bold; }}
.asset-card .ac-var-neu {{ color:#D4AF37;font-size:0.68em;font-weight:bold; }}
.asset-card .ac-row {{ display:flex;justify-content:space-between;margin-top:5px;font-size:0.68em;color:#F1EFE8;font-weight:bold;border-top:1px solid rgba(255,255,255,0.07);padding-top:5px; }}
.asset-card .ac-val {{ color:#F1EFE8;font-weight:bold;font-size:0.88em; }}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# ---- Página de entrada ----
if not st.session_state.autenticado:

    # CSS: botão dourado, consistente com o novo tema sóbrio
    st.markdown("""
<style>
div[data-testid="stButton"] button[kind="primary"] {
    background-color: #D4AF37 !important;
    color: #0B1929 !important;
    border: none !important;
    font-weight: 700 !important;
    font-size: 1em !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
    background-color: #BFA033 !important;
}
</style>
""", unsafe_allow_html=True)

    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)

    # Texto centralizado em coluna larga
    tl, tc, tr = st.columns([1, 2, 1])
    with tc:
        st.markdown(
            "<h1 style='text-align:center; font-size:clamp(1.5em, 7vw, 2.8em); font-weight:900; "
            "letter-spacing:3px; text-transform:uppercase; color:#F1EFE8; "
            "margin:0 0 6px 0; word-wrap:break-word;'>Radar Fundamentalista</h1>"
            "<p style='text-align:center; font-size:0.85em; color:rgba(255,255,255,0.4); "
            "letter-spacing:3px; text-transform:uppercase; margin:0 0 18px 0;'>Diego Castro</p>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='text-align:center; font-size:0.9em; color:#ccc; "
            "line-height:1.6; margin:0 0 12px 0;'>"
            "Ferramenta de análise quantitativa e qualitativa de ações brasileiras "
            "desenvolvida para apoiar o processo de tomada de decisão em investimentos "
            "de longo prazo.</p>"
            "<p style='text-align:center; font-size:0.85em; color:#aaa; "
            "line-height:1.6; margin:0 0 12px 0;'>"
            "O score proprietário combina múltiplos critérios com pesos diferenciados "
            "por setor: qualidade operacional, crescimento e consistência dos resultados, "
            "solidez financeira, valuation relativo, retorno ao acionista e "
            "governança corporativa — avaliada de forma qualitativa e aplicada "
            "como penalizador.</p>"
            "<p style='text-align:center; font-size:0.78em; color:#888; "
            "line-height:1.5; margin:0 0 16px 0;'>"
            "⚠️ As informações aqui contidas têm caráter exclusivamente educacional "
            "e não constituem recomendação de compra ou venda de ativos. "
            "Invista com responsabilidade.</p>",
            unsafe_allow_html=True
        )

    # Input e botão em coluna estreita
    il, ic, ir = st.columns([1.5, 1, 1.5])
    with ic:
        senha = st.text_input("", placeholder="senha de acesso",
                              type="password", label_visibility="collapsed")
        if st.button("Acessar →", use_container_width=True, type="primary"):
            senha_correta = st.secrets.get("SENHA_ACESSO", "")
            if senha == senha_correta and senha_correta != "":
                st.session_state.autenticado = True
                st.session_state.modo_exibicao = 'Cards'
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()

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
        return "#4CAF6D"
    elif porcentagem >= 25:
        return "#D4AF37"
    else:
        return "#D9534F"

# ---- Score Geral por Setor (0–10) ----
# Estrutura: 70% Qualidade + 30% Valuation
# Qualidade: ROE, CAGR, Dívida, Consistência do lucro (novo)
# Valuation: DY projetado (peso menor), P/L, P/VP
# Sem piso artificial — score honesto para ranking preciso

def consistencia_lucro(historico_lucro):
    """
    Avalia se o lucro cresceu de forma consistente nos últimos anos.
    Retorna valor entre 0 e 1:
    - 1.0: cresceu todos os anos
    - 0.5: cresceu na maioria
    - 0.0: caiu ou muito volátil
    """
    if not historico_lucro or len(historico_lucro) < 3:
        return 0.5  # sem dados suficientes: neutro
    anos  = sorted(historico_lucro.keys())
    vals  = [historico_lucro[a] for a in anos]
    crescimentos = [1 if vals[i] > vals[i-1] else 0 for i in range(1, len(vals))]
    taxa = sum(crescimentos) / len(crescimentos)
    # Bônus se o último ano foi o maior
    if vals[-1] == max(vals):
        taxa = min(1.0, taxa + 0.15)
    return round(taxa, 2)

def classificar_setor(setor):
    s = str(setor).lower()
    if any(x in s for x in ['banco', 'financeiro', 'holding']):
        return 'banco'
    if any(x in s for x in ['seguro', 'segur']):
        return 'seguradora'
    if any(x in s for x in ['elétric', 'eletric', 'energia', 'saneamento', 'utilities']):
        return 'capital_intensivo'
    if any(x in s for x in ['papel', 'celulose', 'mineração', 'minera', 'petróleo', 'petro', 'óleo', 'cíclico', 'química', 'siderur', 'borracha']):
        return 'ciclica'
    return 'geral'

def calcular_score(dy_num, pl_num, div_ebitda_num, cagr_num, roe_num, margem_num,
                   pvp_num=0, setor='', ticker='', historico_lucro=None):
    categoria  = classificar_setor(setor)
    consistencia = consistencia_lucro(historico_lucro or {})
    score = 0.0

    if categoria == 'banco':
        # QUALIDADE 70%: ROE (2.5) + CAGR (2.0) + Consistência (1.5) + Dívida (1.0) = 7.0
        score += min(roe_num / 25.0, 1.0) * 2.5
        score += min(cagr_num / 20.0, 1.0) * 2.0
        score += consistencia * 1.5
        score += max(0, (4 - div_ebitda_num) / 4.0) * 1.0
        # VALUATION 30%: P/VP (1.5) + P/L (1.0) + DY (0.5) = 3.0
        if pvp_num > 0:
            score += max(0, (2.0 - pvp_num) / 2.0) * 1.5
        if pl_num > 0:
            score += max(0, (12 - pl_num) / 12.0) * 1.0
        score += min(dy_num / 10.0, 1.0) * 0.5

    elif categoria == 'seguradora':
        # QUALIDADE 70%: ROE (2.5) + CAGR (2.0) + Consistência (1.5) + Margem (1.0) = 7.0
        score += min(roe_num / 25.0, 1.0) * 2.5
        score += min(cagr_num / 20.0, 1.0) * 2.0
        score += consistencia * 1.5
        score += min(margem_num / 40.0, 1.0) * 1.0
        # VALUATION 30%: P/L (1.5) + DY (1.5) = 3.0
        if pl_num > 0:
            score += max(0, (15 - pl_num) / 15.0) * 1.5
        score += min(dy_num / 10.0, 1.0) * 1.5

    elif categoria == 'capital_intensivo':
        # QUALIDADE 70%: CAGR (2.0) + Consistência (1.5) + Dívida até 4x (2.0) + ROE (1.5) = 7.0
        score += min(cagr_num / 15.0, 1.0) * 2.0
        score += consistencia * 1.5
        score += max(0, (4 - div_ebitda_num) / 4.0) * 2.0
        score += min(roe_num / 18.0, 1.0) * 1.5
        # VALUATION 30%: DY (2.0) + P/L (1.0) = 3.0
        score += min(dy_num / 10.0, 1.0) * 2.0
        if pl_num > 0:
            score += max(0, (18 - pl_num) / 18.0) * 1.0

    elif categoria == 'ciclica':
        # QUALIDADE 70%: ROE (2.5) + Dívida (2.0) + CAGR (1.5) + Consistência (1.0) = 7.0
        # Consistência menor pois cíclicas naturalmente oscilam
        score += min(roe_num / 20.0, 1.0) * 2.5
        score += max(0, (3 - div_ebitda_num) / 3.0) * 2.0
        score += min(cagr_num / 20.0, 1.0) * 1.5
        score += consistencia * 1.0
        # VALUATION 30%: DY (1.5) + P/VP (1.0) + P/L (0.5) = 3.0
        score += min(dy_num / 10.0, 1.0) * 1.5
        if pvp_num > 0:
            score += max(0, (2.0 - pvp_num) / 2.0) * 1.0
        if pl_num > 0:
            score += max(0, (15 - pl_num) / 15.0) * 0.5

    else:
        # GERAL
        # QUALIDADE 70%: ROE (2.5) + CAGR (2.0) + Consistência (1.5) + Dívida (1.0) = 7.0
        score += min(roe_num / 20.0, 1.0) * 2.5
        score += min(cagr_num / 20.0, 1.0) * 2.0
        score += consistencia * 1.5
        score += max(0, (5 - div_ebitda_num) / 5.0) * 1.0
        # VALUATION 30%: DY (1.5) + P/L (1.0) + P/VP (0.5) = 3.0
        score += min(dy_num / 10.0, 1.0) * 1.5
        if pl_num > 0:
            score += max(0, (20 - pl_num) / 20.0) * 1.0
        if pvp_num > 0:
            score += max(0, (3 - pvp_num) / 3.0) * 0.5

    # Penalização de governança
    pen = penalizacao_governanca(GOVERNANCA.get(ticker, {}).get('nota', 7.0))
    score = max(0.0, score + pen)

    # Multiplicador de outlook — cenário 2026 impacta o score
    score = score * penalizacao_outlook(ticker)

    return round(min(score, 10.0), 1)

def badge_score(score):
    if score >= 7:
        cor_bg, cor_txt, label = "#1a3a1a", "#4CAF6D", "Ótimo"
    elif score >= 5:
        cor_bg, cor_txt, label = "#3a3a10", "#D4AF37", "Bom"
    elif score >= 3:
        cor_bg, cor_txt, label = "#3a2010", "#C97D3B", "Regular"
    else:
        cor_bg, cor_txt, label = "#3a1010", "#D9534F", "Fraco"
    return f"""
    <div style="display:flex; align-items:center; gap:10px; margin-top:6px;">
        <span class="score-badge" style="background:{cor_bg}; color:{cor_txt}; border:1px solid {cor_txt};">
            ⭐ Score: {score}/10
        </span>
        <span style="color:{cor_txt}; font-size:0.9em; font-weight:bold;">{label}</span>
    </div>"""


# ---- Preço Justo Multi-Método (Bazin, Graham, Gordon) ----
def calcular_preco_justo(row, vpa_val=None, taxa_desconto=0.12, crescimento_max=0.08):
    """Calcula o preço justo por 3 métodos clássicos de valuation:
    - Bazin: dividendo projetado ÷ 6% (foco renda)
    - Graham: √(22,5 × LPA × VPA) (clássico value investing)
    - Gordon: dividendo×(1+g) ÷ (taxa_desconto−g) (crescimento de dividendos,
      g limitado a crescimento_max pra não estourar o modelo quando o CAGR
      reportado é muito alto/instável)
    Retorna dict com os 3 valores (None se não computável) + a cotação atual."""
    div_proj = limpar_valor(row.get('Dividendo por ação bruto projetado', 0))
    lpa = limpar_valor(row.get('LPA ESTIMADO', 0))
    cagr_pct = limpar_valor(row.get('CAGR lucros (últ. 5 anos)', 0))
    cot = limpar_valor(str(row.get('Cotação atual', 0)).replace('R$', ''))

    pj_bazin = (div_proj / 0.06) if div_proj > 0 else None
    pj_graham = ((22.5 * lpa * vpa_val) ** 0.5) if (lpa and lpa > 0 and vpa_val and vpa_val > 0) else None

    g = min(cagr_pct / 100, crescimento_max) if cagr_pct > 0 else 0
    pj_gordon = None
    if div_proj > 0 and taxa_desconto > g:
        pj_gordon = div_proj * (1 + g) / (taxa_desconto - g)

    return {
        'bazin': pj_bazin, 'graham': pj_graham, 'gordon': pj_gordon,
        'cotacao': cot if cot > 0 else None, 'g_usado': g,
    }


# ---- Dividend Safety Score (0-10) — risco de corte de dividendo ----
def calcular_dividend_safety(payout_raw, div_ebitda_num, roe_num, historico_lucro):
    """Score 0-10 separado do Score geral, focado SÓ em sustentabilidade do
    dividendo: Payout (35%) + Consistência de lucro (25%) + Dívida/EBITDA
    (20%) + ROE (20%)."""
    payout = limpar_valor(payout_raw) if payout_raw not in (None, '-', '') else None

    if payout is None or payout <= 0:
        score_payout = 5.0
    elif payout <= 60:
        score_payout = 10.0
    elif payout <= 90:
        score_payout = 7.0
    elif payout <= 110:
        score_payout = 5.0
    else:
        score_payout = 2.0

    consist = consistencia_lucro(historico_lucro or {})
    score_consist = consist * 10

    if div_ebitda_num <= 1:
        score_div = 10.0
    elif div_ebitda_num <= 2:
        score_div = 8.0
    elif div_ebitda_num <= 3:
        score_div = 6.0
    elif div_ebitda_num <= 4:
        score_div = 4.0
    else:
        score_div = 2.0

    if roe_num >= 20:
        score_roe = 10.0
    elif roe_num >= 15:
        score_roe = 8.0
    elif roe_num >= 10:
        score_roe = 6.0
    elif roe_num >= 5:
        score_roe = 4.0
    else:
        score_roe = 2.0

    score_final = round(score_payout * 0.35 + score_consist * 0.25 +
                        score_div * 0.20 + score_roe * 0.20, 1)

    if score_final >= 7:
        label, cor = "Segurança Alta", "#4CAF6D"
    elif score_final >= 4:
        label, cor = "Segurança Média", "#D4AF37"
    else:
        label, cor = "Risco de Corte", "#D9534F"

    return score_final, label, cor


# ---- Percentil Setorial — compara cada ativo aos pares do MESMO setor ----
def calcular_percentis_setoriais(ativos_com_score):
    """Pra cada ativo, calcula em que percentil ele está dentro do mesmo
    setor (coluna SETOR da planilha) em ROE, DY e P/L. 0 = pior do setor,
    100 = melhor do setor. Pra P/L, 'melhor' = mais barato (invertido)."""
    from collections import defaultdict
    grupos = defaultdict(list)
    for a in ativos_com_score:
        setor = a['row'].get('SETOR', 'Outros')
        grupos[setor].append(a)

    for setor, grupo in grupos.items():
        n = len(grupo)
        for a in grupo:
            a['n_setor'] = n
        if n <= 1:
            for a in grupo:
                a['percentil_roe'] = a['percentil_dy'] = a['percentil_pl'] = None
            continue

        roes = sorted(grupo, key=lambda a: a.get('roe_num_raw', 0))
        for idx, a in enumerate(roes):
            a['percentil_roe'] = round((idx / (n - 1)) * 100)
            a['rank_roe'] = n - idx  # 1 = melhor ROE do setor

        dys = sorted(grupo, key=lambda a: a.get('dy_num', 0))
        for idx, a in enumerate(dys):
            a['percentil_dy'] = round((idx / (n - 1)) * 100)
            a['rank_dy'] = n - idx  # 1 = melhor DY do setor

        com_pl = [a for a in grupo if a.get('pl_num', 0) > 0]
        sem_pl = [a for a in grupo if a.get('pl_num', 0) <= 0]
        pls = sorted(com_pl, key=lambda a: -a.get('pl_num', 0))  # do mais caro pro mais barato
        n_pl = len(pls)
        for idx, a in enumerate(pls):
            a['percentil_pl'] = round((idx / (n_pl - 1)) * 100) if n_pl > 1 else None
            a['rank_pl'] = n_pl - idx  # 1 = mais barato (melhor P/L) do setor
            a['n_pl'] = n_pl
        for a in sem_pl:
            a['percentil_pl'] = None
            a['rank_pl'] = None
            a['n_pl'] = n_pl

    return ativos_com_score


# ---- Ranking "Fórmula Mágica" (Greenblatt) ----
# Busca ROIC pra TODOS os ativos — usado só sob demanda (botão), não a cada
# carregamento da tela principal, já que são até 40 requisições sequenciais
# ao Fundamentus (mitigado pelo cache de 24h de get_indicadores_fundamentus:
# só é lento na primeira vez do dia).
@st.cache_data(ttl=86400, show_spinner=False)
def get_roic_bulk(tickers_tuple):
    """Retorna dict ticker -> ROIC (float) ou None, pra uma lista de tickers."""
    resultado = {}
    for t in tickers_tuple:
        ind, _ = get_indicadores_fundamentus(t)
        resultado[t] = _ind_buscar(ind, 'roic') if ind else None
    return resultado


def calcular_ranking_formula_magica(ativos_com_score):
    """Fórmula Mágica de Joel Greenblatt: combina Earnings Yield (1/P-L,
    quanto maior melhor) com ROIC (quanto maior melhor). Ranqueia cada um
    separadamente e SOMA as posições — menor soma = melhor colocado no
    ranking combinado (ativo bom E barato ao mesmo tempo)."""
    tickers = tuple(a['row']['CÓDIGO'] for a in ativos_com_score)
    roics = get_roic_bulk(tickers)

    candidatos = []
    for a in ativos_com_score:
        ticker = a['row']['CÓDIGO']
        pl = a.get('pl_num', 0)
        roic = roics.get(ticker)
        if pl and pl > 0 and roic is not None:
            candidatos.append({
                'ticker': ticker, 'earnings_yield': 1 / pl, 'roic': roic,
                'pl': pl, 'score_geral': a['score'],
            })

    if not candidatos:
        return []

    candidatos.sort(key=lambda c: -c['earnings_yield'])
    for i, c in enumerate(candidatos):
        c['rank_ey'] = i + 1
    candidatos.sort(key=lambda c: -c['roic'])
    for i, c in enumerate(candidatos):
        c['rank_roic'] = i + 1
    for c in candidatos:
        c['rank_total'] = c['rank_ey'] + c['rank_roic']
    candidatos.sort(key=lambda c: c['rank_total'])
    for i, c in enumerate(candidatos):
        c['posicao'] = i + 1
    return candidatos

# ---- Gráfico de barras — Histórico DY ----
def mini_grafico_dy(historico_dy):
    if not historico_dy:
        return "<span style='color:#888; font-size:0.9em;'>Histórico indisponível</span>"
    max_val = max(historico_dy.values()) or 1
    barras = ""
    for ano, val in sorted(historico_dy.items()):
        altura = max(int((val / max_val) * 90), 6)
        cor = "#4CAF6D" if val >= 8 else "#5B8DB8"
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



# ---- Dados de Governança e Outlook 2026 ----
GOVERNANCA = {
    "BBSE3":  {"nota": 9.2, "obs": "Subsidiária do BB com alta transparência, política clara de dividendos, sem polêmicas relevantes. Tag along 100%."},
    "ITUB4":  {"nota": 8.8, "obs": "Tag along 100%, sólido histórico com minoritários. Controle familiar bem gerido e previsível."},
    "BBAS3":  {"nota": 6.8, "obs": "Banco público com interferência política crescente. Revisão de guidance sem aviso e surpresa na inadimplência em 2023-24 penalizam a relação com minoritários."},
    "BBDC3":  {"nota": 7.2, "obs": "Histórico de polêmicas com minoritários em 2021-22. Tag along 100% mas ações PN sem voto pesam."},
    "ABCB4":  {"nota": 8.0, "obs": "Boa transparência, histórico limpo. Comunicação consistente para o porte."},
    "BRSR6":  {"nota": 6.5, "obs": "Banco público estadual do RS — interferência política do governo gaúcho é risco real e recorrente."},
    "SANB3":  {"nota": 7.8, "obs": "Controle espanhol traz boas práticas europeias. Tag along 100%."},
    "BMGB4":  {"nota": 6.0, "obs": "Histórico de irregularidades no passado. Governança melhorou mas ainda em reconstrução de reputação."},
    "BPAC11": {"nota": 8.5, "obs": "BTG — alta transparência, management alinhado ao resultado. Referência no setor financeiro."},
    "IRBR3":  {"nota": 4.5, "obs": "Fraudes contábeis graves em 2020, gestão substituída. Recuperação em curso mas histórico pesa estruturalmente."},
    "PSSA3":  {"nota": 8.8, "obs": "Porto Seguro — governança exemplar, família fundadora alinhada com minoritários."},
    "CXSE3":  {"nota": 8.0, "obs": "Boa transparência. Vinculação à Caixa traz algum risco político indireto."},
    "ITSA4":  {"nota": 8.5, "obs": "Holding do Itaú — muito transparente, histórico consistente, forte alinhamento com minoritários."},
    "PETR4":  {"nota": 6.2, "obs": "Lava Jato no passado (peso leve — +10 anos de melhora). Interferência política ainda estrutural. Comunicação melhorou muito, mas DNA estatal persiste."},
    "VALE3":  {"nota": 5.5, "obs": "Mariana e Brumadinho — passivo ESG e reputacional gravíssimo. Governança melhorou mas desconto permanente é justo."},
    "BRAP4":  {"nota": 7.0, "obs": "Holding da Vale — herda riscos da controlada, mas histórico próprio limpo."},
    "CMIN3":  {"nota": 7.2, "obs": "CSN Mineração — boa transparência, mas controle concentrado no grupo CSN."},
    "GGBR3":  {"nota": 6.5, "obs": "Gerdau — controle familiar forte, tag along adequado, sem grandes polêmicas recentes."},
    "KLBN4":  {"nota": 8.2, "obs": "Klabin — excelente comunicação com mercado, política de dividendos clara e previsível."},
    "UNIP6":  {"nota": 5.5, "obs": "Controle familiar fechado, baixa liquidez, comunicação limitada com minoritários."},
    "LEVE3":  {"nota": 8.5, "obs": "Mahle Metal Leve — controle alemão traz práticas europeias exemplares."},
    "SHUL4":  {"nota": 7.5, "obs": "Schulz — boa governança para o porte, comunicação adequada e histórico limpo."},
    "VULC3":  {"nota": 7.8, "obs": "Vulcabras — melhora consistente nos últimos anos, gestão cada vez mais transparente."},
    "TIMS3":  {"nota": 8.8, "obs": "TIM — controle italiano, práticas europeias, tag along 100%. Referência no setor."},
    "ALOS3":  {"nota": 8.5, "obs": "Allos — fusão recente mas boa integração, comunicação forte com investidores."},
    "KEPL3":  {"nota": 7.5, "obs": "Kepler Weber — boa governança para o porte, nicho bem gerido."},
    "SLCE3":  {"nota": 7.0, "obs": "SLC Agrícola — transparente, mas setor cíclico gera volatilidade nos comunicados."},
    "RANI3":  {"nota": 7.8, "obs": "Irani — governança sólida, comunicação consistente, estrutura familiar bem organizada."},
    "CMIG4":  {"nota": 6.5, "obs": "Cemig — empresa pública de MG, risco de interferência política relevante."},
    "CPLE3":  {"nota": 6.8, "obs": "Copel — privatizada recentemente, governança em transição positiva."},
    "EGIE3":  {"nota": 8.8, "obs": "Engie — controle francês, ESG exemplar, uma das melhores governanças do setor elétrico."},
    "TAEE11": {"nota": 8.2, "obs": "Taesa — previsibilidade de receita e dividendos, comunicação muito clara."},
    "ISAE4":  {"nota": 7.0, "obs": "Isa Cteep — controle colombiano, boa transparência, menor histórico local."},
    "CPFE3":  {"nota": 8.0, "obs": "CPFL — controle State Grid (China), governança melhorou após aquisição."},
    "SBSP3":  {"nota": 5.8, "obs": "Sabesp — privatização recente, governança em transição. Melhora em curso."},
    "SAPR4":  {"nota": 6.2, "obs": "Sanepar — empresa pública do PR, histórico razoável mas risco político persiste."},
    "CSMG3":  {"nota": 5.5, "obs": "Copasa — empresa pública de MG, interferência política frequente nas decisões."},
    "AXIA3":  {"nota": 8.0, "obs": "Holding de fibra — nova no mercado, mas estrutura de governança bem desenhada."},
    "B3SA3":  {"nota": 9.0, "obs": "B3 — autolistada, padrão máximo de governança no Brasil. Referência para o mercado."},
    "BRBI11": {"nota": 7.5, "obs": "BR Partners — gestão alinhada, transparência adequada para o porte."},
    "CYRE3":  {"nota": 8.3, "obs": "Controle da família Schahin, listada no Novo Mercado com tag along 100%. Criação recente de classe de ações preferenciais especiais (pra distribuir reservas antes da tributação de dividendos em 2026) gerou reação negativa do mercado, mas a estrutura de governança permanece sólida."},
    "DIRR3":  {"nota": 8.5, "obs": "Controle da família fundadora (Gontijo), reforçado por acordo de voto de 10 anos após reorganização societária em 2026 (sem mudança de controle). Novo Mercado, tag along 100%, histórico limpo com minoritários."},
    "MDNE3":  {"nota": 7.0, "obs": "Estrutura anterior da joint venture com a Direcional na marca Ún1ca (controladores/executivos detinham 30% pessoalmente, diluindo o resultado capturado pela companhia) gerou desconforto entre minoritários — resolvida em abr/2026 com a Moura Dubeux assumindo 100%. Sinal positivo de resposta à pressão do mercado, mas o episódio pesa na nota."},
    "CURY3":  {"nota": 8.5, "obs": "Joint venture entre a família Cury (fundadora) e a Cyrela (50% cada). Novo Mercado, comitê de ESG ativo, sem polêmicas relevantes com minoritários."},
    "LREN3":  {"nota": 8.8, "obs": "Capital pulverizado desde 2005 (sem controlador definido), listada no Novo Mercado, maioria independente no Conselho de Administração. Forte reputação ESG e de transparência."},
    "GRND3":  {"nota": 8.0, "obs": "Controle da família fundadora (Grendene Bartelle), com reorganização societária recente (transferência de participação para fundo exclusivo, sem mudança de controle ou regras de governança). Política financeira conservadora, praticamente sem dívida líquida."},
    "CGRA4":  {"nota": 6.5, "obs": "Classificada como 'Governança Tradicional' (não é Novo Mercado) — nível mais básico de exigências da B3. Baixa liquidez (small cap familiar do varejo gaúcho). Aumento de capital recente (abr/2026) via subscrição privada."},
    "WEGE3":  {"nota": 8.8, "obs": "Novo Mercado, capital pulverizado (free float ~35%), forte reputação de transparência e previsibilidade entre as blue chips da bolsa brasileira. Sem polêmicas relevantes."},
    "PRIO3":  {"nota": 8.5, "obs": "Novo Mercado, capital pulverizado sem controlador definido. Histórico de aquisições bem executadas (ativos maduros) e comunicação transparente com o mercado."},
    "EQTL3":  {"nota": 8.3, "obs": "Novo Mercado, capital pulverizado, sem controlador definido. Estratégia de aquisição de concessões em dificuldade seguida de turnaround agressivo é o 'DNA' da empresa — aumenta o risco de execução mas é parte conhecida da tese, não um problema de governança em si."},
    "JHSF3":  {"nota": 7.0, "obs": "Controle concentrado do fundador José Auriemo Neto, com papel decisório forte nas estratégias da companhia. Presença de investidores institucionais ajuda a equilibrar a governança, mas a concentração de poder no fundador é um ponto de atenção típico de holdings familiares."},
    "POMO4":  {"nota": 7.5, "obs": "Controle de famílias fundadoras com longa trajetória, mantendo continuidade estratégica. Ações PN (POMO4) não dão direito a voto — quem compra PN fica sujeito às decisões do bloco ON controlador, estrutura típica de empresas mais antigas da B3."},
}

OUTLOOK_2026 = {
    "BBSE3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Atenção: exposição ao agro (granizo, seca, El Niño) pode pressionar sinistros em 2026. Monitorar sinistralidade agrícola no 1T26 antes de ampliar posição."},
    "ITUB4":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Ciclo de crédito favorável, inadimplência sob controle, ROE elevado. Um dos melhores momentos operacionais da história. Perspectiva positiva para 2026."},
    "BBAS3":  {"icone": "🔴", "cor": "#D9534F", "texto": "Carteira agro comprometida pela crise do crédito rural — inadimplência em alta e sem sinais de reversão rápida. Guidance revisado para baixo sem aviso. Banco público sujeito a pressão política. Perspectiva negativa para 2026 — aguardar pelo menos 2 trimestres antes de reavaliar."},
    "BBDC3":  {"icone": "🟡", "cor": "#D4AF37", "texto": "Recuperação em curso após anos difíceis. Lucro voltando a crescer mas abaixo dos pares. Posição especulativa de melhora — cautela com alocação."},
    "ABCB4":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Carteira corporativa de alta qualidade, inadimplência estruturalmente baixa. Perspectiva positiva, menos sensível ao ciclo de varejo."},
    "BRSR6":  {"icone": "🔴", "cor": "#D9534F", "texto": "Duplo impacto: crise do crédito rural gaúcho + reflexos das enchentes de 2024 ainda presentes na carteira. Inadimplência estruturalmente elevada para 2026. Perspectiva negativa."},
    "SANB3":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Ciclo de melhora operacional. ROE subindo, foco em eficiência. Perspectiva moderadamente positiva para 2026."},
    "BMGB4":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Nicho de consignado INSS sob pressão regulatória. Teto de juros pode impactar margens. Monitorar evolução da regulação em 2026."},
    "BPAC11": {"icone": "✅", "cor": "#4CAF6D", "texto": "Forte expansão de receitas recorrentes. Menos dependente do ciclo de crédito. Uma das melhores perspectivas do setor financeiro para 2026."},
    "IRBR3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Ressegurador em recuperação pós-fraude. Resultados melhorando, mas histórico exige cautela. El Niño e eventos climáticos extremos são risco relevante."},
    "PSSA3":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Momento operacional sólido. Seguros auto e residencial com bons resultados. Perspectiva positiva, mas monitorar sinistralidade climática."},
    "CXSE3":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Crescimento consistente de prêmios via rede da Caixa. Vantagem competitiva de distribuição enorme. Perspectiva positiva para 2026."},
    "ITSA4":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Holding do Itaú — resultado acompanha o banco. Desconto histórico pode se fechar. Perspectiva positiva com menor volatilidade que o banco diretamente."},
    "PETR4":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Petróleo em patamar moderado (~$70-75). Risco fiscal e de interferência na política de dividendos. Monitorar anúncio de investimentos e possível revisão da remuneração em 2026."},
    "VALE3":  {"icone": "🔴", "cor": "#D9534F", "texto": "Minério de ferro pressionado pela desaceleração chinesa. Acordo de Mariana ainda em negociação (provisão bilionária). 2026 desafiador — aguardar estabilização do cenário China."},
    "BRAP4":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Herda o cenário desafiador da Vale com desconto adicional de holding. Monitorar acordo de Mariana e preço do minério."},
    "CMIN3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Sensível ao preço do minério e desaceleração chinesa. Perspectiva cautelosa para 2026."},
    "GGBR3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Dependente do ciclo de construção civil. Perspectiva neutra — programa de infraestrutura pode ser catalisador positivo em 2026."},
    "KLBN4":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Celulose e papel com demanda resiliente. Expansão Puma II maturando. Perspectiva positiva para 2026, menos cíclica que pares do setor."},
    "UNIP6":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Margens pressionadas pelo ciclo químico global e dumping chinês de petroquímicos. Perspectiva neutra a negativa para 2026."},
    "LEVE3":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Reposição automotiva resiliente. Transição para elétricos é risco de longo prazo, irrelevante para 2026. Perspectiva positiva."},
    "SHUL4":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Compressores industriais com demanda estável. Nicho protegido e bem gerido. Perspectiva positiva para 2026."},
    "VULC3":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Marca consolidada no esportivo. Expansão de margens em curso. Perspectiva positiva, dependente do consumo doméstico."},
    "TIMS3":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Crescimento consistente de receita e margens. Mercado consolidado favorece rentabilidade. Excelente perspectiva para 2026."},
    "ALOS3":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Shoppings em ciclo favorável. Consumo aquecido e vacância baixa. Integração da fusão gerando sinergias. Perspectiva positiva para 2026."},
    "KEPL3":  {"icone": "🔴", "cor": "#D9534F", "texto": "Cenário desafiador: inadimplência rural elevada e crédito agrícola travado reduzem investimentos em armazenagem. Clientes endividados adiam expansões. 2026 deve ser ano de contração de receita — aguardar estabilização do crédito rural."},
    "SLCE3":  {"icone": "🔴", "cor": "#D9534F", "texto": "Agro em momento crítico: margens comprimidas por queda de commodities, câmbio desfavorável e clima incerto. Produtores endividados e sem apetite a risco. 2026 deve trazer queda de receita e resultado — cautela máxima."},
    "RANI3":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Embalagens de papel com demanda resiliente e crescente. Expansão de capacidade em andamento. Perspectiva positiva para 2026."},
    "CMIG4":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Distribuição e geração reguladas, mas gestão pública limita eficiência. Perspectiva neutra. Atenção ao processo de renovação de concessões."},
    "CPLE3":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Privatização trazendo eficiência. Perspectiva positiva com potencial de redução de custos e melhora de margens em 2026."},
    "EGIE3":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Geração renovável com contratos longos. Menor exposição a risco hidrológico por mix diversificado. Perspectiva excelente para 2026."},
    "TAEE11": {"icone": "✅", "cor": "#4CAF6D", "texto": "Transmissão com RAP garantido — completamente independente de hidrologia. Perspectiva muito positiva e previsível para 2026."},
    "ISAE4":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Transmissão regulada, receita previsível. Perspectiva positiva similar à Taesa, com ciclo de revisão tarifária favorável."},
    "CPFE3":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Mix equilibrado de distribuição e geração. Perspectiva positiva beneficiada por revisão tarifária e expansão renovável em 2026."},
    "SBSP3":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Pós-privatização acelerando investimentos. Perspectiva positiva de médio prazo, mas 2026 ainda é ano de transição e reorganização."},
    "SAPR4":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Saneamento com demanda inelástica. Perspectiva estável. Revisão tarifária pendente pode ser catalisador positivo em 2026."},
    "CSMG3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Ainda pública. Privatização em discussão pode ser catalisador, mas risco político de MG é relevante. Perspectiva neutra."},
    "AXIA3":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Fibra óptica em expansão acelerada. Demanda por conectividade crescente e estrutural. Perspectiva positiva para 2026."},
    "B3SA3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Dependente do volume de negociação. Juros altos reduzem fluxo para renda variável. Melhora depende de queda de juros e volta do PF — perspectiva neutra para 2026."},
    "BRBI11": {"icone": "✅", "cor": "#4CAF6D", "texto": "Banco de investimento em crescimento. Perspectiva positiva dependente do ambiente de M&A e mercado de capitais em 2026."},
    "CYRE3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Bonificação em PN especiais (criada pra antecipar valor antes da tributação de dividendos a partir de 2026) provocou queda nos papéis na virada do ano. Negócio segue sólido e diversificado, mas atenção à diluição e à reação do mercado à nova estrutura de capital."},
    "DIRR3":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Foco em habitação popular (MCMV Faixas 1-3) torna o negócio mais resiliente ao ciclo de juros. Geração de caixa forte, baixo endividamento e dividendos elevados. Início de 2026 com fundamentos sólidos e ROIC bem acima do custo de capital."},
    "MDNE3":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Maior construtora do Nordeste. Follow-on de R$500 milhões em jan/2026 dobrou a liquidez do papel. Marca Única (baixa renda/MCMV) é o principal vetor de crescimento, com parceria com a Direcional. Dividend yield esperado de ~7% para 2026."},
    "CURY3":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Foco em SP e RJ, MCMV + médio padrão. ROE de ~78% e múltiplos baratos (P/L 2026E entre 7x-8,5x). Riscos: pressão de custos de construção, cancelamentos e sensibilidade a mudanças no financiamento do MCMV/FGTS."},
    "LREN3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Setor de varejo de moda pressionado por alta alavancagem das famílias, juros altos e concorrência de plataformas cross-border (Shein, AliExpress). Em contrapartida, P/VPA perto de mínimas históricas (~1,5x) e analistas (Citi, Santander, BTG) seguem recomendando compra, com plano estratégico 2026-2030 prevendo aceleração de aberturas de loja."},
    "GRND3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Lucro recuou em 2025 e o dividendo extraordinário recente (~R$1 bi) não deve se repetir no mesmo nível — payout acima de 170% é insustentável estruturalmente. Caixa líquido robusto (~R$1,1 bi) e baixa alavancagem sustentam a tese de renda, mas crescimento operacional é fraco; 2026 deve trazer normalização dos proventos."},
    "CGRA4":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Varejo regional tradicional (tecidos/vestuário, RS), baixa cobertura de analistas e liquidez reduzida. Aumento de capital recente dilui a base acionária. Distribuição de JCP retomada em mai/2026, mas sem garantia de regularidade dado o histórico de proventos irregulares."},
    "WEGE3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "1T26 fraco: lucro -5,7% A/A, receita -6,1%, puxados por queda de 36% em GTD doméstico (solar) e câmbio desfavorável. Bancos cortaram projeção de lucro 2026. BTG mantém compra apostando em reaceleração via T&D a partir do 2S26/2027. Curto prazo exige cautela; tese estrutural de longo prazo permanece."},
    "PRIO3":  {"icone": "✅", "cor": "#4CAF6D", "texto": "1T26 forte: produção +42% T/T, lifting cost caiu para ~US$9,4/bbl, EBITDA ajustado quase dobrou T/T. Alavancagem caiu para 2,0x dívida líquida/EBITDA. Wahoo entrou em produção sem problemas. Queda da ação no pregão foi por correção do petróleo, não por fraqueza operacional."},
    "EQTL3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "1T26 misto: EBITDA ajustado +11,3% A/A (acima do consenso), mas lucro líquido ajustado caiu -23,6%, pressionado por despesa financeira maior (CDI médio subiu A/A) e maior dívida. Distribuição segue como destaque operacional positivo. Mercado reagiu de forma cautelosa."},
    "JHSF3":  {"icone": "✅", "cor": "#4CAF6D", "texto": "Melhor 1T da história da companhia: lucro +9,3% A/A, Ebitda ajustado +27%, receita +33%. Crescimento em shoppings, hospitalidade (Fasano) e expansão internacional (Miami, Punta del Este, Milão). Caixa líquido ajustado de R$1,8bi reforça a estrutura de capital mais sólida da história."},
    "POMO4":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "1T26 neutro: receita -1% A/A, EBITDA recorrente estável, margem mantida apesar de menor produção. Mercado externo (México) fraco. XP e BTG mantêm compra, citando catalisadores: programa Move Brasil, leilão Caminho da Escola e pedidos do Ministério da Saúde — volumes devem melhorar a partir do 2º trimestre."},
}

# ---- Estudos Específicos ----
# Diferente de GOVERNANCA/OUTLOOK_2026 (que tentam cobrir os 40), este
# dicionario e DELIBERADAMENTE ESPARSO: so entra ticker que tenha um estudo
# de verdade, especifico, que agregue algo que nao se acha pronto por ai.
# Sem entrada = sem card (nao aparece "N/A" pra ninguem, simplesmente nao
# mostra nada -- igual GOVERNANCA/OUTLOOK_2026 quando faltam).
#
# 'metrica': (label, valor) opcional -- numero computado pelo proprio RADAR
# (ex: pvp_str) que ancora o estudo num dado ATUAL, nao so historico.
# ---- Análise do Último Resultado ----
# Diferente de GOVERNANCA/OUTLOOK_2026 (que tentam cobrir os 50), e diferente
# de ESTUDOS_ESPECIFICOS (permanente), este dicionário e atualizado a cada
# resultado trimestral -- fica "congelado" entre uma divulgação e outra (nao
# se apaga, nao muda sozinho). Pesquisado e escrito por mim (Claude) a
# pedido do Diego, com base em releases, casas de análise (XP, BTG, Genial,
# Nord, etc) e noticias -- NAO e dado estruturado/automatico como o resto
# do RADAR. Atualizar = o Diego pede aqui no chat, eu pesquiso de novo.
ANALISE_RESULTADO = {
    "WEGE3": {
        "trimestre": "1T26", "data": "29/04/2026",
        "numeros": "Lucro líquido R$1,46 bi (-5,7% A/A, -8,2% T/T) — abaixo do consenso "
                   "(R$1,58bi esperado). Receita R$9,46bi (-6,1% A/A). EBITDA R$2,10bi "
                   "(-3,2% A/A), margem EBITDA 22,2% (+0,6 p.p. A/A). ROIC 33,1% (estável).",
        "pontos_fortes": "Margens resilientes mesmo com queda de receita. ROIC elevado e "
                   "estável. Mercado externo resiliente (receita em dólar +16% A/A). "
                   "Caixa líquido subiu para R$3,3bi.",
        "pontos_fracos": "Receita doméstica de Geração/Transmissão/Distribuição caiu 36% "
                   "A/A (forte queda em solar). Câmbio desvalorizado prejudicou a conversão "
                   "da receita externa. Bancos cortaram estimativa de lucro 2026 (Safra "
                   "-10,7%, Itaú BBA de R$6,6bi para R$6bi).",
        "expectativa": "BTG mantém compra (TP R$65, upside ~37%) apostando em reaceleração "
                   "da divisão de Transmissão & Distribuição a partir do 2S2026/2027. Risco "
                   "de novas revisões para baixo no curto prazo segundo a XP. Tese estrutural "
                   "de longo prazo (eletrificação, automação industrial) segue intacta para "
                   "a maioria das casas, mas o próximo trimestre precisa mostrar reversão.",
    },
    "PRIO3": {
        "trimestre": "1T26", "data": "05/05/2026",
        "numeros": "Produção +42% T/T (~155kbpd). Lifting cost caiu para ~US$9,4-9,5/bbl. "
                   "EBITDA ajustado quase dobrou T/T (~US$839-859mi). Volume vendido +45% "
                   "(14,8 milhões de barris). Receita +60% (Brent +5% e menor desconto).",
        "pontos_fortes": "Forte tração operacional: eficiência de 95-99% nos clusters. "
                   "Wahoo entrou em produção sem problemas. Alavancagem caiu para 2,0x "
                   "dívida líquida/EBITDA (de 2,3x no 4T25). Desconto vs. Brent caiu para "
                   "US$8 (pode cair para US$5-6 no 2T26).",
        "pontos_fracos": "Geração de caixa ficou perto de zero no trimestre, por causa do "
                   "capex de Wahoo (US$300mi) e consumo de capital de giro. Dívida líquida "
                   "ainda em ~US$4,3bi. Ação caiu no pregão de divulgação, mas por correção "
                   "do petróleo (tensão no Oriente Médio), não por fraqueza do resultado.",
        "expectativa": "BTG eleva preço-alvo para R$72/ação, citando contribuição mais cheia "
                   "de Wahoo no 2T26, entrada do 4º poço e queda adicional de custo em "
                   "Peregrino. Management mantém meta de 1,0x dívida líquida/EBITDA até fim "
                   "de 2027 (Genial considera conservador). Sem recompra ou dividendo extra "
                   "esperado neste ano.",
    },
    "EQTL3": {
        "trimestre": "1T26", "data": "14/05/2026",
        "numeros": "Receita líquida R$12,7-12,8bi (+12% A/A). EBITDA ajustado R$2,9bi "
                   "(+11,3% A/A, acima do consenso). Lucro líquido ajustado R$359mi "
                   "(-23,6% A/A).",
        "pontos_fortes": "Distribuição segue como motor: margem bruta ajustada do segmento "
                   "+14%, puxada por efeito tarifário e crescimento de mercado (destaque "
                   "Maranhão, Pará, Piauí). Sabesp (equivalência patrimonial) contribuiu com "
                   "R$254mi, crescendo R$40mi A/A — tese de turnaround avançando.",
        "pontos_fracos": "Lucro líquido caiu apesar do EBITDA forte, pressionado por despesa "
                   "financeira maior (CDI médio subiu A/A, dívida bruta +14,7%). PMSO ficou "
                   "13% acima do esperado pela XP, com inadimplência em algumas concessões. "
                   "Renováveis ainda pressionado por restrições de geração.",
        "expectativa": "Em base comparável (mesmos ativos), lucro ficou praticamente estável "
                   "(-0,3%). XP espera reação levemente negativa do mercado, mas mantém "
                   "EQTL3 como 'must-own' do setor, com TIR real de 12,5%. Capex elevado "
                   "(R$2,58bi) sustenta crescimento de longo prazo.",
    },
    "JHSF3": {
        "trimestre": "1T26", "data": "08/05/2026",
        "numeros": "Lucro líquido R$371,6mi (+9,3% A/A) — melhor 1º trimestre da história "
                   "da companhia. Receita líquida R$537,7mi (+33,3% A/A). EBITDA ajustado "
                   "R$250,6mi (+27% A/A, acima do esperado pelo mercado).",
        "pontos_fortes": "Crescimento em todas as verticais: shoppings (+8,4% vendas, SSR "
                   "+11,5% acima da inflação), hospitalidade/Fasano, residências de alto "
                   "padrão (+45% receita). Caixa líquido ajustado de R$1,8bi (revertendo "
                   "dívida líquida de R$1,5bi um ano atrás) — estrutura de capital mais "
                   "sólida da história. Expansão internacional acelerando (Miami, Punta "
                   "del Este, Milão).",
        "pontos_fracos": "Parte relevante do lucro (R$278mi) vem de apreciação contábil de "
                   "propriedades, sem efeito caixa imediato. Margem EBITDA recuou 2,4 p.p. "
                   "(despesas operacionais +36,8%). Dívida bruta subiu 5% (nova captação "
                   "via CRI).",
        "expectativa": "XP vê potencial de continuidade com a expansão internacional do "
                   "Fasano, crescimento de shoppings e o aeroporto Catarina (+18,3% "
                   "movimentos) como próximo catalisador. Empresa segue investindo em ativos "
                   "de luxo fora do Brasil — risco e oportunidade ao mesmo tempo.",
    },
    "POMO4": {
        "trimestre": "1T26", "data": "05/05/2026",
        "numeros": "Receita líquida R$1,66bi (-1,3% A/A, -36% T/T por sazonalidade). EBITDA "
                   "R$305mi (+16,3% A/A, mas inclui ganho não recorrente da NFI/Canadá). "
                   "Lucro líquido R$264,6mi (+8,8% A/A), margem 16% (vs 14,5% no 1T25).",
        "pontos_fortes": "Margem sustentada por mix de produtos de maior valor agregado, "
                   "mesmo com menor volume produzido (-11% A/A). Alavancagem muito baixa "
                   "(dívida líquida/EBITDA ~0,2x). Equivalência patrimonial da NFI saltou "
                   "de R$16mi para R$76mi (efeito não recorrente).",
        "pontos_fracos": "Exportações caíram 27% em unidades (México fraco). EBITDA "
                   "recorrente, excluindo o ganho não recorrente da NFI, ficou praticamente "
                   "estável A/A (R$236mi) — resultado mais neutro do que o número headline "
                   "sugere. XP e BTG apontam números um pouco abaixo das próprias estimativas.",
        "expectativa": "Catalisadores concretos pela frente: programa Move Brasil (R$2bi "
                   "alocados a ônibus), leilão Caminho da Escola (~5,2 mil unidades "
                   "garantidas, podendo chegar a 7,2 mil) e pedidos do Ministério da Saúde "
                   "a partir do 2T26. BTG/XP mantêm compra; dividend yield na faixa de 7-8% "
                   "considerado atrativo dado valuation de 6-7x P/L 2026.",
    },
    "RANI3": {
        "trimestre": "1T26", "data": "30/04/2026",
        "numeros": "Lucro líquido R$19,4mi (-68,1% A/A, -50,2% T/T) — bem abaixo do "
                   "consenso (Bloomberg esperava R$44mi). Receita líquida R$409,8mi (-3,1% "
                   "A/A). EBITDA ajustado R$113,5mi (-17,1% A/A), margem 27,7% (-4,5 p.p.). "
                   "Dívida líquida/EBITDA em 2,11x (melhora vs 2,21x no 1T25).",
        "pontos_fortes": "ROIC subiu para 12,3% (+1,0 p.p. A/A), mantendo spread positivo "
                   "sobre o custo da dívida. Alavancagem caiu (de 2,21x para 2,11x). Lucro "
                   "recorrente acumulado em 12 meses (desconsiderando ativos biológicos) "
                   "cresceu 13,3% A/A, para R$102,9mi — mostra que o trimestre fraco foi "
                   "pontual, não uma deterioração estrutural. Geração de caixa mantida, com "
                   "proposta de dividendo (25% do lucro).",
        "pontos_fracos": "Queda forte e concentrada em eventos pontuais: parada programada "
                   "da Máquina de Papel 5 (Projeto Gaia XI) e inspeção bianual da Caldeira "
                   "de Força (parada da MP#1), somando R$20,7mi de impacto negativo no "
                   "EBITDA. Problema técnico no transformador do turbo gerador 4 (TG4) "
                   "obrigou compra extra de energia de terceiros (~R$6,1mi de efeito "
                   "negativo adicional). Resultado ficou bem abaixo das expectativas do "
                   "mercado.",
        "expectativa": "A própria empresa afirma que, sem os efeitos das paradas "
                   "programadas, o EBITDA teria CRESCIDO na comparação anual — ou seja, o "
                   "problema é tratado como temporário/pontual, ligado ao calendário de "
                   "manutenção do Projeto Gaia, não a uma fraqueza de demanda. Mercado deve "
                   "observar o 2T26 para confirmar se a operação volta ao normal sem as "
                   "paradas programadas.",
    },
    "PSSA3": {
        "trimestre": "1T26", "data": "07/05/2026",
        "numeros": "Lucro líquido total R$1,13bi (+36,3% A/A) — lucro recorrente de "
                   "R$958mi (+15,1% A/A), 8% acima do consenso. ROAE de 29,0% (vs 23,9% "
                   "no 1T25). Receita total R$10,58bi (+8,8% A/A).",
        "pontos_fortes": "Quinto trimestre consecutivo de crescimento de dois dígitos no "
                   "lucro recorrente. Vertical Seguro entregou lucro de R$467mi (+49% A/A) "
                   "com melhora de sinistralidade (índice combinado caiu 4 p.p., para 85%). "
                   "Saúde cresceu 20% no lucro, com 858 mil vidas (+22%). Bank cresceu 10% "
                   "no lucro mesmo com custo de crédito mais alto, puxado por carteira "
                   "+13,7%.",
        "pontos_fracos": "Resultado financeiro caiu ~20% (R$307mi vs R$382,6mi), por "
                   "rolagem de títulos a taxas melhores — efeito esperado se revertendo "
                   "nos próximos trimestres. Perdas de crédito no Bank subiram 44,3% A/A, "
                   "sinal de ambiente de crédito mais desafiador. Parte da melhora do ROAE "
                   "recorrente veio de uma alíquota de impostos menor, não só de operação "
                   "mais lucrativa.",
        "expectativa": "Casas de análise avaliam o resultado como positivo, com "
                   "diversificação (Saúde + Bank) sustentando o crescimento enquanto o "
                   "Seguro Auto (negócio principal histórico) enfrenta crescimento mais "
                   "limitado por já ser líder de mercado. Guidance da própria empresa para "
                   "2026 mantido: Seguro +3-7% em prêmios, Saúde +14-22%, Bank entre "
                   "R$7,5-7,9bi em receita.",
    },
    "BBSE3": {
        "trimestre": "1T26", "data": "04/05/2026",
        "numeros": "Lucro líquido gerencial R$2,2bi (+11,2% A/A), dentro do esperado pelo "
                   "mercado. Resultado financeiro combinado R$507,1mi (+58,5% A/A), "
                   "respondendo por ~23% do lucro total.",
        "pontos_fortes": "Brasilprev (previdência) foi o destaque: lucro +51% A/A "
                   "(R$538,1mi), puxado por melhora de 716% no resultado financeiro "
                   "(redução do custo do passivo) e alta de 7% no resultado operacional. "
                   "Brasilcap (capitalização) também subiu 50,6% (R$81,3mi). Sinistralidade "
                   "da Brasilseg seguiu em patamar historicamente baixo. Reservas de "
                   "previdência avançaram 9,1%.",
        "pontos_fracos": "Brasilseg (maior negócio, seguros) mostrou crescimento fraco — "
                   "lucro +1% apenas, com prêmios emitidos caindo 2,3% (segmento agrícola "
                   "-27,9% e penhor rural -14,2%, refletindo piora do agronegócio). O "
                   "resultado depende cada vez mais do resultado financeiro (juros), não "
                   "do crescimento operacional puro — em cenário de juros mais baixos, "
                   "esse suporte desaparece.",
        "expectativa": "Crescimento dentro do guidance da própria empresa, mas perto do "
                   "piso (prêmios -2,3% vs faixa de -3% a +2%) — pouca margem de segurança "
                   "se o agro continuar fraco. JPMorgan cortou preço-alvo após o 4T25 fraco "
                   "e mantém venda; outras casas (Nord) seguem compradas, citando P/L de 7x "
                   "(abaixo da média histórica de 13,5x) e dividend yield de ~12-13%.",
    },
    "ITUB4": {
        "trimestre": "1T26", "data": "05/05/2026",
        "numeros": "Lucro líquido recorrente R$12,28bi (+10,4% A/A, -0,3% T/T) — levemente "
                   "acima do consenso (R$12,19bi). ROE de 24,8% (+2,3 p.p. A/A). Carteira "
                   "de crédito R$1,48tri (+7,2% A/A, +9% A/A ex-câmbio).",
        "pontos_fortes": "ROE no Brasil de 26,4% — bem acima de pares (Santander reportou "
                   "16% no mesmo trimestre). Índice de eficiência de 34,4%, o menor da "
                   "série histórica do banco. Crescimento da carteira concentrado em "
                   "linhas colateralizadas (consignado +4,4% T/T, imobiliário +3,3% T/T) "
                   "— menos risco. Receitas de serviços e seguros cresceram 5,3% em 12 "
                   "meses (administração de recursos +15,1%, seguros +17,2%).",
        "pontos_fracos": "Lucro ficou estável/levemente menor (-0,3% T/T) por sazonalidade "
                   "do 1T (menos dias úteis) e antecipação do pagamento de dividendos no "
                   "fim de 2025 (que reduziu o patrimônio disponível pra gerar receita). "
                   "Custo de crédito subiu 4,5% A/A (R$10bi), refletindo maior pressão no "
                   "varejo. CEO sinalizou 2026 como ano que 'exige cautela e disciplina' "
                   "no crédito.",
        "expectativa": "Casas de análise (Genial, BTG) mantêm recomendação de compra, "
                   "vendo 2026 como 'ano de transição' com crescimento mais moderado que "
                   "os anos anteriores excepcionais, mas tese estrutural intacta — "
                   "guidance da própria empresa aponta lucro de ~R$51bi pro ano "
                   "(crescimento de dígito baixo). Banco vai saindo do varejo na Colômbia "
                   "para focar só no atacado, melhorando rentabilidade internacional.",
    },
    "BBAS3": {
        "trimestre": "1T26", "data": "13/05/2026",
        "numeros": "Lucro líquido ajustado R$3,4bi (-53,5% A/A, -40,2% T/T) — dentro do "
                   "esperado pelo mercado, mas mostra deterioração real. ROE caiu para "
                   "7,3% (de 16,7% no 1T25) — bem abaixo de todos os bancos privados pares.",
        "pontos_fortes": "Margem financeira bruta cresceu 14,8% A/A (R$27,4bi), mostrando "
                   "que a geração de receita 'bruta' do banco continua forte. Carteira de "
                   "pessoa física cresceu 8%, puxada por consignado privado. Receitas de "
                   "prestação de serviços subiram 5,5%.",
        "pontos_fracos": "Custo de crédito disparou 85,8% A/A (R$18,9bi), com inadimplência "
                   "rural subindo para 6,22% e custeio rural a 10,56% — a pior leitura em "
                   "anos do segmento. PJ encolheu (-6% A/A), puxado por MPME (-10%) e "
                   "grandes empresas (-9%). O banco cortou o guidance de lucro de 2026 de "
                   "R$22-26bi para R$18-22bi, reconhecendo que o problema do agro deve "
                   "continuar pressionando os próximos trimestres.",
        "expectativa": "Casas de análise adotaram postura mais neutra/cautelosa. O corte "
                   "de guidance reduziu a visibilidade sobre quando o lucro deve se "
                   "recuperar; o banco intensificou medidas de cobrança e uso de garantias, "
                   "mas a CEO reconheceu que 'o primeiro semestre tende a ser mais "
                   "apertado'. Dividend yield deve ficar pressionado no curto prazo "
                   "(payout de 30% sobre lucro menor).",
    },
    "PETR4": {
        "trimestre": "1T26", "data": "11/05/2026",
        "numeros": "Lucro líquido reportado R$32,7bi (+109,9% T/T; -7,2% A/A excluindo "
                   "eventos não recorrentes, R$23,8bi). Receita líquida R$123,7bi (estável "
                   "A/A). EBITDA ajustado R$61,7bi (estável A/A). Produção total de óleo e "
                   "gás 3,23 milhões boed (+16,1% A/A).",
        "pontos_fortes": "Produção em forte expansão, puxada pelo ramp-up de novas "
                   "plataformas no pré-sal (Búzios e Mero). ROE de 29,3% (melhor que 26,4% "
                   "em 2025). Refino (RTC) teve desempenho excepcional. Dividendos de R$9bi "
                   "anunciados, mantendo política de remuneração robusta mesmo com "
                   "resultado mais fraco.",
        "pontos_fracos": "Resultado ficou abaixo do consenso (esperado R$30,68bi) porque a "
                   "alta recente do Brent (por tensão no Oriente Médio) ainda não foi "
                   "capturada na receita — efeito de defasagem entre exportação e "
                   "reconhecimento contábil. Lifting cost no pré-sal subiu (câmbio mais "
                   "valorizado e custos do ramp-up de novas unidades). Geração de caixa "
                   "veio mais fraca que o esperado, por maior consumo de capital de giro.",
        "expectativa": "A própria empresa e analistas (Genial, XP) apontam o 2T26 como o "
                   "trimestre em que o Brent mais alto deve aparecer 'cheio' no resultado "
                   "— a tese é que o 1T26 foi operacionalmente sólido mas represado "
                   "contabilmente, com upside represado para frente.",
    },
    "VALE3": {
        "trimestre": "1T26", "data": "28/04/2026",
        "numeros": "Lucro líquido atribuível US$1,893bi (+36% A/A, revertendo prejuízo de "
                   "US$3,844bi no 4T25). Receita líquida US$9,3bi (+14% A/A). EBITDA "
                   "proforma US$3,89bi (+23% A/A).",
        "pontos_fortes": "Maior volume de vendas de minério de ferro desde 2018. Cobre com "
                   "EBITDA +74% A/A. Recordes de produção em múltiplos ativos (S11D, "
                   "Brucutu, e melhor produção de cobre desde 2017, níquel desde 2020). "
                   "Fluxo de caixa livre positivo (US$813mi), revertendo trimestre "
                   "anterior fraco.",
        "pontos_fracos": "EBITDA ficou abaixo do esperado por algumas casas (Safra viu "
                   "resultado 'levemente negativo'): geração de caixa livre 44% abaixo da "
                   "projeção do Safra, por maior necessidade de capital de giro. Custo "
                   "caixa C1 subiu 12% A/A (US$23,6/tonelada), por valorização do real. "
                   "Alavancagem subiu para 0,8x dívida líquida/EBITDA, reduzindo a chance "
                   "de dividendo extraordinário em 2026 segundo o Safra.",
        "expectativa": "BTG e XP mantêm recomendação de compra, vendo o trimestre como "
                   "reforço da tese de execução operacional consistente. Vale segue "
                   "mirando produção de minério de ferro acima de 360 milhões de "
                   "toneladas/ano até 2030 (+10% vs guidance 2025). Atenção do mercado "
                   "migra para geração de caixa e disciplina de capex nos próximos "
                   "trimestres.",
    },
    "B3SA3": {
        "trimestre": "1T26", "data": "07/05/2026",
        "numeros": "Lucro líquido recorrente R$1,5-1,54bi (+33,5% A/A; +39,4% A/A em base "
                   "ajustada). Receita líquida recorde R$3,2bi (+20,5% A/A). EBITDA "
                   "recorrente R$2,05-2,1bi. ROE de 33,8% (+10 p.p. A/A).",
        "pontos_fortes": "Receita recorde histórica, puxada por fluxo estrangeiro recorde "
                   "(R$53,8bi líquidos no trimestre — mais que o dobro de TODO o ano de "
                   "2025). Volume médio diário em ações +46% A/A. ADV de derivativos "
                   "+16,4% A/A. Despesas cresceram só 6% A/A, bem menos que a receita "
                   "(+20%), mostrando alavancagem operacional forte. Receitas recorrentes "
                   "(Tesouro Direto +45,5% em estoque, renda fixa) também cresceram bem.",
        "pontos_fracos": "Parte da melhora veio de uma alíquota de imposto menor que a "
                   "esperada (28% vs 34% projetado pelo Citi) — 'a cereja do bolo', segundo "
                   "o próprio banco, não repetível todo trimestre. Concorrência começando "
                   "a aparecer no radar (Base Exchange/Mubadala, BEE4, CSD BR), ainda sem "
                   "efeito prático.",
        "expectativa": "Citi reiterou compra com preço-alvo de R$23 (upside de ~30%). "
                   "Resultado tão forte levanta a pergunta se foi um pico pontual (fluxo "
                   "estrangeiro é variável volátil, depende de humor global e taxas de "
                   "juros americanas) ou um novo patamar — o 2T26 deve esclarecer.",
    },
}


# ---- Panorama da Empresa ----
# Resumo de orientação: o que a empresa faz, de onde vem a receita (por
# segmento), e um detalhe que REALMENTE diferencia essa empresa dos pares
# do setor -- do tipo que só aparece numa apresentação institucional de
# 40 páginas, não numa descrição genérica de "o que a empresa faz".
# Exemplos do tipo de detalhe que vale ouro (a pedido do Diego): a Irani
# não é afetada pelo preço da celulose porque só produz pra uso próprio;
# a Klabin tem ~40% da receita exposta a celulose; a Suzano, quase 100%.
# Mesmo espirito de GOVERNANCA/OUTLOOK_2026: pesquisado por mim, atualizado
# raramente (isso muda pouco, diferente de ANALISE_RESULTADO).
PANORAMA_EMPRESA = {
    "WEGE3": {
        "o_que_faz": "Fabricante global de equipamentos elétricos: motores, geradores, "
                     "transformadores, automação industrial e tintas/vernizes. Sede em "
                     "Jaraguá do Sul (SC), fábricas em 17 países, vendas para mais de 135 "
                     "países.",
        "segmentos": [
            ("Equipamentos Eletroeletrônicos Industriais", "motores de baixa/alta tensão, "
             "redutores, automação — vendidos pra praticamente todo tipo de indústria."),
            ("GTD — Geração, Transmissão e Distribuição", "transformadores, geração solar/"
             "eólica/hidrelétrica/biomassa — maior motor de crescimento recente, mas também "
             "o mais cíclico."),
            ("Motores Comerciais e Appliance", "motores de menor porte pra uso comercial/"
             "residencial."),
            ("Tintas e Vernizes", "menor participação na receita total."),
        ],
        "insight_chave": "Receita externa já é maior que a doméstica (57% em 2024) — e "
                     "dentro do Brasil, a WEG vende motores pra praticamente todo setor "
                     "industrial (mineração, papel e celulose, óleo e gás, saneamento, "
                     "agro). Isso significa que a WEG não depende da saúde de um setor "
                     "específico — diferente de uma empresa de celulose ou mineração, que "
                     "sofre inteira quando o preço da commodity cai. A fragilidade recente "
                     "(1T26) não veio de um setor só: foi uma queda pontual em geração "
                     "solar doméstica (-36%) somada ao câmbio mais valorizado.",
        "setor_dinamica": "Bens de capital industrial — o crescimento segue ciclos de "
                     "investimento industrial (motores/automação, mais estável) e ciclos "
                     "de energia renovável (GTD, mais volátil mês a mês).",
    },
    "PRIO3": {
        "o_que_faz": "Maior petroleira privada do Brasil. Compra campos de petróleo "
                     "maduros — que grandes petroleiras como a Petrobras já exploraram e "
                     "querem vender — e os torna mais eficientes e rentáveis.",
        "segmentos": [
            ("Peregrino", "maior ativo atual, adquirido da Equinor/Statoil — produção em "
             "ramp-up."),
            ("Albacora Leste", "comprado da Petrobras, eficiência operacional recorde "
             "(~95-99%)."),
            ("Wahoo", "campo novo, entrou em produção em 2026 — principal vetor de "
             "crescimento de produção daqui pra frente."),
            ("Polvo e Frade", "ativos mais antigos, já maduros na carteira da PRIO."),
        ],
        "insight_chave": "A receita da PRIO é 100% ligada ao preço do petróleo Brent "
                     "(cotado em dólar) — diferente de uma empresa industrial que define "
                     "seu próprio preço, a PRIO 'recebe' o preço que o mercado mundial de "
                     "petróleo determinar. Por isso, mesmo com a empresa operando "
                     "PERFEITAMENTE (produção +42% e custo em queda no 1T26), a ação pode "
                     "cair só porque o petróleo caiu por um motivo geopolítico que nada tem "
                     "a ver com a empresa — foi o que aconteceu em mai/2026 com a tensão no "
                     "Oriente Médio.",
        "setor_dinamica": "Petróleo e gás (E&P) — pense nela como uma 'gestora de ativos "
                     "maduros de petróleo': quanto mais eficiente em reduzir o custo de "
                     "extração (lifting cost), maior a margem em qualquer cenário de preço. "
                     "Mas o TAMANHO do lucro segue extremamente ligado ao Brent e ao câmbio.",
    },
    "EQTL3": {
        "o_que_faz": "Holding de energia elétrica e saneamento. O modelo é comprar "
                     "concessões de distribuição de energia mal cuidadas/endividadas e "
                     "fazer um turnaround — reduzir perdas, melhorar a cobrança, modernizar "
                     "a rede.",
        "segmentos": [
            ("Distribuição (principal)", "energia elétrica em Maranhão, Pará, Piauí, "
             "Alagoas, Goiás — cada estado é uma concessão separada, em estágio diferente "
             "de turnaround."),
            ("Transmissão", "linhas de transmissão com receita contratada e previsível."),
            ("Geração Renovável", "eólica, atualmente pressionada por restrições de "
             "geração (curtailment) impostas pelo regulador."),
            ("Saneamento", "água/esgoto no Amapá, além de participação relevante na Sabesp "
             "(contabilizada por equivalência patrimonial)."),
        ],
        "insight_chave": "Cada estado onde a Equatorial atua está numa fase diferente de "
                     "'maturidade' do turnaround — Maranhão e Pará (mais antigos na "
                     "carteira) já entregam resultado consistente, enquanto concessões mais "
                     "recentes ainda estão corrigindo perdas e inadimplência. O resultado "
                     "consolidado é uma MÉDIA de várias reformas em estágios diferentes — "
                     "entender qual concessão está 'pesando' no trimestre é mais informativo "
                     "do que só olhar o número final.",
        "setor_dinamica": "Utilities (serviço regulado) — receita previsível no longo prazo "
                     "(tarifas reguladas), mas o LUCRO sofre no curto prazo com juros altos "
                     "(mais dívida pra financiar aquisições/turnarounds) e com a qualidade "
                     "da execução em cada concessão.",
    },
    "JHSF3": {
        "o_que_faz": "Holding de negócios de alta renda/luxo, fundada e ainda liderada "
                     "pela família Auriemo.",
        "segmentos": [
            ("Shoppings", "Shopping Cidade Jardim e outros — aluguel + % das vendas das "
             "lojas (R$92mi no 1T26, +11,4% A/A)."),
            ("Hospitalidade (Fasano)", "hotéis e restaurantes, com expansão internacional "
             "recente (Miami, Punta del Este, Milão) — R$104,8mi no 1T26."),
            ("Residências e Clubs", "imóveis de alto padrão pra locação + clubes (São Paulo "
             "Surf Club, Fasano Tennis Club) — segmento de maior crescimento, +45% A/A."),
            ("Aviação Executiva", "aeroporto Catarina (SP) + FBO recém-adquirido em Miami "
             "— crescimento de 18,3% nos movimentos."),
        ],
        "insight_chave": "A JHSF vendeu TODO o estoque de imóveis residenciais 'pronto pra "
                     "vender' em dez/2025 (operação de R$5,2bi com um fundo estruturado pela "
                     "própria JHSF Capital) — ou seja, deixou de ser uma incorporadora "
                     "tradicional (constrói e vende) e está virando uma holding de RENDA "
                     "RECORRENTE (aluguel, hotelaria, clubes, aviação). Isso muda o tipo de "
                     "risco: menos exposição a ciclo de venda de imóveis, mais exposição à "
                     "capacidade de manter ocupação/demanda nos ativos de luxo no longo prazo.",
        "setor_dinamica": "Consumo de alta renda — o público-alvo é mais resiliente a "
                     "crises econômicas gerais, mas a empresa carrega risco de execução real "
                     "na expansão internacional (administrar hotel em Milão é "
                     "operacionalmente diferente de administrar em SP).",
    },
    "POMO4": {
        "o_que_faz": "Uma das maiores fabricantes de carrocerias de ônibus do mundo, "
                     "fundada em Caxias do Sul (RS) em 1949.",
        "segmentos": [
            ("Mercado doméstico", "ônibus urbanos, rodoviários e micro-ônibus pra empresas "
             "de transporte público/privado no Brasil — maior parte da receita, mas "
             "sensível a programas governamentais."),
            ("Exportação direta do Brasil", "vendas pra Argentina e outros países da "
             "América Latina."),
            ("Operações no exterior", "fábricas próprias no México (Polomex), Austrália "
             "(Volgren) e África do Sul — produção local pra mercados específicos."),
            ("Participação na NFI (Canadá)", "fabricante norte-americana de ônibus "
             "elétricos/GNV — contabilizada por equivalência patrimonial, contribuição "
             "não-operacional relevante e crescente."),
        ],
        "insight_chave": "Parte relevante do lucro da Marcopolo no 1T26 não veio da venda "
                     "de ônibus no Brasil — veio da equivalência patrimonial da NFI "
                     "(Canadá), que saltou de R$16mi pra R$76mi por um efeito não-recorrente "
                     "(reversão de provisão de recall de bateria). Sem esse efeito, o "
                     "resultado operacional do trimestre foi praticamente neutro — separar "
                     "'o que veio da operação de ônibus' do 'que veio da participação no "
                     "Canadá' evita achar o resultado melhor do que realmente foi.",
        "setor_dinamica": "Bens de capital / transporte — extremamente ligado a programas "
                     "governamentais de renovação de frota (Caminho da Escola, Move Brasil, "
                     "compras do Ministério da Saúde) e à saúde de crédito das empresas de "
                     "transporte público, que são os clientes finais.",
    },
    "RANI3": {
        "o_que_faz": "A Irani é uma das poucas 'pure players' de papel e embalagens "
                     "sustentáveis listadas na B3 (Novo Mercado), com mais de 80 anos de "
                     "operação, sede em Santa Catarina. Encerrou o segmento de resinas em "
                     "2025 para focar 100% em papel e embalagens.",
        "segmentos": [
            ("Embalagens (papelão ondulado)", "63% da receita (UDM 1T26) — a maior parte "
             "vendida pro setor alimentício (71,3% das vendas de embalagem), um cliente "
             "final historicamente pouco cíclico."),
            ("Papéis para embalagens sustentáveis", "36,4% da receita — linhas como "
             "Finekraft, Flashkraft, Bagkraft, com ~4,85% de market share nacional."),
            ("Ativos florestais (RS)", "apenas 0,6% da receita — venda de madeira e "
             "arrendamento, um complemento pequeno, não o núcleo do negócio."),
        ],
        "insight_chave": "Diferente da Suzano (praticamente toda a receita exposta ao "
                     "preço internacional da celulose) e da Klabin (~40% exposta, já que "
                     "vende parte da celulose que produz), a Irani produz celulose só pra "
                     "consumo próprio — não vende celulose pro mercado. Isso significa que "
                     "a Irani não sofre diretamente com a oscilação do preço internacional "
                     "da celulose; o que importa pra ela é o preço do PAPEL e da EMBALAGEM "
                     "que ela mesma fabrica e vende. Além disso, 68,9% da matéria-prima vem "
                     "de fibra reciclada (não virgem), reduzindo até a dependência do preço "
                     "da madeira.",
        "setor_dinamica": "Papel e embalagem — setor com crescimento estrutural "
                     "(substituição do plástico, e-commerce, delivery), historicamente "
                     "menos volátil que celulose pura porque a demanda majoritária vem do "
                     "setor alimentício (baixa ciclicidade) e a receita é 91% doméstica "
                     "(91% mercado interno, 9% exportação) — pouco exposta a câmbio.",
    },
    "PSSA3": {
        "o_que_faz": "A Porto deixou de ser 'só' uma seguradora de carros e se tornou um "
                     "ecossistema de proteção e serviços financeiros, com 4 verticais: "
                     "Porto Seguro, Porto Saúde, Porto Bank e Porto Serviço.",
        "segmentos": [
            ("Porto Seguro (auto, residência, empresas, vida)", "51% do lucro em 2025 — "
             "ainda o maior negócio, mas caiu de 67% em 2023 por crescimento mais rápido "
             "das outras verticais."),
            ("Porto Saúde", "25% do lucro — a vertical que mais cresce: receita +37%/ano "
             "e lucro +78%/ano entre 2021-2025."),
            ("Porto Bank", "18% do lucro — cartão, crédito, consórcio, conta digital; "
             "carteira de crédito de R$22,9bi."),
            ("Porto Serviço", "7% do lucro — assistência residencial/automotiva; menor em "
             "lucro, mas ajuda a reter cliente."),
        ],
        "insight_chave": "O dado mais importante: em 2023, seguro tradicional (auto/"
                     "residência) era 67% do lucro da Porto; em 2025, caiu para 51% — não "
                     "porque o seguro piorou, mas porque Saúde e Bank cresceram muito mais "
                     "rápido. Hoje quase metade do lucro (49%) já vem de negócios que não "
                     "são seguro tradicional, e todas as 4 verticais entregam ROAE acima de "
                     "20% — raro entre empresas brasileiras com tantas frentes diferentes "
                     "ao mesmo tempo.",
        "setor_dinamica": "Seguros e serviços financeiros diversificados — menos cíclico "
                     "que uma seguradora pura de automóvel. Saúde tem dinâmica de "
                     "crescimento estrutural (mais vidas seguradas, mais beneficiários "
                     "odonto); Bank é sensível ao ciclo de crédito (custo de crédito subiu "
                     "44% A/A no 1T26, sinal de atenção); o seguro tradicional já é líder "
                     "de mercado (26% de market share em auto), com menos espaço de "
                     "crescimento orgânico forte.",
    },
    "BBSE3": {
        "o_que_faz": "A BB Seguridade é uma holding de seguros, previdência e "
                     "capitalização ligada ao Banco do Brasil — não vende diretamente, usa "
                     "a rede de agências do BB pra distribuir os produtos das suas "
                     "controladas/joint ventures (Brasilseg, Brasilprev, Brasilcap, "
                     "Brasildental).",
        "segmentos": [
            ("Seguro Rural (Brasilseg)", "35,9% do lucro — a maior fatia, maior até que "
             "previdência ou vida. Líder absoluta com 62,9% de market share, mas só ~7% "
             "da área agrícola brasileira tem seguro."),
            ("Previdência (Brasilprev)", "22,6% do lucro — maior empresa de previdência "
             "privada do país, R$484bi em reservas."),
            ("Prestamista", "15,4% do lucro — seguro que protege operações de crédito, "
             "crescendo junto com o crédito brasileiro."),
            ("Vida e Capitalização", "13,2% + 6% do lucro — segmentos mais estáveis e "
             "diversificadores."),
        ],
        "insight_chave": "A maior fatia do lucro da BB Seguridade não vem de previdência "
                     "nem de seguro de vida — vem do Seguro Rural (35,9%). Isso significa "
                     "que o resultado da empresa está mais ligado à saúde do agronegócio "
                     "brasileiro (safra, clima, crédito rural) do que a maioria das pessoas "
                     "imagina quando pensa numa 'seguradora ligada a banco'. Foi exatamente "
                     "isso que pressionou o resultado no 1T26: os prêmios do segmento "
                     "agrícola caíram 27,9% A/A por causa de um agro mais fraco. Ao mesmo "
                     "tempo, a empresa avalia que só 7% da área agrícola tem seguro hoje — "
                     "vê isso como o segmento com mais espaço pra crescer no longo prazo, "
                     "mesmo sendo o mais sensível no curto prazo.",
        "setor_dinamica": "Seguros e previdência distribuídos via rede bancária — modelo "
                     "de baixíssimo custo de aquisição (usa a estrutura do Banco do Brasil, "
                     "que é também o controlador com 68% do capital). Receitas diferidas "
                     "(R$14,9bi em prêmios + R$6,3bi em comissões a apropriar) funcionam "
                     "como um 'colchão' que reduz a volatilidade trimestre a trimestre. O "
                     "resultado tem dupla blindagem: em cenário de juros altos, o resultado "
                     "financeiro (rendimento das reservas) compensa um resultado "
                     "operacional mais fraco — foi exatamente o que sustentou o 1T26.",
    },
    "ITUB4": {
        "o_que_faz": "O Itaú Unibanco é o maior banco privado da América Latina, com "
                     "atuação em varejo, crédito, investimentos, seguros e banco de "
                     "investimento — negociando tanto no Brasil quanto em outros países "
                     "da América Latina.",
        "segmentos": [
            ("Pessoas Físicas (varejo)", "crédito consignado, financiamento imobiliário, "
             "cartões — cresceu 6,8% no 1T26, puxado por linhas colateralizadas (mais "
             "seguras)."),
            ("Empresas (PJ)", "de micro/pequenas até grandes empresas — crescimento "
             "sustentado por programas governamentais de crédito."),
            ("Serviços e Seguros", "administração de recursos, seguros, banco de "
             "investimento — R$14bi de receita no 1T26, crescendo mais rápido que o "
             "crédito puro (administração de recursos +15,1%, seguros +17,2%)."),
            ("América Latina (ex-Brasil)", "o banco está saindo do varejo na Colômbia "
             "(operação deficitária), mantendo só o atacado — reduzindo exposição "
             "internacional de menor retorno."),
        ],
        "insight_chave": "O Itaú é conhecido no mercado como o banco mais 'sem "
                     "surpresas' da bolsa — o ROE no Brasil (26,4% no 1T26) é "
                     "consistentemente maior que o de seus pares (Santander reportou 16% "
                     "no mesmo trimestre). A maior parte do crescimento recente vem de "
                     "linhas de crédito colateralizadas (consignado, imobiliário) — "
                     "empréstimos com garantia, que dão menos risco de inadimplência "
                     "mesmo crescendo a carteira. É uma escolha deliberada da gestão: "
                     "crescer 'mais devagar e com mais segurança' em vez de perseguir "
                     "crescimento bruto.",
        "setor_dinamica": "Bancos — resultado sensível ao ciclo de crédito (juros, "
                     "inadimplência) e à Selic. Diferente de bancos menores, o Itaú tem "
                     "escala suficiente pra manter o índice de eficiência no menor nível "
                     "da própria história (34,4% no 1T26) mesmo em cenário de juros "
                     "altos, sustentando rentabilidade acima dos pares mesmo em "
                     "trimestres mais fracos.",
    },
    "BBAS3": {
        "o_que_faz": "O Banco do Brasil é o maior banco estatal do país e o maior "
                     "financiador do agronegócio brasileiro — atua em crédito, "
                     "investimentos, seguros, gestão de patrimônio e serviços bancários, "
                     "com presença nacional muito ampla.",
        "segmentos": [
            ("Agronegócio (crédito rural)", "carteira de R$418,4bi (+3% A/A) — é a maior "
             "vantagem competitiva histórica do BB, mas hoje também é a maior fonte de "
             "risco."),
            ("Pessoa Física", "+8% A/A, puxado por consignado (R$151,8bi, +7,2%) e o "
             "novo 'crédito do trabalhador' (+2.000% em 12 meses, ainda pequeno em "
             "volume)."),
            ("Pessoa Jurídica", "-6% A/A — recuou tanto em médias/pequenas empresas "
             "(-10%) quanto em grandes empresas (-9%), reflexo de um ambiente de crédito "
             "mais seletivo."),
        ],
        "insight_chave": "O BB é, ao mesmo tempo, o banco com maior exposição ao "
                     "agronegócio e o que mais sofreu quando esse setor entrou em "
                     "dificuldade: no 1T26, a inadimplência rural saltou para 6,22% (de "
                     "níveis bem mais baixos), o custo de crédito disparou 86% e o lucro "
                     "caiu 53,5% — a maior queda trimestral em anos, encerrando uma "
                     "sequência de 16 trimestres de crescimento. Isso é o oposto do "
                     "Itaú: enquanto o Itaú cresce 'mais devagar e com mais segurança' "
                     "via crédito colateralizado, o BB tem uma concentração estrutural "
                     "em agro que vira vantagem em anos boas de safra e vira problema "
                     "quando o agro aperta — como está acontecendo agora.",
        "setor_dinamica": "Bancos com exposição concentrada a um setor específico (agro) "
                     "tendem a ter resultado mais cíclico que bancos diversificados — o "
                     "ROE do BB (7,3% no 1T26) ficou bem abaixo de todos os pares "
                     "privados (Itaú 24%, Santander 16%, Bradesco 15,8%) justamente "
                     "nesse trimestre de crise agrícola.",
    },
    "PETR4": {
        "o_que_faz": "A Petrobras é uma das maiores empresas integradas de energia do "
                     "mundo, com atuação em exploração e produção (E&P) de petróleo e "
                     "gás, refino, transporte e comercialização (RTC) de derivados, além "
                     "de uma divisão de gás e energias de baixo carbono.",
        "segmentos": [
            ("E&P (Exploração e Produção)", "o motor da empresa — produção de ~3,2 "
             "milhões de barris/dia, com ~2,19 milhões vindo do pré-sal (Búzios, Mero), "
             "que tem o menor custo de extração do mundo."),
            ("RTC (Refino, Transporte e Comercialização)", "transforma o petróleo bruto "
             "em derivados (gasolina, diesel, querosene) e vende — teve desempenho "
             "excepcional no 1T26."),
            ("Gás e Energias de Baixo Carbono", "ainda um segmento menor e mais "
             "desafiado, com EBITDA caindo 24% T/T no 1T26 por efeitos contratuais e de "
             "preço."),
        ],
        "insight_chave": "Um detalhe que confunde muita gente ao olhar só o resultado "
                     "trimestral: a Petrobras vende boa parte do petróleo pra exportação, "
                     "e existe um intervalo de tempo entre o navio sair carregado e a "
                     "venda ser reconhecida na receita ('descasamento' entre embarque e "
                     "reconhecimento contábil). Isso significa que quando o preço do "
                     "petróleo sobe de repente (como aconteceu com a tensão no Oriente "
                     "Médio em 2026), o efeito positivo não aparece imediatamente no "
                     "resultado — aparece com defasagem, no trimestre seguinte.",
        "setor_dinamica": "Petróleo integrado — resultado depende do preço internacional "
                     "do Brent, mas amortecido pelo Refino (que ganha margem mesmo "
                     "quando o petróleo sobe) e pelo baixo custo de extração do pré-sal "
                     "(lifting cost de ~US$9,3/barril, um dos mais baixos do mundo), o "
                     "que protege a margem mesmo em cenários de preço mais baixo.",
    },
    "VALE3": {
        "o_que_faz": "A Vale é uma das maiores mineradoras do mundo, com foco em "
                     "minério de ferro (seu principal produto histórico) e uma divisão "
                     "crescente de metais básicos (cobre e níquel), usados em baterias, "
                     "eletrônicos e na transição energética.",
        "segmentos": [
            ("Soluções de Minério de Ferro", "ainda a maior fonte de resultado — EBITDA "
             "de ~US$2,9bi no 1T26, com produção recorde em vários ativos (S11D, "
             "Brucutu) e preço realizado de ~US$95,8/tonelada."),
            ("Metais Básicos (cobre e níquel)", "a divisão que mais cresce em "
             "importância — a participação do cobre no EBITDA total saltou de 10% em "
             "2024 pra mais de 17% em 2025, com o níquel registrando altas expressivas."),
        ],
        "insight_chave": "Por muitos anos, a Vale foi vista como 'a empresa do minério "
                     "de ferro' — e ainda é, em tamanho. Mas o que está mudando de "
                     "verdade é a importância crescente do cobre e do níquel: como esses "
                     "metais aparecem nas mesmas minas que produzem ouro como "
                     "subproduto, o custo de produção do cobre da Vale está caindo pra "
                     "perto de zero, o que pode transformar esse segmento (hoje menor) "
                     "num motor de resultado relevante nos próximos anos — uma "
                     "característica que diferencia a Vale de mineradoras de minério de "
                     "ferro 'puro'.",
        "setor_dinamica": "Mineração — resultado extremamente ligado ao preço "
                     "internacional das commodities e à demanda chinesa (maior "
                     "compradora de minério de ferro do mundo). Vale tem vantagem de "
                     "custo por possuir reservas de alto teor (Carajás), o que ajuda a "
                     "manter margem mesmo em cenários de preço mais baixo.",
    },
    "B3SA3": {
        "o_que_faz": "A B3 é a única bolsa de valores do Brasil — dona de toda a "
                     "infraestrutura de negociação, registro, depósito e liquidação de "
                     "ações, derivativos, renda fixa e outros ativos financeiros no "
                     "país. Funciona quase como uma 'utility' do mercado financeiro: "
                     "ganha com o volume negociado, não com o resultado dos investidores.",
        "segmentos": [
            ("Listados (ações e ETFs)", "ganha taxa sobre o volume negociado de ações, "
             "ETFs, BDRs e fundos listados — segmento mais cíclico, depende de "
             "volatilidade e fluxo de investidores."),
            ("Derivativos", "contratos de juros, câmbio, índices — maior e mais estável "
             "fonte de receita; cresce com volatilidade do mercado."),
            ("Renda Fixa, Crédito Privado e Tesouro Direto", "receitas mais recorrentes "
             "e menos cíclicas — crescimento constante mesmo em mercado de ações fraco."),
            ("Dados, Listagem e Soluções pra Emissores", "menor em tamanho, mas "
             "crescendo — venda de dados analíticos, taxas de IPO/follow-on."),
        ],
        "insight_chave": "A B3 tem hoje um monopólio prático no Brasil — é a única "
                     "bolsa de ações relevante do país. Isso está mudando: já existem 3 "
                     "iniciativas de concorrência avançando (a Base Exchange, ligada ao "
                     "fundo Mubadala de Abu Dhabi; a BEE4, focada em pequenas/médias "
                     "empresas; e a CSD BR, que já compete no registro/depósito). "
                     "Nenhuma dessas ameaças deve afetar o resultado no curto prazo — a "
                     "entrada efetiva só é esperada a partir de 2027 — mas é o tipo de "
                     "risco estrutural de longo prazo que ainda não aparece nos números "
                     "de hoje.",
        "setor_dinamica": "Bolsa de valores — modelo de negócio com altíssima "
                     "alavancagem operacional (custos fixos, margem cresce muito quando "
                     "o volume sobe) e baixa necessidade de capital novo. Receita "
                     "'pró-cíclica' (derivativos, ações) sobe com volatilidade e fluxo "
                     "estrangeiro; receita 'recorrente' (dados, Tesouro Direto, renda "
                     "fixa) cresce de forma mais previsível, independente do humor do "
                     "mercado.",
    },
}


ESTUDOS_ESPECIFICOS = {
    "BBAS3": {
        "titulo": "P/VP raramente abaixo de 0,50x",
        "texto": (
            "Historicamente, o Banco do Brasil raríssimas vezes negociou com P/VP "
            "abaixo de 0,50x — mesmo em períodos de estresse (crise de crédito rural, "
            "revisões de guidance). Esse piso histórico é uma referência relevante "
            "pra avaliar se o desconto atual já é extremo ou ainda tem espaço."
        ),
        "metrica": "pvp_str",
    },
}

def penalizacao_outlook(ticker):
    """
    Aplica multiplicador no score baseado no outlook 2026.
    ✅ Positivo  → sem alteração
    ⚠️ Atenção   → −5%
    🔴 Cautela   → −12%
    """
    out = OUTLOOK_2026.get(ticker, {})
    icone = out.get('icone', '✅')
    if icone == '🔴':
        return 0.88   # −12%
    elif icone == '⚠️':
        return 0.95   # −5%
    else:
        return 1.0    # sem alteração

def penalizacao_governanca(nota_gov):
    if nota_gov >= 9.0:
        return 0.0
    elif nota_gov >= 8.0:
        return -0.3
    elif nota_gov >= 7.0:
        return -0.6
    elif nota_gov >= 6.0:
        return -1.0
    elif nota_gov >= 5.0:
        return -1.3
    else:
        return -1.5

def status_aporte(cotacao_raw, preco_teto, target):
    """
    Retorna (status, cor, icone, descricao) com base na cotação vs teto vs target.
    Abaixo do teto = comprar. Acima do target = reduzir/vender.
    Quanto mais abaixo do teto, melhor a oportunidade.
    """
    try:
        cot = limpar_valor(str(cotacao_raw).replace('R$',''))
        if cot <= 0 or preco_teto <= 0 or target <= 0:
            return ('neutro', '#888888', '⚪', 'Sem dados de preço')

        if cot > target:
            # Acima do target — zona de venda/redução
            pct_acima = ((cot - target) / target) * 100
            return ('acima_target', '#D9534F', '🔴',
                    f"Acima do target (+{pct_acima:.1f}%) — considerar redução")

        elif cot > preco_teto:
            # Entre teto e target — zona de atenção
            pct = ((cot - preco_teto) / preco_teto) * 100
            return ('acima_teto', '#C97D3B', '🟠',
                    f"Acima do preço teto (+{pct:.1f}%) — aguardar recuo")

        else:
            # Abaixo do teto — zona de compra
            pct_teto   = ((preco_teto - cot) / preco_teto) * 100
            pct_target = ((target - cot) / target) * 100
            if pct_teto >= 15:
                return ('oportunidade', '#4CAF6D', '🟢',
                        f"Forte oportunidade — {pct_teto:.1f}% abaixo do teto / {pct_target:.1f}% abaixo do target")
            else:
                return ('compra', '#5B8DB8', '🔵',
                        f"Zona de compra — {pct_teto:.1f}% abaixo do teto / {pct_target:.1f}% abaixo do target")

    except:
        return ('neutro', '#888888', '⚪', 'Sem dados de preço')


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
    for _ in range(2):  # 1 retry simples -- defesa contra falha transitória da API
        try:
            url = f"https://brapi.dev/api/quote/{ticker}?token=qX942ePxQaNWzSEs9gphZi"
            r = requests.get(url, timeout=8).json()
            if r.get('results'):
                logo = r['results'][0].get('logourl', '') or ''
                if logo:
                    return logo
        except Exception:
            pass
    return ''

# ---- Insiders e Recompras via Fundamentus ----
# Páginas públicas, HTML puro, sem login. Buscamos só na página de detalhe
# do ativo (não nos 40 cards da grade) pra não disparar 80+ requisições
# extras a cada carregamento da tela principal.
def _parse_tabela_fundamentus(ticker, pagina):
    """Busca e parseia a tabela de insiders ou recompras do Fundamentus.
    pagina: 'insiders' ou 'recompras'. Retorna (df, erro) — erro é None se
    deu certo, ou uma string explicando o motivo da falha (útil pra
    diagnosticar bloqueio de IP em hospedagem na nuvem, por exemplo)."""
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                       '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Referer': 'https://fundamentus.com.br/',
    }
    try:
        url = f"https://fundamentus.com.br/{pagina}.php?papel={ticker}"
        r = requests.get(url, timeout=12, headers=headers)
        if r.status_code != 200:
            return pd.DataFrame(), f"HTTP {r.status_code} ao acessar Fundamentus"
        r.encoding = 'iso-8859-1'  # Fundamentus não usa UTF-8 — sem isso os acentos corrompem
        tabelas = pd.read_html(io.StringIO(r.text), decimal=',', thousands='.')
        if not tabelas:
            return pd.DataFrame(), "nenhuma tabela encontrada na página (possível bloqueio ou página alterada)"
        df = tabelas[0]
        if df.shape[1] < 4:
            return pd.DataFrame(), "estrutura da tabela inesperada"
        df = df.iloc[:, :4]
        df.columns = ['data', 'quantidade', 'valor', 'preco_medio']
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y', errors='coerce')
        df = df.dropna(subset=['data']).reset_index(drop=True)
        return df, None
    except Exception as e:
        return pd.DataFrame(), f"erro: {e}"


@st.cache_data(ttl=86400, show_spinner=False)
def get_insiders_data(ticker):
    """Histórico mensal de compras/vendas de ações por controladores,
    diretoria, conselho — direto do Fundamentus (fonte original: CVM).
    Retorna (df, erro)."""
    return _parse_tabela_fundamentus(ticker, 'insiders')


@st.cache_data(ttl=86400, show_spinner=False)
def get_recompras_data(ticker):
    """Histórico mensal de recompras de ações pela própria empresa
    (tesouraria) — direto do Fundamentus (fonte original: CVM).
    Retorna (df, erro)."""
    return _parse_tabela_fundamentus(ticker, 'recompras')


def resumo_periodo(df, meses=6):
    """Retorna o resumo mais útil disponível:
    - Se houver transação não-zero nos últimos `meses`: soma do período.
    - Senão, se houver QUALQUER transação não-zero no histórico: a mais
      recente (mesmo que tenha sido há mais tempo).
    - Senão: None (sem nenhuma movimentação registrada)."""
    if df.empty:
        return None
    corte = pd.Timestamp.now() - pd.DateOffset(months=meses)
    recente = df[(df['data'] >= corte) & (df['valor'] != 0)]
    if not recente.empty:
        return {'tipo': 'periodo', 'valor': recente['valor'].sum(), 'meses': meses}
    nao_zero = df[df['valor'] != 0]
    if not nao_zero.empty:
        linha = nao_zero.sort_values('data', ascending=False).iloc[0]
        return {'tipo': 'ultima', 'valor': linha['valor'], 'data': linha['data']}
    return None


_FUNDAMENTUS_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    'Referer': 'https://fundamentus.com.br/',
}


@st.cache_data(ttl=86400, show_spinner=False)
def get_proventos_data(ticker):
    """Histórico de proventos (dividendos/JCP) direto do Fundamentus.
    Retorna (df_detalhado, df_anual, erro)."""
    try:
        url = f"https://fundamentus.com.br/proventos.php?papel={ticker}&tipo=2"
        r = requests.get(url, timeout=12, headers=_FUNDAMENTUS_HEADERS)
        if r.status_code != 200:
            return pd.DataFrame(), pd.DataFrame(), f"HTTP {r.status_code} ao acessar Fundamentus"
        r.encoding = 'iso-8859-1'
        tabelas = pd.read_html(io.StringIO(r.text), decimal=',', thousands='.')
        if not tabelas:
            return pd.DataFrame(), pd.DataFrame(), "nenhuma tabela encontrada na página"

        df_det = tabelas[0].copy()
        n_cols = min(df_det.shape[1], 5)
        df_det = df_det.iloc[:, :n_cols]
        nomes = ['data', 'valor', 'tipo', 'data_pagamento', 'por_acoes'][:n_cols]
        df_det.columns = nomes
        df_det['data'] = pd.to_datetime(df_det['data'], format='%d/%m/%Y', errors='coerce')
        df_det = df_det.dropna(subset=['data']).reset_index(drop=True)

        df_ano = pd.DataFrame()
        if len(tabelas) >= 2:
            df_ano = tabelas[1].copy().iloc[:, :2]
            df_ano.columns = ['ano', 'valor']
            df_ano = df_ano.dropna()

        return df_det, df_ano, None
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), f"erro: {e}"


@st.cache_data(ttl=86400, show_spinner=False)
def get_apresentacoes_data(ticker):
    """Lista de apresentações/comunicados da empresa, com link de download
    direto da CVM, via Fundamentus. Retorna (df, erro). df tem colunas:
    data (texto), data_dt (datetime), descricao, link."""
    try:
        url = f"https://fundamentus.com.br/apresentacoes.php?papel={ticker}"
        r = requests.get(url, timeout=12, headers=_FUNDAMENTUS_HEADERS)
        if r.status_code != 200:
            return pd.DataFrame(), f"HTTP {r.status_code} ao acessar Fundamentus"
        r.encoding = 'iso-8859-1'
        tabelas = pd.read_html(io.StringIO(r.text))
        if not tabelas:
            return pd.DataFrame(), "nenhuma tabela encontrada na página"

        df = tabelas[0].copy()
        n_cols = min(df.shape[1], 3)
        df = df.iloc[:, :n_cols]
        df.columns = ['data', 'descricao', 'download'][:n_cols]

        # pd.read_html só traz o TEXTO do link ("Download"), não o href —
        # extraímos os links reais direto do HTML, na mesma ordem das linhas.
        links = re.findall(r'href="(https://www\.rad\.cvm\.gov\.br/ENET/[^"]+)"', r.text)
        if len(links) == len(df):
            df['link'] = links
        else:
            df['link'] = None

        df['data_dt'] = pd.to_datetime(df['data'].astype(str).str.split(' ').str[0],
                                       format='%d/%m/%Y', errors='coerce')
        df = df.dropna(subset=['data_dt']).reset_index(drop=True)
        return df, None
    except Exception as e:
        return pd.DataFrame(), f"erro: {e}"


def ultimo_release_resultado(df, data_referencia=None):
    """Acha o documento de resultado mais recente. NÃO é uma categoria
    oficial da CVM nessa página -- é heurística baseada no texto da
    descrição, então pode ocasionalmente errar.

    Se `data_referencia` (string 'DD/MM/AAAA', a data de divulgação que eu
    já pesquisei em ANALISE_RESULTADO) for passada, prioriza match EXATO de
    data -- muito mais confiável que tentar adivinhar pelo texto, que já
    pegou "Call de resultados" (um convite, não o release) por engano.

    Sem data de referência, cai pro texto: "release" > "resultado", sempre
    excluindo "call"/"video"/"webcast"/"teleconferência" (que são convites
    pra ouvir o resultado, não o documento do resultado em si)."""
    if df.empty:
        return None
    df = df.sort_values('data_dt', ascending=False)

    if data_referencia:
        try:
            dt_ref = pd.to_datetime(data_referencia, format='%d/%m/%Y')
            match_data = df[df['data_dt'] == dt_ref]
            if not match_data.empty:
                return match_data.iloc[0].to_dict()
        except Exception:
            pass

    desc = df['descricao'].astype(str)
    mask_excluir = desc.str.contains('video|webcast|teleconfer|conference call|^call ', case=False, na=False, regex=True)
    mask_release = desc.str.contains('release', case=False, na=False) & ~mask_excluir
    mask_resultado = desc.str.contains('resultado', case=False, na=False) & ~mask_excluir

    if mask_release.any():
        df_filtrado = df[mask_release]
    elif mask_resultado.any():
        df_filtrado = df[mask_resultado]
    else:
        return None
    return df_filtrado.iloc[0].to_dict()


# ---- Volatilidade Implícita, IV Rank e IV Percentil via OpLab (sem login) ----
# Portal público https://opcoes.oplab.com.br/mercado-de-opcoes — diferente da
# plataforma/API principal da OpLab (que exige token). Busca-se a página UMA
# VEZ (lista todos os ~150 ativos) e fica em cache de 1h — não precisa de uma
# requisição por ticker.
# ---- Grade de opções via OpLab (página pública, sem login) ----------------
# NUNCA TESTADO contra o HTML de verdade (minhas ferramentas de pesquisa só
# leem o texto da página, não a tabela HTML brura que o requests vai ver) --
# usa pd.read_html() como estratégia mais robusta (lida com tabelas HTML bem
# formadas de forma generica, sem depender de eu adivinhar a estrutura exata
# por regex). Precisa ser validado rodando de verdade antes de confiar.
_MESES_PT = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho",
    7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}


@st.cache_data(ttl=900, show_spinner=False)
def get_grade_opcoes_oplab(ticker, mes=None, ano=None):
    """Busca a grade de opções (CALL/PUT, strikes, delta, bid/ask) de um
    ticker na página pública da OpLab, sem precisar de login/token.
    Retorna (df_ou_None, erro_ou_None)."""
    hoje = pd.Timestamp.today()
    mes = mes or hoje.month
    ano = ano or hoje.year
    mes_nome = _MESES_PT.get(mes, "junho")
    url = f"https://opcoes.oplab.com.br/mercado/acoes/opcoes/{ticker}/{mes_nome}/{ano}"
    try:
        r = requests.get(url, timeout=15, headers=_FUNDAMENTUS_HEADERS)
        if r.status_code != 200:
            return None, f"HTTP {r.status_code} ao acessar OpLab"
        try:
            tabelas = pd.read_html(io.StringIO(r.text))
        except Exception as e:
            return None, f"não consegui ler tabelas da página: {e}"
        if not tabelas:
            return None, "nenhuma tabela encontrada na página"
        # A grade de opções deve ser a maior tabela (mais linhas) da página.
        tabela_opcoes = max(tabelas, key=lambda t: len(t))
        if len(tabela_opcoes) < 2:
            return None, "tabela encontrada parece vazia (sem opções pra esse vencimento)"
        return tabela_opcoes, None
    except Exception as e:
        return None, str(e)


@st.cache_data(ttl=3600, show_spinner=False)
def get_volatilidade_oplab():
    """Retorna (dict_por_ticker, erro). dict_por_ticker mapeia
    TICKER -> {'vol_implicita': float|None, 'iv_rank': float|None, 'iv_percentil': float|None}."""
    try:
        url = "https://opcoes.oplab.com.br/mercado-de-opcoes"
        r = requests.get(url, timeout=15, headers=_FUNDAMENTUS_HEADERS)
        if r.status_code != 200:
            return {}, f"HTTP {r.status_code} ao acessar OpLab"
        html = r.text

        # Cada ativo é um link <a href=".../mercado/acoes/opcoes/TICKER">...</a>
        # contendo o ticker e, em algum lugar dentro, os 3 números (ou "-")
        # de Vol. Implícita / IV Rank / IV Percentil, nessa ordem.
        blocos = re.findall(
            r'href="[^"]*?/mercado/acoes/opcoes/([A-Z0-9]+)"[^>]*>(.*?)</a>',
            html, re.DOTALL
        )
        if not blocos:
            return {}, "nenhum ativo encontrado na página (estrutura pode ter mudado)"

        padrao_num = re.compile(r'(\d{1,3},\d{2}|-)')
        resultado = {}
        for ticker, conteudo in blocos:
            texto = re.sub(r'<[^>]+>', '', conteudo)  # remove tags HTML internas
            # Pega só o trecho após "Percentil" (label), que é onde os 3
            # números aparecem — evita capturar números do preço/variação.
            partes = texto.split('Percentil')
            trecho_numeros = partes[-1] if len(partes) > 1 else texto
            valores = padrao_num.findall(trecho_numeros)[:3]

            def _conv(v):
                if v == '-' or v is None:
                    return None
                try:
                    return float(v.replace(',', '.'))
                except ValueError:
                    return None

            if len(valores) == 3:
                resultado[ticker] = {
                    'vol_implicita': _conv(valores[0]),
                    'iv_rank': _conv(valores[1]),
                    'iv_percentil': _conv(valores[2]),
                }
        if not resultado:
            return {}, "ativos encontrados, mas não foi possível extrair os números de volatilidade"
        return resultado, None
    except Exception as e:
        return {}, f"erro: {e}"


def get_volatilidade_ticker(ticker):
    """Busca a volatilidade implícita/IV Rank/IV Percentil de UM ticker
    específico, usando o cache compartilhado de get_volatilidade_oplab
    (que busca todos os ativos de uma vez, evitando 40 requisições)."""
    dados, erro = get_volatilidade_oplab()
    if erro:
        return None, erro
    item = dados.get(ticker.upper())
    if item is None:
        return None, "ativo não encontrado na lista do OpLab (pode não ter opções líquidas o suficiente)"
    return item, None


# ---- Indicadores extras (ROIC, VPA, P/EBIT, EV/EBITDA, margens, liquidez) ----
@st.cache_data(ttl=86400, show_spinner=False)
def get_indicadores_fundamentus(ticker):
    """Busca indicadores fundamentalistas extras direto da página de
    detalhes do Fundamentus (a mesma usada pro site mostrar P/L, P/VP etc).
    Retorna (dict_label->valor_bruto, erro). O dict guarda os valores como
    string crua (formato BR) — use _ind_buscar() pra extrair como float."""
    try:
        url = f"https://fundamentus.com.br/detalhes.php?papel={ticker}"
        r = requests.get(url, timeout=12, headers=_FUNDAMENTUS_HEADERS)
        if r.status_code != 200:
            return {}, f"HTTP {r.status_code} ao acessar Fundamentus"
        r.encoding = 'iso-8859-1'
        tabelas = pd.read_html(io.StringIO(r.text), decimal=',', thousands='.')
        if not tabelas:
            return {}, "nenhuma tabela encontrada"

        indicadores = {}
        for tabela in tabelas:
            n_cols = tabela.shape[1]
            if n_cols < 2 or n_cols % 2 != 0:
                continue
            # As tabelas do Fundamentus alternam rótulo/valor nas colunas
            # (rótulo na coluna par, valor na ímpar seguinte).
            for _, linha in tabela.iterrows():
                for i in range(0, n_cols, 2):
                    rotulo = str(linha.iloc[i]).strip().lstrip('?').strip()
                    valor = linha.iloc[i + 1] if i + 1 < n_cols else None
                    if rotulo and rotulo.lower() not in ('nan', '') and valor is not None:
                        indicadores[rotulo] = valor
        return indicadores, None
    except Exception as e:
        return {}, f"erro: {e}"


def _ind_buscar(indicadores, *termos):
    """Procura um indicador cujo nome contenha qualquer um dos termos
    (case-insensitive) e retorna como float. O pandas, com decimal=',', já
    normaliza vírgula->ponto mesmo em colunas mistas (ex: '5,97' -> '5.97'
    como string) — por isso tentamos float() direto primeiro, e só usamos a
    limpeza manual de formato BR como fallback caso isso falhe."""
    termos_lower = [t.lower() for t in termos]
    for rotulo, valor in indicadores.items():
        if any(t in rotulo.lower() for t in termos_lower):
            if isinstance(valor, (int, float)):
                return None if pd.isna(valor) else float(valor)
            v = str(valor).strip().replace('%', '').strip()
            if v in ('-', '', 'nan', 'None'):
                return None
            try:
                return float(v)
            except ValueError:
                pass
            v2 = v.replace('.', '').replace(',', '.')
            try:
                return float(v2)
            except ValueError:
                continue
    return None


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
        pvp_str    = f"{pvp:.2f}x".replace(".", ",") if pvp    else "-"

        low52  = info.get('fiftyTwoWeekLow',  0)
        high52 = info.get('fiftyTwoWeekHigh', 0)
        low_str  = f"R$ {low52:.2f}".replace(".", ",")  if low52  else "-"
        high_str = f"R$ {high52:.2f}".replace(".", ",") if high52 else "-"

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
        # dropna(how='all') só remove linhas 100% vazias — uma linha com
        # algum resíduo de formatação mas sem CÓDIGO sobrevive e gera um
        # "ativo fantasma" (tudo NaN) na listagem. Filtramos explicitamente
        # por CÓDIGO válido.
        if 'CÓDIGO' in df.columns:
            df = df[df['CÓDIGO'].notna()]
            df = df[df['CÓDIGO'].astype(str).str.strip() != '']
            df = df[df['CÓDIGO'].astype(str).str.lower() != 'nan']
        df = df.reset_index(drop=True)

        # Blindagem: ticker duplicado na planilha (ex: adicionado 2x por
        # engano) gera 2 cards com a MESMA chave interna no Streamlit e
        # derruba o app inteiro (StreamlitDuplicateElementKey). Mantém só a
        # primeira ocorrência -- silenciosamente resolve o crash, mas o
        # aviso abaixo (lido no app principal) avisa que tem duplicata.
        duplicados = df['CÓDIGO'][df['CÓDIGO'].duplicated()].unique().tolist() if 'CÓDIGO' in df.columns else []
        if duplicados:
            df = df.drop_duplicates(subset='CÓDIGO', keep='first').reset_index(drop=True)

        df['pl_num']      = df['P/L PROJETADO'].apply(limpar_valor)
        df['dy_num']      = df['Dividend Yield bruto estimado'].apply(limpar_valor)
        df['div_num']     = df['Dívida líquida/EBITDA'].apply(limpar_valor)
        df['cagr_num']    = df['CAGR lucros (últ. 5 anos)'].apply(limpar_valor)
        df['res_val_num'] = df['RESULTADO 2026 (1/4)'].apply(limpar_valor_resultado)
        df['preco_teto']  = df['PREÇO TETO'].apply(limpar_valor) if 'PREÇO TETO' in df.columns else 0
        df['target']      = df['TARGET'].apply(limpar_valor) if 'TARGET' in df.columns else 0

        return df, duplicados
    except:
        return pd.DataFrame(), []

df, _tickers_duplicados = carregar_dados()
if _tickers_duplicados:
    st.warning(
        f"⚠️ Ticker(s) duplicado(s) na planilha (mantive só a primeira linha de cada): "
        f"{', '.join(_tickers_duplicados)}. Verifique e remova a linha repetida pra "
        f"evitar inconsistência nos dados."
    )


# ---- Tese de Investimento + Alerta de Divergência ----
# GID_TESE: PLACEHOLDER — Diego, troque pelo GID real depois de criar a aba
# TESE na mesma planilha do RADAR, com colunas: TICKER | TESE | ROE_MIN |
# PL_MAX | DIV_EBITDA_MAX | DATA_REGISTRO
GID_TESE = "0000000002"

@st.cache_data(ttl=60, show_spinner=False)
def load_tese():
    """Lê a aba TESE: a tese de investimento escrita pelo usuário pra cada
    ativo, com limites numéricos opcionais (ROE mínimo, P/L máximo, Dívida
    máxima). Usado pra alertar quando a realidade diverge da tese original —
    combate o viés de continuar confiando numa tese que já não é mais
    verdade. Retorna dict ticker -> {tese, roe_min, pl_max, div_max, data}."""
    try:
        spreadsheet_id = "1QM3xaaiZHleTJb8MEChy95LJSX3j3hLs8-ecQydMHYM"
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={GID_TESE}"
        df_tese = pd.read_csv(url, header=None)

        idx = 0
        for i, row in df_tese.iterrows():
            if "TICKER" in [str(x).upper().strip() for x in row.values]:
                idx = i
                break
        df_tese.columns = [str(c).strip().upper() for c in df_tese.iloc[idx]]
        df_tese = df_tese.iloc[idx + 1:].reset_index(drop=True)
        df_tese = df_tese[df_tese['TICKER'].notna()]
        df_tese = df_tese[df_tese['TICKER'].astype(str).str.strip() != '']

        resultado = {}
        for _, r in df_tese.iterrows():
            ticker = str(r.get('TICKER', '')).strip().upper()
            if not ticker:
                continue
            resultado[ticker] = {
                'tese': str(r.get('TESE', '')).strip(),
                'roe_min': limpar_valor(r.get('ROE_MIN', 0)) or None,
                'pl_max': limpar_valor(r.get('PL_MAX', 0)) or None,
                'div_max': limpar_valor(r.get('DIV_EBITDA_MAX', 0)) or None,
                'data': str(r.get('DATA_REGISTRO', '-')).strip(),
            }
        return resultado
    except Exception:
        return {}

tese_dict = load_tese()


def checar_divergencia_tese(ticker, tese_info, roe_atual, pl_atual, div_atual):
    """Compara os limites definidos na tese com os valores atuais.
    Retorna lista de strings descrevendo cada divergência encontrada
    (lista vazia = tese ainda válida, nada divergiu)."""
    divergencias = []
    if tese_info.get('roe_min') and roe_atual and roe_atual < tese_info['roe_min']:
        divergencias.append(
            f"ROE: sua tese assumia mínimo de {tese_info['roe_min']:.1f}% — atual é {roe_atual:.1f}%"
        )
    if tese_info.get('pl_max') and pl_atual and pl_atual > tese_info['pl_max']:
        divergencias.append(
            f"P/L: sua tese assumia máximo de {tese_info['pl_max']:.1f}x — atual é {pl_atual:.1f}x"
        )
    if tese_info.get('div_max') and div_atual and div_atual > tese_info['div_max']:
        divergencias.append(
            f"Dívida/EBITDA: sua tese assumia máximo de {tese_info['div_max']:.1f}x — atual é {div_atual:.1f}x"
        )
    return divergencias

# --- SIDEBAR ---
st.sidebar.markdown("""
<div style="padding:4px 0 12px 0; border-bottom:1px solid rgba(255,255,255,0.08);
            margin-bottom:16px;">
    <span style="font-size:1.1em; font-weight:800; color:#F1EFE8; letter-spacing:1px;">
        🎯 Filtros
    </span>
</div>
""", unsafe_allow_html=True)

# Busca rápida sempre visível
busca_ticker = st.sidebar.text_input("🔍 Buscar ticker:", placeholder="ex: BBSE3").strip().upper()

# Filtro por setor — protegido contra NaN/células vazias na coluna SETOR
# (uma linha com SETOR em branco vira NaN no pandas, e sorted() não consegue
# comparar float (NaN) com str, gerando TypeError)
if not df.empty and 'SETOR' in df.columns:
    setores_brutos = df['SETOR'].dropna().unique().tolist()
    setores_disponiveis = sorted([s for s in setores_brutos if str(s).strip() != ''])
else:
    setores_disponiveis = []
filtro_setor = st.sidebar.multiselect("🏢 Setor:", setores_disponiveis)

st.sidebar.markdown("---")

# Status de preço
st.sidebar.markdown("**💰 Status de Preço**")
status_opcoes = {
    "Todos":                 None,
    "🟢 Forte oportunidade": "oportunidade",
    "🔵 Zona de compra":     "compra",
    "🟠 Acima do teto":      "acima_teto",
    "🔴 Acima do target":    "acima_target",
}
filtro_status = st.sidebar.radio(
    "", list(status_opcoes.keys()),
    index=0, label_visibility="collapsed"
)
filtro_status_val = status_opcoes[filtro_status]

st.sidebar.markdown("---")

# Filtros quantitativos em expander (oculto por padrão)
with st.sidebar.expander("⚙️ Filtros Quantitativos", expanded=False):
    ativar_filtros = st.checkbox("Ativar filtros", value=False)
    min_score  = st.slider("⭐ Score mínimo:",            0.0, 10.0,  0.0, step=0.5)
    max_pl     = st.slider("P/L abaixo de:",              0.0, 50.0, 20.0)
    min_dy     = st.slider("DY acima de (%):",            0.0, 20.0,  6.0)
    max_div    = st.slider("Dívida/EBITDA abaixo de:",    0.0, 10.0,  3.0)
    min_cagr   = st.slider("CAGR Lucros acima de (%):",  0.0, 50.0, 10.0)

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
    st.session_state.modo_exibicao = 'Cards'


@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)
def _programa_recompra_cache():
    return baixar_programa_recompra()


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def _mapa_tickers_cache(ano_ref):
    return baixar_mapa_tickers(int(ano_ref))


def montar_extras_confluencia(lista_ativos_com_score, meses=6):
    """
    Converte a recompra (Fundamentus) pro formato que score_confluencia()
    espera em `extras`: ['ticker', 'recompra'].

    Por que SÓ recompra, e não mais valuation/dividend safety (como já foi):
    o Score de Confluência é sobre MOVIMENTAÇÃO -- quem está comprando ou
    vendendo (insiders, controlador, a própria empresa). Valuation e
    dividend safety são dimensões DIFERENTES (quanto custa o papel, quão
    seguro é o dividendo) que não têm relação causal com quem está
    comprando/vendendo -- misturar os dois numa "concordância" só confundia
    a leitura, sem ganho real de sinal.

    recompra: líquido (R$) de recompra de ações pela própria empresa, na
    mesma janela (`meses`) usada pro resto do Score -- vem do Fundamentus
    (get_recompras_data, já usado na aba Movimentação), e NÃO da CVM. O
    arquivo da CVM (Art. 11) só cobre negociação de PESSOAS (insiders);
    recompra de tesouraria não aparece lá -- confirmado depois de um
    ticker (AXIA3) mostrar "recompra" idêntica ao "insider" no Score, o
    que era a mesma linha sendo contada duas vezes, não dois sinais reais.

    Atenção de performance: assim como o Ranking Fórmula Mágica, isso busca
    Fundamentus pra cada ticker do universo -- lento só na primeira carga do
    dia (depois fica em cache de 24h via get_recompras_data).
    """
    linhas = []
    for a in lista_ativos_com_score:
        ticker = a['row'].get('CÓDIGO')

        recompra_val = 0.0
        try:
            df_rec, _ = get_recompras_data(ticker)
            resumo_rec = resumo_periodo(df_rec, meses=meses)
            if resumo_rec and resumo_rec.get('tipo') == 'periodo':
                recompra_val = resumo_rec['valor']
        except Exception:
            recompra_val = 0.0

        linhas.append({
            'ticker': ticker,
            'recompra': recompra_val,
        })
    return pd.DataFrame(linhas)


def pagina_ativo(ticker, row, ativo_data, lista_ativos_com_score=None):
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

    # ---- Cabeçalho — sempre visível, fora das abas ----
    hcol1, hcol2 = st.columns([1, 5])
    with hcol1:
        if logo_url:
            st.markdown(
                "<img src='{}' style='height:64px;width:auto;border-radius:11px;background:#F1EFE8;padding:4px;'/>".format(logo_url),
                unsafe_allow_html=True)
    with hcol2:
        st.markdown(
            "<h1 style='margin:0;color:#D4AF37;font-size:1.8em;font-weight:900;letter-spacing:1.5px;'>{}</h1>"
            "<span style='color:#ccc;font-size:0.88em;'>{}</span>".format(
                ticker, row.get('SETOR','-')),
            unsafe_allow_html=True)

    st.markdown("<div style='margin:8px 0 4px 0;height:1px;background:rgba(255,255,255,0.1);'></div>", unsafe_allow_html=True)

    card_style = (
        "display:flex; flex-direction:column; padding:15px 17px; border-radius:11px; "
        "background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.12); "
        "min-height:100px; box-sizing:border-box; "
    )

    # ---- Indicadores extras (ROIC, VPA, PEG) — buscados uma vez, usados na aba de Valuation ----
    with st.spinner("Buscando indicadores fundamentalistas extras..."):
        ind_extras, erro_ind = get_indicadores_fundamentus(ticker)

    roic_val = _ind_buscar(ind_extras, 'roic') if ind_extras else None
    vpa_val = _ind_buscar(ind_extras, 'vpa') if ind_extras else None
    pl_atual_val = _ind_buscar(ind_extras, 'p/l', 'p / l') if ind_extras else None
    # Blindagem: P/L real de empresa nao passa de algumas centenas. Se vier
    # um numero absurdo (ex: 2720x), e sinal de erro de leitura na pagina do
    # Fundamentus (celula deslocada) -- melhor mostrar "-" do que um numero
    # errado.
    if pl_atual_val is not None and (pl_atual_val <= 0 or pl_atual_val > 300):
        pl_atual_val = None
    p_ebit_val = _ind_buscar(ind_extras, 'p/ebit', 'p / ebit') if ind_extras else None
    ev_ebitda_val = _ind_buscar(ind_extras, 'ev/ebitda', 'ev / ebitda') if ind_extras else None
    marg_liq_val = _ind_buscar(ind_extras, 'marg. l', 'margem l') if ind_extras else None
    roa_val = _ind_buscar(ind_extras, 'roa') if ind_extras else None
    div_liq_patrim_val = _ind_buscar(ind_extras, 'patrim') if ind_extras else None

    pl_proj_num = limpar_valor(row.get('P/L PROJETADO', 0))
    cagr_num_peg = limpar_valor(row.get('CAGR lucros (últ. 5 anos)', 0))
    peg_val = (pl_proj_num / cagr_num_peg) if (pl_proj_num > 0 and cagr_num_peg > 0) else None

    # ---- Tese de Investimento + Alerta de Divergência ----
    tese_info = tese_dict.get(ticker.upper())
    if tese_info and tese_info.get('tese'):
        roe_atual = ativo_data.get('roe_num_raw', 0)
        div_atual = limpar_valor(row.get('Dívida líquida/EBITDA', 0))
        divergencias = checar_divergencia_tese(ticker, tese_info, roe_atual, pl_proj_num, div_atual)

        cor_tese = "#D9534F" if divergencias else "#4CAF6D"
        st.markdown(
            "<div style='background:rgba(255,255,255,0.04);border:1px solid {cor}66;"
            "border-radius:11px;padding:14px 18px;margin-bottom:14px;'>"
            "<div style='font-size:0.78em;color:#ccc;font-weight:600;letter-spacing:0.5px;"
            "text-transform:uppercase;margin-bottom:6px;'>📝 Sua Tese de Investimento "
            "<span style='color:#888;font-weight:400;'>({data})</span></div>"
            "<div style='font-size:0.92em;color:#F1EFE8;line-height:1.5;'>{tese}</div>"
            "</div>".format(cor=cor_tese, data=tese_info.get('data', '-'), tese=tese_info['tese']),
            unsafe_allow_html=True
        )
        if divergencias:
            st.warning(
                "⚠️ **Sua tese pode estar desatualizada — a realidade mudou:**\n\n" +
                "\n".join(f"- {d}" for d in divergencias)
            )
        else:
            st.success("✅ Os limites da sua tese ainda estão sendo respeitados pelos números atuais.")

    # ---- Abas (botões com estado, não st.tabs) ----
    # st.tabs() executa o codigo de TODAS as abas a cada rerun, mesmo as que
    # nao estao visiveis -- isso significa buscar Fundamentus/CVM/OpLab/Yahoo
    # pras 6 abas de uma vez so, sempre, mesmo so querendo ver "Visao Geral".
    # Com botoes + session_state, só a aba selecionada de fato executa.
    if 'aba_ativa' not in st.session_state or st.session_state.get('aba_ativa_ticker') != ticker:
        st.session_state.aba_ativa = "📊 Visão Geral"
        st.session_state.aba_ativa_ticker = ticker

    _NOMES_ABAS = ["📊 Visão Geral", "🧭 Panorama", "💰 Valuation", "📈 Dividendos",
                   "👤 Movimentação", "📑 Resultado", "📐 Volatilidade"]
    _cols_abas = st.columns(len(_NOMES_ABAS))
    for _col, _nome in zip(_cols_abas, _NOMES_ABAS):
        with _col:
            if st.button(_nome, key=f"aba_btn_{ticker}_{_nome}", use_container_width=True,
                        type="primary" if st.session_state.aba_ativa == _nome else "secondary"):
                st.session_state.aba_ativa = _nome
                st.rerun()
    st.markdown("<div style='margin-bottom:14px;'></div>", unsafe_allow_html=True)
    aba_ativa = st.session_state.aba_ativa

    # ════════════════════════════════════════════════════════════════════
    # ABA: VISÃO GERAL
    # ════════════════════════════════════════════════════════════════════
    if aba_ativa == "📊 Visão Geral":
        gov = GOVERNANCA.get(ticker, {})
        out = OUTLOOK_2026.get(ticker, {})
        nota_gov = gov.get('nota', None)
        obs_gov  = gov.get('obs', '')

        gcol1, gcol2 = st.columns(2)

        with gcol1:
            if nota_gov is not None:
                if nota_gov >= 8:
                    gov_cor, gov_label = "#4CAF6D", "Alta"
                elif nota_gov >= 6:
                    gov_cor, gov_label = "#D4AF37", "Média"
                else:
                    gov_cor, gov_label = "#D9534F", "Baixa"
                st.markdown(
                    "<div style='{base}'>"
                    "<div style='font-size:0.78em;color:#ccc;font-weight:600;letter-spacing:0.5px;"
                    "text-transform:uppercase;margin-bottom:8px;'>🏛️ Governança Corporativa</div>"
                    "<div style='display:flex;align-items:center;gap:10px;margin-bottom:6px;'>"
                    "<span style='font-size:1.9em;font-weight:900;color:{cor};line-height:1;'>{nota}</span>"
                    "<span style='font-size:0.85em;color:{cor};font-weight:700;'>{label}</span>"
                    "</div>"
                    "<div style='font-size:0.92em;color:#ddd;line-height:1.6;'>{obs}</div>"
                    "</div>".format(base=card_style, cor=gov_cor, nota=nota_gov,
                                    label=gov_label, obs=obs_gov),
                    unsafe_allow_html=True
                )

        with gcol2:
            if out:
                st.markdown(
                    "<div style='{base}'>"
                    "<div style='font-size:0.78em;font-weight:600;color:#ccc;letter-spacing:0.5px;"
                    "text-transform:uppercase;margin-bottom:8px;'>{icone} Outlook 2026</div>"
                    "<div style='font-size:0.92em;color:#ddd;line-height:1.6;'>{texto}</div>"
                    "</div>".format(base=card_style, icone=out['icone'], texto=out['texto']),
                    unsafe_allow_html=True
                )

        # ---- Estudo Específico (so aparece se existir entrada pro ticker) ----
        estudo = ESTUDOS_ESPECIFICOS.get(ticker)
        if estudo:
            metrica_valor = locals().get(estudo.get('metrica', ''), None)
            metrica_html = (
                f"<div style='margin-top:10px;font-size:0.95em;color:#D4AF37;font-weight:800;'>"
                f"P/VP atual: {metrica_valor}</div>"
                if metrica_valor and metrica_valor != '-' else ""
            )
            st.markdown(
                "<div style='{base}margin-top:14px;border:1px solid rgba(212,175,55,0.35);'>"
                "<div style='font-size:0.78em;font-weight:600;color:#D4AF37;letter-spacing:0.5px;"
                "text-transform:uppercase;margin-bottom:8px;'>🔬 Estudo Específico — {titulo}</div>"
                "<div style='font-size:0.85em;color:#ddd;line-height:1.55;'>{texto}</div>"
                "{metrica_html}"
                "</div>".format(base=card_style, titulo=estudo['titulo'], texto=estudo['texto'],
                                metrica_html=metrica_html),
                unsafe_allow_html=True
            )

        # Teto / Target / Status
        pt_v  = ativo_data.get('preco_teto_val', 0) if isinstance(ativo_data, dict) else 0
        tg_v  = ativo_data.get('target_val', 0)      if isinstance(ativo_data, dict) else 0
        s_cor = ativo_data.get('st_cor', '#888')      if isinstance(ativo_data, dict) else '#888'
        s_ico = ativo_data.get('st_icone', '⚪')      if isinstance(ativo_data, dict) else '⚪'
        s_desc= ativo_data.get('st_desc', '')         if isinstance(ativo_data, dict) else ''
        cot_v = limpar_valor(str(ativo_data.get('row', {}).get('Cotação atual', 0) if isinstance(ativo_data, dict) else 0).replace('R$',''))

        if pt_v > 0 and tg_v > 0:
            pct_teto   = ((pt_v - cot_v) / pt_v * 100) if cot_v < pt_v else -((cot_v - pt_v) / pt_v * 100)
            pct_target = ((tg_v - cot_v) / tg_v * 100) if cot_v < tg_v else -((cot_v - tg_v) / tg_v * 100)

            st.markdown(
                f"<div style='padding:18px 20px;border-radius:11px;margin:12px 0 6px 0;"
                f"background:rgba(255,255,255,0.04);border:2px solid {s_cor};'>"
                f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:12px;'>"
                f"<span style='font-size:1.5em;'>{s_ico}</span>"
                f"<span style='font-size:1.05em;font-weight:700;color:{s_cor};'>{s_desc}</span>"
                f"</div>"
                f"<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;text-align:center;'>"
                f"<div><div style='font-size:0.85em;color:#ccc;margin-bottom:5px;'>COTAÇÃO ATUAL</div>"
                f"<div style='font-size:1.5em;font-weight:800;color:#F1EFE8;'>R$ {cot_v:.2f}</div></div>"
                f"<div><div style='font-size:0.85em;color:#ccc;margin-bottom:5px;'>PREÇO TETO</div>"
                f"<div style='font-size:1.5em;font-weight:800;color:#D4AF37;'>R$ {pt_v:.2f}</div>"
                f"<div style='font-size:0.85em;color:#ccc;'>{'▼' if pct_teto > 0 else '▲'} {abs(pct_teto):.1f}%</div></div>"
                f"<div><div style='font-size:0.85em;color:#ccc;margin-bottom:5px;'>TARGET</div>"
                f"<div style='font-size:1.5em;font-weight:800;color:#4CAF6D;'>R$ {tg_v:.2f}</div>"
                f"<div style='font-size:0.85em;color:#ccc;'>{'▼' if pct_target > 0 else '▲'} {abs(pct_target):.1f}%</div></div>"
                f"</div></div>",
                unsafe_allow_html=True
            )

        # ---- Caixas-resumo: 4 caixas do MESMO tamanho (altura fixa) ----
        st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)

        ALTURA_RESUMO = "200px"

        def _card_resumo(col, titulo, itens, tamanho_linha="0.95em"):
            linhas = ""
            for item in itens:
                label, valor, cor = (item + ("#F1EFE8",))[:3] if len(item) == 2 else item
                linhas += (
                    f"<div style='display:flex;justify-content:space-between;font-size:{tamanho_linha};"
                    "margin-top:7px;'>"
                    f"<span style='color:#94A3B8;'>{label}</span>"
                    f"<span style='color:{cor};font-weight:700;'>{valor}</span></div>"
                )
            col.markdown(
                "<div style='{base}height:{altura};display:flex;flex-direction:column;"
                "justify-content:flex-start;box-sizing:border-box;'>"
                "<div style='font-size:0.82em;color:#ccc;text-transform:uppercase;"
                "margin-bottom:4px;text-align:center;'>{titulo}</div>"
                "{linhas}"
                "</div>".format(base=card_style, altura=ALTURA_RESUMO, titulo=titulo, linhas=linhas),
                unsafe_allow_html=True
            )

        def _card_score_hero(col, valor):
            col.markdown(
                "<div style='{base}height:{altura};display:flex;flex-direction:column;"
                "justify-content:center;align-items:center;text-align:center;box-sizing:border-box;'>"
                "<div style='font-size:0.72em;color:#ccc;text-transform:uppercase;margin-bottom:8px;'>"
                "⭐ Score Fundamentalista</div>"
                "<div style='font-size:2.6em;font-weight:900;color:#D4AF37;line-height:1;'>{valor}/10</div>"
                "</div>".format(base=card_style, altura=ALTURA_RESUMO, valor=valor),
                unsafe_allow_html=True
            )

        def _texto_rank_resumo(rank, n):
            if rank is None or not n or n <= 1:
                return "—"
            if rank == 1:
                return "🥇 Melhor do setor"
            if rank == n:
                return "Último do setor"
            return f"{rank}º de {n}"

        r0, r1, r2, r3 = st.columns(4)

        var_resumo_str = f"{variacao_dia:+.2f}%".replace(".", ",")
        cor_var = "#4CAF6D" if variacao_dia > 0 else ("#D9534F" if variacao_dia < 0 else "#D4AF37")
        _card_resumo(r0, "💹 Mercado", [
            ("Cotação Atual", cot),
            ("Variação (dia)", var_resumo_str, cor_var),
            ("Mínima (12m)", ativo_data.get('low', '-')),
            ("Máxima (12m)", ativo_data.get('high', '-')),
        ])

        pl_atual_resumo = f"{pl_atual_val:.2f}".replace(".", ",") + "x" if pl_atual_val is not None else "—"
        ds_score_resumo = ativo_data.get('div_safety_score')
        _card_resumo(r1, "💰 Valuation & Dividendos", [
            ("P/L Atual", pl_atual_resumo),
            ("ROE", roe),
            ("Dividend Yield", f"{dy_clean}%"),
            ("Dividend Safety", f"{ds_score_resumo}/10" if ds_score_resumo is not None else "—"),
        ])

        n_setor_resumo = ativo_data.get('n_setor')
        n_pl_setor_resumo = ativo_data.get('n_pl')
        _card_resumo(r2, "🎯 Posição no Setor", [
            ("ROE", _texto_rank_resumo(ativo_data.get('rank_roe'), n_setor_resumo)),
            ("Dividend Yield", _texto_rank_resumo(ativo_data.get('rank_dy'), n_setor_resumo)),
            ("P/L (mais barato)", _texto_rank_resumo(ativo_data.get('rank_pl'), n_pl_setor_resumo)),
        ], tamanho_linha="0.95em")

        _card_score_hero(r3, score)

    # ════════════════════════════════════════════════════════════════════
    # ABA: PANORAMA (orientação pra quem não conhece a empresa)
    # ════════════════════════════════════════════════════════════════════
    if aba_ativa == "🧭 Panorama":
        panorama = PANORAMA_EMPRESA.get(ticker)
        if panorama:
            st.markdown(
                "<div style='font-size:1.05em;color:#F1EFE8;line-height:1.65;"
                "padding:4px 2px 18px 2px;border-bottom:1px solid rgba(255,255,255,0.10);"
                "margin-bottom:18px;'>{texto}</div>".format(texto=panorama["o_que_faz"]),
                unsafe_allow_html=True
            )

            st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
            st.markdown(
                "<div style='font-size:0.78em;color:#ccc;font-weight:600;text-transform:uppercase;"
                "letter-spacing:0.5px;margin-bottom:8px;'>💵 De onde vem a receita</div>",
                unsafe_allow_html=True
            )
            seg_cols = st.columns(2)
            for i, (nome_seg, desc_seg) in enumerate(panorama["segmentos"]):
                with seg_cols[i % 2]:
                    st.markdown(
                        "<div style='{base}margin-bottom:10px;'>"
                        "<div style='font-size:0.85em;color:#D4AF37;font-weight:700;margin-bottom:4px;'>{nome}</div>"
                        "<div style='font-size:0.82em;color:#ddd;line-height:1.5;'>{desc}</div>"
                        "</div>".format(base=card_style, nome=nome_seg, desc=desc_seg),
                        unsafe_allow_html=True
                    )

            st.markdown(
                "<div style='{base}border:1px solid rgba(212,175,55,0.4);margin-top:4px;'>"
                "<div style='font-size:0.78em;color:#D4AF37;font-weight:700;text-transform:uppercase;"
                "letter-spacing:0.5px;margin-bottom:8px;'>💡 Detalhe que faz diferença</div>"
                "<div style='font-size:0.88em;color:#F1EFE8;line-height:1.6;'>{texto}</div>"
                "</div>".format(base=card_style, texto=panorama["insight_chave"]),
                unsafe_allow_html=True
            )

            st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
            st.markdown(
                "<div style='{base}'>"
                "<div style='font-size:0.78em;color:#ccc;font-weight:600;text-transform:uppercase;"
                "letter-spacing:0.5px;margin-bottom:8px;'>📐 Dinâmica do Setor</div>"
                "<div style='font-size:0.88em;color:#ddd;line-height:1.6;'>{texto}</div>"
                "</div>".format(base=card_style, texto=panorama["setor_dinamica"]),
                unsafe_allow_html=True
            )

            st.caption(
                "Fonte: apresentações institucionais, releases e demonstrações financeiras "
                "da própria empresa. Atualizado periodicamente."
            )
        else:
            st.info("Panorama ainda não disponível para este ativo.")

    # ════════════════════════════════════════════════════════════════════
    # ABA: VALUATION & FUNDAMENTOS
    # ════════════════════════════════════════════════════════════════════
    if aba_ativa == "💰 Valuation":
        def _card_metric(col, titulo, texto, cor_valor="#F1EFE8"):
            col.markdown(
                "<div style='{base}text-align:center;'>"
                "<div style='font-size:0.72em;color:#ccc;text-transform:uppercase;'>{titulo}</div>"
                "<div style='font-size:1.25em;font-weight:900;color:{cor};'>{texto}</div>"
                "</div>".format(base=card_style, titulo=titulo, texto=texto, cor=cor_valor),
                unsafe_allow_html=True
            )

        st.markdown("#### 📊 Valuation")

        # ---- Linha 1: Resultado Projetado + Resultado Último Tri ----
        v1, v2 = st.columns([1, 1])
        _card_metric(v1, "Resultado Projetado 2026", row.get('LL PROJETADO', '-'))
        _card_metric(v2, "⭐ Resultado Último Tri (1/4)", row.get('RESULTADO 2026 (1/4)', '-'), cor_valor="#4CAF6D")
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        barra = "<div style='background:#222;border-radius:5px;height:9px;width:100%;margin:5px 0 3px 0;'><div style='background:{};width:{}%;height:9px;border-radius:5px;'></div></div>".format(cor, porcentagem)
        st.markdown(barra, unsafe_allow_html=True)
        st.markdown("<span style='font-size:0.85em;color:{};font-weight:bold;'>Status: {}% do resultado projetado</span>".format(cor, porcentagem), unsafe_allow_html=True)

        # ---- Linha 2: trio de P/L ----
        # P/L Atual  = Fundamentus (trailing, igual Status Invest/Investidor10)
        # P/L Médio  = planilha do Diego (coluna "P/L médio (últ. 10 anos)")
        # P/L Projetado = planilha do Diego (cenário próprio, normalmente
        #                  conservador/pessimista -- por isso tende a vir
        #                  mais alto que o atual quando ele projeta queda de lucro)
        st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
        pl_proj = row.get('P/L PROJETADO', '-')
        pl_atual_str = f"{pl_atual_val:.2f}".replace(".", ",") + "x" if pl_atual_val is not None else "-"
        pl1, pl2, pl3 = st.columns(3)
        _card_metric(pl1, "P/L Atual", pl_atual_str, cor_valor="#D4AF37")
        _card_metric(pl2, "P/L Médio (10 anos)", f"{row.get('P/L médio (últ. 10 anos)', '-')}x")
        _card_metric(pl3, "P/L Projetado", f"{pl_proj}x")
        st.caption(
            "P/L Médio (10 anos) é uma referência histórica. P/L Projetado reflete o cenário "
            "de resultado adotado na modelagem — quando esse cenário é conservador, o P/L "
            "Projetado tende a ficar acima do P/L Atual."
        )

        # ---- Os 2 graficos lado a lado, cada um ocupando metade da pagina ----
        st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            if historico_lucro:
                st.markdown("<span style='font-size:0.8em;color:#ccc;font-weight:bold;'>📈 Lucro Líquido (5 anos)</span>", unsafe_allow_html=True)
                st.markdown(mini_grafico_linha(historico_lucro, "#4CAF6D"), unsafe_allow_html=True)
        with g2:
            if historico_pl:
                st.markdown("<span style='font-size:0.8em;color:#ccc;font-weight:bold;'>📈 P/L Histórico (5 anos)</span>", unsafe_allow_html=True)
                st.markdown(mini_grafico_linha(historico_pl, "#5B8DB8", label_suffix="x"), unsafe_allow_html=True)

        st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)
        st.markdown("#### 🔎 Indicadores")

        # ---- Demais indicadores (Operacional + Fundamentus, unificados) ----
        def _card_ind(col, titulo, valor, sufixo="", prefixo="", fmt="{:.2f}"):
            texto = (prefixo + fmt.format(valor) + sufixo).replace(".", ",") if valor is not None else "—"
            _card_metric(col, titulo, texto)

        i1, i2, i3, i4 = st.columns(4)
        _card_metric(i1, "Dívida Líq/EBITDA", row.get('Dívida líquida/EBITDA', '-'))
        _card_metric(i2, "CAGR Lucros", row.get('CAGR lucros (últ. 5 anos)', '-'))
        _card_metric(i3, "ROE", roe)
        _card_metric(i4, "Margem Líq.", margem)
        i5, i6, i7, i8 = st.columns(4)
        _card_metric(i5, "Beta (vs IBOV)", beta)
        if ind_extras:
            _card_ind(i6, "ROIC", roic_val, sufixo="%")
            _card_ind(i7, "VPA", vpa_val, prefixo="R$ ")
            _card_ind(i8, "PEG Ratio", peg_val, sufixo="x")
            i9, i10, i11, i12 = st.columns(4)
            _card_ind(i9, "P/EBIT", p_ebit_val, sufixo="x")
            _card_ind(i10, "EV/EBITDA", ev_ebitda_val, sufixo="x")
            _card_metric(i11, "P/VP", pvp_str if pvp_str != "-" else "—")
            _card_ind(i12, "ROA", roa_val, sufixo="%")
            st.caption(
                "PEG Ratio é calculado (P/L Projetado ÷ CAGR de Lucros) — abaixo de 1x "
                "geralmente indica crescimento 'baixo' em relação ao preço pago; acima de "
                "2x pode indicar preço esticado frente ao crescimento."
            )
        else:
            st.info("Indicadores extras indisponíveis para este ativo.")
            if erro_ind:
                st.caption(f"🔧 Detalhe técnico: {erro_ind}")

        # ---- Percentil Setorial ----
        st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)
        st.markdown("#### 🎯 Posição no Setor")
        n_setor = ativo_data.get('n_setor')
        rank_roe = ativo_data.get('rank_roe')
        rank_dy = ativo_data.get('rank_dy')
        rank_pl = ativo_data.get('rank_pl')
        n_pl_setor = ativo_data.get('n_pl')
        if n_setor and n_setor > 1:
            def _cor_rank(rank, n):
                if rank is None or not n:
                    return "#888"
                pct_topo = (n - rank) / (n - 1) if n > 1 else 0
                return "#4CAF6D" if pct_topo >= 0.7 else ("#D4AF37" if pct_topo >= 0.3 else "#D9534F")
            def _texto_rank(rank, n):
                if rank is None or not n:
                    return "—"
                if rank == 1:
                    return "🥇 Melhor do setor"
                if rank == n:
                    return "Último do setor"
                return f"{rank}º de {n}"
            pcol1, pcol2, pcol3 = st.columns(3)
            pcol1.markdown(
                "<div style='{base}text-align:center;'>"
                "<div style='font-size:0.72em;color:#ccc;text-transform:uppercase;'>ROE</div>"
                "<div style='font-size:1.15em;font-weight:900;color:{cor};'>{texto}</div>"
                "</div>".format(base=card_style, texto=_texto_rank(rank_roe, n_setor), cor=_cor_rank(rank_roe, n_setor)),
                unsafe_allow_html=True
            )
            pcol2.markdown(
                "<div style='{base}text-align:center;'>"
                "<div style='font-size:0.72em;color:#ccc;text-transform:uppercase;'>Dividend Yield</div>"
                "<div style='font-size:1.15em;font-weight:900;color:{cor};'>{texto}</div>"
                "</div>".format(base=card_style, texto=_texto_rank(rank_dy, n_setor), cor=_cor_rank(rank_dy, n_setor)),
                unsafe_allow_html=True
            )
            pcol3.markdown(
                "<div style='{base}text-align:center;'>"
                "<div style='font-size:0.72em;color:#ccc;text-transform:uppercase;'>P/L (mais barato)</div>"
                "<div style='font-size:1.15em;font-weight:900;color:{cor};'>{texto}</div>"
                "</div>".format(base=card_style, texto=_texto_rank(rank_pl, n_pl_setor), cor=_cor_rank(rank_pl, n_pl_setor)),
                unsafe_allow_html=True
            )
            st.caption(
                f"Comparado a {n_setor} ativo(s) do setor '{row.get('SETOR', '-')}' no RADAR "
                f"(P/L compara só com {n_pl_setor or 0}, já que ativos com P/L negativo/zero ficam de fora). "
                "Com poucos ativos no setor, é normal o resultado ser bem extremo (1º ou último) — "
                "isso não é erro, é só uma amostra pequena."
            )
        else:
            st.info("Posição setorial indisponível (setor com só este ativo no RADAR, ou dado faltando).")

        # ---- Preço Justo Multi-Método ----
        st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)
        st.markdown("#### 🎯 Preço Justo (3 Métodos)")
        pj = calcular_preco_justo(row, vpa_val=vpa_val)
        cot_pj = pj.get('cotacao')
        pjcol1, pjcol2, pjcol3 = st.columns(3)

        def _card_pj(col, metodo, valor):
            if valor is None:
                col.markdown(
                    "<div style='{base}text-align:center;'>"
                    "<div style='font-size:0.75em;color:#ccc;text-transform:uppercase;'>{metodo}</div>"
                    "<div style='font-size:0.85em;color:#888;margin-top:6px;'>Não computável</div>"
                    "</div>".format(base=card_style, metodo=metodo),
                    unsafe_allow_html=True
                )
                return
            diff_pct = ((valor - cot_pj) / cot_pj * 100) if cot_pj else None
            cor_pj = "#4CAF6D" if (diff_pct or 0) > 0 else "#D9534F"
            sub = f"{'+' if diff_pct and diff_pct>=0 else ''}{diff_pct:.1f}% vs cotação" if diff_pct is not None else ""
            col.markdown(
                "<div style='{base}text-align:center;'>"
                "<div style='font-size:0.75em;color:#ccc;text-transform:uppercase;'>{metodo}</div>"
                "<div style='font-size:1.3em;font-weight:900;color:#F1EFE8;'>R$ {valor:.2f}</div>"
                "<div style='font-size:0.78em;color:{cor};font-weight:700;margin-top:4px;'>{sub}</div>"
                "</div>".format(base=card_style, metodo=metodo, valor=valor, cor=cor_pj, sub=sub),
                unsafe_allow_html=True
            )

        _card_pj(pjcol1, "Bazin (dividendo)", pj['bazin'])
        _card_pj(pjcol2, "Graham (LPA × VPA)", pj['graham'])
        _card_pj(pjcol3, "Gordon (crescimento)", pj['gordon'])
        st.caption(
            f"Cotação atual: R$ {cot_pj:.2f}".replace(".", ",") if cot_pj else "" +
            " · Gordon usa taxa de desconto fixa de 12% a.a. e crescimento limitado a 8% a.a. "
            "(evita o modelo 'explodir' com CAGRs muito altos/instáveis) — por isso costuma dar "
            "valores mais altos que Bazin/Graham quando o crescimento reportado é forte. "
            "Nenhum desses é uma 'verdade' — são 3 lentes diferentes; quando os 3 apontam pra "
            "mesma direção (barato ou caro), o sinal é mais forte."
        )

    # ════════════════════════════════════════════════════════════════════
    # ABA: DIVIDENDOS
    # ════════════════════════════════════════════════════════════════════
    if aba_ativa == "📈 Dividendos":
        st.markdown("#### 💰 Dividendos")
        style_dy = "color:#4CAF6D;font-weight:bold;" if dy_num > 8 else ""
        st.markdown("<div style='font-size:0.88em;line-height:1.7;'>"
            "<b>Dividend Yield:</b> <span style='{}'>{}</span><br>"
            "<b>Payout:</b> {}<br>"
            "<b>LPA Est.:</b> {}<br>"
            "<b>Div. Projetado:</b> {}<br>"
            "<b>Data Ex (último):</b> {}<br>"
            "<b>Valor Último Div.:</b> {}"
            "</div>".format(
                style_dy, dy_clean + "%", row.get('PAYOUT', '-'),
                row.get('LPA ESTIMADO', '-'), row.get('Dividendo por ação bruto projetado', '-'),
                dt, val),
            unsafe_allow_html=True)
        if proximo_provento_data != "-":
            st.markdown(
                "<div style='margin-top:6px;padding:5px 8px;border-radius:6px;background:#1a3a1a;border:1px solid #4CAF6D;font-size:0.84em;'>"
                "<span style='color:#4CAF6D;font-weight:bold;'>📅 Próximo Provento em Aberto</span><br>"
                "<span style='color:#F1EFE8;'>Data COM: <b>{}</b> | Valor Est.: <b>{}</b></span></div>".format(
                    proximo_provento_data, proximo_provento_valor),
                unsafe_allow_html=True)
        else:
            st.markdown(
                "<div style='margin-top:6px;padding:4px 8px;border-radius:6px;background:#2a2a2a;border:1px solid #777;color:#ccc;font-size:0.8em;'>📅 Nenhum provento futuro identificado</div>",
                unsafe_allow_html=True)
        st.markdown("<span style='font-size:0.85em;font-weight:bold;'>Histórico DY (5 anos):</span>", unsafe_allow_html=True)
        st.markdown(mini_grafico_dy(historico_dy), unsafe_allow_html=True)

        # ---- Dividend Safety Score ----
        st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)
        ds_score = ativo_data.get('div_safety_score')
        ds_label = ativo_data.get('div_safety_label')
        ds_cor = ativo_data.get('div_safety_cor', '#888')
        if ds_score is not None:
            st.markdown(
                "<div style='{base}'>"
                "<div style='font-size:0.78em;color:#ccc;font-weight:600;letter-spacing:0.5px;"
                "text-transform:uppercase;margin-bottom:8px;'>🛡️ Dividend Safety Score</div>"
                "<div style='display:flex;align-items:center;gap:10px;'>"
                "<span style='font-size:1.9em;font-weight:900;color:{cor};'>{score}/10</span>"
                "<span style='font-size:0.9em;color:{cor};font-weight:700;'>{label}</span>"
                "</div>"
                "<div style='font-size:0.78em;color:#999;margin-top:8px;line-height:1.4;'>"
                "Score separado do Score geral — foca só no risco de corte do dividendo. "
                "Combina Payout (35%), consistência de lucro (25%), Dívida/EBITDA (20%) e ROE (20%)."
                "</div></div>".format(base=card_style, cor=ds_cor, score=ds_score, label=ds_label),
                unsafe_allow_html=True
            )

        st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)
        st.markdown("#### 💵 Proventos")
        with st.spinner("Buscando histórico de proventos..."):
            df_prov_det, df_prov_ano, erro_prov = get_proventos_data(ticker)

        if not df_prov_det.empty:
            corte_12m = pd.Timestamp.now() - pd.DateOffset(months=12)
            total_12m = df_prov_det[df_prov_det['data'] >= corte_12m]['valor'].sum()
            st.markdown(
                "<div style='{base}'>"
                "<div style='font-size:0.78em;color:#ccc;font-weight:600;letter-spacing:0.5px;"
                "text-transform:uppercase;margin-bottom:8px;'>Últimos 12 meses</div>"
                "<div style='font-size:1.3em;font-weight:900;color:#4CAF6D;'>R$ {total:.4f} / ação</div>"
                "<div style='font-size:0.75em;color:#999;margin-top:6px;line-height:1.4;'>"
                "Soma de dividendos e JCP pagos nos últimos 12 meses.</div>"
                "</div>".format(base=card_style, total=total_12m),
                unsafe_allow_html=True
            )
            with st.expander("Ver histórico de proventos (detalhado e por ano)"):
                if not df_prov_ano.empty:
                    st.markdown("**Resumo por ano:**")
                    show_ano = df_prov_ano.copy()
                    show_ano['valor'] = show_ano['valor'].apply(lambda v: f"R$ {v:.4f}".replace(".", ","))
                    show_ano.columns = ['Ano', 'Valor por Ação']
                    st.dataframe(show_ano, use_container_width=True, hide_index=True)
                st.markdown("**Histórico detalhado (últimos 24 lançamentos):**")
                show_det = df_prov_det.head(24).copy()
                show_det['data'] = show_det['data'].dt.strftime('%d/%m/%Y')
                show_det['valor'] = show_det['valor'].apply(lambda v: f"R$ {v:.4f}".replace(".", ","))
                cols_mostrar = [c for c in ['data', 'valor', 'tipo', 'data_pagamento'] if c in show_det.columns]
                show_det = show_det[cols_mostrar]
                show_det.columns = ['Data', 'Valor', 'Tipo', 'Data Pagamento'][:len(cols_mostrar)]
                st.dataframe(show_det, use_container_width=True, hide_index=True)
        else:
            st.info("Dados de proventos indisponíveis para este ativo.")
            if erro_prov:
                st.caption(f"🔧 Detalhe técnico: {erro_prov}")

    # ════════════════════════════════════════════════════════════════════
    # ABA: MOVIMENTAÇÃO (Insiders + Recompras)
    # ════════════════════════════════════════════════════════════════════
    if aba_ativa == "👤 Movimentação":
        # ---- Síntese (CVM) — vem primeiro: é a leitura interpretada ----
        st.markdown(
            "<div style='font-size:0.78em;color:#94A3B8;margin-bottom:10px;line-height:1.5;'>"
            f"ℹ️ O número abaixo (Score de Confluência) é <b>diferente</b> do Score "
            f"Fundamentalista (⭐ {score}/10) mostrado no topo da página. Aqui medimos "
            "só sinais de insider/recompra/controlador via CVM — não fundamentos, "
            "valuation ou dividendos."
            "</div>",
            unsafe_allow_html=True
        )
        render_confluencia_card(
            st, ticker,
            tickers_universo=df['CÓDIGO'].dropna().astype(str).tolist(),
            extras=montar_extras_confluencia(lista_ativos_com_score) if lista_ativos_com_score else None,
        )

        st.markdown("<div style='margin:20px 0 4px 0;height:1px;background:rgba(255,255,255,0.08);'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:0.78em;color:#ccc;font-weight:600;letter-spacing:0.5px;"
            "text-transform:uppercase;margin:14px 0 4px 0;'>📋 Histórico Detalhado</div>"
            "<div style='font-size:0.78em;color:#94A3B8;margin-bottom:12px;'>"
            "Ledger mês a mês, com histórico de múltiplos anos — mais longo que a janela "
            "da síntese acima, mas sem separar diretoria/conselho de controlador.</div>",
            unsafe_allow_html=True
        )

        icol1, icol2 = st.columns(2)

        with st.spinner("Buscando dados de insiders e recompras..."):
            df_ins, erro_ins = get_insiders_data(ticker)
            df_rec, erro_rec = get_recompras_data(ticker)

        with icol1:
            if not df_ins.empty:
                resumo = resumo_periodo(df_ins, 6)
                if resumo is None:
                    cor_ins, sub_ins = "#888", "Nenhuma movimentação registrada"
                elif resumo['tipo'] == 'periodo':
                    cor_ins = "#4CAF6D" if resumo['valor'] >= 0 else "#D9534F"
                    label = "Compra líquida" if resumo['valor'] >= 0 else "Venda líquida"
                    sub_ins = f"{label} (6m): R$ {abs(resumo['valor']):,.0f}".replace(",", ".")
                else:
                    cor_ins = "#4CAF6D" if resumo['valor'] >= 0 else "#D9534F"
                    label = "Última compra" if resumo['valor'] >= 0 else "Última venda"
                    sub_ins = f"{label} ({resumo['data'].strftime('%m/%Y')}): R$ {abs(resumo['valor']):,.0f}".replace(",", ".")
                st.markdown(
                    "<div style='{base}'>"
                    "<div style='font-size:0.78em;color:#ccc;font-weight:600;letter-spacing:0.5px;"
                    "text-transform:uppercase;margin-bottom:8px;'>👤 Insiders</div>"
                    "<div style='font-size:1.3em;font-weight:900;color:{cor};'>{sub}</div>"
                    "<div style='font-size:0.75em;color:#999;margin-top:6px;line-height:1.4;'>"
                    "Movimentação de controladores, diretoria e conselho.</div>"
                    "</div>".format(base=card_style, cor=cor_ins, sub=sub_ins),
                    unsafe_allow_html=True
                )
                with st.expander("Ver histórico mensal de insiders"):
                    show_ins = df_ins.head(12).copy()
                    show_ins['data'] = show_ins['data'].dt.strftime('%m/%Y')
                    show_ins['valor'] = show_ins['valor'].apply(lambda v: f"R$ {v:,.0f}".replace(",", "."))
                    show_ins['preco_medio'] = show_ins['preco_medio'].apply(lambda v: f"R$ {v:.2f}".replace(".", ","))
                    show_ins.columns = ['Mês', 'Quantidade', 'Valor', 'Preço Médio']
                    st.dataframe(show_ins, use_container_width=True, hide_index=True)
            else:
                st.markdown(
                    "<div style='{base}'>"
                    "<div style='font-size:0.78em;color:#ccc;font-weight:600;letter-spacing:0.5px;"
                    "text-transform:uppercase;margin-bottom:8px;'>👤 Insiders</div>"
                    "<div style='font-size:0.85em;color:#888;'>Dados indisponíveis para este ativo.</div>"
                    "</div>".format(base=card_style),
                    unsafe_allow_html=True
                )
                if erro_ins:
                    st.caption(f"🔧 Detalhe técnico: {erro_ins}")

        with icol2:
            if not df_rec.empty:
                resumo = resumo_periodo(df_rec, 6)
                if resumo is None:
                    cor_rec, sub_rec = "#888", "Nenhuma recompra registrada"
                elif resumo['tipo'] == 'periodo':
                    cor_rec = "#5B8DB8"
                    sub_rec = f"Total (6m): R$ {abs(resumo['valor']):,.0f}".replace(",", ".")
                else:
                    cor_rec = "#5B8DB8"
                    sub_rec = f"Última recompra ({resumo['data'].strftime('%m/%Y')}): R$ {abs(resumo['valor']):,.0f}".replace(",", ".")
                st.markdown(
                    "<div style='{base}'>"
                    "<div style='font-size:0.78em;color:#ccc;font-weight:600;letter-spacing:0.5px;"
                    "text-transform:uppercase;margin-bottom:8px;'>🏢 Recompras</div>"
                    "<div style='font-size:1.3em;font-weight:900;color:{cor};'>{sub}</div>"
                    "<div style='font-size:0.75em;color:#999;margin-top:6px;line-height:1.4;'>"
                    "Ações recompradas pela própria empresa (tesouraria).</div>"
                    "</div>".format(base=card_style, cor=cor_rec, sub=sub_rec),
                    unsafe_allow_html=True
                )
                with st.expander("Ver histórico mensal de recompras"):
                    show_rec = df_rec.head(12).copy()
                    show_rec['data'] = show_rec['data'].dt.strftime('%m/%Y')
                    show_rec['valor'] = show_rec['valor'].apply(lambda v: f"R$ {v:,.0f}".replace(",", "."))
                    show_rec['preco_medio'] = show_rec['preco_medio'].apply(lambda v: f"R$ {v:.2f}".replace(".", ","))
                    show_rec.columns = ['Mês', 'Quantidade', 'Valor', 'Preço Médio']
                    st.dataframe(show_rec, use_container_width=True, hide_index=True)
            else:
                st.markdown(
                    "<div style='{base}'>"
                    "<div style='font-size:0.78em;color:#ccc;font-weight:600;letter-spacing:0.5px;"
                    "text-transform:uppercase;margin-bottom:8px;'>🏢 Recompras</div>"
                    "<div style='font-size:0.85em;color:#888;'>Sem programa de recompra ativo ou dados indisponíveis.</div>"
                    "</div>".format(base=card_style),
                    unsafe_allow_html=True
                )
                if erro_rec:
                    st.caption(f"🔧 Detalhe técnico: {erro_rec}")

        # ---- Programa de Recompra ativo (fato verificável, sem ambiguidade) ----
        # Dataset separado e dedicado da CVM (atualizado diariamente). Diz SE
        # existe autorização do conselho em vigor pra recomprar -- não diz
        # quanto foi efetivamente comprado (essa informação não tem fonte
        # estruturada confiável -- já tentamos 3 vezes e nenhuma se sustentou).
        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        with st.spinner(" "):
            try:
                df_programas = _programa_recompra_cache()
                mapa_prog = _mapa_tickers_cache(pd.Timestamp.now().year)
                cnpj_ticker = mapa_prog.get(ticker.upper())
                programa = programa_recompra_ativo(df_programas, cnpj_ticker) if cnpj_ticker else None
            except Exception:
                programa = None

        if programa:
            data_final_str = programa["data_final"].strftime("%d/%m/%Y")
            qtds = []
            if programa.get("qtd_on") and str(programa["qtd_on"]) not in ("0", "nan", "None"):
                qtds.append(f"{int(float(programa['qtd_on'])):,} ON".replace(",", "."))
            if programa.get("qtd_pn") and str(programa["qtd_pn"]) not in ("0", "nan", "None"):
                qtds.append(f"{int(float(programa['qtd_pn'])):,} PN".replace(",", "."))
            qtd_str = " + ".join(qtds) if qtds else "quantidade não informada"
            st.markdown(
                "<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(212,175,55,0.35);"
                "border-radius:10px;padding:12px 16px;'>"
                "<div style='font-size:0.78em;color:#D4AF37;font-weight:600;text-transform:uppercase;"
                "margin-bottom:4px;'>📋 Programa de Recompra Ativo</div>"
                f"<div style='font-size:0.88em;color:#ddd;'>Autorizado até <b>{data_final_str}</b> — "
                f"até {qtd_str} (máximo autorizado, não é o que já foi comprado).</div>"
                "</div>", unsafe_allow_html=True
            )
        else:
            st.caption(
                "📋 Nenhum programa de recompra em andamento no cadastro atual da CVM "
                "(esse dataset é novo, de nov/2025, e pode ter atraso pra refletir "
                "renovações recentes — confirme no site da própria empresa se tiver dúvida)."
            )

    # ════════════════════════════════════════════════════════════════════
    # ABA: DOCUMENTOS (Apresentações)
    # ════════════════════════════════════════════════════════════════════
    if aba_ativa == "📑 Resultado":
        analise = ANALISE_RESULTADO.get(ticker)
        if analise:
            st.markdown(
                "<div style='{base}border:1px solid rgba(212,175,55,0.35);'>"
                "<div style='display:flex;justify-content:space-between;align-items:baseline;"
                "margin-bottom:10px;'>"
                "<div style='font-size:0.85em;color:#D4AF37;font-weight:700;text-transform:uppercase;"
                "letter-spacing:0.5px;'>📊 Análise do Último Resultado — {tri}</div>"
                "<div style='font-size:0.72em;color:#888;'>Divulgado em {data}</div>"
                "</div>"
                "<div style='font-size:0.85em;color:#F1EFE8;font-weight:700;margin-bottom:4px;'>Números</div>"
                "<div style='font-size:0.85em;color:#ddd;line-height:1.55;margin-bottom:12px;'>{numeros}</div>"
                "<div style='font-size:0.85em;color:#4CAF6D;font-weight:700;margin-bottom:4px;'>✓ Pontos fortes</div>"
                "<div style='font-size:0.85em;color:#ddd;line-height:1.55;margin-bottom:12px;'>{fortes}</div>"
                "<div style='font-size:0.85em;color:#D9534F;font-weight:700;margin-bottom:4px;'>✗ Pontos de atenção</div>"
                "<div style='font-size:0.85em;color:#ddd;line-height:1.55;margin-bottom:12px;'>{fracos}</div>"
                "<div style='font-size:0.85em;color:#5B8DB8;font-weight:700;margin-bottom:4px;'>→ O que esperar</div>"
                "<div style='font-size:0.85em;color:#ddd;line-height:1.55;'>{expectativa}</div>"
                "</div>".format(
                    base=card_style, tri=analise["trimestre"], data=analise["data"],
                    numeros=analise["numeros"], fortes=analise["pontos_fortes"],
                    fracos=analise["pontos_fracos"], expectativa=analise["expectativa"],
                ),
                unsafe_allow_html=True
            )
            st.caption(
                "Fonte: release de resultados e casas de análise (XP, BTG, Genial, Nord e "
                "outras). Referente ao trimestre indicado acima."
            )
            st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)
        else:
            st.info("Análise do último resultado ainda não disponível para este ativo.")
            st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)

        with st.spinner("Buscando apresentações..."):
            df_apres, erro_apres = get_apresentacoes_data(ticker)

        if not df_apres.empty:
            data_ref = analise["data"] if analise else None
            ultimo_release = ultimo_release_resultado(df_apres, data_referencia=data_ref)

            def _card_apresentacao(item, titulo, cor):
                if item is None:
                    return (
                        "<div style='{base}'>"
                        "<div style='font-size:0.78em;color:#ccc;font-weight:600;'>{titulo}</div>"
                        "<div style='font-size:0.85em;color:#888;margin-top:6px;'>Nenhuma encontrada.</div>"
                        "</div>".format(base=card_style, titulo=titulo)
                    )
                data_fmt = item['data_dt'].strftime('%d/%m/%Y')
                desc = str(item['descricao'])[:90]
                link = item.get('link')
                link_html = (
                    f"<a href='{link}' target='_blank' style='display:inline-block;margin-top:8px;"
                    f"padding:5px 12px;border-radius:6px;background:{cor};color:#000;"
                    f"font-weight:700;font-size:0.78em;text-decoration:none;'>⬇ Abrir / Baixar</a>"
                    if link else "<span style='color:#888;font-size:0.78em;'>Link indisponível</span>"
                )
                return (
                    "<div style='{base}'>"
                    "<div style='font-size:0.78em;color:#ccc;font-weight:600;margin-bottom:6px;'>{titulo}</div>"
                    "<div style='font-size:0.85em;color:#F1EFE8;font-weight:600;'>{data}</div>"
                    "<div style='font-size:0.78em;color:#ddd;margin-top:4px;line-height:1.4;'>{desc}</div>"
                    "{link_html}"
                    "</div>".format(base=card_style, titulo=titulo, data=data_fmt, desc=desc, link_html=link_html)
                )

            st.markdown(_card_apresentacao(ultimo_release, "📊 Release/Apresentação de Resultados mais recente", "#4CAF6D"),
                       unsafe_allow_html=True)

            with st.expander("Ver todas as apresentações e comunicados"):
                show_apres = df_apres.head(30).copy()
                show_apres['data'] = show_apres['data_dt'].dt.strftime('%d/%m/%Y')
                for _, linha in show_apres.iterrows():
                    link_l = linha.get('link')
                    link_md = f"[Download]({link_l})" if link_l else "—"
                    st.markdown(f"**{linha['data']}** — {linha['descricao']} — {link_md}")
            st.caption(
                "⚠️ A identificação do documento é baseada no texto da descrição (não é uma "
                "categoria oficial da CVM nesta página) — pode ocasionalmente pegar um "
                "documento com nome atípico. Confira a data antes de considerar definitivo."
            )
        else:
            st.info("Nenhuma apresentação encontrada para este ativo.")
            if erro_apres:
                st.caption(f"🔧 Detalhe técnico: {erro_apres}")

    # ════════════════════════════════════════════════════════════════════
    # ABA: GRÁFICO (candlestick + volatilidade implícita)
    # ════════════════════════════════════════════════════════════════════
    if aba_ativa == "📐 Volatilidade":
        with st.spinner("Buscando volatilidade implícita..."):
            vol_info, erro_vol = get_volatilidade_ticker(ticker)

        if vol_info is not None:
            vi = vol_info['vol_implicita']
            rank = vol_info['iv_rank']
            pct = vol_info['iv_percentil']
            cor_vi = "#D9534F" if (rank or 0) >= 70 else ("#D4AF37" if (rank or 0) >= 30 else "#4CAF6D")
            vcol1, vcol2, vcol3 = st.columns(3)
            with vcol1:
                st.markdown(
                    "<div style='{base}text-align:center;'>"
                    "<div style='font-size:0.75em;color:#ccc;text-transform:uppercase;'>Vol. Implícita</div>"
                    "<div style='font-size:1.4em;font-weight:900;color:{cor};'>{v}</div>"
                    "</div>".format(base=card_style, cor=cor_vi,
                                    v=f"{vi:.2f}%".replace(".", ",") if vi is not None else "—"),
                    unsafe_allow_html=True
                )
            with vcol2:
                st.markdown(
                    "<div style='{base}text-align:center;'>"
                    "<div style='font-size:0.75em;color:#ccc;text-transform:uppercase;'>IV Rank</div>"
                    "<div style='font-size:1.4em;font-weight:900;color:{cor};'>{v}</div>"
                    "</div>".format(base=card_style, cor=cor_vi,
                                    v=f"{rank:.0f}%".replace(".", ",") if rank is not None else "—"),
                    unsafe_allow_html=True
                )
            with vcol3:
                st.markdown(
                    "<div style='{base}text-align:center;'>"
                    "<div style='font-size:0.75em;color:#ccc;text-transform:uppercase;'>IV Percentil</div>"
                    "<div style='font-size:1.4em;font-weight:900;color:{cor};'>{v}</div>"
                    "</div>".format(base=card_style, cor=cor_vi,
                                    v=f"{pct:.0f}%".replace(".", ",") if pct is not None else "—"),
                    unsafe_allow_html=True
                )
        else:
            st.info("Volatilidade implícita indisponível para este ativo.")
            if erro_vol:
                st.caption(f"🔧 Detalhe técnico: {erro_vol}")

        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("##### 📉 Preço Histórico")
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
                    increasing_line_color='#4CAF6D', decreasing_line_color='#D9534F', name=ticker
                )])
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.3)',
                    font_color='#F1EFE8',
                    xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                    margin=dict(l=0, r=0, t=10, b=0), height=420,
                    xaxis_rangeslider_visible=False,
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.warning("Não foi possível carregar o gráfico de preços.")

    # Respiro no final da página -- sem isso o último conteúdo (seja qual
    # for a aba aberta) fica colado na borda inferior da tela.
    st.markdown("<div style='margin-bottom:70px;'></div>", unsafe_allow_html=True)


# --- DASHBOARD ---
st.markdown("""
<div style="position:relative; margin-bottom:20px; padding:10px 0 16px 0;
            border-bottom:1px solid rgba(255,255,255,0.08);">
    <h1 style="margin:0; font-size:clamp(1.4em, 6vw, 2.4em); font-weight:900; letter-spacing:2px;
               text-transform:uppercase; color:#F1EFE8; line-height:1.1; word-wrap:break-word;">
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

@st.cache_data(ttl=3600, show_spinner=False)
def get_ibov():
    """Retorna (valor_atual, variacao_dia_pct) do Ibovespa via Yahoo Finance,
    ou (None, None) em erro. Tenta o histórico primeiro (mais estável que o
    endpoint .info, que falha com mais frequência)."""
    try:
        ibov = yf.Ticker("^BVSP")
        atual = anterior = None
        try:
            hist = ibov.history(period="5d")
            if len(hist) >= 2:
                atual = hist['Close'].iloc[-1]
                anterior = hist['Close'].iloc[-2]
        except Exception:
            pass
        if not atual or not anterior:
            info = ibov.info
            atual = info.get('regularMarketPrice') or info.get('currentPrice')
            anterior = info.get('previousClose')
        if atual and anterior:
            return atual, ((atual - anterior) / anterior) * 100
        return None, None
    except Exception:
        return None, None


@st.cache_data(ttl=3600, show_spinner=False)
def get_selic():
    """Retorna a Selic atual (% a.a.) via API do Banco Central (série
    432 do SGS), ou None em erro."""
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        dados = r.json()
        if not dados:
            return None
        valor = dados[-1]['valor']
        return float(valor.replace(',', '.')) if isinstance(valor, str) else float(valor)
    except Exception:
        return None


ibov_val, ibov_var = get_ibov()
selic_val = get_selic()

# ---- Linha 1: Total+Filtrados (juntas = largura de 1 caixa de baixo);
# Ibovespa+Selic (juntas = largura de 2 caixas de baixo, centralizadas) ----
c1, c2, c3, c4 = st.columns([0.5, 0.5, 1, 1])
with c1:
    st.markdown(f"""<div class='top-card'>
        <div class='label'>📋 Total de Ativos</div>
        <div class='value'>{len(df)}</div>
    </div>""", unsafe_allow_html=True)
with c2:
    card_filtrados = st.empty()
with c3:
    if ibov_val is not None:
        cor_ibov = "#4CAF6D" if ibov_var > 0 else ("#D9534F" if ibov_var < 0 else "#D4AF37")
        ibov_fmt = f"{ibov_val:,.0f}".replace(",", ".")
        st.markdown(f"""<div class='top-card'>
            <div class='label'>📊 Ibovespa</div>
            <div class='value'>{ibov_fmt}</div>
            <div class='sub' style='color:{cor_ibov};'>{ibov_var:+.2f}%</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class='top-card'>
            <div class='label'>📊 Ibovespa</div>
            <div class='value'>—</div>
        </div>""", unsafe_allow_html=True)
with c4:
    if selic_val is not None:
        selic_fmt = f"{selic_val:.2f}".replace(".", ",")
        st.markdown(f"""<div class='top-card'>
            <div class='label'>🏦 Selic</div>
            <div class='value'>{selic_fmt}% a.a.</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class='top-card'>
            <div class='label'>🏦 Selic</div>
            <div class='value'>—</div>
        </div>""", unsafe_allow_html=True)

st.markdown(
    "<div style='margin:14px 0 14px 0;border-bottom:1px solid rgba(255,255,255,0.08);'></div>",
    unsafe_allow_html=True
)

# ---- Linha 2: Maior Desconto P/L, Maior DY, Maior Score -- 3 cards iguais ----
c5, c6, c7 = st.columns(3)
with c5:
    card_menor_pl = st.empty()
with c6:
    st.markdown(f"""<div class='top-card'>
        <div class='label'>🏆 Maior DY</div>
        <div class='value'>{ticker_max_dy}</div>
        <div class='sub'>{val_max_dy}</div>
    </div>""", unsafe_allow_html=True)
with c7:
    card_maior_score = st.empty()



st.markdown("""
<style>
div[data-testid="stButton"] button[kind="primary"] {
    background-color: #D4AF37 !important;
    color: #0B1929 !important;
    border: none !important;
    font-weight: 700 !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
    background-color: #BFA033 !important;
}
</style>
""", unsafe_allow_html=True)
tcol2, tcol3, tcol4, tcol5 = st.columns([1, 1, 1.4, 6])
with tcol2:
    if st.button("⊞ Cards", use_container_width=True,
                 type="primary" if st.session_state.modo_exibicao == 'Cards' else "secondary"):
        st.session_state.modo_exibicao = 'Cards'
        st.rerun()
with tcol3:
    if st.button("⚖ Comparar", use_container_width=True,
                 type="primary" if st.session_state.modo_exibicao == 'Comparar' else "secondary"):
        st.session_state.modo_exibicao = 'Comparar'
        st.rerun()
with tcol4:
    if st.button("🎯 Confluência", use_container_width=True,
                 type="primary" if st.session_state.modo_exibicao == 'Confluência' else "secondary"):
        st.session_state.modo_exibicao = 'Confluência'
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
                               pvp_num=pvp_num_raw, setor=row.get('SETOR', ''),
                               ticker=row.get('CÓDIGO', ''), historico_lucro=historico_lucro)

        preco_teto_val = row.get('preco_teto', 0) if 'preco_teto' in row.index else limpar_valor(str(row.get('PREÇO TETO', 0)))
        target_val     = row.get('target', 0) if 'target' in row.index else limpar_valor(str(row.get('TARGET', 0)))
        st_status, st_cor, st_icone, st_desc = status_aporte(row.get('Cotação atual', 0), preco_teto_val, target_val)

        div_safety_score, div_safety_label, div_safety_cor = calcular_dividend_safety(
            row.get('PAYOUT', '-'), div_ebitda_num, roe_num_raw, historico_lucro
        )

        ativos_com_score.append({
            'row': row, 'score': score,
            'dy_num': dy_num, 'dy_clean': dy_clean, 'pl_num': pl_num,
            'progresso': progresso, 'porcentagem': porcentagem,
            'dt': dt, 'val': val, 'roe': roe, 'margem': margem,
            'low': low, 'high': high,
            'roe_num_raw': roe_num_raw,
            'beta': beta, 'pvp_str': pvp_str,
            'historico_dy': historico_dy,
            'historico_pl': historico_pl,
            'historico_lucro': historico_lucro,
            'proximo_provento_data': proximo_provento_data,
            'proximo_provento_valor': proximo_provento_valor,
            'variacao_dia': variacao_dia,
            'iv_str': iv_str,
            'logo_url': logo_url,
            'st_status': st_status,
            'st_cor': st_cor,
            'st_icone': st_icone,
            'st_desc': st_desc,
            'preco_teto_val': preco_teto_val,
            'target_val': target_val,
            'div_safety_score': div_safety_score,
            'div_safety_label': div_safety_label,
            'div_safety_cor': div_safety_cor,
        })

    ativos_com_score = calcular_percentis_setoriais(ativos_com_score)
    ativos_com_score = [a for a in ativos_com_score if a['score'] >= _min_score_efetivo]

    # Filtro por status de preço
    if filtro_status_val:
        ativos_com_score = [a for a in ativos_com_score if a.get('st_status') == filtro_status_val]

    ativos_com_score.sort(key=lambda x: x['score'], reverse=True)

    # Sem piso artificial — score honesto reflete a realidade
    # Teto 9.5: o 10 é reservado para casos verdadeiramente excepcionais
    for a in ativos_com_score:
        a['score'] = round(min(a['score'], 9.5), 1)

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

    # ---- Maior desconto: P/L projetado vs P/L médio histórico (10 anos) ----
    # Exclui empresas cíclicas (Vale, Petrobras, Klabin etc.) pois o P/L
    # delas é naturalmente distorcido pelo ciclo de commodities
    melhor_desconto = None
    melhor_pct = 0
    for a in ativos_com_score:
        row = a['row']
        if classificar_setor(row.get('SETOR', '')) == 'ciclica':
            continue
        try:
            pl_proj = float(str(row.get('P/L PROJETADO', '0')).replace(',', '.'))
            pl_med  = float(str(row.get('P/L médio (últ. 10 anos)', '0')).replace(',', '.'))
            if pl_proj > 0 and pl_med > 0 and pl_proj < pl_med:
                desconto_pct = ((pl_med - pl_proj) / pl_med) * 100
                if desconto_pct > melhor_pct:
                    melhor_pct = desconto_pct
                    melhor_desconto = row['CÓDIGO']
        except:
            continue

    if melhor_desconto:
        card_menor_pl.markdown(f"""<div class='top-card'>
            <div class='label'>📉 Maior Desconto P/L</div>
            <div class='value'>{melhor_desconto}</div>
            <div class='sub'>-{melhor_pct:.0f}% vs média 10a</div>
        </div>""", unsafe_allow_html=True)
    else:
        card_menor_pl.markdown("""<div class='top-card'>
            <div class='label'>📉 Maior Desconto P/L</div>
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
                pagina_ativo(ticker_sel, ativo_sel['row'], ativo_sel, ativos_com_score)
                st.stop()
            else:
                st.session_state.ativo_selecionado = None

        # ---- Ranking Fórmula Mágica (Greenblatt) — sob demanda ----
        with st.expander("🪄 Ranking Fórmula Mágica (Greenblatt)"):
            st.caption(
                "Combina Earnings Yield (1/P-L, quanto maior melhor) com ROIC (quanto maior "
                "melhor). Ranqueia cada métrica separadamente e soma as posições — o vencedor "
                "não precisa ser #1 em nenhuma das duas isoladamente, só equilibrado nas duas. "
                "Busca ROIC de todos os ativos (pode demorar uns segundos na primeira vez do dia)."
            )
            if st.button("Calcular Ranking", key="btn_formula_magica"):
                with st.spinner("Buscando ROIC de todos os ativos..."):
                    ranking_fm = calcular_ranking_formula_magica(ativos_com_score)
                if not ranking_fm:
                    st.warning("Não foi possível calcular o ranking (ROIC indisponível pra esses ativos).")
                else:
                    show_fm = pd.DataFrame(ranking_fm[:15])
                    show_fm['earnings_yield'] = (show_fm['earnings_yield'] * 100).round(1).astype(str) + '%'
                    show_fm['roic'] = show_fm['roic'].round(1).astype(str) + '%'
                    show_fm['pl'] = show_fm['pl'].round(1).astype(str) + 'x'
                    show_fm = show_fm[['posicao', 'ticker', 'earnings_yield', 'roic', 'pl', 'rank_total']]
                    show_fm.columns = ['#', 'Ticker', 'Earnings Yield', 'ROIC', 'P/L', 'Soma dos Ranks']
                    st.dataframe(show_fm, use_container_width=True, hide_index=True)

        # Modo Cards
        if st.session_state.modo_exibicao == 'Cards':
            cols_n = 8
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

                    dy_color = "#4CAF6D" if dy_num_c > 8 else "#5B8DB8"
                    logo_html = "<div class='ac-logo-area'><img src='{}' class='ac-logo'/></div>".format(logo_c) if logo_c else "<div class='ac-logo-area' style='font-size:1.8em;'>{}</div>".format(ic_c)

                    with cols[idx]:
                        st_s   = ativo.get('st_status', 'neutro')
                        st_c   = ativo.get('st_cor', '#888888')
                        st_i   = ativo.get('st_icone', '⚪')
                        status_labels = {
                            'oportunidade': 'Forte oportunidade',
                            'compra':       'Zona de compra',
                            'acima_teto':   'Acima do teto',
                            'acima_target': 'Acima do target',
                            'neutro':       'Sem dados',
                        }
                        st_label = status_labels.get(st_s, 'Sem dados')
                        st.markdown(
                            f"<div class='asset-card' style='border:1.5px solid {st_c};'>"
                            + logo_html
                            + f"<div class='ac-ticker'>{ticker_c}</div>"
                            + f"<div class='ac-cot'>{cot_c}</div>"
                            + f"<div style='margin-top:4px;'>{var_html}</div>"
                            + "<div style='display:flex;justify-content:center;gap:14px;"
                              "margin-top:10px;padding-top:8px;"
                              "border-top:1px solid rgba(255,255,255,0.07);'>"
                            + f"<div style='text-align:center;'>"
                              f"<div style='font-size:0.68em;color:#bbb;font-weight:600;'>DY</div>"
                              f"<div style='font-size:0.92em;font-weight:800;color:#F1EFE8;'>{dy_c}%</div></div>"
                            + f"<div style='text-align:center;'>"
                              f"<div style='font-size:0.68em;color:#bbb;font-weight:600;'>P/L</div>"
                              f"<div style='font-size:0.92em;font-weight:800;color:#F1EFE8;'>{pl_c}x</div></div>"
                            + f"<div style='text-align:center;'>"
                              f"<div style='font-size:0.68em;color:#bbb;font-weight:600;'>Score</div>"
                              f"<div style='font-size:0.92em;font-weight:800;color:#D4AF37;'>⭐{score_c}</div></div>"
                            + "</div>"
                            + f"<div style='margin-top:8px;padding:5px 8px;border-radius:6px;"
                              f"background:rgba(255,255,255,0.04);display:flex;align-items:center;"
                              f"justify-content:center;gap:5px;'>"
                              f"<span style='font-size:0.9em;'>{st_i}</span>"
                              f"<span style='font-size:0.72em;color:{st_c};font-weight:600;'>{st_label}</span>"
                            + "</div>"
                            + "</div>",
                            unsafe_allow_html=True
                        )
                        if st.button("Ver detalhes", key="card_{}".format(ticker_c), use_container_width=True):
                            st.session_state.ativo_selecionado = ticker_c
                            st.session_state.aba_ativa = "📊 Visão Geral"
                            st.rerun()
            st.stop()

        # Modo Comparar — tabela lado a lado de 2 a 4 ativos
        if st.session_state.modo_exibicao == 'Comparar':
            st.markdown("#### ⚖ Comparador Par-a-Par")
            st.caption(
                "Escolha de 2 a 4 ativos pra comparar todos os indicadores numa tabela só — "
                "a decisão mais comum não é 'olhar o ativo X', é 'X ou Y, qual eu compro?'."
            )
            tickers_disponiveis = sorted([a['row']['CÓDIGO'] for a in ativos_com_score])
            selecionados = st.multiselect(
                "Ativos para comparar:", tickers_disponiveis, max_selections=4,
                key="comparador_multiselect"
            )

            if len(selecionados) < 2:
                st.info("Selecione pelo menos 2 ativos.")
            else:
                with st.spinner("Buscando ROIC/VPA dos ativos selecionados..."):
                    linhas_comp = {}
                    for tk in selecionados:
                        a = next((x for x in ativos_com_score if x['row']['CÓDIGO'] == tk), None)
                        if a is None:
                            continue
                        r = a['row']
                        ind_extra, _ = get_indicadores_fundamentus(tk)
                        roic_c = _ind_buscar(ind_extra, 'roic') if ind_extra else None
                        vpa_c = _ind_buscar(ind_extra, 'vpa') if ind_extra else None
                        pl_c = a.get('pl_num', 0)
                        cagr_c = limpar_valor(r.get('CAGR lucros (últ. 5 anos)', 0))
                        peg_c = (pl_c / cagr_c) if (pl_c > 0 and cagr_c > 0) else None

                        linhas_comp[tk] = {
                            "Cotação": formatar_cotacao(r.get('Cotação atual', 0)),
                            "Variação (dia)": f"{a.get('variacao_dia', 0):+.2f}%",
                            "Score": f"⭐ {a['score']}/10",
                            "Status": a.get('st_desc', '-'),
                            "P/L Projetado": f"{pl_c:.1f}x" if pl_c else "-",
                            "P/VP": a.get('pvp_str', '-'),
                            "PEG Ratio": f"{peg_c:.2f}x" if peg_c is not None else "-",
                            "ROIC": f"{roic_c:.1f}%" if roic_c is not None else "-",
                            "VPA": f"R$ {vpa_c:.2f}" if vpa_c is not None else "-",
                            "Dividend Yield": f"{a.get('dy_clean', '-')}%",
                            "ROE": a.get('roe', '-'),
                            "Margem Líquida": a.get('margem', '-'),
                            "CAGR Lucros": r.get('CAGR lucros (últ. 5 anos)', '-'),
                            "Dívida Líq/EBITDA": r.get('Dívida líquida/EBITDA', '-'),
                            "Beta": a.get('beta', '-'),
                            "Dividend Safety": f"{a.get('div_safety_score','-')}/10 ({a.get('div_safety_label','-')})",
                        }

                if linhas_comp:
                    df_comp = pd.DataFrame(linhas_comp)
                    st.dataframe(df_comp, use_container_width=True)
                    st.caption("ROIC e VPA buscados em tempo real pra esses ativos — não vêm do cache dos 40 da grade.")
            st.stop()

        # Modo Confluência — ranking de Score de Confluência (CVM) de todos
        # os ativos. Fica DEPOIS da checagem de ativo_selecionado (igual
        # Cards/Comparar) para nunca "sequestrar" a navegação de quem está
        # vendo o detalhe de um ativo.
        if st.session_state.modo_exibicao == 'Confluência':
            try:
                df_programas_completo = _programa_recompra_cache()
            except Exception:
                df_programas_completo = None
            render_confluencia(
                st, tickers=df['CÓDIGO'].dropna().astype(str).tolist(),
                extras=montar_extras_confluencia(ativos_com_score),
                df_programas=df_programas_completo,
            )
            st.stop()
        st.stop()  # blindagem -- nunca deveria chegar aqui (Cards/Comparar/Confluência sempre stopam antes)
