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
#   positivo     #22C55E (verde seco)
#   negativo     #EF4444 (vermelho seco)
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
    color: #22C55E;
    margin-top: 4px;
    font-weight: bold;
}}

/* ---- Cards de DESTAQUE (Maior Desconto P/L, Maior DY, Maior Score) ----
   Mesma estrutura do .top-card, mas com borda/fundo dourados -- são
   destaques reais do radar, não dados neutros como Ibovespa/Selic. ---- */
.destaque-card {{
    background: rgba(212,175,55,0.08);
    border: 1px solid rgba(212,175,55,0.45);
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
    height: 110px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-sizing: border-box;
}}
.destaque-card .label {{
    font-size: 0.78em;
    color: #D4AF37;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
}}
.destaque-card .value {{
    font-size: 1.9em;
    font-weight: 800;
    color: #F1EFE8;
    line-height: 1.1;
}}
.destaque-card .sub {{
    font-size: 0.85em;
    color: #22C55E;
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
.asset-card .ac-var-pos {{ color:#22C55E;font-size:0.85em;font-weight:bold; }}
.asset-card .ac-var-neg {{ color:#EF4444;font-size:0.85em;font-weight:bold; }}
.asset-card .ac-var-neu {{ color:#D4AF37;font-size:0.85em;font-weight:bold; }}
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
        return "#22C55E"
    elif porcentagem >= 25:
        return "#D4AF37"
    else:
        return "#EF4444"

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


def aplicar_ajuste_preco(score_fundamentos, cotacao, preco_teto):
    """Ajusta o score de fundamentos considerando o quanto a cotação ATUAL
    está acima do Preço Teto -- sem isso, uma empresa pode ter ótimos
    fundamentos mas estar "esticada" agora (preço já correu muito) e ainda
    aparecer no topo do ranking, o que não ajuda na decisão de COMPRAR hoje.

    - Preço abaixo do teto: sem penalidade (ainda tem desconto, no pior caso
      o score fica como já era).
    - Preço acima do teto: desconta proporcionalmente, mais forte quanto
      mais esticada -- a cada 10% acima do teto, desconta 0,4 ponto, com um
      teto de penalidade de -2,0 (pra não zerar uma empresa boa só porque a
      ação subiu muito num curto período).

    Retorna (score_ajustado, pct_acima_teto) -- pct_acima_teto é None se não
    houver teto/cotação válidos pra calcular."""
    try:
        cot = float(cotacao)
        teto = float(preco_teto)
    except (TypeError, ValueError):
        return score_fundamentos, None
    if cot <= 0 or teto <= 0:
        return score_fundamentos, None

    pct_acima = ((cot - teto) / teto) * 100
    if pct_acima <= 0:
        return score_fundamentos, pct_acima

    penalidade = min((pct_acima / 10.0) * 0.4, 2.0)
    score_ajustado = round(max(0.0, score_fundamentos - penalidade), 1)
    return score_ajustado, pct_acima


def badge_score(score):
    if score >= 7:
        cor_bg, cor_txt, label = "#1a3a1a", "#22C55E", "Ótimo"
    elif score >= 5:
        cor_bg, cor_txt, label = "#3a3a10", "#D4AF37", "Bom"
    elif score >= 3:
        cor_bg, cor_txt, label = "#3a2010", "#C97D3B", "Regular"
    else:
        cor_bg, cor_txt, label = "#3a1010", "#EF4444", "Fraco"
    return f"""
    <div style="display:flex; align-items:center; gap:10px; margin-top:6px;">
        <span class="score-badge" style="background:{cor_bg}; color:{cor_txt}; border:1px solid {cor_txt};">
            ⭐ Score: {score}/10
        </span>
        <span style="color:{cor_txt}; font-size:0.9em; font-weight:bold;">{label}</span>
    </div>"""


# ---- TIR esperada para 2026 (metodologia própria do Diego) ----
def calcular_tir_2026(row, roe_num, dy_num=None, crescimento_max=0.10, tir_nominal_max=0.20):
    """TIR esperada para o ano corrente, sem valor de saída/terminal --
    metodologia: 'quanto a ação rende esse ano, considerando o que ela paga
    de dividendo mais o quanto ela deve crescer'. Mesma lógica que bancos
    publicam em relatório (retorno implícito comparável a uma NTN-B):

    1. Parte que vira dividendo = Dividend Yield bruto estimado (dy_num) --
       o MESMO número já usado em todo o resto do app (cards, Dividendos).
       Se não disponível, cai pro cálculo derivado (Earnings Yield × Payout)
       como respaldo.
    2. Crescimento esperado -- a fonte muda por tipo de negócio, porque
       "lucro retido reinvestido ao ROE atual" só faz sentido pra empresa
       que CRESCE RETENDO CAPITAL (ex: banco, que usa capital retido pra
       sustentar mais empréstimo). Pra holding de distribuição/seguros
       (asset-light -- cresce vendendo mais apólice pela rede do parceiro,
       não reinvestindo capital), essa lógica não reflete a realidade do
       negócio -- nesse caso usamos o CAGR de lucros histórico (crescimento
       de verdade já observado) em vez da fórmula teórica de reinvestimento.
       - Bancos (capital intensivo de verdade): g = (1−Payout) × ROE
       - Seguradoras/demais (asset-light ou crescimento não-ligado a
         reinvestimento de capital): g = CAGR de lucros histórico
       Ambos limitados a crescimento_max, pelo mesmo motivo (evitar a conta
       "explodir" com ROE ou CAGR muito alto/instável).
    3. TIR nominal = (1) + (2)
    4. TIR real = TIR nominal − IPCA acumulado 12 meses, apresentada como
       'IPCA + X%' (igual o mercado de renda fixa apresenta NTN-B)

    Atualiza sozinha conforme o resultado trimestral muda o DY, o Payout, o
    ROE e o CAGR -- não precisa recalcular manualmente.

    NÃO se aplica bem a empresas cíclicas, com lucro projetado negativo,
    payout ausente/fora de faixa razoável, ROE não disponível, OU quando o
    resultado nominal passa de tir_nominal_max (20% a.a. por padrão) --
    nesses casos retorna None."""
    pl_proj = limpar_valor(row.get('P/L PROJETADO', 0))
    payout_raw = row.get('PAYOUT', '-')
    payout_pct = limpar_valor(payout_raw) if payout_raw not in (None, '-', '') else None

    if payout_pct is None or not (0 < payout_pct <= 150) or roe_num is None or roe_num <= 0:
        return None

    payout = min(payout_pct / 100, 1.0)  # capa em 100% -- acima disso a empresa
                                          # estaria distribuindo mais que o lucro

    if dy_num and dy_num > 0:
        parte_dividendo = dy_num / 100
        ey_exibicao = parte_dividendo / payout * 100 if payout > 0 else None  # só pra mostrar na legenda
    elif pl_proj > 0:
        ey_exibicao = (1 / pl_proj) * 100
        parte_dividendo = (1 / pl_proj) * payout
    else:
        return None

    _setor_cat_tir = classificar_setor(row.get('SETOR', ''))
    _fonte_crescimento = 'reinvestimento_roe' if _setor_cat_tir == 'banco' else 'cagr_historico'
    if _fonte_crescimento == 'reinvestimento_roe':
        g = min((1 - payout) * (roe_num / 100), crescimento_max)
    else:
        cagr_pct_tir = limpar_valor(row.get('CAGR lucros (últ. 5 anos)', 0))
        g = min(max(cagr_pct_tir / 100, 0), crescimento_max)

    tir_nominal = parte_dividendo + g

    if tir_nominal > tir_nominal_max:
        return None

    ipca = get_ipca_12m()
    tir_real = (tir_nominal * 100) - ipca if ipca is not None else None

    return {
        'ey': ey_exibicao if ey_exibicao is not None else 0, 'payout_usado': payout * 100,
        'g': g * 100, 'dy_usado': parte_dividendo * 100, 'fonte_crescimento': _fonte_crescimento,
        'tir_nominal': tir_nominal * 100, 'tir_real': tir_real, 'ipca_usado': ipca,
        'g_no_teto': g >= crescimento_max - 1e-9,
        'payout_baixo': payout < 0.30,  # menos de 30% do retorno vem de dividendo
                                          # de fato pago -- resultado depende mais
                                          # de premissa de crescimento que de caixa real
    }


# ---- Preço Justo Multi-Método (Bazin, Graham, Gordon) ----
def calcular_preco_justo(row, vpa_val=None, taxa_desconto=None, crescimento_max=0.08,
                         premio_risco=0.045):
    """Calcula o preço justo por 3 métodos clássicos de valuation:
    - Bazin: dividendo projetado ÷ taxa real do Tesouro IPCA+ de longo prazo
      (referência de renda fixa "sem risco" indexada à inflação -- mesma
      lógica usada por gestores profissionais pra avaliar se o yield de uma
      ação compensa o risco extra de não ser renda fixa). ANTES usava 6% fixo
      (convenção antiga do livro do Bazin, anos 90) -- desatualizado num
      cenário de juros reais mais altos.
    - Graham: √(22,5 × LPA × VPA) (clássico value investing)
    - Gordon: dividendo×(1+g) ÷ (taxa_desconto−g) (crescimento de dividendos,
      g limitado a crescimento_max pra não estourar o modelo quando o CAGR
      reportado é muito alto/instável). taxa_desconto, se não informada,
      vira taxa real do Tesouro IPCA+ + prêmio de risco (4,5 p.p. por
      padrão) -- antes era 12% fixo, sem nenhuma âncora com a taxa de juros
      vigente.
    Retorna dict com os 3 valores (None se não computável) + a cotação atual."""
    div_proj = limpar_valor(row.get('Dividendo por ação bruto projetado', 0))
    lpa = limpar_valor(row.get('LPA ESTIMADO', 0))
    cagr_pct = limpar_valor(row.get('CAGR lucros (últ. 5 anos)', 0))
    cot = limpar_valor(str(row.get('Cotação atual', 0)).replace('R$', ''))

    taxa_real_pct = get_taxa_real_referencia()  # % a.a., ex: 7.85
    taxa_real = taxa_real_pct / 100

    pj_bazin = (div_proj / taxa_real) if (div_proj > 0 and taxa_real > 0) else None
    pj_graham = ((22.5 * lpa * vpa_val) ** 0.5) if (lpa and lpa > 0 and vpa_val and vpa_val > 0) else None

    if taxa_desconto is None:
        taxa_desconto = taxa_real + premio_risco
    g = min(cagr_pct / 100, crescimento_max) if cagr_pct > 0 else 0
    pj_gordon = None
    if div_proj > 0 and taxa_desconto > g:
        pj_gordon = div_proj * (1 + g) / (taxa_desconto - g)

    return {
        'bazin': pj_bazin, 'graham': pj_graham, 'gordon': pj_gordon,
        'cotacao': cot if cot > 0 else None, 'g_usado': g,
        'taxa_real_usada': taxa_real_pct, 'taxa_desconto_usada': taxa_desconto * 100,
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
        label, cor = "Segurança Alta", "#22C55E"
    elif score_final >= 4:
        label, cor = "Segurança Média", "#D4AF37"
    else:
        label, cor = "Risco de Corte", "#EF4444"

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
        cor = "#22C55E" if val >= 8 else "#5B8DB8"
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
    "ITUB4":  {"icone": "✅", "cor": "#22C55E", "texto": "Ciclo de crédito favorável, inadimplência sob controle, ROE elevado. Um dos melhores momentos operacionais da história. Perspectiva positiva para 2026."},
    "BBAS3":  {"icone": "🔴", "cor": "#EF4444", "texto": "Carteira agro comprometida pela crise do crédito rural — inadimplência em alta e sem sinais de reversão rápida. Guidance revisado para baixo sem aviso. Banco público sujeito a pressão política. Perspectiva negativa para 2026 — aguardar pelo menos 2 trimestres antes de reavaliar."},
    "BBDC3":  {"icone": "🟡", "cor": "#D4AF37", "texto": "Recuperação em curso após anos difíceis. Lucro voltando a crescer mas abaixo dos pares. Posição especulativa de melhora — cautela com alocação."},
    "ABCB4":  {"icone": "✅", "cor": "#22C55E", "texto": "Carteira corporativa de alta qualidade, inadimplência estruturalmente baixa. Perspectiva positiva, menos sensível ao ciclo de varejo."},
    "BRSR6":  {"icone": "🔴", "cor": "#EF4444", "texto": "Duplo impacto: crise do crédito rural gaúcho + reflexos das enchentes de 2024 ainda presentes na carteira. Inadimplência estruturalmente elevada para 2026. Perspectiva negativa."},
    "SANB3":  {"icone": "✅", "cor": "#22C55E", "texto": "Ciclo de melhora operacional. ROE subindo, foco em eficiência. Perspectiva moderadamente positiva para 2026."},
    "BMGB4":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Nicho de consignado INSS sob pressão regulatória. Teto de juros pode impactar margens. Monitorar evolução da regulação em 2026."},
    "BPAC11": {"icone": "✅", "cor": "#22C55E", "texto": "Forte expansão de receitas recorrentes. Menos dependente do ciclo de crédito. Uma das melhores perspectivas do setor financeiro para 2026."},
    "IRBR3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Ressegurador em recuperação pós-fraude. Resultados melhorando, mas histórico exige cautela. El Niño e eventos climáticos extremos são risco relevante."},
    "PSSA3":  {"icone": "✅", "cor": "#22C55E", "texto": "Momento operacional sólido. Seguros auto e residencial com bons resultados. Perspectiva positiva, mas monitorar sinistralidade climática."},
    "CXSE3":  {"icone": "✅", "cor": "#22C55E", "texto": "Crescimento consistente de prêmios via rede da Caixa. Vantagem competitiva de distribuição enorme. Perspectiva positiva para 2026."},
    "ITSA4":  {"icone": "✅", "cor": "#22C55E", "texto": "Holding do Itaú — resultado acompanha o banco. Desconto histórico pode se fechar. Perspectiva positiva com menor volatilidade que o banco diretamente."},
    "PETR4":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Petróleo em patamar moderado (~$70-75). Risco fiscal e de interferência na política de dividendos. Monitorar anúncio de investimentos e possível revisão da remuneração em 2026."},
    "VALE3":  {"icone": "🔴", "cor": "#EF4444", "texto": "Minério de ferro pressionado pela desaceleração chinesa. Acordo de Mariana ainda em negociação (provisão bilionária). 2026 desafiador — aguardar estabilização do cenário China."},
    "BRAP4":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Herda o cenário desafiador da Vale com desconto adicional de holding. Monitorar acordo de Mariana e preço do minério."},
    "CMIN3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Sensível ao preço do minério e desaceleração chinesa. Perspectiva cautelosa para 2026."},
    "GGBR3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Dependente do ciclo de construção civil. Perspectiva neutra — programa de infraestrutura pode ser catalisador positivo em 2026."},
    "KLBN4":  {"icone": "✅", "cor": "#22C55E", "texto": "Celulose e papel com demanda resiliente. Expansão Puma II maturando. Perspectiva positiva para 2026, menos cíclica que pares do setor."},
    "UNIP6":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Margens pressionadas pelo ciclo químico global e dumping chinês de petroquímicos. Perspectiva neutra a negativa para 2026."},
    "LEVE3":  {"icone": "✅", "cor": "#22C55E", "texto": "Reposição automotiva resiliente. Transição para elétricos é risco de longo prazo, irrelevante para 2026. Perspectiva positiva."},
    "SHUL4":  {"icone": "✅", "cor": "#22C55E", "texto": "Compressores industriais com demanda estável. Nicho protegido e bem gerido. Perspectiva positiva para 2026."},
    "VULC3":  {"icone": "✅", "cor": "#22C55E", "texto": "Marca consolidada no esportivo. Expansão de margens em curso. Perspectiva positiva, dependente do consumo doméstico."},
    "TIMS3":  {"icone": "✅", "cor": "#22C55E", "texto": "Crescimento consistente de receita e margens. Mercado consolidado favorece rentabilidade. Excelente perspectiva para 2026."},
    "ALOS3":  {"icone": "✅", "cor": "#22C55E", "texto": "Shoppings em ciclo favorável. Consumo aquecido e vacância baixa. Integração da fusão gerando sinergias. Perspectiva positiva para 2026."},
    "KEPL3":  {"icone": "🔴", "cor": "#EF4444", "texto": "Cenário desafiador: inadimplência rural elevada e crédito agrícola travado reduzem investimentos em armazenagem. Clientes endividados adiam expansões. 2026 deve ser ano de contração de receita — aguardar estabilização do crédito rural."},
    "SLCE3":  {"icone": "🔴", "cor": "#EF4444", "texto": "Agro em momento crítico: margens comprimidas por queda de commodities, câmbio desfavorável e clima incerto. Produtores endividados e sem apetite a risco. 2026 deve trazer queda de receita e resultado — cautela máxima."},
    "RANI3":  {"icone": "✅", "cor": "#22C55E", "texto": "Embalagens de papel com demanda resiliente e crescente. Expansão de capacidade em andamento. Perspectiva positiva para 2026."},
    "CMIG4":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Distribuição e geração reguladas, mas gestão pública limita eficiência. Perspectiva neutra. Atenção ao processo de renovação de concessões."},
    "CPLE3":  {"icone": "✅", "cor": "#22C55E", "texto": "Privatização trazendo eficiência. Perspectiva positiva com potencial de redução de custos e melhora de margens em 2026."},
    "EGIE3":  {"icone": "✅", "cor": "#22C55E", "texto": "Geração renovável com contratos longos. Menor exposição a risco hidrológico por mix diversificado. Perspectiva excelente para 2026."},
    "TAEE11": {"icone": "✅", "cor": "#22C55E", "texto": "Transmissão com RAP garantido — completamente independente de hidrologia. Perspectiva muito positiva e previsível para 2026."},
    "ISAE4":  {"icone": "✅", "cor": "#22C55E", "texto": "Transmissão regulada, receita previsível. Perspectiva positiva similar à Taesa, com ciclo de revisão tarifária favorável."},
    "CPFE3":  {"icone": "✅", "cor": "#22C55E", "texto": "Mix equilibrado de distribuição e geração. Perspectiva positiva beneficiada por revisão tarifária e expansão renovável em 2026."},
    "SBSP3":  {"icone": "✅", "cor": "#22C55E", "texto": "Pós-privatização acelerando investimentos. Perspectiva positiva de médio prazo, mas 2026 ainda é ano de transição e reorganização."},
    "SAPR4":  {"icone": "✅", "cor": "#22C55E", "texto": "Saneamento com demanda inelástica. Perspectiva estável. Revisão tarifária pendente pode ser catalisador positivo em 2026."},
    "CSMG3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Ainda pública. Privatização em discussão pode ser catalisador, mas risco político de MG é relevante. Perspectiva neutra."},
    "AXIA3":  {"icone": "✅", "cor": "#22C55E", "texto": "Fibra óptica em expansão acelerada. Demanda por conectividade crescente e estrutural. Perspectiva positiva para 2026."},
    "B3SA3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Dependente do volume de negociação. Juros altos reduzem fluxo para renda variável. Melhora depende de queda de juros e volta do PF — perspectiva neutra para 2026."},
    "BRBI11": {"icone": "✅", "cor": "#22C55E", "texto": "Banco de investimento em crescimento. Perspectiva positiva dependente do ambiente de M&A e mercado de capitais em 2026."},
    "CYRE3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Bonificação em PN especiais (criada pra antecipar valor antes da tributação de dividendos a partir de 2026) provocou queda nos papéis na virada do ano. Negócio segue sólido e diversificado, mas atenção à diluição e à reação do mercado à nova estrutura de capital."},
    "DIRR3":  {"icone": "✅", "cor": "#22C55E", "texto": "Foco em habitação popular (MCMV Faixas 1-3) torna o negócio mais resiliente ao ciclo de juros. Geração de caixa forte, baixo endividamento e dividendos elevados. Início de 2026 com fundamentos sólidos e ROIC bem acima do custo de capital."},
    "MDNE3":  {"icone": "✅", "cor": "#22C55E", "texto": "Maior construtora do Nordeste. Follow-on de R$500 milhões em jan/2026 dobrou a liquidez do papel. Marca Única (baixa renda/MCMV) é o principal vetor de crescimento, com parceria com a Direcional. Dividend yield esperado de ~7% para 2026."},
    "CURY3":  {"icone": "✅", "cor": "#22C55E", "texto": "Foco em SP e RJ, MCMV + médio padrão. ROE de ~78% e múltiplos baratos (P/L 2026E entre 7x-8,5x). Riscos: pressão de custos de construção, cancelamentos e sensibilidade a mudanças no financiamento do MCMV/FGTS."},
    "LREN3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Setor de varejo de moda pressionado por alta alavancagem das famílias, juros altos e concorrência de plataformas cross-border (Shein, AliExpress). Em contrapartida, P/VPA perto de mínimas históricas (~1,5x) e analistas (Citi, Santander, BTG) seguem recomendando compra, com plano estratégico 2026-2030 prevendo aceleração de aberturas de loja."},
    "GRND3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Lucro recuou em 2025 e o dividendo extraordinário recente (~R$1 bi) não deve se repetir no mesmo nível — payout acima de 170% é insustentável estruturalmente. Caixa líquido robusto (~R$1,1 bi) e baixa alavancagem sustentam a tese de renda, mas crescimento operacional é fraco; 2026 deve trazer normalização dos proventos."},
    "CGRA4":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "Varejo regional tradicional (tecidos/vestuário, RS), baixa cobertura de analistas e liquidez reduzida. Aumento de capital recente dilui a base acionária. Distribuição de JCP retomada em mai/2026, mas sem garantia de regularidade dado o histórico de proventos irregulares."},
    "WEGE3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "1T26 fraco: lucro -5,7% A/A, receita -6,1%, puxados por queda de 36% em GTD doméstico (solar) e câmbio desfavorável. Bancos cortaram projeção de lucro 2026. BTG mantém compra apostando em reaceleração via T&D a partir do 2S26/2027. Curto prazo exige cautela; tese estrutural de longo prazo permanece."},
    "PRIO3":  {"icone": "✅", "cor": "#22C55E", "texto": "1T26 forte: produção +42% T/T, lifting cost caiu para ~US$9,4/bbl, EBITDA ajustado quase dobrou T/T. Alavancagem caiu para 2,0x dívida líquida/EBITDA. Wahoo entrou em produção sem problemas. Queda da ação no pregão foi por correção do petróleo, não por fraqueza operacional."},
    "EQTL3":  {"icone": "⚠️", "cor": "#D4AF37", "texto": "1T26 misto: EBITDA ajustado +11,3% A/A (acima do consenso), mas lucro líquido ajustado caiu -23,6%, pressionado por despesa financeira maior (CDI médio subiu A/A) e maior dívida. Distribuição segue como destaque operacional positivo. Mercado reagiu de forma cautelosa."},
    "JHSF3":  {"icone": "✅", "cor": "#22C55E", "texto": "Melhor 1T da história da companhia: lucro +9,3% A/A, Ebitda ajustado +27%, receita +33%. Crescimento em shoppings, hospitalidade (Fasano) e expansão internacional (Miami, Punta del Este, Milão). Caixa líquido ajustado de R$1,8bi reforça a estrutura de capital mais sólida da história."},
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
    "BPAC11": {
        "trimestre": "1T26", "data": "11/05/2026",
        "numeros": "Lucro líquido ajustado recorde R$4,8bi (+42% A/A), acima do consenso "
                   "(R$4,58bi). Receita total recorde R$9,97bi (+34% A/A). ROE de 26,6% "
                   "(+3,4 p.p. A/A).",
        "pontos_fortes": "Diversificação ampla: Wealth Management (+44,6% A/A, receita "
                   "recorde R$1,52bi), Corporate Lending (+20,7% A/A, carteira R$281bi), "
                   "Sales & Trading (+43% A/A). Consolidação do Banco PAN criou nova "
                   "vertical de Consumer Finance & Banking (+40% A/A). Índice de "
                   "eficiência controlado em 38,1%, próximo da média histórica.",
        "pontos_fracos": "Despesas operacionais subiram 25,5% A/A, puxadas por reajustes "
                   "salariais e maior amortização de ágio das aquisições recentes. "
                   "Investment Banking desacelerou (-9,3% T/T) por maior volatilidade de "
                   "mercado. ROE caiu 1 p.p. T/T (de 27,6% no 4T25).",
        "expectativa": "BTG superou o Itaú em rentabilidade (ROE 26,6% vs 24% do Itaú no "
                   "mesmo trimestre) — junto com o Itaú, é um dos únicos bancos grandes "
                   "com ROE consistentemente acima de 20%. Banco também avalia ativos do "
                   "BRB. Tese de crescimento via diversificação (varejo via Pan/Too "
                   "Seguros, M&A da Meu Tudo) segue sendo o principal vetor.",
    },
    "CXSE3": {
        "trimestre": "1T26", "data": "07/05/2026",
        "numeros": "Lucro líquido gerencial R$1,14bi (+13,2% A/A), maior trimestre da "
                   "história da empresa. Receita operacional R$1,52bi (+10,3% A/A). ROE "
                   "de 38%.",
        "pontos_fortes": "Seguro habitacional (carro-chefe da tese) cresceu 13% A/A em "
                   "prêmios, ligado à força do crédito imobiliário da Caixa. Sinistralidade "
                   "de 22,5%, bem melhor que o esperado (-2,1 p.p.). Capitalização com "
                   "receita de títulos crescendo ~30% A/A. Estoque de cartas de crédito de "
                   "consórcio +39,1% A/A.",
        "pontos_fracos": "Seguro prestamista (ligado a crédito pessoal) caiu 21% A/A, "
                   "pressionado pela Selic alta encarecendo o crédito. 32% do lucro vem do "
                   "resultado financeiro (juros sobre o caixa) — se a Selic cair, essa "
                   "fonte de lucro perde força, embora o crédito imobiliário deva ganhar "
                   "tração em compensação.",
        "expectativa": "Resultado em linha com a XP e 2% acima do consenso do BTG. Casas "
                   "de análise mantêm preferência por BBSE3 (P/L menor, dividend yield "
                   "maior) frente a CXSE3, mas reconhecem a qualidade operacional. "
                   "Dependência da Caixa Econômica Federal (controladora, >80% do "
                   "capital) é estrutural.",
    },
    "AXIA3": {
        "trimestre": "1T26", "data": "06/05/2026",
        "numeros": "Lucro líquido ajustado R$3,2bi, revertendo prejuízo de R$409mi no "
                   "1T25 (quase 8x de melhora). Receita líquida regulatória R$11,6bi "
                   "(+20-22% A/A). EBITDA ajustado R$8,6bi (+60% A/A), com margem "
                   "saltando de 56% para 74%.",
        "pontos_fortes": "Segmento de geração (o mais relevante) teve receita +34-35% "
                   "A/A, beneficiado pela 'descotização' (venda de energia a preço de "
                   "mercado em vez de preço de custo regulado) e por preços de energia de "
                   "longo prazo bem mais altos (R$240/MWh vs R$100-150/MWh nos últimos "
                   "anos). Redução de R$2,2bi no estoque de provisões do empréstimo "
                   "compulsório (passivo jurídico histórico). Migração para o Novo "
                   "Mercado aprovada.",
        "pontos_fracos": "Segmento de transmissão caiu (~-3 a -11% A/A), por provisão de "
                   "R$725mi ligada a ativos/passivos de restituição regulatória. Dívida "
                   "líquida subiu 17% A/A (R$46bi), alavancagem em 1,8-1,9x. Parte "
                   "relevante do lucro vem de efeitos não-recorrentes (reversão de "
                   "provisões), não só de operação recorrente.",
        "expectativa": "Genial mantém compra, citando TIR implícita de 10% real e "
                   "dividend yield esperado de ~10% para 2026, considerando AXIA3 'Top "
                   "Pick' do setor de energia. Atenção do mercado: ritmo de crescimento "
                   "da dívida vs geração de caixa, e transição de liderança executiva "
                   "(saída de Ivan Monteiro, entrada de Elio Wolff).",
    },
    "CPLE3": {
        "trimestre": "1T26", "data": "05/05/2026",
        "numeros": "Lucro líquido R$694mi (+4,4% A/A); lucro recorrente R$639mi (+10,7% "
                   "A/A). Receita líquida recorrente R$6,9bi (+19,2% A/A). EBITDA "
                   "recorrente R$1,75bi (+16,7% A/A).",
        "pontos_fortes": "Geração e Transmissão (GeT) foi o destaque, com EBITDA +30,7% "
                   "A/A, beneficiado por ganhos de modulação hídrica e maior exposição a "
                   "preços spot no submercado Sul. Distribuição cresceu 10% no EBITDA, "
                   "beneficiada pelo reajuste tarifário anual e crescimento de 2,1% no "
                   "mercado fio faturado.",
        "pontos_fracos": "Resultado financeiro negativo cresceu 9,6% A/A. Alavancagem "
                   "subiu de 2,7x para 2,8x dívida líquida/EBITDA. Maior carga tributária "
                   "limitou a expansão do lucro líquido final, mesmo com EBITDA forte. "
                   "Curtailment (restrição de geração eólica) continua pressionando "
                   "custos de compra de energia.",
        "expectativa": "XP destaca a Copel como nome 'premium' do setor pós-privatização "
                   "(2023), negociando a uma TIR real atrativa de 11,5%, com a atual "
                   "gestão considerada uma das melhores do setor de utilities. Empresa "
                   "segue ativa em desinvestimentos de ativos não-core.",
    },
    "ALOS3": {
        "trimestre": "1T26", "data": "07/05/2026",
        "numeros": "Lucro líquido R$248,3mi (-2,5% A/A) — ou R$239mi ex-ajuste de "
                   "aluguel linear. Receita líquida R$683-692mi (+9,8-10,9% A/A). EBITDA "
                   "ajustado R$502mi (+10,2% A/A).",
        "pontos_fortes": "Vendas nos shoppings aceleraram (+6,6% A/A), com vendas em "
                   "mesmas lojas (SSS) de 5,0% (+250 bps A/A) — destaque para Alimentação "
                   "(+7,9%). Despesas (SG&A) caíram 13% A/A. Excluindo o Shopping Tijuca "
                   "(fechado temporariamente por incêndio em janeiro), o crescimento de "
                   "EBITDA seria de 17% e do FFO, 18,2%.",
        "pontos_fracos": "Lucro ficou estável/levemente negativo por causa de um incêndio "
                   "no Shopping Tijuca em janeiro/2026 (~2 semanas de operação "
                   "interrompida) e por despesas financeiras 52% maiores. Taxa de "
                   "ocupação recuou 0,6 p.p. A/A (96,2%).",
        "expectativa": "Nord não vê grande atratividade em ALOS3 no momento (negociando "
                   "a 18x lucros, acima da média histórica) mesmo com dividend yield "
                   "estimado de 12-13%. Allos segue reciclando portfólio: parceria com a "
                   "Kinea para criar um fundo imobiliário (até R$2bi), venda do Shopping "
                   "Curitiba.",
    },
    "TIMS3": {
        "trimestre": "1T26", "data": "05/05/2026",
        "numeros": "Lucro líquido normalizado R$821mi (+1,3% A/A, 12,9% abaixo do "
                   "esperado pela XP). Receita líquida R$6,8bi (+6,5% A/A). EBITDA "
                   "normalizado R$3,287bi (+6,6% A/A), margem 48,3%.",
        "pontos_fortes": "Receita pós-paga (principal motor) cresceu 7,5% A/A, com ARPU "
                   "pós-pago em R$55,1 (+1,6%). Receita do segmento fixo (fibra) acelerou "
                   "+22,8% A/A. Fluxo de caixa operacional livre subiu 54% A/A.",
        "pontos_fracos": "Lucro líquido cresceu muito menos que a receita/EBITDA (apenas "
                   "+1,3%) por causa de uma carga tributária 75% maior (menor dedução de "
                   "Juros sobre Capital Próprio). Receita pré-paga caiu 6,5% A/A, com "
                   "perda líquida de 355 mil linhas no trimestre. TIM foi a operadora que "
                   "mais perdeu participação de mercado em alguns estados nos últimos 12 "
                   "meses.",
        "expectativa": "XP mantém recomendação Neutra, achando que o valuation já "
                   "reflete boa parte da melhora operacional recente. Pressão competitiva "
                   "e agenda de convergência (fixo+móvel) devem exigir alocação de "
                   "capital mais complexa nos próximos trimestres.",
    },
    "KLBN4": {
        "trimestre": "1T26", "data": "06/05/2026",
        "numeros": "Prejuízo líquido de R$497mi, revertendo lucro de R$446mi no 1T25. "
                   "Receita líquida R$4,9bi (+2% A/A). EBITDA ajustado R$1,67-1,7bi (-9 a "
                   "-10% A/A), margem caindo de 38% para 34%.",
        "pontos_fortes": "Volume total vendido cresceu 12% A/A (recorde), com celulose "
                   "+16%, papel +15%. Containerboard cresceu 31% A/A em volume, puxado "
                   "por exportação. Dívida bruta caiu R$3,9bi no trimestre (resgate "
                   "antecipado de green bonds e amortizações).",
        "pontos_fracos": "Prejuízo veio principalmente de um resultado financeiro muito "
                   "negativo (-R$570mi, vs -R$158mi no 1T25), por despesas ligadas à "
                   "liquidação de swap no pagamento antecipado de dívida — efeito "
                   "praticamente contábil, não operacional. Real mais valorizado (-10% "
                   "A/A) pressionou receitas de exportação. Alavancagem em 3,1x dívida "
                   "líquida/EBITDA, ainda elevada.",
        "expectativa": "JPMorgan rebaixou a recomendação para neutra em abril/2026, "
                   "citando preços fracos da celulose de fibra curta (preço-alvo R$22). "
                   "Analistas avaliam o resultado operacional como 'em linha', e "
                   "reconhecem que o prejuízo contábil (efeitos financeiros pontuais) não "
                   "deve se repetir necessariamente.",
    },
    "CYRE3": {
        "trimestre": "1T26", "data": "14/05/2026",
        "numeros": "Lucro líquido R$297mi (-9% A/A, -56% T/T). Receita líquida R$2,02bi "
                   "(+4% A/A). Margem bruta 32,9% (+0,4 p.p. A/A).",
        "pontos_fortes": "Geração de caixa positiva de R$134mi no trimestre (revertendo "
                   "queima de caixa do trimestre anterior). Lucro bruto a apropriar de "
                   "R$4,2bi (+22% A/A). Equivalência patrimonial de participações em "
                   "outras incorporadoras (Cury, Plano&Plano, Lavvi) contribuiu R$128mi "
                   "(+14% A/A).",
        "pontos_fracos": "Lançamentos desaceleraram fortemente: VGV de R$1,7bi no "
                   "trimestre, queda de 48% A/A e 47% T/T. Despesas comerciais/"
                   "administrativas cresceram como % da receita (20,3%, +3,5 p.p. A/A). "
                   "Vendas ex-permuta praticamente estáveis (+2% A/A).",
        "expectativa": "Santander via a Cyrela com resultados 'razoáveis' no trimestre. "
                   "A empresa está rotacionando parte da atividade para o segmento "
                   "econômico (MCMV) — 39% dos lançamentos do trimestre já são desse "
                   "segmento, vs 22% um ano antes.",
    },
    "DIRR3": {
        "trimestre": "1T26", "data": "11/05/2026",
        "numeros": "Lucro líquido R$213,2mi (+29,6% A/A); lucro operacional ajustado "
                   "R$200mi (+27% A/A). Receita líquida R$1,16-1,2bi (+30% A/A). Margem "
                   "bruta ajustada recorde de 42,9% (+1,3 p.p. A/A).",
        "pontos_fortes": "ROE de 38% (+9 p.p. A/A), um dos maiores do setor. VSO "
                   "(velocidade de vendas) de 24%, o maior nível já registrado para um "
                   "primeiro trimestre. Lançamentos de R$1bi em VGV (+12% A/A); vendas "
                   "líquidas de R$1,35-1,6bi (+19-23% A/A). Resultado financeiro passou "
                   "de negativo para positivo.",
        "pontos_fracos": "Distratos aumentaram, atribuído pela empresa ao fim de alguns "
                   "programas regionais de subsídio complementar ao MCMV. Dívida líquida "
                   "subiu 15% no trimestre, com alavancagem em 24% (vs 23% no 4T25). "
                   "Despesas administrativas e comerciais subiram 33% cada.",
        "expectativa": "Nord reforça recomendação de compra, citando múltiplo de apenas "
                   "9x lucros e dividend yield de 16,9% nos últimos 12 meses. Direcional "
                   "segue como uma das principais beneficiárias do MCMV, com receita a "
                   "apropriar de R$3,8bi (+34% A/A) garantindo visibilidade futura.",
    },
    "MDNE3": {
        "trimestre": "1T26", "data": "07/05/2026",
        "numeros": "Lucro líquido recorde R$155,5-156mi (+121-122% A/A), o maior da "
                   "história da empresa. Receita líquida R$628mi (+43% A/A). ROE de ~33%.",
        "pontos_fortes": "Vendas e adesões líquidas de R$1,02bi (+85,7% A/A). "
                   "Lançamentos saltaram 218-255% A/A em VGV. Margem bruta ajustada de "
                   "~42%. LPA de R$1,66 (+99% A/A). Consolidou 100% da marca Ún1ca "
                   "(joint venture com a Direcional no segmento econômico).",
        "pontos_fracos": "Empresa consumiu caixa por causa de aquisições de terrenos e "
                   "novos lançamentos — precisou de um follow-on de R$483mi para manter "
                   "a dívida líquida em níveis baixos. Ação caiu forte (-7,29%) no dia da "
                   "divulgação, mesmo com resultado recorde.",
        "expectativa": "BTG destaca a Moura Dubeux como combinando o que se espera de "
                   "uma boa construtora: estrutura de capital enxuta, ROE forte e baixa "
                   "alavancagem, mesmo crescendo rápido. Expansão da joint venture Ún1ca "
                   "amplia a presença no segmento econômico.",
    },
    "CURY3": {
        "trimestre": "1T26", "data": "12/05/2026",
        "numeros": "Lucro líquido recorde R$302,9mi (+41,9% A/A). Receita líquida "
                   "R$1,613bi (+32,6% A/A), recorde. EBITDA R$411,4mi (+42,9% A/A), "
                   "margem 25,5% (+1,8 p.p. A/A).",
        "pontos_fortes": "Preço médio dos apartamentos vendidos subiu 5% A/A "
                   "(R$325,4mil), mostrando poder de repasse de preço. Custos mantidos "
                   "sob controle mesmo com inflação setorial. Segundo trimestre já "
                   "começou forte em vendas, segundo a própria empresa, beneficiado "
                   "pelos ajustes recentes no MCMV.",
        "pontos_fracos": "Santander projetava compressão de margem na comparação "
                   "trimestral para a Cury, por descontos em vendas e revisões de "
                   "orçamento — o resultado forte do 1T26 contraria parcialmente essa "
                   "expectativa, mas o setor segue monitorando o impacto da alta do "
                   "petróleo nos custos de construção.",
        "expectativa": "Resultado reforça a Cury como uma das incorporadoras mais "
                   "eficientes do segmento MCMV/econômico, com forte geração de caixa. "
                   "Mercado atento às mudanças recentes no MCMV (ampliação de faixas de "
                   "renda elegíveis), que devem ampliar o público endereçável.",
    },
    "ABCB4": {
        "trimestre": "1T26", "data": "07/05/2026",
        "numeros": "Lucro líquido recorrente R$230,2mi (+2,1% A/A). Margem financeira "
                   "R$647,8mi (+14,3% A/A).",
        "pontos_fortes": "Margem financeira em forte expansão, mostrando capacidade de "
                   "ampliar ganhos com crédito e tesouraria mesmo num ambiente "
                   "competitivo. Banco de nicho corporativo, menos exposto a varejo e "
                   "agro do que os grandes bancos.",
        "pontos_fracos": "Crescimento de lucro bem mais lento que a margem financeira "
                   "(+2,1% vs +14,3%), sugerindo pressão de custos/provisões absorvendo "
                   "parte do ganho de receita. Seletividade no crédito corporativo limita "
                   "o ritmo de expansão da carteira.",
        "expectativa": "Resultado reforça a resiliência operacional do banco em ambiente "
                   "de juros elevados, mas sem grande surpresa positiva ou negativa — "
                   "trimestre dentro do esperado para um banco de nicho corporativo.",
    },
    "BRSR6": {
        "trimestre": "1T26", "data": "14/05/2026",
        "numeros": "Lucro líquido R$221,6mi (-8,2% A/A, -66% T/T). ROE de 7,9%.",
        "pontos_fortes": "Resultado ficou 5% acima das estimativas mais recentes do "
                   "BTG, com provisões cíveis/trabalhistas/tributárias abaixo da média e "
                   "receitas operacionais diversas maiores que o esperado.",
        "pontos_fracos": "Queda forte T/T (-66%) reflete desaceleração da carteira de "
                   "crédito combinada com deterioração de qualidade de ativos, em "
                   "intensidade maior que o projetado pelo mercado. Provisões cobriram "
                   "quase 95% da formação de inadimplência. ROE de 7,9% é baixo mesmo "
                   "pra um banco regional.",
        "expectativa": "BTG segue cauteloso mesmo após a ação já ter caído 23% desde a "
                   "recomendação de venda — vê fraca capacidade de geração de resultados "
                   "do banco persistindo.",
    },
    "SANB3": {
        "trimestre": "1T26", "data": "29/04/2026",
        "numeros": "Lucro líquido recorrente R$3,78bi (-1,9% A/A, -7,3% T/T) — abaixo "
                   "do consenso (R$4,066bi). Margem financeira R$15,8bi (+3,1% T/T).",
        "pontos_fortes": "Índice de eficiência em 37,7% (melhora de 1,1 p.p. T/T). "
                   "Margem financeira com o mercado (tesouraria) melhorou 48,1% T/T, "
                   "mesmo ainda negativa. Custo de crédito estável em 3,73%.",
        "pontos_fracos": "Normalização da carga tributária (alíquota efetiva subiu pra "
                   "15-17%, depois de trimestres com alíquota atipicamente baixa) "
                   "pressionou o lucro. Banco manteve postura conservadora na concessão "
                   "de crédito, limitando crescimento da carteira no curto prazo.",
        "expectativa": "CEO defende que 'pagar mais imposto é bom sinal' (reflete maior "
                   "lucro antes de impostos) e mantém meta de ROE de 20%. UBS BB segue "
                   "vendo motivos para investir na história, mesmo com mercado menos "
                   "otimista após o trimestre.",
    },
    "BMGB4": {
        "trimestre": "1T26", "data": "maio/2026",
        "numeros": "Lucro líquido R$147mi (+27,8% A/A, -14,5% T/T).",
        "pontos_fortes": "Crescimento sólido na comparação anual, com mix de produtos "
                   "sustentando margem.",
        "pontos_fracos": "PDD (provisão para devedores duvidosos) limitou o lucro no "
                   "trimestre, segundo a Genial — sinal de atenção em qualidade de "
                   "crédito, mesmo com crescimento anual positivo.",
        "expectativa": "Genial nota que o mix de produtos sustenta a margem, mas o "
                   "crescimento das provisões é o ponto a monitorar nos próximos "
                   "trimestres.",
    },
    "IRBR3": {
        "trimestre": "1T26", "data": "04/05/2026",
        "numeros": "Lucro líquido recorrente R$101,6mi (-14,3 a -14,8% A/A, -29,1% T/T) "
                   "— abaixo do esperado pelo mercado. ROE de 8,2%. Prêmios emitidos "
                   "R$1,28-1,29bi (+3,2% A/A).",
        "pontos_fortes": "Resultado operacional (subscrição) positivo em R$7mi, "
                   "revertendo prejuízo operacional de R$31mi no 1T25. Índice combinado "
                   "melhorou de 102% para 98%. Sinistralidade caiu 8,5 p.p. A/A. Ações "
                   "chegaram a subir mais de 3% mesmo com queda no lucro.",
        "pontos_fracos": "Retração de prêmios é estratégia deliberada (a empresa prefere "
                   "fechar menos negócios a preços ruins, num momento de 'soft market' "
                   "global no resseguro), mas isso reduz volume e lucro no curto prazo. "
                   "Despesas com retrocessão subiram 42,9% A/A.",
        "expectativa": "Genial vê a retração de prêmios como intencional, alinhada à "
                   "estratégia de cautela, sustentando melhora estrutural do resultado "
                   "técnico nos próximos ciclos. Início de pagamento de JCP deve trazer "
                   "benefícios fiscais a partir do 2T26.",
    },
    "ITSA4": {
        "trimestre": "1T26", "data": "11/05/2026",
        "numeros": "Lucro líquido R$4,4bi (lucro recorrente das investidas R$4,794bi, "
                   "+15,8% A/A). Setor financeiro (Itaú) contribuiu R$4,383bi (+10,9%), "
                   "setor não-financeiro R$454mi (+75,6%).",
        "pontos_fortes": "Crescimento forte do setor não-financeiro (+75,6%), puxado por "
                   "Alpargatas, Copa Energia, Motiva e Aegea, além de variação positiva "
                   "no valor justo da NTS. Aumento de participação na Aegea (saneamento) "
                   "para 13,27%.",
        "pontos_fracos": "Dívida líquida subiu de R$351mi (1T25) para R$1,010bi, "
                   "influenciada pela redução de caixa e pelo aporte na Aegea.",
        "expectativa": "Genial mantém tese de fechamento do desconto da Itaúsa frente à "
                   "soma das partes (desconto de holding de 19,4% no trimestre), vendo "
                   "ainda espaço para reprecificação.",
    },
    "BRAP4": {
        "trimestre": "1T26", "data": "14/05/2026",
        "numeros": "Lucro líquido R$553,5mi (+73,9% A/A). Receita operacional R$553mi "
                   "(vs R$314,7mi no 1T25).",
        "pontos_fortes": "Resultado quase 100% explicado pela forte contribuição da "
                   "Vale (principal investida), via equivalência patrimonial e JCP — "
                   "estrutura financeira sem endividamento.",
        "pontos_fracos": "Ação caiu no dia da divulgação mesmo com lucro forte, sinal de "
                   "realização de lucros — a Bradespar não tem operação própria "
                   "relevante, então seu resultado é 100% derivado do desempenho de "
                   "outra empresa.",
        "expectativa": "Resultado é, na prática, um espelho do resultado da Vale do "
                   "mesmo período — qualquer análise de BRAP4 precisa necessariamente "
                   "passar pela tese de VALE3.",
    },
    "CMIN3": {
        "trimestre": "1T26", "data": "13/05/2026",
        "numeros": "Lucro líquido R$222mi, revertendo prejuízo de R$357mi no 1T25. "
                   "EBITDA ajustado R$1,42bi (-0,5% A/A). Receita líquida R$3,165bi "
                   "(-7,2% A/A).",
        "pontos_fortes": "Produção própria cresceu 6,7% A/A, sustentando volume de "
                   "vendas estável (9,6 milhões de toneladas) mesmo com chuvas acima da "
                   "média. Alavancagem extremamente baixa (0,11x dívida líquida/EBITDA). "
                   "Caixa de R$8,8bi.",
        "pontos_fracos": "Receita unitária por tonelada caiu (US$62,60, -1,1% T/T), "
                   "pressionada pela alta nos preços de frete marítimo (US$24,83/t, "
                   "+27,5% A/A) — exposição ao mercado spot de frete aumenta a "
                   "volatilidade do resultado. Custo caixa C1 subiu 10% A/A.",
        "expectativa": "BB-BI mantém recomendação de Venda (preço-alvo R$5,40), "
                   "destacando resultado operacional 'neutro' e a elevada exposição da "
                   "companhia à volatilidade dos fretes marítimos como risco específico.",
    },
    "GGBR3": {
        "trimestre": "1T26", "data": "27-28/04/2026",
        "numeros": "Lucro líquido ajustado R$1bi (+33,6% A/A, +51,2% T/T). Receita "
                   "líquida R$16,7bi (-3,8% A/A). EBITDA ajustado R$3bi (+23,2% A/A), "
                   "margem 17,7% (+3,7 p.p.).",
        "pontos_fortes": "América do Norte respondeu por ~75% do EBITDA ajustado "
                   "consolidado (+88,1% em 12 meses) — motor quase exclusivo do "
                   "resultado. Programa de recompra já 21% executado (R$210,7mi). "
                   "Dividendos de R$354,1mi aprovados.",
        "pontos_fracos": "Operação Brasil 'derreteu quase pela metade': receita -12,7% "
                   "T/T, EBITDA -47%, margem caindo 5,4 p.p. — pressionada pela elevada "
                   "penetração de aço importado (28,5% em aços planos). Guerra no "
                   "Oriente Médio já começa a pesar nas projeções de custo.",
        "expectativa": "Mercado trata a Gerdau cada vez mais como 'uma história de aço "
                   "americano', com o Brasil funcionando como motor secundário. Pergunta "
                   "chave: até quando os EUA seguram o resultado enquanto o Brasil tenta "
                   "se recuperar.",
    },
    "UNIP6": {
        "trimestre": "1T26", "data": "24/04/2026",
        "numeros": "Lucro líquido R$37mi (-75% A/A, revertendo prejuízo de R$7mi no "
                   "4T25). Receita líquida R$1,2bi (-10% A/A). EBITDA ajustado R$145-174mi "
                   "(-59% A/A).",
        "pontos_fortes": "Geração de caixa sustentada por entrada de capital de giro "
                   "(~R$110mi) e capex menor. Preços internacionais e spreads já "
                   "mostraram recuperação em março/abril, após o início do conflito "
                   "entre EUA e Irã.",
        "pontos_fracos": "Queda de preços internacionais da soda cáustica (-11% A/A) e "
                   "do PVC (-13% A/A), com real desvalorizado adicionando pressão. "
                   "Alavancagem subiu de 2,2x para 2,6x dívida líquida/EBITDA. Taxa de "
                   "utilização das plantas caiu para 73%.",
        "expectativa": "XP espera melhora no 2T26 com a recuperação de preços/spreads "
                   "internacionais já em curso. Nord mantém recomendação neutra, citando "
                   "baixa visibilidade sobre o ciclo das commodities petroquímicas.",
    },
    "LEVE3": {
        "trimestre": "1T26", "data": "06-07/05/2026",
        "numeros": "Lucro líquido R$214,2mi (+34,9% A/A). Receita líquida R$1,3bi. "
                   "EBITDA +5,2% A/A.",
        "pontos_fortes": "Crescimento robusto de lucro acima do crescimento de receita, "
                   "indicando ganho de margem. Empresa expandindo pra novas frentes "
                   "(solução de carregamento de veículos elétricos no Brasil).",
        "pontos_fracos": "Crescimento de EBITDA (+5,2%) bem mais modesto que o de lucro "
                   "(+34,9%) — parte da melhora pode vir de itens abaixo da linha "
                   "operacional (financeiro, tributário), não só de operação.",
        "expectativa": "Empresa amplia portfólio para alémde autopeças tradicionais, "
                   "buscando capturar a transição para veículos elétricos sem abandonar "
                   "o negócio principal (peças pra motores a combustão).",
    },
    "SHUL4": {
        "trimestre": "1T26", "data": "21/05/2026",
        "numeros": "Lucro líquido R$56mi (-22% A/A). Receita líquida R$448mi (-9% A/A). "
                   "EBITDA R$63mi (-26% A/A). ROE de 18,2%.",
        "pontos_fortes": "Caixa líquido (mais caixa que dívida) de R$135mi — estrutura "
                   "de capital muito confortável, que permite atravessar ciclos "
                   "desfavoráveis sem aperto financeiro. Fluxo de caixa livre positivo "
                   "(R$7,5mi), revertendo queima de caixa do ano anterior.",
        "pontos_fracos": "Divisão Automotiva (compressores) e máquinas agrícolas/"
                   "construção seguem pressionadas: vendas nos EUA -7% A/A (em dólar), "
                   "vendas pra máquinas agrícolas -14% A/A, refletindo juros altos, "
                   "estoques elevados e câmbio desfavorável.",
        "expectativa": "Nord mantém posição na empresa via série de valor, citando "
                   "múltiplo de apenas 6,5x lucros e valor de mercado de R$1,8bi — vendo "
                   "a empresa bem posicionada para uma eventual virada de ciclo do "
                   "mercado automotivo no longo prazo.",
    },
    "VULC3": {
        "trimestre": "1T26", "data": "05/05/2026",
        "numeros": "Lucro líquido R$80,1mi (-24,5% A/A) ou R$86,1mi recorrente (-18,9% "
                   "A/A). Receita líquida recorde R$776,4mi (+10,7% A/A) — 23º trimestre "
                   "consecutivo de crescimento.",
        "pontos_fortes": "23 trimestres seguidos de crescimento de receita — uma das "
                   "sequências mais consistentes do varejo de calçados. Volume bruto "
                   "+6,8% A/A. Boa aceitação das marcas (Olympikus, Mizuno, Under "
                   "Armour no Brasil).",
        "pontos_fracos": "Lucro caiu mesmo com receita recorde — alta volatilidade "
                   "geopolítica e pressões fiscais no trimestre pressionaram a última "
                   "linha. Volume sequencial (T/T) caiu (7,6 milhões de pares vs 9,2 "
                   "milhões no 4T25, efeito sazonal esperado).",
        "expectativa": "Administração reforça resiliência do modelo de negócio mesmo em "
                   "ambiente desafiador de consumo, mas o descolamento entre receita "
                   "recorde e lucro menor é o ponto que o mercado deve monitorar nos "
                   "próximos trimestres.",
    },
    "KEPL3": {
        "trimestre": "1T26", "data": "08/05/2026",
        "numeros": "Lucro líquido R$17,1mi. Receita R$318,1mi. Margem EBITDA de 10,6%.",
        "pontos_fortes": "Resultado positivo mesmo em cenário mais seletivo no "
                   "agronegócio (cliente final da Kepler Weber), mostrando alguma "
                   "resiliência da demanda por armazenagem de grãos.",
        "pontos_fracos": "Margem EBITDA de 10,6% é relativamente baixa para o setor, "
                   "refletindo o ambiente mais seletivo e cauteloso entre os produtores "
                   "rurais (clientes da empresa) em meio a um agro mais fraco.",
        "expectativa": "Resultado reflete diretamente o humor do produtor rural — em "
                   "anos de agro mais fraco (como 2026), a Kepler Weber sente o impacto "
                   "indireto via menor investimento em armazenagem.",
    },
    "SLCE3": {
        "trimestre": "1T26", "data": "13/05/2026",
        "numeros": "Lucro líquido R$236,1mi (-53,8% A/A). Receita líquida R$2,27bi "
                   "(-2,7% A/A). EBITDA ajustado R$695mi (-26,3% A/A), margem 30,7% "
                   "(-9,8 p.p.).",
        "pontos_fortes": "Produtividade da soja 4,7% acima da última safra, com seis "
                   "fazendas acima de 4.800 kg/ha. Geração de caixa teve leve melhora "
                   "anual (+4,6%), mesmo ainda negativa. Empresa atribui a queda de "
                   "faturamento da soja a um evento pontual de mix de fazendas, não a "
                   "uma deterioração estrutural.",
        "pontos_fracos": "Queda de volume em quase todos os produtos (algodão em pluma "
                   "-5%, soja -3%, caroço de algodão -35%). Resultado financeiro "
                   "negativo cresceu 124% por maior endividamento. Dívida líquida subiu "
                   "para R$5,2-6,6bi, alavancagem em 2,7x dívida líquida/EBITDA (vs 2x "
                   "no 4T25). Fluxo de caixa livre negativo em R$1,3-1,35bi.",
        "expectativa": "A própria administração espera normalização ao longo dos "
                   "próximos trimestres, à medida que a melhor produtividade das "
                   "demais regiões (além das fazendas com mix mais fraco neste "
                   "trimestre) seja incorporada aos resultados.",
    },
    "CMIG4": {
        "trimestre": "1T26", "data": "07/05/2026",
        "numeros": "Resultado pressionado pelo maior programa de investimentos da "
                   "história da companhia, refletindo em maior alavancagem.",
        "pontos_fortes": "Diversificação de receita entre distribuição (~46% do "
                   "EBITDA), geração (~27%), gás natural (~12%), transmissão (~8%) e "
                   "comercialização (~7%) — poucas utilities têm portfólio tão "
                   "diversificado.",
        "pontos_fracos": "Alta alavancagem, fruto do maior programa de investimentos da "
                   "história da empresa, pesa sobre a lucratividade no curto prazo.",
        "expectativa": "Nord mantém preferência por outras companhias do setor (como a "
                   "CPFL) frente à Cemig, citando a pressão de alavancagem como fator "
                   "que limita a atratividade no momento.",
    },
    "ISAE4": {
        "trimestre": "1T26", "data": "04/05/2026",
        "numeros": "Lucro líquido R$357,7mi. ROE de 19,1%.",
        "pontos_fortes": "Melhores indicadores de endividamento entre os pares "
                   "(Taesa, Alupar) do setor de transmissão, com o vencimento médio de "
                   "contratos mais longo do setor e múltiplos mais baixos. ROE de "
                   "19,1% é elevado para uma transmissora pura.",
        "pontos_fracos": "Negócio de transmissão pura tem crescimento mais limitado que "
                   "geração/distribuição — depende de novos leilões para expandir a "
                   "base de ativos.",
        "expectativa": "Nord recomenda compra, citando múltiplo de 7x lucros e dividend "
                   "yield de ~10% — vista como a transmissora com melhor relação "
                   "risco-retorno do setor elétrico.",
    },
    "TAEE11": {
        "trimestre": "1T26", "data": "06/05/2026",
        "numeros": "Lucro líquido regulatório R$192,6mi.",
        "pontos_fortes": "Negócio de transmissão pura, com receita contratada e "
                   "previsível via reajustes anuais (IPCA/IGPM), pouco sensível a "
                   "ciclos econômicos de curto prazo.",
        "pontos_fracos": "Crescimento limitado sem novos leilões de transmissão — "
                   "modelo de negócio maduro, com poucas avenidas de expansão orgânica.",
        "expectativa": "Política robusta de distribuição de dividendos mantida, com "
                   "JCP anunciado no mesmo período — tese de renda permanece o principal "
                   "atrativo da ação.",
    },
    "SBSP3": {
        "trimestre": "1T26", "data": "07-08/05/2026",
        "numeros": "Lucro líquido R$1,55bi (+32% A/A).",
        "pontos_fortes": "Crescimento robusto de lucro, sustentado por disciplina de "
                   "custos e despesas, segundo a Nord. Caixa disponível de R$19,2bi "
                   "frente a dívida líquida de R$32,5bi.",
        "pontos_fracos": "Dívida líquida elevada (R$32,5bi) é estrutural ao negócio de "
                   "saneamento, que exige investimento constante em infraestrutura.",
        "expectativa": "Privatizada em 2024, a Sabesp segue em processo de "
                   "reestruturação e ganho de eficiência, com o mercado acompanhando de "
                   "perto se o ritmo de melhora operacional se sustenta nos próximos "
                   "trimestres.",
    },
    "CSMG3": {
        "trimestre": "1T26", "data": "08/05/2026",
        "numeros": "Lucro líquido R$368,1mi (-14,1% A/A). Receita líquida R$1,91bi "
                   "(+2,5% A/A). EBITDA R$787,4mi.",
        "pontos_fortes": "Receita em crescimento, com a companhia mantendo presença "
                   "relevante no saneamento de Minas Gerais (estado ainda detém 50,3% "
                   "das ações).",
        "pontos_fracos": "Lucro caiu mesmo com receita maior, por margens menores e "
                   "endividamento maior. Atraso no cronograma do processo de "
                   "privatização aumentou a incerteza sobre parte relevante da tese de "
                   "investimento (a expectativa de venda do controle estatal).",
        "expectativa": "Tese de privatização (gatilho de re-rating, como aconteceu com "
                   "a Sabesp) segue sendo o principal catalisador de longo prazo, mas o "
                   "atraso no cronograma reduz a visibilidade no curto prazo.",
    },
    "BRBI11": {
        "trimestre": "1T26", "data": "07-08/05/2026",
        "numeros": "Lucro líquido R$37,7-38mi (-12,5 a -13% A/A, -15,3% T/T) — abaixo do "
                   "consenso. Receita total R$134,8-135mi (+5,7-6% A/A). ROE de 19,1%.",
        "pontos_fortes": "Receita com clientes cresceu 7,7-8% A/A. Wealth Management "
                   "(gestão de fortunas) atingiu R$6,1bi sob assessoria (+10% A/A), "
                   "ampliando a base de receita recorrente. Treasury Sales & "
                   "Structuring cresceu 7,9-10,4%.",
        "pontos_fracos": "Despesas com pessoal subiram fortemente (+30,3% vs estimado), "
                   "fruto de uma decisão estratégica de reforçar o time, não de piora de "
                   "disciplina — mas pressionou o lucro no trimestre. M&A demorou mais "
                   "que o esperado para fechar negócios, mesmo com pipeline acelerando.",
        "expectativa": "O próprio DRI da empresa reconhece que 'o trimestre foi "
                   "positivo, mas poderia ter sido melhor'. Negociando a múltiplos bem "
                   "inferiores aos pares (BTG no Brasil), Nord recomenda compra, citando "
                   "ROE histórico acima de 20% desde o IPO.",
    },
    "LREN3": {
        "trimestre": "1T26", "data": "07/05/2026",
        "numeros": "Lucro líquido R$257,3mi (+16,4% A/A). Receita de varejo R$2,9bi. "
                   "EBITDA de varejo R$487,5mi. ROIC (12 meses) de 15,2% (+1,9 p.p. "
                   "A/A).",
        "pontos_fortes": "Fluxo de caixa livre de R$258mi (vs R$70,9mi no 1T25) — mais "
                   "que triplicou. Caixa líquido de R$1,5bi. Recompra de ações (R$100mi) "
                   "e distribuição de R$217,4mi em JCP no trimestre.",
        "pontos_fracos": "Setor de varejo de moda segue pressionado pela alta "
                   "alavancagem das famílias e concorrência de plataformas cross-border "
                   "(Shein, AliExpress) — risco estrutural de médio prazo que não "
                   "aparece diretamente no resultado do trimestre.",
        "expectativa": "Empresa mantém meta de crescimento de receita entre 9-13% ao "
                   "ano até 2030, com margem EBITDA de varejo (ex-IFRS 16) entre 18-20% "
                   "— plano de expansão de longo prazo segue intacto.",
    },
    "GRND3": {
        "trimestre": "1T26", "data": "07/05/2026",
        "numeros": "Lucro líquido R$102,1mi (-9,9% A/A).",
        "pontos_fortes": "Queda de lucro moderada (-9,9%) considerando que o ano "
                   "anterior teve dividendo extraordinário não recorrente que elevou a "
                   "base de comparação em outras métricas.",
        "pontos_fracos": "Continuidade da normalização de resultados após o pico de "
                   "2025 (puxado por dividendo extraordinário não recorrente) — "
                   "crescimento operacional segue fraco.",
        "expectativa": "Caixa líquido robusto e baixa alavancagem sustentam a tese de "
                   "renda (dividendos), mas o crescimento operacional fraco deve manter "
                   "o foco do mercado na normalização dos proventos em 2026.",
    },
    "EGIE3": {
        "trimestre": "1T26", "data": "07-08/05/2026",
        "numeros": "Lucro líquido ajustado R$789-792mi (-4,1% A/A). Receita líquida "
                   "R$3,4bi (+13,1% A/A). EBITDA ajustado R$2,2-2,25bi (+10% A/A), "
                   "acima do esperado pelo mercado (consenso R$1,8bi).",
        "pontos_fortes": "EBITDA veio bem acima do consenso, puxado por +8% na geração "
                   "hidrelétrica e +7% nas complementares. Vendeu 195,78 MW da usina "
                   "Jaguara em contrato de 15 anos com receita fixa anual de R$270mi+ a "
                   "partir de 2030 — trava receita futura. Participação na TAG "
                   "(gasoduto) contribuiu R$133mi via equivalência patrimonial.",
        "pontos_fracos": "Lucro caiu mesmo com EBITDA forte, pressionado por maior "
                   "despesa financeira (+33%, mais juros de dívida) e maior "
                   "depreciação. Dívida líquida saltou 20,9% A/A (R$25bi), elevando "
                   "alavancagem para 3,2x (de 2,7x). Investimentos caíram 80% no "
                   "trimestre, após ciclo pesado anterior.",
        "expectativa": "Nord encerrou posição na empresa, vendo melhor assimetria de "
                   "risco/retorno em outros nomes do setor — sem recomendação de "
                   "compra no momento. Para 2026, expectativa é de redução do nível de "
                   "investimento e maior foco em geração de caixa para preservar "
                   "capacidade de pagamento da dívida.",
    },
    "CPFE3": {
        "trimestre": "1T26", "data": "14/05/2026",
        "numeros": "Lucro líquido R$1,9bi (+18,2% A/A). Receita operacional líquida "
                   "R$10,1-11,3bi (+6,4-7% A/A). EBITDA R$3,86-3,9bi (~estável, +0,2% "
                   "A/A).",
        "pontos_fortes": "Conclusão histórica da renovação das concessões das "
                   "distribuidoras CPFL Paulista, CPFL Piratininga e RGE por mais 30 "
                   "anos (em 08/05/2026) — remove um risco de longo prazo que pesava "
                   "sobre a tese. Lucro cresceu bem mais que o EBITDA, puxado por "
                   "melhora no resultado financeiro líquido e efeitos tributários "
                   "favoráveis. Demanda de data centers cresceu 24% nas regiões onde a "
                   "empresa atua.",
        "pontos_fracos": "Energia faturada para consumidores cativos caiu 7,8% A/A — "
                   "sinal de desaceleração de consumo/maior migração para o mercado "
                   "livre. Custos com energia elétrica subiram 13% (leilões, contratos "
                   "bilaterais e curto prazo mais caros). Dívida líquida subiu 15% A/A "
                   "(R$30,6bi), alavancagem em 2,3x (de 2x).",
        "expectativa": "Nord recomenda compra, citando múltiplo baixo (9x lucros, 6x "
                   "EBITDA) e novo plano de investimentos 2026-2030 de R$31bi (R$25bi "
                   "em distribuição), buscando maior solidez e previsibilidade nos "
                   "próximos anos.",
    },
    "SAPR4": {
        "trimestre": "1T26", "data": "14/05/2026",
        "numeros": "Lucro líquido R$352,7mi (-70,8% A/A). Receita líquida "
                   "R$1,946-1,95bi (+7,8% A/A). EBITDA R$843-843,5mi (-24,4% A/A), "
                   "margem caindo de 61,8% para 43,3%.",
        "pontos_fortes": "Receita em crescimento real (volume de água +1,2%, esgoto "
                   "+2,4%, novas ligações). Dívida líquida caiu 59,6% A/A (para "
                   "R$1,921bi), com alavancagem de apenas 0,7x dívida líquida/EBITDA "
                   "(de 1,5x) — balanço muito mais saudável. Inadimplência caiu de "
                   "2,8% para 2,5%.",
        "pontos_fracos": "A queda de 70,8% no lucro é enganosa se olhada sem contexto: "
                   "o 1T25 teve um efeito contábil extraordinário (reconhecimento de "
                   "um ganho de ação judicial de IRPJ), que infla artificialmente a "
                   "base de comparação. Sem esse efeito pontual do ano passado, a "
                   "queda real do negócio operacional é bem menor. Despesas de pessoal "
                   "e custos subiram 60% A/A.",
        "expectativa": "A própria empresa atribui a queda 'basicamente' ao efeito de "
                   "comparação contra a base extraordinária do 1T25 — investidores "
                   "precisam normalizar essa comparação pra entender a real trajetória "
                   "operacional da empresa, que segue de crescimento de receita e "
                   "desalavancagem.",
    },
    "CGRA4": {
        "trimestre": "1T26", "data": "15-16/05/2026",
        "numeros": "Lucro líquido R$5,2mi (+18% A/A). EBITDA R$10,8mi (+58,2% A/A).",
        "pontos_fortes": "Crescimento expressivo de EBITDA (+58,2%), bem acima do "
                   "crescimento do lucro — sinal de melhora operacional real no "
                   "trimestre. Margem EBITDA de 12,71% nos últimos 12 meses.",
        "pontos_fracos": "Empresa pequena e pouco coberta por analistas — poucas casas "
                   "de research acompanham CGRA4 de perto, o que significa menos "
                   "'segunda opinião' disponível pra validar o resultado. Aumento de "
                   "capital recente (por subscrição privada, anunciado em abr-mai/2026) "
                   "dilui a base acionária existente.",
        "expectativa": "Resultado positivo, mas a empresa segue sendo uma small cap de "
                   "baixa liquidez e cobertura — qualquer análise mais profunda depende "
                   "mais dos números trimestrais brutos do que de relatórios de "
                   "bancos/casas de research, que praticamente não cobrem o papel.",
    },
    "BBDC3": {
        "trimestre": "1T26", "data": "06/05/2026",
        "numeros": "Lucro líquido recorrente R$6,8bi (+16,1% A/A, +4,5% T/T) — nono "
                   "trimestre consecutivo de melhora. ROE de 15,4-15,8%. Receitas "
                   "totais R$36,9bi (+14% A/A).",
        "pontos_fortes": "Margem financeira com clientes cresceu 16,3% A/A (R$19,49bi). "
                   "Unidade de Seguros entregou R$2,8bi de lucro (+13% A/A), "
                   "representando ~41% do lucro total do grupo. Índice de eficiência "
                   "caiu para 49,2% (melhora de 2,6 p.p.). O evento mais importante do "
                   "trimestre não está nem no resultado: a cisão da BradSaúde (SAUD3) "
                   "foi concluída em maio/2026, com o ativo saindo do balanço do banco "
                   "a R$14bi para ser avaliado em R$49bi — um ganho de capital "
                   "potencial de R$35bi.",
        "pontos_fracos": "Provisões para devedores duvidosos aumentaram, com custo de "
                   "risco subindo para 3,5%, puxado por um caso específico no Atacado "
                   "(grandes empresas) e normalização gradual da inadimplência. "
                   "Deterioração pontual em carteiras mais antigas de crédito rural. "
                   "Ação caiu quase 4% no dia da divulgação, mesmo com lucro acima do "
                   "esperado — mercado reagiu à qualidade de crédito, não ao resultado "
                   "em si.",
        "expectativa": "Genial mantém compra (preço-alvo R$25), citando a reorganização "
                   "da BradSaúde como destravamento de capital relevante — o banco "
                   "ainda detém 91,35% da nova empresa, e uma eventual venda parcial "
                   "futura (o free float de 8,65% está abaixo do mínimo de 20% do Novo "
                   "Mercado) pode liberar ainda mais capital. BTG classificou o "
                   "trimestre como 'forte', destacando ser o único entre os grandes "
                   "bancos com crescimento sequencial de lucro.",
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
            ("Equipamentos Eletroeletrônicos Industriais (EEI)", "~52% da receita — "
             "motores de baixa/alta tensão, redutores, automação, vendidos pra "
             "praticamente todo tipo de indústria; crescimento recente puxado também "
             "por aquisições (Marathon, Cemp, Rotor, Volt Electric Motor)."),
            ("GTD — Geração, Transmissão e Distribuição", "~36% da receita — "
             "transformadores, geração solar/eólica/hidrelétrica/biomassa e, mais "
             "recentemente, sistemas de armazenamento de energia (BESS); maior motor "
             "de crescimento recente, mas também o mais cíclico."),
            ("Motores Comerciais e Appliance", "motores de menor porte pra uso "
             "comercial/residencial."),
            ("Tintas e Vernizes", "menor participação na receita total."),
        ],
        "insight_chave": "Receita externa já é maior que a doméstica (57% em 2024) — e "
                     "dentro do Brasil, a WEG vende motores pra praticamente todo setor "
                     "industrial (mineração, papel e celulose, óleo e gás, saneamento, "
                     "agro). Isso significa que a WEG não depende da saúde de um setor "
                     "específico — diferente de uma empresa de celulose ou mineração, que "
                     "sofre inteira quando o preço da commodity cai. Um ângulo recente "
                     "pouco notado: os geradores que a WEG vende nos EUA (via Marathon) "
                     "têm sido usados como energia de reserva para data centers — a "
                     "empresa está capturando parte do boom de infraestrutura de IA sem "
                     "depender diretamente de tecnologia digital. A fragilidade do 1T26 "
                     "não veio de um setor só: foi uma queda pontual em geração solar "
                     "doméstica somada ao câmbio mais valorizado.",
        "setor_dinamica": "Bens de capital industrial — o crescimento segue ciclos de "
                     "investimento industrial (motores/automação, mais estável) e ciclos "
                     "de energia renovável (GTD, mais volátil mês a mês). Verticalização "
                     "da produção (a empresa fabrica boa parte dos próprios componentes) "
                     "já se mostrou uma vantagem em crises de cadeia de suprimentos, "
                     "garantindo mais disponibilidade de produto que concorrentes "
                     "dependentes de terceiros.",
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
        "insight_chave": "Um dos maiores segredos de eficiência da PRIO é técnico, não "
                     "financeiro: ao invés de construir uma plataforma nova pra cada "
                     "campo novo, a empresa conecta a produção de campos vizinhos via "
                     "'tieback' (tubulação submarina) à infraestrutura que já existe — "
                     "foi assim que uniu Wahoo ao Frade (35 km de tieback) e o cluster "
                     "Polvo+Tubarão Martelo, economizando bilhões em capex que "
                     "concorrentes gastariam construindo plataformas do zero. Na "
                     "revitalização do Frade (2022-2023), a PRIO já aumentou a "
                     "produção em mais de 200% e reduziu as emissões de CO2 por barril "
                     "em 70% — uma combinação de eficiência econômica e ambiental que "
                     "poucas petroleiras conseguem entregar ao mesmo tempo. A receita "
                     "da PRIO é 100% ligada ao preço do petróleo Brent (cotado em "
                     "dólar) — por isso, mesmo operando perfeitamente, a ação pode "
                     "cair só porque o petróleo caiu por um motivo geopolítico que "
                     "nada tem a ver com a empresa, como aconteceu em mai/2026 com a "
                     "tensão no Oriente Médio.",
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
        "insight_chave": "Houve uma mudança estrutural silenciosa na Marcopolo: em "
                     "2025, os negócios internacionais (exportação + vendas das "
                     "fábricas no exterior) já representaram 45,4% da receita líquida "
                     "total — contra 36,3% em 2024. A empresa também passou a usar "
                     "'plataformas globais': o mesmo modelo de ônibus é produzido em "
                     "fábricas de países diferentes, dando flexibilidade pra exportar "
                     "do Brasil OU do México pra um mesmo mercado, dependendo de qual "
                     "rota é mais vantajosa no momento. Outro movimento recente: "
                     "parceria com a Volvo pra entrar no mercado europeu pela primeira "
                     "vez. Já dentro do Brasil, parte relevante do lucro trimestral "
                     "não vem da venda de ônibus em si — vem da equivalência "
                     "patrimonial da NFI (Canadá), que pode oscilar bastante por "
                     "efeitos contábeis não-recorrentes (como já aconteceu com a "
                     "reversão de uma provisão de recall de bateria).",
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
        "insight_chave": "Internamente, os executivos do Itaú falam em 'profit pool' — a "
                     "soma de todo o lucro que existe pra se ganhar no setor financeiro "
                     "brasileiro — e o banco captura mais de 20% desse total, sozinho. A "
                     "escala é difícil de replicar: cerca de 30% de toda a folha de "
                     "pagamento do Brasil passa por contas do Itaú, e o banco cobre o "
                     "'complexo imobiliário' inteiro — desde o crédito pra construtoras "
                     "até o financiamento do comprador final do imóvel. A própria gestão "
                     "reconhece que replicar UM produto ou segmento é possível, mas "
                     "replicar o ecossistema completo (varejo + atacado + seguros + "
                     "gestão de recursos, tudo conectado) é muito mais difícil — e isso "
                     "é o que sustenta o ROE consistentemente acima dos pares. O banco "
                     "também administra, gerencia e custodia cerca de R$4,1 trilhões em "
                     "recursos de terceiros, um negócio de taxa que cresce "
                     "independentemente do ciclo de crédito.",
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
                     "quando o agro aperta — como está acontecendo agora. Um detalhe "
                     "operacional pouco visto: o BB alcança áreas rurais sem agência "
                     "física através de 'carretas agro' (agências móveis que já "
                     "percorreram mais de 200 mil km pelo país) e de uma subsidiária, a "
                     "BBTS, que mantém uma rede de mais de 2.000 correspondentes "
                     "bancários em municípios desbancarizados — formas de estender o "
                     "alcance do banco no campo sem o custo de abrir uma agência "
                     "completa em cada cidade pequena.",
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
                     "resultado — aparece com defasagem, no trimestre seguinte. Outro "
                     "ponto pouco comentado: a própria Petrobras projeta seus "
                     "investimentos em cenários de Brent BEM mais baixo do que o preço "
                     "atual (média de US$25-28/barril no longo prazo) — ou seja, o "
                     "plano de US$109bi em investimentos até 2030 (62% no pré-sal) já "
                     "foi desenhado pra continuar viável mesmo se o petróleo despencar, "
                     "não depende de preços altos pra fazer sentido financeiramente.",
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
            ("Vale Base Metals — cobre e níquel", "a divisão que mais cresce em "
             "importância — EBITDA do segmento cresceu 116% A/A no 1T26. O custo "
             "all-in do níquel caiu 48% A/A, e o do cobre já é NEGATIVO (a receita de "
             "subprodutos como ouro e prata cobre todo o custo de produção)."),
        ],
        "insight_chave": "A Vale está investindo R$70bi no programa 'Novo Carajás', que "
                     "pretende elevar a capacidade de minério de ferro pra 200 milhões "
                     "de toneladas/ano até 2030 E expandir a produção de cobre em 32% "
                     "(via minas de Sossego, Salobo e Onça Puma, no mesmo complexo do "
                     "Pará) — ou seja, ferro e cobre crescem juntos, na mesma região, "
                     "compartilhando infraestrutura. Outro ponto que poucos sabem: o "
                     "S11D (maior mina da Vale) processa o minério A SECO, sem usar "
                     "água nem precisar de barragens de rejeito — uma escolha técnica "
                     "que reduz diretamente o tipo de risco que causou os desastres de "
                     "Brumadinho e Mariana. A conclusão do acordo de Mariana em 2025 "
                     "removeu, nas palavras do próprio CEO, um 'grande risco de cauda' "
                     "que pesava sobre a empresa há quase uma década.",
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
    "BPAC11": {
        "o_que_faz": "O BTG Pactual é o maior banco de investimento da América Latina, "
                     "com atuação diversificada em banco de investimento, gestão de "
                     "patrimônio (wealth management), crédito corporativo, trading, asset "
                     "management e, mais recentemente, varejo bancário (via aquisição do "
                     "Banco PAN).",
        "segmentos": [
            ("Corporate Lending & Business Banking", "crédito para grandes empresas — "
             "maior carteira do banco, R$281bi, crescendo 22% ao ano, mais que o dobro "
             "do mercado."),
            ("Wealth Management & Personal Banking", "gestão de patrimônio para clientes "
             "de alta renda — R$1,28tri sob gestão, maior motor de crescimento recente."),
            ("Sales & Trading", "mesa de operações — receita mais volátil, sobe e desce "
             "com a movimentação dos mercados."),
            ("Consumer Finance & Banking", "nova vertical, criada com a consolidação do "
             "Banco Pan e da Too Seguros — crédito consignado e financiamento de "
             "veículos para o varejo."),
        ],
        "insight_chave": "O segredo por trás do ROE consistentemente alto do BTG não é "
                     "só diversificação — é a estrutura de 'Partnership': os executivos "
                     "mais importantes do banco são também SÓCIOS, através de uma holding "
                     "separada que reúne o capital de mais de 400 sócios. Essa "
                     "partnership não compete com o cliente — ela entra DEPOIS dos "
                     "fundos e dos clientes institucionais em uma operação, mas "
                     "frequentemente com o maior cheque de todos, e usa parte dos "
                     "dividendos para investir diretamente na economia real (participações "
                     "em empresas como Light, Veste e Metalfrio, por exemplo). Isso "
                     "cria um incentivo muito mais forte que um salário: o sócio só "
                     "ganha se o banco (e os investimentos da partnership) performarem "
                     "bem — e explica por que o BTG hoje se parece menos com 'só um "
                     "banco' e mais com um grupo empresarial diversificado, no estilo "
                     "Itaúsa/Bradespar, só que mais agressivo. Além disso, com a compra "
                     "do Banco Pan e da Too Seguros, o BTG criou uma vertical de varejo "
                     "(Consumer Finance & Banking) que muda seu perfil de risco, "
                     "aproximando-o de um banco de varejo tradicional.",
        "setor_dinamica": "Banco de investimento diversificado — menos dependente de um "
                     "único motor, com receitas vindas de fontes muito diferentes entre "
                     "si (trading, wealth, M&A, crédito). Isso reduz a volatilidade "
                     "trimestral comparado a um banco mono-linha, mas exige executar bem "
                     "em várias frentes ao mesmo tempo.",
    },
    "CXSE3": {
        "o_que_faz": "A Caixa Seguridade é a holding de seguros, previdência, "
                     "capitalização e consórcio ligada à Caixa Econômica Federal — assim "
                     "como a BB Seguridade usa a rede do Banco do Brasil, a Caixa "
                     "Seguridade usa a rede da Caixa para vender seus produtos.",
        "segmentos": [
            ("Seguro Habitacional", "o principal motor — ligado direto ao financiamento "
             "imobiliário, onde a Caixa é a maior financiadora do Brasil."),
            ("Seguro Residencial e Prestamista", "prestamista (ligado a crédito pessoal) "
             "é o mais sensível à Selic — sobe quando o crédito está barato, cai quando "
             "os juros sobem."),
            ("Previdência e Capitalização", "reservas de previdência em expansão, "
             "capitalização com forte crescimento de receita de títulos."),
            ("Consórcio", "cartas de crédito administradas crescendo forte, +39% A/A."),
        ],
        "insight_chave": "A tese da Caixa Seguridade está praticamente amarrada ao "
                     "financiamento imobiliário da Caixa: o seguro habitacional (ligado "
                     "direto a cada novo contrato de financiamento de imóvel) é o que "
                     "mais cresce e mais pesa no resultado. Isso é diferente da BB "
                     "Seguridade, cujo maior motor é o Seguro Rural — mesmo sendo as duas "
                     "'seguradoras de banco público', elas têm exposições de risco bem "
                     "diferentes: a Caixa Seguridade está mais ligada ao mercado "
                     "imobiliário, a BB Seguridade ao agronegócio. Um detalhe pouco "
                     "comentado: a Caixa Seguridade não vende só pela rede da Caixa — "
                     "tem uma parceria de 49% com o BTG Pactual (Too Seguros, "
                     "distribuída via Banco PAN) e de 60% com a francesa CNP Assurances "
                     "(vida e previdência), diversificando os canais de venda além das "
                     "agências da Caixa. A receita de BDF (taxa que as seguradoras "
                     "parceiras pagam pra usar a marca e a rede de distribuição da "
                     "Caixa) é, na prática, a empresa 'alugando' sua marca e capilaridade "
                     "pra terceiros.",
        "setor_dinamica": "Bancassurance (seguros vendidos via banco) — modelo de baixo "
                     "custo de aquisição, mas dependente da saúde e do apetite de crédito "
                     "do banco controlador. Juros altos ajudam o resultado financeiro mas "
                     "pressionam produtos ligados a crédito (prestamista); juros baixos "
                     "fazem o oposto.",
    },
    "AXIA3": {
        "o_que_faz": "A Axia Energia (antiga Eletrobras) é a maior empresa de energia "
                     "elétrica da América Latina, líder em geração e transmissão no "
                     "Brasil, com ~22% da capacidade de geração instalada e 38% das "
                     "linhas de transmissão do país.",
        "segmentos": [
            ("Geração", "hidrelétricas (incluindo metade de Itaipu), eólicas e outras "
             "fontes renováveis — segmento mais representativo do lucro, beneficiado "
             "pela venda de energia a preço de mercado após a privatização."),
            ("Transmissão", "73 mil km de linhas — receita regulada e mais previsível, "
             "mas sujeita a revisões tarifárias e provisões regulatórias."),
        ],
        "insight_chave": "Desde a privatização em 2022, a Axia passou por uma mudança "
                     "estrutural que poucos investidores acompanham de perto: a "
                     "'descotização' — antes, parte da energia da empresa era vendida a "
                     "preço de CUSTO (regulado, baixo) para garantir energia barata ao "
                     "consumidor; depois da privatização, essa energia passou a ser "
                     "vendida a preço de MERCADO. Com os preços de energia de longo prazo "
                     "tendo saltado de R$100-150/MWh para R$240/MWh, esse único fator "
                     "explica boa parte do salto de lucro recente — não é só 'eficiência "
                     "operacional', é uma mudança de regra do jogo que beneficia "
                     "diretamente a receita.",
        "setor_dinamica": "Utilities (energia elétrica) — geração tem receita mais "
                     "sensível a preço de mercado de energia (mais parecido com uma "
                     "commodity agora, pós-privatização); transmissão é mais estável e "
                     "regulada. Ainda carrega passivos jurídicos históricos da era "
                     "estatal (como o empréstimo compulsório), que vêm sendo equacionados "
                     "gradualmente e afetam a leitura trimestre a trimestre.",
    },
    "CPLE3": {
        "o_que_faz": "A Copel é uma companhia de energia elétrica integrada (geração, "
                     "transmissão, distribuição e comercialização), com forte presença "
                     "no Paraná, privatizada em 2023 (o governo deixou de ser o acionista "
                     "controlador).",
        "segmentos": [
            ("Distribuição (Copel DIS)", "energia elétrica para o consumidor final no "
             "Paraná — ~43% do EBITDA, receita ligada ao crescimento do mercado fio "
             "faturado e reajustes tarifários anuais."),
            ("Geração e Transmissão (Copel GeT/COM)", "~57% do EBITDA — inclui "
             "hidrelétricas, eólicas e linhas de transmissão, com receita mais sensível "
             "a preços de energia no mercado de curto prazo."),
        ],
        "insight_chave": "A privatização da Copel em 2023 é o ponto de virada da tese: "
                     "deixou de ter o governo do Paraná como controlador e passou a ser "
                     "uma corporação com capital pulverizado. Desde então, a empresa vem "
                     "fazendo o que governos raramente fazem rápido — programa de "
                     "desligamento voluntário, venda de ativos fora do core business, e "
                     "disciplina de alocação de capital. O mercado já trata a Copel como "
                     "um dos nomes 'premium' do setor justamente por essa mudança de "
                     "gestão, não pelos ativos em si (que sempre foram bons).",
        "setor_dinamica": "Utilities integradas — distribuição é mais previsível (tarifa "
                     "regulada), geração/transmissão tem mais exposição a preço de "
                     "mercado de energia e a fatores hidrológicos (chuva, modulação). "
                     "Alavancagem na faixa de 2,7-2,8x é considerada saudável para o "
                     "setor, mas limita espaço para grandes aquisições sem aumentar risco.",
    },
    "ALOS3": {
        "o_que_faz": "A Allos é a maior administradora e proprietária de shopping "
                     "centers do Brasil, formada pela fusão entre Aliansce Sonae e "
                     "brMalls em 2023 — hoje com 59 shoppings em todo o país e mais de "
                     "15 mil lojistas.",
        "segmentos": [
            ("Locação (aluguel)", "principal fonte de receita — cobrada como % fixo + % "
             "das vendas das lojas."),
            ("Estacionamento, mídia e desenvolvimento imobiliário", "receitas "
             "complementares, crescendo mais rápido que a locação tradicional."),
            ("Serviços de administração para terceiros", "a Allos administra alguns "
             "shoppings que não são dela, cobrando taxa de gestão."),
        ],
        "insight_chave": "Um diferencial operacional pouco visível de fora: a Allos "
                     "mapeia mais de 170 mil lojas ao redor de cada um dos seus "
                     "shoppings pra decidir, com dados (não 'feeling'), qual tipo de "
                     "loja está faltando em cada empreendimento — uma mudança de "
                     "modelo 'artesanal' pra um mais analítico depois da fusão. Isso "
                     "orienta tanto a escolha de novos lojistas quanto decisões de "
                     "expansão, como a reforma do Shopping Campo Grande (R$216mi "
                     "investidos, 150 lojas novas, expectativa de +40% nas vendas do "
                     "shopping). Além disso, boa parte da 'fraqueza' do lucro no 1T26 "
                     "não teve nada a ver com o negócio em si — foi um incêndio "
                     "pontual no Shopping Tijuca em janeiro, que interrompeu a "
                     "operação por ~2 semanas; sem esse evento isolado, o crescimento "
                     "de EBITDA e FFO teria sido de 17-18%.",
        "setor_dinamica": "Shopping centers — receita ligada ao consumo das famílias, "
                     "taxa de juros (afeta crédito ao consumidor e custo de capital da "
                     "própria Allos) e ocupação dos shoppings. Negócio tende a ser bom "
                     "pagador de dividendos (modelo de REIT/FII implícito), mas com "
                     "crescimento mais lento que setores de maior expansão.",
    },
    "TIMS3": {
        "o_que_faz": "A TIM é uma das 3 grandes operadoras de telecomunicações do "
                     "Brasil (junto com Vivo e Claro), oferecendo serviços de telefonia "
                     "móvel, internet fixa (fibra) e serviços digitais.",
        "segmentos": [
            ("Serviço Móvel Pós-pago", "principal motor de crescimento — clientes com "
             "plano fixo mensal, maior receita por usuário (ARPU) e mais "
             "previsibilidade."),
            ("Serviço Móvel Pré-pago", "em declínio estrutural — clientes migrando para "
             "o pós-pago, que é mais lucrativo para a operadora."),
            ("Serviço Fixo (TIM UltraFibra)", "ainda pequeno (menos de 6% da receita) "
             "mas crescendo rápido, frente de expansão para os próximos anos."),
            ("B2B / IoT", "conectividade pra empresas (logística, iluminação "
             "inteligente, agronegócio) — receita contratada cresceu 30% A/A, para "
             "R$1,08bi no 1T26."),
        ],
        "insight_chave": "A TIM optou por NÃO ser dona da própria infraestrutura "
                     "física de fibra: em 2024, vendeu a I-Systems (sua operação de "
                     "fibra) para a IHS Towers por R$1,1bi, recebendo de volta o "
                     "serviço como locatária — o mesmo modelo já usado com torres de "
                     "celular. A própria empresa admite que 'não temos data centers, "
                     "não temos infraestrutura fixa' como discurso deliberado, "
                     "preferindo alugar capacidade de terceiros especializados a "
                     "carregar esses ativos no próprio balanço. Isso libera capital "
                     "pra focar em rede móvel e cliente, mas também significa que "
                     "parte da infraestrutura crítica do negócio não está sob "
                     "controle direto da TIM.",
        "setor_dinamica": "Telecomunicações — setor maduro e intensivo em capital "
                     "(precisa investir constantemente em rede/5G), com crescimento "
                     "vindo da migração pré-pago→pós-pago e da expansão de fibra, não de "
                     "novos clientes (o mercado de celular já está saturado no Brasil). "
                     "Competição via preço é constante.",
    },
    "KLBN4": {
        "o_que_faz": "A Klabin é a maior produtora e exportadora de papéis do Brasil, "
                     "com mais de 125 anos de história e operação verticalizada em 4 "
                     "unidades de negócio: Florestal, Celulose, Papel e Conversão "
                     "(embalagens) — vendendo tanto para o mercado interno quanto "
                     "para mais de 80 países.",
        "segmentos": [
            ("Florestal", "911 mil hectares de área de fibras (eucalipto + pinus) — "
             "base que sustenta toda a cadeia, com excedente de terras que a empresa "
             "tem monetizado separadamente."),
            ("Celulose", "a Klabin é a ÚNICA empresa do Brasil que oferece "
             "simultaneamente celulose de fibra curta, fibra longa E fluff — vende "
             "parte ao mercado internacional, exposta ao preço da commodity."),
            ("Papéis (Kraftliner, cartões etc.)", "papel para embalagens, com forte "
             "presença em exportação."),
            ("Conversão (embalagens de papelão ondulado, sacos industriais)", "consumo "
             "mais doméstico e estável, ligado a alimentos, bebidas e produtos de "
             "consumo."),
        ],
        "insight_chave": "Diferente da Irani (que só produz celulose para uso próprio) "
                     "e da Suzano (praticamente 100% exposta ao preço da celulose), a "
                     "Klabin fica no meio do caminho: produz celulose suficiente para "
                     "consumir na própria fábrica de papel/embalagens E ainda vende o "
                     "excedente ao mercado internacional — essa parcela 'exposta' fica "
                     "em torno de 40% da receita. Outro movimento pouco comentado: o "
                     "'Projeto Plateau', que antecipa a monetização de parte das "
                     "terras do Projeto Caetê — a Klabin, assim como a SLC Agrícola, "
                     "também usa o valor das próprias terras como fonte de capital, "
                     "sem precisar vender a operação florestal por completo.",
        "setor_dinamica": "Papel e celulose — negócio cíclico, dependente do preço "
                     "internacional da celulose (cotado em dólar) e do câmbio (receita "
                     "de exportação em dólar, parte dos custos em real). Resultados "
                     "financeiros (juros, swap, dívida em moeda estrangeira) podem "
                     "distorcer bastante o lucro contábil de um trimestre para outro.",
    },
    "CYRE3": {
        "o_que_faz": "A Cyrela é uma das maiores incorporadoras do Brasil, com foco "
                     "histórico no segmento médio/alto padrão, mas também detém "
                     "participações relevantes em outras incorporadoras (Cury, "
                     "Plano&Plano, Lavvi) focadas em outros nichos.",
        "segmentos": [
            ("Incorporação própria (médio/alto padrão)", "o negócio principal — constrói "
             "e vende apartamentos sob a marca Cyrela."),
            ("Participações em outras incorporadoras", "Cury (MCMV), Plano&Plano "
             "(econômico) e Lavvi (alto padrão) — reconhecidas via equivalência "
             "patrimonial, sem a Cyrela operar diretamente esses negócios."),
            ("CashMe", "braço de crédito/financiamento do grupo, complementar ao "
             "negócio imobiliário."),
        ],
        "insight_chave": "Uma parte relevante e crescente do lucro da Cyrela não vem de "
                     "vender apartamento com a própria marca — vem das participações que "
                     "ela tem em outras incorporadoras: em 2025, Cury, Plano&Plano e "
                     "Lavvi contribuíram juntas com cerca de R$395mi ao lucro líquido da "
                     "Cyrela (~20% do total), via equivalência patrimonial. O JP Morgan "
                     "já calculou que vender essas 3 participações poderia liberar até "
                     "R$1,9bi em dividendos extraordinários — mas reduziria o ROE da "
                     "empresa (de ~18-19% para ~16%), o que mostra que essas "
                     "participações não são só 'caixa parado': sustentam parte real da "
                     "rentabilidade do grupo. A Cyrela também tem acordos que a obrigam "
                     "a manter participação mínima nessas empresas (15% na Lavvi, 14% "
                     "na Cury e na Plano&Plano), limitando a liquidez imediata dessas "
                     "posições.",
        "setor_dinamica": "Incorporação residencial médio/alto padrão — mais sensível a "
                     "juros (financiamento imobiliário tradicional, sem subsídio do "
                     "governo como o MCMV) e à renda das famílias de classe média/alta. "
                     "Ciclo de reconhecimento de receita é longo (lucro bruto a "
                     "apropriar vai sendo realizado conforme a obra avança).",
    },
    "DIRR3": {
        "o_que_faz": "A Direcional é uma das maiores construtoras focadas no programa "
                     "Minha Casa Minha Vida (MCMV) do Brasil, com mais de 40 anos de "
                     "história e presença em 8 estados.",
        "segmentos": [
            ("Marca Direcional", "foco nas faixas mais baixas de renda do MCMV — ~70% "
             "dos lançamentos recentes."),
            ("Marca Riva", "empreendimentos de padrão médio/médio-baixo fora do "
             "programa MCMV tradicional — ~30% dos lançamentos."),
        ],
        "insight_chave": "O grande diferencial operacional da Direcional é o método "
                     "construtivo: a empresa consegue erguer duas torres, da fundação "
                     "ao acabamento, em até 45 dias, com 99,6% de industrialização no "
                     "canteiro de obras — um nível de padronização que poucas "
                     "concorrentes conseguem replicar com a mesma qualidade. Também usa "
                     "o 'modelo associativo': o contrato de venda só é assinado DEPOIS "
                     "que o crédito do cliente é aprovado pelo banco financiador, "
                     "reduzindo drasticamente o risco de distrato (cancelamento) que "
                     "afeta concorrentes que vendem antes da aprovação bancária. Em "
                     "dezembro/2025, a Direcional vendeu uma fatia da Riva pra gestora "
                     "Riza (que tem ~R$15bi sob gestão) por um valor que avaliou a Riva "
                     "sozinha em R$2,6bi — mais da metade do valor de mercado de toda a "
                     "Direcional na época, mostrando o quanto a Riva estava 'escondida' "
                     "dentro do valuation da controladora.",
        "setor_dinamica": "Construção de baixa renda via MCMV — negócio com ROE "
                     "historicamente alto (ciclo de capital de giro mais rápido que "
                     "construção de alto padrão) e fortemente ligado a decisões de "
                     "política pública (faixas de subsídio do MCMV, juros do FGTS). "
                     "Mudanças nas regras do programa podem impactar rapidamente o ritmo "
                     "de vendas.",
    },
    "MDNE3": {
        "o_que_faz": "A MDNE (antiga Moura Dubeux) é a holding que reúne as principais "
                     "incorporadoras do Nordeste brasileiro, líder regional há mais de "
                     "40 anos, organizada em 2026 sob uma estrutura de 3 marcas com "
                     "públicos bem definidos.",
        "segmentos": [
            ("Moura Dubeux (alto padrão e segunda residência)", "negócio histórico, com "
             "a linha Beach Class — mais de 30 empreendimentos litorâneos usados como "
             "segunda residência, hotelaria ou investimento para locação."),
            ("Mood (médio padrão)", "lançada em 2023, atende famílias com renda entre "
             "R$12-15 mil/mês — já ~30% dos lançamentos, com projeção de chegar a "
             "metade nos próximos anos."),
            ("Ún1ca (MCMV/econômico)", "lançada em 2025, joint venture com a "
             "Direcional, voltada à Faixa 3 do programa habitacional."),
        ],
        "insight_chave": "Um detalhe que poucos sabem sobre a história da empresa: por "
                     "volta de 2010, grandes incorporadoras de São Paulo (incluindo a "
                     "própria Cyrela) tentaram entrar no Nordeste e fracassaram — "
                     "tiveram que 'queimar' estoque a preços baixos quando saíram da "
                     "região, o que paradoxalmente ajudou a Moura Dubeux a consolidar "
                     "ainda mais a liderança local, com menos concorrência por terrenos "
                     "(banco de terras) depois desse episódio. O modelo de condomínio "
                     "fechado (onde o cliente entra como cotista e paga conforme a obra "
                     "avança) funciona como uma 'blindagem' contra a inflação de "
                     "custos de construção, repassando parte do risco de orçamento ao "
                     "comprador em vez de a construtora assumir sozinha.",
        "setor_dinamica": "Incorporação regional (Nordeste) — a diversificação entre 3 "
                     "marcas/faixas de renda (alto padrão, médio, MCMV) e entre estados "
                     "(presença em 7 do Nordeste) protege a empresa de revisões de "
                     "plano diretor ou desaceleração específica de uma única praça, "
                     "ainda que a empresa permaneça mais exposta à inflação de custos "
                     "de construção (INCC) que construtoras puramente MCMV.",
    },
    "CURY3": {
        "o_que_faz": "A Cury é uma joint venture entre a família Cury (fundadora) e a "
                     "Cyrela, focada em incorporação residencial de baixa renda dentro "
                     "do programa Minha Casa Minha Vida, concentrada em São Paulo e Rio "
                     "de Janeiro.",
        "segmentos": [
            ("MCMV (Minha Casa Minha Vida)", "praticamente todo o negócio da empresa — "
             "apartamentos econômicos voltados às faixas de renda do programa."),
        ],
        "insight_chave": "A própria Cury se descreve como um modelo 'Asset Light' — "
                     "precisa de muito menos capital próprio que concorrentes pra gerar "
                     "o mesmo volume de negócio, o que sustenta um ROE que já chegou a "
                     "quase 80% em trimestres recordes (1T26), muito acima da média do "
                     "setor (~15%). A empresa entrega margem bruta de ~38-39% (vs ~30% "
                     "da média do setor) e margem EBITDA de ~21% (vs ~13% da média) — "
                     "uma combinação de controle de custo rígido, concentração "
                     "geográfica (forte presença em São Paulo, onde já tem ~28% de "
                     "participação nos lançamentos do MCMV) e o 'crédito associativo' "
                     "(contrato só fecha após aprovação bancária do cliente, reduzindo "
                     "o risco de distrato).",
        "setor_dinamica": "Construção de baixa renda via MCMV — assim como a Direcional, "
                     "depende fortemente das regras do programa habitacional (faixas de "
                     "subsídio, juros do FGTS) e tende a ter ROE mais alto que "
                     "construtoras de padrão mais alto, pela maior velocidade de giro do "
                     "capital.",
    },
    "ABCB4": {
        "o_que_faz": "O Banco ABC Brasil é um banco de nicho corporativo, focado em "
                     "médias e grandes empresas, sem rede de agências de varejo nem "
                     "cliente pessoa física relevante.",
        "segmentos": [
            ("Crédito Corporativo", "operações de crédito com médias e grandes "
             "empresas."),
            ("Tesouraria", "operações financeiras próprias, complementares ao crédito."),
        ],
        "insight_chave": "Diferente dos grandes bancos (Itaú, BB, Santander), o ABC "
                     "Brasil não tem agências de varejo — é um banco 'atacadista', que "
                     "vive de relacionamento direto com empresas. Isso o protege de "
                     "crises de inadimplência de varejo (cartão, consignado), mas o "
                     "deixa mais exposto ao ciclo de crédito corporativo puro.",
        "setor_dinamica": "Bancos de nicho corporativo — menos diversificado que os "
                     "grandes bancos, com seletividade maior na originação de crédito e "
                     "resultado mais ligado à margem financeira que à escala.",
    },
    "BRSR6": {
        "o_que_faz": "O Banrisul é o banco estadual do Rio Grande do Sul, controlado "
                     "pelo governo do estado, com forte presença regional.",
        "segmentos": [
            ("Varejo bancário no RS", "agências concentradas no estado, atendendo "
             "pessoas físicas."),
            ("Crédito corporativo/agro", "exposição a empresas e produtores rurais "
             "gaúchos."),
        ],
        "insight_chave": "Sendo controlado pelo governo do RS, o Banrisul tem uma "
                     "dinâmica de governança diferente de bancos privados — decisões "
                     "de crédito e expansão podem ser influenciadas por objetivos de "
                     "política estadual, não só por retorno financeiro puro, o que "
                     "ajuda a explicar por que sua rentabilidade (ROE) historicamente "
                     "fica abaixo dos pares privados.",
        "setor_dinamica": "Bancos regionais/estaduais — menor escala que os bancos "
                     "nacionais, com ROE estruturalmente mais baixo e resultado mais "
                     "concentrado na economia de um único estado.",
    },
    "SANB3": {
        "o_que_faz": "O Santander Brasil é o terceiro maior banco privado do país, "
                     "controlado pelo Santander Espanha.",
        "segmentos": [
            ("Varejo", "pessoas físicas — cartão, crédito pessoal, financiamento."),
            ("Corporate/PJ", "empresas de todos os portes."),
        ],
        "insight_chave": "O Santander Brasil tem entregado ROE consistentemente menor "
                     "que Itaú e BTG nos últimos trimestres (16% no 1T26, vs 24% do "
                     "Itaú e 26,6% do BTG) — a própria gestão reconhece que isso é "
                     "parcialmente uma escolha deliberada: postura mais conservadora no "
                     "crédito, priorizando uma carteira mais 'limpa' no longo prazo em "
                     "vez de crescer rápido agora.",
        "setor_dinamica": "Bancos grandes privados — ROE é o principal termômetro de "
                     "comparação entre pares; resultado sensível ao ciclo de crédito e "
                     "à carga tributária.",
    },
    "BMGB4": {
        "o_que_faz": "O Banco BMG é focado em crédito consignado (público e privado) e "
                     "cartão consignado, com forte presença via correspondentes "
                     "bancários.",
        "segmentos": [
            ("Crédito Consignado", "principal produto — empréstimo com desconto "
             "direto em folha de pagamento."),
            ("Cartão Consignado", "linha de crédito rotativo vinculada ao consignado."),
        ],
        "insight_chave": "O BMG foi pioneiro no consignado privado no Brasil, mas hoje "
                     "compete com praticamente todos os grandes bancos nesse mercado, "
                     "que se tornou bem mais concorrido. A vantagem histórica de 'ser o "
                     "primeiro' foi erodindo, e hoje o BMG precisa competir em execução "
                     "e relacionamento com correspondentes, não mais em exclusividade "
                     "de produto.",
        "setor_dinamica": "Bancos de crédito consignado — produto de baixo risco "
                     "(desconto automático em folha), mas mercado cada vez mais "
                     "disputado por grandes bancos.",
    },
    "IRBR3": {
        "o_que_faz": "O IRB é a maior resseguradora da América Latina — vende 'seguro "
                     "de seguradoras', protegendo outras seguradoras que querem "
                     "repassar parte do risco que assumiram.",
        "segmentos": [
            ("P&C Brasil", "resseguro patrimonial, rural, riscos especiais no Brasil."),
            ("Exterior", "operações internacionais, incluindo Londres e Buenos Aires."),
        ],
        "insight_chave": "A IRB passou por uma crise contábil/de governança grave em "
                     "2020 (escândalo que derrubou a ação mais de 90%) e desde então "
                     "vem reconstruindo a confiança do mercado através de disciplina de "
                     "subscrição — a empresa hoje prefere recusar negócios mal "
                     "precificados (mesmo perdendo volume) a repetir os erros do "
                     "passado. Essa cicatriz histórica explica por que a empresa é tão "
                     "conservadora hoje, mesmo perdendo prêmios.",
        "setor_dinamica": "Resseguro — negócio cíclico ligado a 'hard market' (quando "
                     "há catástrofes, sobe a demanda e o preço do resseguro) vs 'soft "
                     "market' (poucos eventos, mais concorrência, preços caem).",
    },
    "ITSA4": {
        "o_que_faz": "A Itaúsa é a holding controladora do Itaú Unibanco, com "
                     "participações também em empresas não-financeiras (Alpargatas, "
                     "Dexco, Copa Energia, Aegea).",
        "segmentos": [
            ("Itaú Unibanco", "principal ativo — responde pela maior parte do valor e "
             "do lucro da holding."),
            ("Participações não-financeiras", "Alpargatas (calçados/vestuário), Dexco "
             "(madeira/louças), Copa Energia (GLP), Aegea (saneamento)."),
        ],
        "insight_chave": "A Itaúsa historicamente negocia com DESCONTO em relação à "
                     "soma das partes (valor de mercado de tudo que ela possui, "
                     "somado) — no 1T26 esse desconto era de 19,4%. Em teoria, comprar "
                     "Itaúsa pode ser 'mais barato' que comprar Itaú direto mais as "
                     "outras participações separadamente — mas esse desconto de "
                     "holding é estrutural (existe há anos) e pode nunca 'fechar' "
                     "completamente.",
        "setor_dinamica": "Holding diversificada — risco e retorno são uma média "
                     "ponderada de todas as investidas, dominada pelo peso do Itaú.",
    },
    "BRAP4": {
        "o_que_faz": "A Bradespar é uma holding controlada pelo Bradesco, cujo único "
                     "ativo relevante é uma participação na Vale.",
        "segmentos": [
            ("Participação na Vale", "praticamente 100% do valor e do resultado da "
             "empresa."),
        ],
        "insight_chave": "Diferente da Itaúsa (diversificada), a Bradespar é, na "
                     "prática, uma forma de comprar exposição à Vale com uma estrutura "
                     "societária diferente — não tem operação própria relevante. "
                     "Investir em BRAP4 é, na essência, uma aposta na Vale, só que com "
                     "uma camada extra de holding no meio.",
        "setor_dinamica": "Holding mono-ativo — sem diversificação, 100% dependente do "
                     "desempenho de uma única investida (Vale).",
    },
    "CMIN3": {
        "o_que_faz": "A CSN Mineração é o braço de mineração de ferro do grupo CSN, "
                     "com minas próprias e parceria logística com a CSN (siderúrgica).",
        "segmentos": [
            ("Minério de Ferro", "produção e venda, com forte exposição ao mercado "
             "chinês."),
            ("Logística (frete marítimo)", "exposição relevante ao mercado spot de "
             "frete, que distorce o resultado."),
        ],
        "insight_chave": "Diferente da Vale (que tem escala e contratos de frete mais "
                     "estáveis), a CSN Mineração tem MAIOR exposição ao mercado SPOT de "
                     "frete marítimo — quando o frete sobe (por conflitos geopolíticos "
                     "ou menor disponibilidade de navios), a receita líquida por "
                     "tonelada da CMIN3 cai mais que a de outras mineradoras, mesmo com "
                     "o preço do minério estável.",
        "setor_dinamica": "Mineração de ferro — menor escala que a Vale, com estrutura "
                     "de custo mais sensível a frete marítimo.",
    },
    "GGBR3": {
        "o_que_faz": "A Gerdau é a maior produtora de aço do Brasil e uma das "
                     "principais fornecedoras de aços longos das Américas, com "
                     "operações no Brasil e nos EUA.",
        "segmentos": [
            ("América do Norte", "hoje responde por ~75% do EBITDA — motor principal "
             "do resultado."),
            ("Brasil (aços longos e planos)", "pressionado por importação de aço, "
             "especialmente em aços planos."),
            ("Mineração", "minério de ferro próprio, usado internamente e vendido."),
        ],
        "insight_chave": "A Gerdau se tornou, na prática, 'uma história de aço "
                     "americano com uma opção brasileira' — 75% do EBITDA vem dos EUA, "
                     "que se beneficia de tarifas protecionistas (menos concorrência de "
                     "aço importado) e demanda mais forte. O Brasil, ao contrário, "
                     "sofre justamente com importação (28,5% de penetração em aços "
                     "planos), mostrando como a mesma empresa pode ter sorte muito "
                     "diferente em geografias diferentes ao mesmo tempo.",
        "setor_dinamica": "Siderurgia — altamente cíclica, sensível a tarifas de "
                     "comércio internacional, custo de minério/carvão e demanda da "
                     "construção civil/industrial.",
    },
    "UNIP6": {
        "o_que_faz": "A Unipar é a maior produtora de cloro e soda cáustica da América "
                     "do Sul, e a segunda maior produtora de PVC da região.",
        "segmentos": [
            ("Cloro-soda", "produto base, usado em saneamento, papel e celulose, "
             "alimentos."),
            ("PVC", "usado em construção civil — tubos, conexões, esquadrias."),
        ],
        "insight_chave": "O negócio da Unipar depende do 'spread' entre o preço de "
                     "venda dos produtos petroquímicos e o custo da matéria-prima "
                     "(eletricidade, sal, eteno) — não é tanto sobre volume vendido, é "
                     "sobre a diferença de preço. Quando esse spread aperta (como em "
                     "2024-2026), o lucro cai mesmo com volume de vendas estável, "
                     "porque a margem por tonelada encolhe.",
        "setor_dinamica": "Petroquímica — altamente cíclica, ligada a preços "
                     "internacionais de commodities petroquímicas e câmbio.",
    },
    "LEVE3": {
        "o_que_faz": "A Mahle Metal Leve é controlada pelo grupo alemão MAHLE (um dos "
                     "30 maiores fornecedores da indústria automotiva mundial, com "
                     "mais de 160 fábricas em 35 países) — no Brasil, fabrica "
                     "autopeças (pistões, anéis, filtros, bronzinas, camisas de "
                     "cilindro) em 5 unidades industriais (4 no Brasil, 1 na "
                     "Argentina).",
        "segmentos": [
            ("Mercado de reposição (aftermarket)", "historicamente a maior parte da "
             "receita (chegou a ~70% em alguns trimestres) — vendas pra manutenção "
             "de carros já em circulação, menos cíclico."),
            ("OEM (fabricação original)", "vendas pra montadoras — mais cíclico, "
             "ligado à produção de carros novos."),
            ("Exportação", "relevante e diversificada: Europa (~47%), América do "
             "Norte (~38%) e América Latina (~12%) — câmbio de várias moedas afeta o "
             "resultado, não só o dólar."),
        ],
        "insight_chave": "Por ter forte presença no aftermarket (peças de reposição), "
                     "a Mahle Metal Leve tem uma característica defensiva que outras "
                     "autopeças não têm: carros velhos continuam precisando de peça de "
                     "reposição, mesmo quando a venda de carros NOVOS desacelera. A "
                     "empresa ajusta deliberadamente o mix entre OEM e aftermarket, e "
                     "entre mercado interno e externo, justamente pra equilibrar essas "
                     "oscilações e estabilizar a margem ao longo do tempo — uma "
                     "decisão de gestão, não um acaso. Sendo controlada por um grupo "
                     "alemão gigante, a empresa também se beneficia de tecnologia e "
                     "P&D desenvolvidos centralmente pela matriz, sem precisar "
                     "replicar esse investimento sozinha no Brasil.",
        "setor_dinamica": "Autopeças — ligado ao ciclo da indústria automotiva, mas com "
                     "a camada de reposição (aftermarket) trazendo mais estabilidade.",
    },
    "SHUL4": {
        "o_que_faz": "A Schulz opera duas unidades de negócio bem distintas: Schulz "
                     "Automotiva (a maior fundição com usinagem e pintura integradas da "
                     "América do Sul) e Schulz Compressores (líder absoluta na América "
                     "Latina em compressores de ar de pistão), com fábricas no Brasil, "
                     "China e filial nos EUA.",
        "segmentos": [
            ("Schulz Automotiva (~75% do negócio)", "fundição de ferro nodular e "
             "cinzento, usinagem e montagem de peças para veículos comerciais "
             "pesados, máquinas agrícolas e equipamentos de construção, além de "
             "reposição (aftermarket)."),
            ("Schulz Compressores (~25% do negócio)", "compressores de ar pra "
             "indústria, oficinas e uso residencial, com mais de 10 mil revendas e "
             "distribuidores na América Latina."),
        ],
        "insight_chave": "Em 2024, a Schulz comprou a Janus & Pergher e criou a "
                     "'Schulz Gases' — uma terceira frente que produz oxigênio, "
                     "nitrogênio e purificação de biometano pra hospitais e indústrias, "
                     "diversificando pra além de compressores e autopeças. A empresa "
                     "também lançou em 2026 o 'Ecossistema Schulz', que integra "
                     "compressores, ferramentas, peças de reposição e monitoramento "
                     "via telemetria (sensores de pneus, gestão de frota) numa única "
                     "proposta pra transportadoras — uma tentativa de vender solução "
                     "recorrente, não só produto pontual. A Schulz tem caixa líquido "
                     "positivo (mais caixa do que dívida), raro entre indústrias "
                     "menores, o que permite esperar a virada de ciclo sem pressão "
                     "financeira.",
        "setor_dinamica": "Bens de capital/autopeças — cíclico, ligado à indústria "
                     "automotiva e de máquinas agrícolas, com exposição cambial "
                     "relevante (vendas em dólar nos EUA).",
    },
    "VULC3": {
        "o_que_faz": "A Vulcabras é a maior indústria de calçados esportivos do "
                     "Brasil, com mais de 70 anos de história, gestora das marcas "
                     "Olympikus e licenciada exclusiva de Mizuno e Under Armour no "
                     "país.",
        "segmentos": [
            ("Calçados Esportivos (Olympikus, Mizuno, Under Armour)", "~83% da "
             "receita — o motor principal, com crescimento em todas as marcas há "
             "mais de 15 trimestres consecutivos."),
            ("Outros Calçados (chinelos, botas profissionais, femininos)", "~7% da "
             "receita — mais instável, sensível à demanda por equipamento "
             "profissional."),
            ("Vestuário e Acessórios", "~10% da receita — meias, roupas esportivas; "
             "crescimento mais lento que calçados."),
        ],
        "insight_chave": "A Vulcabras opera o maior centro de P&D de calçados "
                     "esportivos da América Latina, em Parobé (RS), que desenvolve "
                     "mais de 800 novos modelos por ano — foi lá que nasceu o "
                     "Olympikus Corre Supra, o primeiro 'supertênis' 100% brasileiro "
                     "(placa de carbono + grafeno), que venceu a Maratona de São Paulo "
                     "na semana de lançamento. A fabricação é concentrada em duas "
                     "plantas no Nordeste (Ceará e Bahia), região com incentivo fiscal "
                     "de ICMS — esse benefício ajudou a sustentar margem bruta acima "
                     "de 40% por treze trimestres seguidos, até a Lei 14.789/23 mudar "
                     "a tributação sobre subvenções a partir de 2024, reduzindo parte "
                     "desse ganho. O e-commerce já responde por ~13% da receita e "
                     "cresce bem mais rápido que o varejo físico (+52% em um ano em "
                     "alguns trimestres).",
        "setor_dinamica": "Calçados esportivos — a empresa mantém ROIC consistentemente "
                     "acima de 25% (chegando a ~29% ajustado) e historicamente opera "
                     "com caixa líquido positivo (mais caixa que dívida), uma posição "
                     "rara entre fabricantes de bens de consumo no Brasil — dá "
                     "resiliência mesmo em trimestres de varejo mais fraco, e "
                     "sustenta uma política de dividendos generosa.",
    },
    "KEPL3": {
        "o_que_faz": "A Kepler Weber é a maior fabricante de equipamentos de "
                     "armazenagem de grãos (silos) do Brasil, com mais de 100 anos de "
                     "história, e está em processo de fusão com a americana GSI (Grain "
                     "& Protein Technologies) anunciado em março/2026.",
        "segmentos": [
            ("Fazendas", "~27% da receita — venda direta a produtores rurais, o "
             "segmento mais sensível a juros altos e seletividade de crédito."),
            ("Agroindústrias", "silos pra usinas, cooperativas e processadoras."),
            ("Negócios Internacionais", "~19% da receita, crescendo forte — Argentina "
             "vem sendo o destaque, depois de mais de 20 anos sem investimento em "
             "armazenagem no país vizinho."),
            ("Portos e Terminais", "projetos grandes e pontuais — só ~5 por ano, mas "
             "de alto valor (é um segmento 'tudo ou nada')."),
            ("Reposição e Serviços", "peças e manutenção — fluxo mais recorrente, "
             "~11 mil pedidos/ano."),
        ],
        "insight_chave": "Em março/2026, a Kepler Weber anunciou uma fusão com a "
                     "americana GSI (marca da Grain & Protein Technologies), que tem "
                     "fábricas em mais de 10 países — criando um gigante global de "
                     "armazenagem agrícola. A tese de fundo segue intacta: o Brasil "
                     "armazena só ~63% da produção de grãos, contra 108% nos EUA "
                     "(ou seja, os americanos têm MAIS capacidade de armazenagem do "
                     "que produzem em um ano, o Brasil tem bem menos) — um déficit "
                     "estrutural que sustenta demanda de longo prazo mesmo quando o "
                     "produtor rural está com margem apertada e investindo menos no "
                     "curto prazo.",
        "setor_dinamica": "Bens de capital agrícola — depende da saúde financeira e do "
                     "apetite de investimento do produtor rural, mais do que do preço "
                     "das commodities em si. A margem EBITDA atual (~14,7%) já é bem "
                     "superior à registrada no último grande ciclo de baixa do agro "
                     "(2015-2017, abaixo de 5%), mostrando maior resiliência da "
                     "empresa mesmo num cenário parecido de juros altos.",
    },
    "SLCE3": {
        "o_que_faz": "A SLC Agrícola é uma das maiores produtoras agrícolas do Brasil "
                     "em área cultivada (mais de 830 mil hectares, em 26 unidades e 8 "
                     "estados), com foco em soja, algodão, milho e sementes.",
        "segmentos": [
            ("Soja", "principal cultura em área plantada — mais de 50% da área total."),
            ("Algodão (pluma e caroço)", "segunda cultura mais relevante — maior "
             "valor agregado, foco crescente da estratégia."),
            ("Milho e sementes", "complementares, geralmente segunda safra."),
        ],
        "insight_chave": "Desde 2008, a SLC vem migrando deliberadamente para um "
                     "modelo 'asset light': em vez de só plantar em terra própria, "
                     "vendeu parte do seu patrimônio fundiário e passou a crescer via "
                     "arrendamento e joint ventures — hoje já mais de 50% da área "
                     "plantada é arrendada/JV, e cerca de 30% da colheita de soja é "
                     "terceirizada (não usa máquina própria), o que reduz a "
                     "necessidade de capital fixo (capex). A parceria com fundos "
                     "ligados ao PSP Investments (fundo de pensão canadense, gerido "
                     "pelo BTG) pra financiar irrigação é a evolução mais recente "
                     "dessa estratégia: dados da própria empresa mostram que o "
                     "algodão irrigado já rendeu 360 arrobas/hectare, contra 120 no "
                     "sequeiro (3x mais) — e a soja, 73,6 sacas/hectare irrigada "
                     "contra 35,2 no sequeiro (mais que o dobro).",
        "setor_dinamica": "Agricultura (commodities) — resultado muito ligado ao preço "
                     "internacional de soja/algodão/milho, clima (produtividade da "
                     "safra) e câmbio (boa parte da receita é dolarizada via "
                     "exportação).",
    },
    "CMIG4": {
        "o_que_faz": "A Cemig é uma holding de energia elétrica e gás natural de "
                     "Minas Gerais, com a maior diversificação de segmentos entre as "
                     "utilities brasileiras.",
        "segmentos": [
            ("Distribuição", "~46% do EBITDA — energia elétrica pra 9 milhões de "
             "consumidores em MG."),
            ("Geração", "~27% do EBITDA — hidrelétricas e outras fontes."),
            ("Gás Natural", "~12% do EBITDA — distribuição de gás em MG."),
            ("Transmissão e Comercialização", "~15% combinados."),
        ],
        "insight_chave": "A Cemig é a utility mais diversificada do Brasil em termos "
                     "de segmentos (energia + gás, distribuição + geração + "
                     "transmissão) — isso reduz a dependência de um único negócio, mas "
                     "a empresa também carrega um dos maiores programas de "
                     "investimento da história entre as utilities, o que pressiona a "
                     "alavancagem no curto prazo mesmo com a diversificação ajudando a "
                     "estabilizar receita.",
        "setor_dinamica": "Utilities integradas — diversificação ampla é uma vantagem "
                     "estrutural, mas o ciclo atual de investimento pesado exige "
                     "paciência do investidor antes de ver o retorno completo.",
    },
    "ISAE4": {
        "o_que_faz": "A ISA Energia (antiga ISA CTEEP) é a maior transmissora de "
                     "energia elétrica do Brasil, controlada pelo grupo colombiano "
                     "ISA, responsável por transmitir ~30% de toda a energia consumida "
                     "no país.",
        "segmentos": [
            ("Transmissão", "praticamente 100% do negócio — linhas de alta tensão que "
             "levam energia das usinas até as distribuidoras."),
        ],
        "insight_chave": "Sendo uma transmissora pura (sem geração nem distribuição), "
                     "a ISA Energia tem o perfil de receita mais 'parecido com renda "
                     "fixa' entre as utilities — a receita é definida por contratos de "
                     "longo prazo com reajuste predefinido (RAP), com pouquíssima "
                     "exposição a chuva, preço de energia no mercado de curto prazo ou "
                     "inadimplência de consumidor final.",
        "setor_dinamica": "Transmissão de energia — o segmento mais previsível e menos "
                     "cíclico do setor elétrico; crescimento vem de novos leilões de "
                     "concessão.",
    },
    "TAEE11": {
        "o_que_faz": "A Taesa é uma das maiores transmissoras de energia elétrica do "
                     "Brasil, fundada como parceria entre a Cemig e a colombiana ISA.",
        "segmentos": [
            ("Transmissão", "linhas de transmissão de alta tensão em várias regiões "
             "do país."),
        ],
        "insight_chave": "Assim como a ISA Energia, a Taesa vive de contratos de "
                     "transmissão com receita praticamente garantida por lei (RAP) — a "
                     "diferença entre as duas está mais na carteira de ativos e no "
                     "histórico de aquisições/leilões que cada uma venceu ao longo dos "
                     "anos, não tanto na dinâmica fundamental do negócio, que é "
                     "parecida.",
        "setor_dinamica": "Transmissão de energia — negócio de 'renda fixa de "
                     "infraestrutura', com dividendos consistentes e crescimento "
                     "dependente de vencer novos leilões.",
    },
    "SBSP3": {
        "o_que_faz": "A Sabesp é a maior empresa de saneamento básico do Brasil, "
                     "responsável por água e esgoto na maior parte do estado de São "
                     "Paulo, privatizada em 2024.",
        "segmentos": [
            ("Água", "captação, tratamento e distribuição."),
            ("Esgoto", "coleta e tratamento."),
        ],
        "insight_chave": "A privatização da Sabesp em 2024 é o evento que redefine a "
                     "tese de investimento — assim como aconteceu com a Eletrobras "
                     "(Axia) e a Copel, o mercado está observando se a gestão privada "
                     "vai conseguir extrair eficiência operacional que o controle "
                     "estatal não conseguia (redução de perdas de água, melhoria de "
                     "cobrança, disciplina de custos). O crescimento de lucro de 32% no "
                     "1T26 é um primeiro sinal nessa direção, mas ainda é início de "
                     "jogo.",
        "setor_dinamica": "Saneamento — monopólio natural regulado, com receita "
                     "previsível mas dependente de investimento constante em "
                     "infraestrutura (tubos, estações de tratamento).",
    },
    "CSMG3": {
        "o_que_faz": "A Copasa é a empresa de saneamento básico de Minas Gerais (água "
                     "e esgoto), ainda controlada pelo governo do estado (~50,3% das "
                     "ações).",
        "segmentos": [
            ("Água", "captação, tratamento e distribuição em MG."),
            ("Esgoto", "coleta e tratamento."),
        ],
        "insight_chave": "A Copasa é vista pelo mercado como uma 'Sabesp em "
                     "potencial' — a tese de privatização (que já aconteceu com a "
                     "Sabesp e gerou forte valorização) é o principal catalisador de "
                     "longo prazo pra ação, mas atrasos no cronograma desse processo "
                     "geram volatilidade e incerteza, já que boa parte do valor da "
                     "tese depende de um evento político/regulatório específico "
                     "acontecer.",
        "setor_dinamica": "Saneamento estatal — mesmo modelo de negócio da Sabesp, mas "
                     "ainda sem o catalisador da privatização, o que historicamente faz "
                     "negociar com desconto frente a pares já privatizados.",
    },
    "BRBI11": {
        "o_que_faz": "O BR Partners é um banco de investimento independente "
                     "brasileiro (não ligado a nenhum banco de varejo), especializado "
                     "em M&A, mercado de capitais (DCM/ECM), tesouraria e wealth "
                     "management.",
        "segmentos": [
            ("Investment Banking & Mercado de Capitais", "~62% da receita — "
             "assessoria em fusões/aquisições e emissões de dívida/ações."),
            ("Treasury Sales & Structuring", "~14% da receita — hedge em moedas, "
             "commodities e juros pra empresas."),
            ("Wealth Management", "gestão de fortunas — menor em receita, mas "
             "crescendo e trazendo mais previsibilidade."),
        ],
        "insight_chave": "O BR Partners é conhecido informalmente como o 'mini-BTG' — "
                     "réplica em menor escala (cerca de 1% do tamanho do BTG em valor "
                     "de mercado) do mesmo modelo de banco de investimento "
                     "independente, com ROE historicamente acima de 20%. A empresa "
                     "está deliberadamente investindo em Wealth Management justamente "
                     "pra reduzir a dependência das receitas mais voláteis (M&A, "
                     "trading), buscando se tornar mais parecida com o BTG também "
                     "nesse aspecto de receita recorrente.",
        "setor_dinamica": "Banco de investimento independente — receita mais volátil "
                     "que bancos de varejo (depende do volume de negócios fechados), "
                     "mas margens e ROE estruturalmente mais altos.",
    },
    "LREN3": {
        "o_que_faz": "A Lojas Renner é a maior varejista de moda do Brasil, dona das "
                     "marcas Renner, Camicado e Youcom, com operação de banco digital "
                     "(Realize) complementar.",
        "segmentos": [
            ("Varejo de moda (Renner)", "principal negócio — vestuário."),
            ("Camicado", "casa e decoração."),
            ("Realize (financeira)", "cartão de crédito e crédito ao consumidor, "
             "complementar ao varejo."),
        ],
        "insight_chave": "Diferente de outras varejistas de moda, a Renner tem capital "
                     "pulverizado desde 2005 (sem controlador definido) e é listada no "
                     "Novo Mercado — governança considerada referência no setor. O "
                     "maior risco estrutural de longo prazo não é concorrência de "
                     "outra loja física, é a entrada de plataformas cross-border como "
                     "Shein e AliExpress, que vendem direto da China com preços muito "
                     "mais baixos, sem precisar manter lojas físicas no Brasil.",
        "setor_dinamica": "Varejo de moda — sensível a juros (afeta tanto o consumo "
                     "quanto a financeira/cartão da empresa) e a concorrência de "
                     "e-commerce internacional.",
    },
    "GRND3": {
        "o_que_faz": "A Grendene é uma das maiores fabricantes de calçados do Brasil "
                     "(Melissa, Ipanema, Rider, entre outras), com forte presença em "
                     "exportação.",
        "segmentos": [
            ("Calçados femininos/infantis (Melissa, Ipanema)", "marcas mais "
             "conhecidas no Brasil e exterior."),
            ("Calçados masculinos/esportivos (Rider, Cartago)", "complementares."),
        ],
        "insight_chave": "Em 2025, a Grendene distribuiu um dividendo extraordinário "
                     "relevante (~R$1bi), elevando bastante a base de comparação de "
                     "2026 — o 'recuo' no lucro de 2026 não significa necessariamente "
                     "que o negócio piorou, é em parte um efeito de comparação contra "
                     "um ano atípico. A empresa mantém política financeira "
                     "conservadora, com caixa líquido robusto e baixa alavancagem.",
        "setor_dinamica": "Calçados — exportação relevante (câmbio importa), consumo "
                     "de massa, ligado ao poder de compra do consumidor brasileiro e "
                     "de mercados de exportação (América Latina principalmente).",
    },
    "EGIE3": {
        "o_que_faz": "A Engie Brasil é a segunda maior geradora de energia elétrica "
                     "privada do Brasil, com portfólio diversificado entre "
                     "hidrelétricas, eólicas, solares e participação em transmissão e "
                     "gás (via TAG).",
        "segmentos": [
            ("Geração Hidrelétrica", "principal fonte — mais estável e previsível."),
            ("Geração Eólica e Solar", "complementares, mas com risco de 'frustração "
             "de geração' (vento/sol abaixo do esperado) — foi de 17% no 1T26, em "
             "linha com o sistema nacional."),
            ("Transmissão e participação na TAG (gasoduto)", "diversificação fora da "
             "geração pura, incluindo equivalência patrimonial de uma participação de "
             "17,5% num gasoduto."),
        ],
        "insight_chave": "Diferente de uma geradora pura, a Engie Brasil tem uma "
                     "'pernada' silenciosa de receita vindo da participação na TAG "
                     "(Transportadora Associada de Gás) — um gasoduto, não uma usina "
                     "elétrica. Essa diversificação fora do setor elétrico tradicional "
                     "ajuda a estabilizar o resultado em trimestres onde a geração de "
                     "energia (hídrica, eólica, solar) sofre com clima desfavorável.",
        "setor_dinamica": "Geração de energia — resultado depende de fatores "
                     "climáticos (chuva para hidrelétrica, vento para eólica, sol "
                     "para solar) e do nível de investimento em curso, que tem "
                     "pressionado a dívida e a alavancagem recentemente.",
    },
    "CPFE3": {
        "o_que_faz": "A CPFL Energia é uma das maiores distribuidoras/geradoras de "
                     "energia do Brasil, controlada pela State Grid (estatal chinesa), "
                     "atendendo milhões de consumidores em SP, RS, PR e MG.",
        "segmentos": [
            ("Distribuição", "~61% do EBITDA — principal negócio, recém renovado por "
             "mais 30 anos de concessão."),
            ("Geração", "~28% do EBITDA."),
            ("Transmissão e Comercialização", "~11% combinados."),
        ],
        "insight_chave": "Em maio/2026, a CPFL concluiu a renovação das concessões de "
                     "suas 3 principais distribuidoras (CPFL Paulista, CPFL "
                     "Piratininga, RGE) por mais 30 anos — um evento que remove um "
                     "risco estrutural de longo prazo que existia sobre a tese (a "
                     "possibilidade de o governo não renovar e a empresa perder o "
                     "direito de operar essas redes). Mesmo sendo controlada por uma "
                     "estatal chinesa, a empresa mantém elevados níveis de governança "
                     "e o mesmo rating soberano da China.",
        "setor_dinamica": "Distribuição de energia — negócio regulado e bastante "
                     "estável, mas sensível à migração de clientes para o mercado "
                     "livre de energia (que reduz a base de consumidores cativos) e ao "
                     "custo de compra de energia em leilões.",
    },
    "SAPR4": {
        "o_que_faz": "A Sanepar é a empresa de saneamento básico do estado do Paraná, "
                     "com forte presença em água e esgoto, ainda com participação "
                     "relevante do governo estadual.",
        "segmentos": [
            ("Água", "captação, tratamento e distribuição no PR."),
            ("Esgoto", "coleta e tratamento."),
        ],
        "insight_chave": "A queda de 70,8% no lucro da Sanepar no 1T26 parece um "
                     "desastre, mas é majoritariamente um efeito de comparação: o "
                     "1T25 teve um ganho contábil extraordinário (vitória numa ação "
                     "judicial de IRPJ) que infla a base de comparação anterior. "
                     "Olhando só para receita (+7,8%) e para dívida (que caiu 59,6%, "
                     "com alavancagem de apenas 0,7x), a saúde operacional da empresa "
                     "está, na verdade, melhorando — não piorando. Um exemplo clássico "
                     "de por que comparar 'ano contra ano' sem entender o que compõe "
                     "cada lado pode dar uma impressão errada.",
        "setor_dinamica": "Saneamento estadual — monopólio natural regulado, com "
                     "receita previsível, mas sujeito a efeitos contábeis pontuais "
                     "(ações judiciais, revisões tarifárias) que podem distorcer "
                     "comparações de curto prazo entre trimestres.",
    },
    "CGRA4": {
        "o_que_faz": "A Grazziotin é uma rede de varejo tradicional do Rio Grande do "
                     "Sul e Santa Catarina, vendendo tecidos, vestuário, materiais de "
                     "construção e produtos de decoração, com mais de 70 anos de "
                     "história.",
        "segmentos": [
            ("Varejo de vestuário/tecidos (lojas Tottal, PorMenos, Franco Giorgi)", "negócio "
             "histórico da empresa."),
            ("Materiais de construção e acabamentos", "frente mais recente de "
             "diversificação."),
            ("Grazziotin Financeira", "crédito ao consumidor complementar ao varejo, "
             "cartão próprio."),
        ],
        "insight_chave": "A Grazziotin é classificada pela própria B3 como "
                     "'Governança Tradicional' (não é Novo Mercado) — o nível mais "
                     "básico de exigências de governança da bolsa. Isso, combinado "
                     "com baixa liquidez (poucas casas de análise cobrem o papel) e um "
                     "aumento de capital recente que dilui acionistas, faz da CGRA4 "
                     "uma 'small cap regional' no sentido mais literal: pouca "
                     "visibilidade externa, decisões mais concentradas na família "
                     "fundadora, mas com histórico de mais de 70 anos de operação no "
                     "varejo gaúcho.",
        "setor_dinamica": "Varejo regional tradicional — menos exposto a concorrência "
                     "de e-commerce nacional/internacional que varejistas de moda "
                     "maiores (como a Renner), mas também com crescimento mais "
                     "limitado e dependente da economia regional do Sul do Brasil.",
    },
    "BBDC3": {
        "o_que_faz": "O Bradesco é um dos maiores bancos privados do Brasil, com "
                     "modelo de negócio estruturado em dois pilares igualmente "
                     "estratégicos: banco (crédito, varejo, atacado) e seguridade "
                     "(seguros, saúde, previdência).",
        "segmentos": [
            ("Banco (varejo e atacado)", "crédito para pessoas físicas e empresas — "
             "carteira expandida de R$1,1 trilhão."),
            ("Seguros, Previdência e Capitalização", "~41% do lucro do grupo — "
             "Bradesco Vida e Previdência, Bradesco Capitalização, Bradesco Auto/RE."),
            ("Saúde (BradSaúde / SAUD3)", "recém desmembrada e listada na bolsa em "
             "maio/2026 — reúne Bradesco Saúde, Odontoprev, Atlântica Hospitais, "
             "Mediservice e uma participação de 25% no Fleury."),
        ],
        "insight_chave": "Em 2026, o Bradesco fez o maior 'IPO reverso' da história da "
                     "B3: separou todo o seu ecossistema de saúde (operadora, "
                     "odontologia, hospitais, laboratórios) numa empresa só — a "
                     "BradSaúde, com R$52bi de receita e 13 milhões de beneficiários — "
                     "e listou no Novo Mercado sob o ticker SAUD3. O Bradesco continua "
                     "sendo o controlador (91,35%), mas esse movimento 'destrava' "
                     "valor: o ativo estava registrado no balanço do banco por R$14bi, "
                     "mas o mercado avalia a nova empresa em R$49bi — um ganho de "
                     "capital de R$35bi que melhora os índices de capital do banco sem "
                     "precisar vender ações ou se endividar.",
        "setor_dinamica": "Bancos com braço de seguros forte — diferente de bancos "
                     "puramente de crédito, o Bradesco tem quase a metade do lucro "
                     "vindo de seguros/seguridade, um negócio com dinâmica de risco "
                     "bem diferente (menos ligado ao ciclo de crédito, mais à "
                     "sinistralidade e à gestão de reservas).",
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
    "SLCE3": {
        "titulo": "P/NAV: mercado precifica a empresa por menos da metade do valor das próprias terras",
        "texto": (
            "Todo mês de junho, a SLC Agrícola divulga uma avaliação independente "
            "(feita pela consultoria Deloitte) do valor de mercado de todas as suas "
            "terras. Na avaliação de 15/06/2026, o portfólio (incluindo áreas em "
            "parceria com fundos do BTG Pactual) foi avaliado em R$13,53 bilhões, com "
            "o hectare agricultável médio em R$59.534 — e o NAV (Net Asset Value, valor "
            "líquido dos ativos) total da companhia em R$13,8 bilhões. Comparado ao "
            "valor de mercado da SLC na bolsa (~R$6,7 bilhões), o P/NAV fica em torno "
            "de 0,49x — o mercado avalia a empresa por menos da metade do que vale só "
            "o patrimônio de terras, segundo a própria avaliação da companhia. Isso não "
            "significa que a ação está '50% barata' de forma automática — o NAV é uma "
            "estimativa de valor de liquidação dos ativos, não um preço-alvo de bolsa, "
            "e o mercado pode estar descontando a dificuldade prática de vender 840 mil "
            "hectares rapidamente, ou o ciclo de baixa nos preços de soja/algodão/milho "
            "que pressiona o lucro operacional no curto prazo. Mas é uma referência "
            "relevante de 'piso patrimonial': mesmo com o agronegócio fraco, a empresa "
            "tem um patrimônio fundiário avaliado por consultoria independente que vale "
            "mais que o dobro do valor de mercado atual."
        ),
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
            return ('acima_target', '#EF4444', '🔴',
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
                return ('oportunidade', '#22C55E', '🟢',
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
    _token_brapi = st.secrets.get("BRAPI_TOKEN", "")
    if not _token_brapi:
        return ''
    # Timeout curto e SEM retry -- com 50 ativos na página, se a brapi.dev
    # estiver lenta/fora do ar, 2 tentativas de 8s cada por ticker travava a
    # tela inteira por minutos. Melhor falhar rápido e seguir sem logo do
    # que travar a página esperando uma API externa fora do nosso controle.
    try:
        url = f"https://brapi.dev/api/quote/{ticker}?token={_token_brapi}"
        r = requests.get(url, timeout=3).json()
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
    limpeza manual de formato BR como fallback caso isso falhe.

    Prioriza correspondência EXATA do rótulo antes de cair pra substring --
    evita pegar o valor de um rótulo errado quando algum texto explicativo
    da página (tooltip) menciona o termo de passagem dentro da descrição de
    OUTRO indicador (foi o que causou o P/L = 2770x errado na TIMS3)."""
    termos_lower = [t.lower() for t in termos]

    def _extrair(valor):
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
            return None

    # 1ª passada: rótulo IDÊNTICO ao termo (ignorando espaços nas pontas).
    for rotulo, valor in indicadores.items():
        if rotulo.lower().strip() in termos_lower:
            resultado = _extrair(valor)
            if resultado is not None:
                return resultado

    # 2ª passada (fallback): substring, igual ao comportamento original.
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
@st.cache_data(ttl=86400, show_spinner=False)
def get_revisao_estimativas(ticker):
    """Revisão de estimativas de lucro pelos analistas (EPS trend) -- sinal
    usado por gestores profissionais pra antecipar movimento de preço: se o
    consenso de analistas está subindo ou caindo a expectativa de lucro nas
    últimas semanas, sem o investidor precisar esperar o resultado sair.

    NUNCA TESTADO contra ticker brasileiro de verdade -- a cobertura de
    dados de analistas do Yahoo Finance pra ações da B3 é historicamente
    inconsistente (boa pra alguns ativos populares, vazia pra outros,
    sobretudo small caps). Retorna (dict_ou_None, erro_ou_None); o dict
    tem 'atual', 'ha_30d', 'ha_90d' (estimativa de EPS do ano fiscal
    corrente) e 'variacao_30d', 'variacao_90d' (em %)."""
    try:
        stock = yf.Ticker(f"{ticker}.SA")
        trend = stock.eps_trend
        if trend is None or trend.empty:
            return None, "Yahoo Finance não tem dados de revisão de estimativas pra este ativo"

        # Linha '0y' = ano fiscal corrente -- a referência mais estável pra
        # ver se o consenso está sendo revisado pra cima ou pra baixo.
        if '0y' not in trend.index:
            return None, "dado de revisão do ano fiscal corrente não disponível"
        linha = trend.loc['0y']

        atual  = linha.get('current', None)
        ha_30d = linha.get('30daysAgo', None)
        ha_90d = linha.get('90daysAgo', None)

        if atual is None or (ha_30d is None and ha_90d is None):
            return None, "dados insuficientes pra calcular a variação"

        variacao_30d = ((atual - ha_30d) / abs(ha_30d) * 100) if ha_30d else None
        variacao_90d = ((atual - ha_90d) / abs(ha_90d) * 100) if ha_90d else None

        return {
            'atual': atual, 'ha_30d': ha_30d, 'ha_90d': ha_90d,
            'variacao_30d': variacao_30d, 'variacao_90d': variacao_90d,
        }, None
    except Exception as e:
        return None, str(e)


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

# Ordenação dos Cards -- não é um "ranking" separado, é só a ordem em que
# os cards aparecem na grade. Não afeta os cards de destaque (Maior Score,
# Maior DY, Maior Desconto P/L), que continuam mostrando o #1 absoluto
# independente de como os cards estão ordenados na tela.
st.sidebar.markdown("**↕️ Ordenar Cards por**")
ordenacao_opcoes = {
    "⭐ Maior Score (de Momento)": ("score", True),
    "🏛️ Maior Score Estrutural":   ("score_estrutural", True),
    "📉 Menor P/L":              ("pl_num", False),
    "🏆 Maior Dividend Yield":   ("dy_num", True),
    "🎯 Maior TIR (2026, real)": ("tir_real", True),
    "💰 Maior Earnings Yield":   ("earnings_yield", True),
    "📈 Maior ROE":              ("roe_num_raw", True),
}
ordenar_por = st.sidebar.selectbox("", list(ordenacao_opcoes.keys()), index=0,
                                    label_visibility="collapsed")
_ord_campo, _ord_desc = ordenacao_opcoes[ordenar_por]

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
    _pl_atual_bruto = pl_atual_val  # guarda o valor ANTES do filtro, só pra diagnóstico
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

        cor_tese = "#EF4444" if divergencias else "#22C55E"
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
                   "👤 Movimentação", "📑 Resultado", "📐 Vol. / Gráfico"]
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
                f"<div style='font-size:1.5em;font-weight:800;color:#22C55E;'>R$ {tg_v:.2f}</div>"
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

        def _card_score_hero(col, valor_momento, valor_estrutural):
            col.markdown(
                "<div style='{base}height:{altura};display:flex;flex-direction:column;"
                "justify-content:center;align-items:center;text-align:center;box-sizing:border-box;'>"
                "<div style='display:flex;width:100%;justify-content:space-around;'>"
                "<div>"
                "<div style='font-size:0.68em;color:#ccc;text-transform:uppercase;margin-bottom:6px;'>"
                "⭐ De Momento</div>"
                "<div style='font-size:2.0em;font-weight:900;color:#D4AF37;line-height:1;'>{momento}/10</div>"
                "</div>"
                "<div style='width:1px;background:rgba(255,255,255,0.12);margin:0 4px;'></div>"
                "<div>"
                "<div style='font-size:0.68em;color:#ccc;text-transform:uppercase;margin-bottom:6px;'>"
                "🏛️ Estrutural</div>"
                "<div style='font-size:2.0em;font-weight:900;color:#5B8DB8;line-height:1;'>{estrutural}/10</div>"
                "</div>"
                "</div>"
                "</div>".format(base=card_style, altura=ALTURA_RESUMO, momento=valor_momento,
                                estrutural=valor_estrutural),
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
        cor_var = "#22C55E" if variacao_dia > 0 else ("#EF4444" if variacao_dia < 0 else "#D4AF37")
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

        _score_estrut = ativo_data.get('score_estrutural') if isinstance(ativo_data, dict) else score
        _card_score_hero(r3, score, _score_estrut)
        _score_fund = ativo_data.get('score_fundamentos') if isinstance(ativo_data, dict) else None
        _pct_teto_sc = ativo_data.get('pct_acima_teto') if isinstance(ativo_data, dict) else None
        st.caption(
            "**De Momento**: qualidade + valuation + governança + cenário cíclico 2026 + "
            "preço atual vs. teto (pune empresa esticada agora, mesmo se for boa). "
            "**Estrutural**: a mesma base de qualidade + valuation + governança, mas SEM o "
            "desconto do cenário cíclico e SEM o ajuste de preço — pra não confundir 'momento "
            "ruim do setor' com 'empresa estruturalmente fraca'."
        )
        if _score_fund is not None and _pct_teto_sc is not None and _pct_teto_sc > 0 and _score_fund != score:
            st.caption(
                f"Score de fundamentos (sem olhar o preço): {_score_fund}/10. Como a cotação "
                f"está {_pct_teto_sc:.0f}% acima do Preço Teto, o score de momento foi ajustado "
                f"pra {score}/10 — boa empresa, mas preço esticado agora."
            )

        # ---- Revisão de Estimativas (consenso de analistas) ----
        st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)
        rev_dados, rev_erro = get_revisao_estimativas(ticker)
        if rev_dados and (rev_dados['variacao_30d'] is not None or rev_dados['variacao_90d'] is not None):
            v30 = rev_dados['variacao_30d']
            v90 = rev_dados['variacao_90d']
            def _cor_variacao(v):
                if v is None:
                    return "#888"
                return "#22C55E" if v > 0.5 else ("#EF4444" if v < -0.5 else "#D4AF37")
            v30_str = f"{v30:+.1f}%".replace(".", ",") if v30 is not None else "—"
            v90_str = f"{v90:+.1f}%".replace(".", ",") if v90 is not None else "—"
            rc1, rc2 = st.columns(2)
            with rc1:
                st.markdown(
                    "<div style='{base}text-align:center;'>"
                    "<div style='font-size:0.78em;color:#ccc;text-transform:uppercase;"
                    "margin-bottom:6px;'>📈 Revisão de Estimativas (30 dias)</div>"
                    "<div style='font-size:1.6em;font-weight:900;color:{cor};'>{v}</div>"
                    "</div>".format(base=card_style, cor=_cor_variacao(v30), v=v30_str),
                    unsafe_allow_html=True
                )
            with rc2:
                st.markdown(
                    "<div style='{base}text-align:center;'>"
                    "<div style='font-size:0.78em;color:#ccc;text-transform:uppercase;"
                    "margin-bottom:6px;'>📈 Revisão de Estimativas (90 dias)</div>"
                    "<div style='font-size:1.6em;font-weight:900;color:{cor};'>{v}</div>"
                    "</div>".format(base=card_style, cor=_cor_variacao(v90), v=v90_str),
                    unsafe_allow_html=True
                )
            st.caption(
                "Mostra se o consenso de analistas está revisando a estimativa de lucro "
                "(EPS) do ano fiscal corrente para cima ou para baixo nas últimas semanas — "
                "um sinal que costuma antecipar movimento de preço, sem precisar esperar o "
                "resultado trimestral sair."
            )
        else:
            st.info("Revisão de estimativas indisponível para este ativo.")
            if rev_erro:
                st.caption(f"🔧 Detalhe técnico: {rev_erro}")

    # ════════════════════════════════════════════════════════════════════
    # ABA: PANORAMA (orientação pra quem não conhece a empresa)
    # ════════════════════════════════════════════════════════════════════
    if aba_ativa == "🧭 Panorama":
        # ---- Governança e Outlook -- mudaram de Visão Geral pra aqui:
        # são texto descritivo/estrutural sobre a empresa, não status de
        # mercado do dia, então combinam mais com o espírito do Panorama. ----
        gov = GOVERNANCA.get(ticker, {})
        out = OUTLOOK_2026.get(ticker, {})
        nota_gov = gov.get('nota', None)
        obs_gov  = gov.get('obs', '')

        if nota_gov is not None or out:
            gcol1, gcol2 = st.columns(2)
            with gcol1:
                if nota_gov is not None:
                    if nota_gov >= 8:
                        gov_cor, gov_label = "#22C55E", "Alta"
                    elif nota_gov >= 6:
                        gov_cor, gov_label = "#D4AF37", "Média"
                    else:
                        gov_cor, gov_label = "#EF4444", "Baixa"
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
            st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)

        # ---- Estudo Específico (so aparece se existir entrada pro ticker) ----
        # Fica no TOPO do Panorama, não em Visão Geral -- é justamente o tipo
        # de detalhe estrutural/permanente que ajuda a entender a empresa,
        # então faz mais sentido logo na "porta de entrada" do panorama.
        estudo = ESTUDOS_ESPECIFICOS.get(ticker)
        if estudo:
            metrica_valor = ativo_data.get(estudo.get('metrica', ''), None) if isinstance(ativo_data, dict) else None
            metrica_html = (
                f"<div style='margin-top:10px;font-size:0.95em;color:#D4AF37;font-weight:800;'>"
                f"P/VP atual: {metrica_valor}</div>"
                if metrica_valor and metrica_valor != '-' else ""
            )
            st.markdown(
                "<div style='{base}border:1px solid rgba(212,175,55,0.35);margin-bottom:18px;'>"
                "<div style='font-size:0.78em;font-weight:600;color:#D4AF37;letter-spacing:0.5px;"
                "text-transform:uppercase;margin-bottom:8px;'>🔬 Estudo Específico — {titulo}</div>"
                "<div style='font-size:0.85em;color:#ddd;line-height:1.55;'>{texto}</div>"
                "{metrica_html}"
                "</div>".format(base=card_style, titulo=estudo['titulo'], texto=estudo['texto'],
                                metrica_html=metrica_html),
                unsafe_allow_html=True
            )

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
        def _card_metric(col, titulo, texto, cor_valor="#F1EFE8", destaque=False):
            estilo_extra = "border:1px solid rgba(212,175,55,0.55);background:rgba(212,175,55,0.07);" if destaque else ""
            prefixo_label = "⭐ " if destaque else ""
            col.markdown(
                "<div style='{base}{extra}text-align:center;'>"
                "<div style='font-size:0.72em;color:#ccc;text-transform:uppercase;'>{prefixo}{titulo}</div>"
                "<div style='font-size:1.25em;font-weight:900;color:{cor};'>{texto}</div>"
                "</div>".format(base=card_style, extra=estilo_extra, prefixo=prefixo_label,
                                titulo=titulo, texto=texto, cor=cor_valor),
                unsafe_allow_html=True
            )

        # ---- Categoria do setor -- define quais indicadores são "chave"
        # pra esse tipo de empresa e merecem destaque visual nesta aba ----
        _setor_cat = classificar_setor(row.get('SETOR', ''))
        _destaca_pl   = _setor_cat in ('banco', 'seguradora')
        _destaca_pvp_roe = _setor_cat == 'banco'
        _destaca_div_ebitda = _setor_cat not in ('banco', 'seguradora', 'capital_intensivo')

        st.markdown("#### 📊 Valuation")

        # ---- Linha 1: Resultado Projetado + Resultado Último Tri ----
        v1, v2 = st.columns([1, 1])
        _card_metric(v1, "Resultado Projetado 2026", row.get('LL PROJETADO', '-'))
        _card_metric(v2, "⭐ Resultado Último Tri (1/4)", row.get('RESULTADO 2026 (1/4)', '-'), cor_valor="#22C55E")
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
        _card_metric(pl1, "P/L Atual", pl_atual_str, cor_valor="#D4AF37", destaque=_destaca_pl)
        _card_metric(pl2, "P/L Médio (10 anos)", f"{row.get('P/L médio (últ. 10 anos)', '-')}x")
        _card_metric(pl3, "P/L Projetado", f"{pl_proj}x")
        st.caption(
            "P/L Médio (10 anos) é uma referência histórica. P/L Projetado reflete o cenário "
            "de resultado adotado na modelagem — quando esse cenário é conservador, o P/L "
            "Projetado tende a ficar acima do P/L Atual."
        )

        # ---- Earnings Yield (1/P-L Atual) e TIR Esperada 2026, lado a lado.
        # TIR: Earnings Yield projetado × Payout (parte que vira dividendo) +
        # (1-Payout) × ROE limitado a 10% a.a. (parte reinvestida, crescendo
        # ao ROE atual), depois descontando o IPCA pra virar retorno REAL
        # ("IPCA + X%"). ----
        st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
        if pl_atual_val and pl_atual_val > 0:
            ey_val = (1 / pl_atual_val) * 100
            ey_str = f"{ey_val:.1f}%".replace(".", ",")
            ey_cor = "#22C55E" if ey_val >= 10 else ("#D4AF37" if ey_val >= 6 else "#EF4444")
        else:
            ey_str, ey_cor = "—", "#888"

        _roe_tir = ativo_data.get('roe_num_raw') if isinstance(ativo_data, dict) else roe_num_raw
        _dy_tir = ativo_data.get('dy_num') if isinstance(ativo_data, dict) else dy_num
        tir_dados = calcular_tir_2026(row, _roe_tir, dy_num=_dy_tir)
        if tir_dados and tir_dados['tir_real'] is not None:
            tir_str = f"IPCA + {tir_dados['tir_real']:.1f}%".replace(".", ",")
            tir_cor = ("#22C55E" if tir_dados['tir_real'] >= 6
                       else "#D4AF37" if tir_dados['tir_real'] >= 3 else "#EF4444")
        else:
            tir_str, tir_cor = "—", "#888"

        eytir1, eytir2, eytir3 = st.columns(3)
        _card_metric(eytir1, "Earnings Yield", ey_str, cor_valor=ey_cor)
        _card_metric(eytir2, "TIR Esperada 2026 (real)", tir_str, cor_valor=tir_cor)

        st.caption(
            "Earnings Yield = 1 ÷ P/L Atual. Mostra quanto a empresa 'rende' em lucro sobre "
            "o preço atual — comparável diretamente com a Selic ou outra renda fixa."
        )
        if tir_dados and tir_dados['tir_real'] is not None:
            aviso_confianca = (
                " ⚠️ Payout baixo (boa parte do retorno vem do crescimento estimado, não do "
                "dividendo de fato pago) — resultado menos confiável, olhe os números acima "
                "com mais cautela." if tir_dados['payout_baixo'] else ""
            )
            _texto_fonte_g = (
                "pelo reinvestimento do lucro retido ao ROE atual (modelo de capital "
                f"intensivo, com Payout de {tir_dados['payout_usado']:.0f}%".replace(".", ",") + ")"
                if tir_dados['fonte_crescimento'] == 'reinvestimento_roe'
                else "com base no CAGR de lucros histórico (modelo asset-light/distribuição — "
                "o crescimento dessas empresas não vem de reinvestir capital, vem de vender "
                "mais volume pela rede do parceiro, então usamos o crescimento real já "
                "observado em vez da fórmula de reinvestimento)"
            )
            st.caption(
                f"TIR nominal de {tir_dados['tir_nominal']:.1f}%".replace(".", ",") +
                f" a.a. (Dividend Yield de {tir_dados['dy_usado']:.1f}%".replace(".", ",") +
                " = parte que vira dividendo de fato — o mesmo número usado no resto do app, "
                "não derivado de outra conta —, mais crescimento esperado de " +
                f"{tir_dados['g']:.1f}%".replace(".", ",") +
                (" (no teto de 10% a.a.)" if tir_dados['g_no_teto'] else "") +
                f" a.a. {_texto_fonte_g}), menos IPCA acumulado de " +
                f"{tir_dados['ipca_usado']:.1f}%".replace(".", ",") +
                " nos últimos 12 meses = retorno REAL esperado, no mesmo formato que o "
                "mercado de renda fixa usa pra apresentar uma NTN-B. Não é previsão garantida." + aviso_confianca
            )
        else:
            st.caption(
                "TIR esperada 2026 não disponível — esse modelo não se aplica bem a "
                "empresas com lucro projetado negativo, payout ausente/fora de faixa "
                "razoável, ROE indisponível, ou quando o resultado nominal passaria de 20% "
                "a.a. (sinal de que o modelo simplificado não está representando bem essa "
                "empresa)."
            )

        # ---- Os 2 graficos lado a lado, cada um ocupando metade da pagina ----
        st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            if historico_lucro:
                st.markdown("<span style='font-size:0.8em;color:#ccc;font-weight:bold;'>📈 Lucro Líquido (5 anos)</span>", unsafe_allow_html=True)
                st.markdown(mini_grafico_linha(historico_lucro, "#22C55E"), unsafe_allow_html=True)
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
        _card_metric(i1, "Dívida Líq/EBITDA", row.get('Dívida líquida/EBITDA', '-'), destaque=_destaca_div_ebitda)
        _card_metric(i2, "CAGR Lucros", row.get('CAGR lucros (últ. 5 anos)', '-'))
        _card_metric(i3, "ROE", roe, destaque=_destaca_pvp_roe)
        _card_metric(i4, "Margem Líq.", margem)
        i5, i6, i7, i8 = st.columns(4)
        _card_metric(i5, "Beta (vs IBOV)", beta)
        if ind_extras:
            _card_ind(i6, "ROIC", roic_val, sufixo="%")
            _card_ind(i7, "VPA", vpa_val, prefixo="R$ ")
            _card_ind(i8, "PEG Ratio", peg_val, sufixo="x")
            i9, i10, i11, i12 = st.columns(4)
            # P/EBIT e EV/EBITDA não existem de forma confiável pra bancos e
            # seguradoras -- essas empresas não têm "Receita Líquida" no
            # formato industrial que EBIT/EBITDA pressupõe, então o Fundamentus
            # às vezes retorna múltiplos absurdos (ex: -370x) pra esse tipo de
            # negócio. Não é erro de leitura -- é a métrica errada pro setor.
            if _setor_cat in ('banco', 'seguradora'):
                _card_metric(i9, "P/EBIT", "—")
                _card_metric(i10, "EV/EBITDA", "—")
            else:
                _card_ind(i9, "P/EBIT", p_ebit_val, sufixo="x")
                _card_ind(i10, "EV/EBITDA", ev_ebitda_val, sufixo="x")
            _card_metric(i11, "P/VP", pvp_str if pvp_str != "-" else "—", destaque=_destaca_pvp_roe)
            _card_ind(i12, "ROA", roa_val, sufixo="%")
            if _setor_cat in ('banco', 'seguradora'):
                st.caption(
                    "P/EBIT e EV/EBITDA não aparecem pra bancos/seguradoras de propósito — "
                    "essas empresas não têm 'Receita Líquida' no formato industrial que esses "
                    "múltiplos pressupõem, então o número que sairia não seria confiável "
                    "(podia vir um valor absurdo, tipo -370x, sem significado real)."
                )
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
                return "#22C55E" if pct_topo >= 0.7 else ("#D4AF37" if pct_topo >= 0.3 else "#EF4444")
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
            cor_pj = "#22C55E" if (diff_pct or 0) > 0 else "#EF4444"
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
            (f"Cotação atual: R$ {cot_pj:.2f}".replace(".", ",") if cot_pj else "") +
            f" · Bazin usa {pj['taxa_real_usada']:.2f}%".replace(".", ",") +
            " a.a. (taxa real do Tesouro IPCA+ de longo prazo, atualizada automaticamente — "
            "referência de quanto a renda fixa 'sem risco' está pagando agora). Gordon usa "
            f"essa mesma taxa + 4,5 p.p. de prêmio de risco ({pj['taxa_desconto_usada']:.1f}%".replace(".", ",") +
            " a.a. no total) e crescimento limitado a 8% a.a. (evita o modelo 'explodir' com "
            "CAGRs muito altos/instáveis). São 3 modelos com premissas diferentes — não devem "
            "ser tratados como verdade absoluta isoladamente, mas quando os 3 apontam pra "
            "mesma direção (barato ou caro), o sinal é mais confiável do que olhar só um deles."
        )

    # ════════════════════════════════════════════════════════════════════
    # ABA: DIVIDENDOS
    # ════════════════════════════════════════════════════════════════════
    if aba_ativa == "📈 Dividendos":
        st.markdown("#### 💰 Dividendos")
        style_dy = "color:#22C55E;font-weight:bold;" if dy_num > 8 else ""
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
                "<div style='margin-top:6px;padding:5px 8px;border-radius:6px;background:#1a3a1a;border:1px solid #22C55E;font-size:0.84em;'>"
                "<span style='color:#22C55E;font-weight:bold;'>📅 Próximo Provento em Aberto</span><br>"
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
                "<div style='font-size:1.3em;font-weight:900;color:#22C55E;'>R$ {total:.4f} / ação</div>"
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
                    cor_ins = "#22C55E" if resumo['valor'] >= 0 else "#EF4444"
                    label = "Compra líquida" if resumo['valor'] >= 0 else "Venda líquida"
                    sub_ins = f"{label} (6m): R$ {abs(resumo['valor']):,.0f}".replace(",", ".")
                else:
                    cor_ins = "#22C55E" if resumo['valor'] >= 0 else "#EF4444"
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
                "<div style='font-size:0.85em;color:#22C55E;font-weight:700;margin-bottom:4px;'>✓ Pontos fortes</div>"
                "<div style='font-size:0.85em;color:#ddd;line-height:1.55;margin-bottom:12px;'>{fortes}</div>"
                "<div style='font-size:0.85em;color:#EF4444;font-weight:700;margin-bottom:4px;'>✗ Pontos de atenção</div>"
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

            st.markdown(_card_apresentacao(ultimo_release, "📊 Release/Apresentação de Resultados mais recente", "#22C55E"),
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
    if aba_ativa == "📐 Vol. / Gráfico":
        with st.spinner("Buscando volatilidade implícita..."):
            vol_info, erro_vol = get_volatilidade_ticker(ticker)

        if vol_info is not None:
            vi = vol_info['vol_implicita']
            rank = vol_info['iv_rank']
            pct = vol_info['iv_percentil']
            cor_vi = "#EF4444" if (rank or 0) >= 70 else ("#D4AF37" if (rank or 0) >= 30 else "#22C55E")
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
                    increasing_line_color='#22C55E', decreasing_line_color='#EF4444', name=ticker
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


@st.cache_data(ttl=86400, show_spinner=False)
def get_ipca_12m():
    """Retorna o IPCA acumulado nos últimos 12 meses (% a.a.), via série 433
    do SGS (BCB) -- IPCA mensal, composto mês a mês (não é a série 433
    direto, que é só a variação MENSAL; aqui pegamos os últimos 12 meses e
    compomos: (1+m1)*(1+m2)*...*(1+m12) - 1). Usado pra converter a TIR
    nominal de uma ação em retorno REAL, no formato 'IPCA + X%' -- igual o
    mercado de renda fixa apresenta o retorno de uma NTN-B."""
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados/ultimos/12?formato=json"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        dados = r.json()
        if not dados or len(dados) < 12:
            return None
        acumulado = 1.0
        for d in dados:
            valor = d['valor']
            v = float(valor.replace(',', '.')) if isinstance(valor, str) else float(valor)
            acumulado *= (1 + v / 100)
        return round((acumulado - 1) * 100, 2)
    except Exception:
        return None


# ---- Taxa real livre de risco (Tesouro IPCA+ de mais longa duração) ----
# Usada como referência pra Bazin, Gordon e comparação de TIR -- mesma
# lógica que bancos/casas de análise usam: comparar o retorno implícito de
# uma ação com o que a renda fixa "sem risco" (indexada à inflação) está
# pagando agora. ANTES disso, o Bazin usava um divisor fixo de 6% (convenção
# antiga do livro do Décio Bazin, anos 90) que não acompanha a taxa real de
# juros de hoje -- com a Selic em ~14% e o Tesouro IPCA+ longo pagando ~8%
# real, usar 6% deixava o preço-teto artificialmente mais alto (permissivo)
# do que devia.
# NUNCA TESTADO contra o token de verdade -- este endpoint da brapi.dev
# (/api/v2/treasury) é novo pra nós; se falhar, cai no valor manual abaixo.
TAXA_IPCA_LONGA_MANUAL = 7.85  # atualizar manualmente em tesourodireto.com.br
                                 # se a busca automática parar de funcionar


@st.cache_data(ttl=86400, show_spinner=False)
def get_taxa_ipca_longa():
    """Busca a taxa atual (% a.a.) do Tesouro IPCA+ com Juros Semestrais de
    maior duração disponível, via brapi.dev (mesmo token usado pros logos).
    Retorna (taxa, descricao, erro) -- taxa é None se a busca falhar (nesse
    caso, use TAXA_IPCA_LONGA_MANUAL como respaldo)."""
    token = st.secrets.get("BRAPI_TOKEN", "")
    if not token:
        return None, None, "BRAPI_TOKEN não configurado"
    try:
        url = f"https://brapi.dev/api/v2/treasury/indicators?token={token}"
        r = requests.get(url, timeout=6)
        if r.status_code != 200:
            return None, None, f"HTTP {r.status_code}"
        dados = r.json().get('results', [])
        candidatos = [
            d for d in dados
            if 'ipca' in str(d.get('indexer', '')).lower()
            and 'semestra' in str(d.get('bondType', '')).lower()
        ]
        if not candidatos:
            return None, None, "nenhum Tesouro IPCA+ com juros semestrais encontrado na resposta"
        melhor = max(candidatos, key=lambda d: d.get('durationDays', 0))
        taxa_raw = melhor.get('buyRate', melhor.get('sellRate'))
        if taxa_raw is None:
            return None, None, "título encontrado mas sem campo de taxa (buyRate/sellRate)"
        taxa = float(taxa_raw) * 100 if float(taxa_raw) < 1 else float(taxa_raw)
        descricao = f"{melhor.get('bondType', 'Tesouro IPCA+')} {melhor.get('maturityDate', '')}"
        return taxa, descricao, None
    except Exception as e:
        return None, None, str(e)


def get_taxa_real_referencia():
    """Wrapper com fallback: tenta a busca live; se falhar, usa o valor
    manual. Sempre retorna um número usável."""
    taxa, _, _ = get_taxa_ipca_longa()
    return taxa if taxa is not None else TAXA_IPCA_LONGA_MANUAL


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
        cor_ibov = "#22C55E" if ibov_var > 0 else ("#EF4444" if ibov_var < 0 else "#D4AF37")
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
    st.markdown(f"""<div class='destaque-card'>
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
if not st.session_state.ativo_selecionado:
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
@st.cache_data(ttl=300, show_spinner=False)
def _construir_ativos_com_score(df_f, _min_score_efetivo, filtro_status_val):
    """Monta os dados de score/indicadores pra TODOS os ativos filtrados.
    Isolado numa função cacheada porque, sem isso, o app recalculava os 50
    ativos (Yahoo, logo, score) a CADA clique -- inclusive só navegando
    entre abas dentro de UM ativo já aberto, onde nada disso muda. Com
    cache, só recalcula quando os filtros do dashboard realmente mudam."""
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

        # ROE e Margem Líquida: prioriza Fundamentus sobre Yahoo -- o Yahoo
        # é inconsistente pra ações da B3 (campos de ROE vazios com
        # frequência, principalmente fora do horário de mercado aberto),
        # enquanto o Fundamentus é a mesma fonte já usada pra ROIC/P-L/VPA
        # em outras partes do app. Yahoo só entra como respaldo se o
        # Fundamentus não tiver o dado.
        ind_extras_lote, _ = get_indicadores_fundamentus(row['CÓDIGO'])
        if ind_extras_lote:
            roe_fund = _ind_buscar(ind_extras_lote, 'roe')
            marg_liq_fund = _ind_buscar(ind_extras_lote, 'marg. l', 'margem l')
            if roe_fund is not None:
                roe_num_raw = roe_fund
                roe = f"{roe_fund:.2f}%".replace('.', ',')
            if marg_liq_fund is not None:
                margem_num_raw = marg_liq_fund
                margem = f"{marg_liq_fund:.2f}%".replace('.', ',')

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
        score_fundamentos = calcular_score(dy_num, pl_num, div_ebitda_num, cagr_num, roe_num_raw, margem_num_raw,
                               pvp_num=pvp_num_raw, setor=row.get('SETOR', ''),
                               ticker=row.get('CÓDIGO', ''), historico_lucro=historico_lucro)

        # Score Estrutural: a mesma base de qualidade + valuation + governança,
        # mas SEM os dois descontos "do momento" -- o multiplicador de outlook
        # (que reflete o cenário cíclico de 2026, ex: juros altos pressionando
        # consumo) e o desconto por preço esticado (que reflete o humor do
        # mercado agora, não a qualidade da empresa). "Desfaz" o multiplicador
        # de outlook matematicamente (é só dividir de volta), sem precisar
        # duplicar a lógica de calcular_score.
        _mult_outlook = penalizacao_outlook(row.get('CÓDIGO', ''))
        score_estrutural = round(min(score_fundamentos / _mult_outlook, 10.0), 1) if _mult_outlook > 0 else score_fundamentos

        preco_teto_val = row.get('preco_teto', 0) if 'preco_teto' in row.index else limpar_valor(str(row.get('PREÇO TETO', 0)))
        target_val     = row.get('target', 0) if 'target' in row.index else limpar_valor(str(row.get('TARGET', 0)))
        st_status, st_cor, st_icone, st_desc = status_aporte(row.get('Cotação atual', 0), preco_teto_val, target_val)

        score, pct_acima_teto = aplicar_ajuste_preco(score_fundamentos, row.get('Cotação atual', 0), preco_teto_val)

        div_safety_score, div_safety_label, div_safety_cor = calcular_dividend_safety(
            row.get('PAYOUT', '-'), div_ebitda_num, roe_num_raw, historico_lucro
        )

        tir_dados_lote = calcular_tir_2026(row, roe_num_raw, dy_num=dy_num)
        tir_real_lote = tir_dados_lote['tir_real'] if tir_dados_lote else None
        earnings_yield_lote = (1 / pl_num * 100) if pl_num > 0 else None

        ativos_com_score.append({
            'row': row, 'score': score,
            'score_fundamentos': score_fundamentos, 'pct_acima_teto': pct_acima_teto,
            'score_estrutural': score_estrutural,
            'tir_real': tir_real_lote, 'earnings_yield': earnings_yield_lote,
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

    return ativos_com_score


if df_f.empty:
    card_filtrados.markdown("""<div class='top-card'>
        <div class='label'>🔍 Ativos Filtrados</div>
        <div class='value'>0</div>
    </div>""", unsafe_allow_html=True)
    st.warning("Nenhum ativo encontrado.")
else:
    ativos_com_score = _construir_ativos_com_score(df_f, _min_score_efetivo, filtro_status_val)

    card_filtrados.markdown(f"""<div class='top-card'>
        <div class='label'>🔍 Ativos Filtrados</div>
        <div class='value'>{len(ativos_com_score)}</div>
    </div>""", unsafe_allow_html=True)

    if ativos_com_score:
        top = ativos_com_score[0]
        card_maior_score.markdown(f"""<div class='destaque-card'>
            <div class='label'>🏅 Maior Score</div>
            <div class='value'>{top['row']['CÓDIGO']}</div>
            <div class='sub'>⭐ {top['score']}/10</div>
        </div>""", unsafe_allow_html=True)
    else:
        card_maior_score.markdown("""<div class='destaque-card'>
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
        card_menor_pl.markdown(f"""<div class='destaque-card'>
            <div class='label'>📉 Maior Desconto P/L</div>
            <div class='value'>{melhor_desconto}</div>
            <div class='sub'>-{melhor_pct:.0f}% vs média 10a</div>
        </div>""", unsafe_allow_html=True)
    else:
        card_menor_pl.markdown("""<div class='destaque-card'>
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
            # Ordena uma CÓPIA pra exibição -- ativos_com_score continua como
            # está (ordenado por score) pros cards de destaque acima, que
            # dependem de [0] ser o #1 absoluto por score.
            def _chave_ordenacao(a):
                valor = a.get(_ord_campo)
                # P/L <= 0 normalmente é empresa com prejuízo no período --
                # não é "barata", é dado que não deveria ranquear como menor
                # P/L. Trata como ausente, igual None.
                if valor is None or (_ord_campo == 'pl_num' and valor <= 0):
                    # sem o dado -- empurra pro fim da lista, em vez de quebrar
                    # a ordenação ou aparecer no topo por engano
                    return (1, 0)
                return (0, -valor if _ord_desc else valor)
            ativos_exibicao = sorted(ativos_com_score, key=_chave_ordenacao)

            cols_n = 8
            rows_c = [ativos_exibicao[i:i+cols_n] for i in range(0, len(ativos_exibicao), cols_n)]
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

                    dy_color = "#22C55E" if dy_num_c > 8 else "#5B8DB8"
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
