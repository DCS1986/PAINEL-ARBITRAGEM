import io
import re
import pandas as pd
import streamlit as st
import yfinance as yf
import requests
from bs4 import BeautifulSoup

from ui_confluencia import render_confluencia, render_confluencia_card
from cvm_insiders import (
    baixar_mapa_tickers, baixar_programa_recompra, programa_recompra_ativo,
) 
from tir_engine import calcular_tir, render_tir, tir_real_valor, TICKERS_TIR_CONFIRMADA

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
    if 'holding' in s:
        return 'holding'
    if any(x in s for x in ['banco', 'financeiro']):
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


def explicar_score(dy_num, pl_num, div_ebitda_num, cagr_num, roe_num, margem_num,
                   pvp_num=0, setor='', ticker='', historico_lucro=None):
    """Espelha EXATAMENTE a mesma lógica de calcular_score, mas devolve o
    detalhamento ponto a ponto (de onde vem cada parte da nota) em vez de só
    o número final -- pra responder "por que essa empresa tem nota X e
    aquela tem nota Y" sem precisar adivinhar. Usado só pra exibição/
    diagnóstico, não substitui calcular_score no cálculo real."""
    categoria = classificar_setor(setor)
    consistencia = consistencia_lucro(historico_lucro or {})
    itens = []  # (label, pontos_obtidos, pontos_possiveis)

    if categoria == 'banco':
        itens.append(("ROE", min(roe_num / 25.0, 1.0) * 2.5, 2.5))
        itens.append(("CAGR de Lucros", min(cagr_num / 20.0, 1.0) * 2.0, 2.0))
        itens.append(("Consistência do Lucro", consistencia * 1.5, 1.5))
        itens.append(("Dívida Líq/EBITDA", max(0, (4 - div_ebitda_num) / 4.0) * 1.0, 1.0))
        itens.append(("P/VP", (max(0, (2.0 - pvp_num) / 2.0) * 1.5) if pvp_num > 0 else 0, 1.5))
        itens.append(("P/L", (max(0, (12 - pl_num) / 12.0) * 1.0) if pl_num > 0 else 0, 1.0))
        itens.append(("Dividend Yield", min(dy_num / 10.0, 1.0) * 0.5, 0.5))
    elif categoria == 'seguradora':
        itens.append(("ROE", min(roe_num / 25.0, 1.0) * 2.5, 2.5))
        itens.append(("CAGR de Lucros", min(cagr_num / 20.0, 1.0) * 2.0, 2.0))
        itens.append(("Consistência do Lucro", consistencia * 1.5, 1.5))
        itens.append(("Margem Líquida", min(margem_num / 40.0, 1.0) * 1.0, 1.0))
        itens.append(("P/L", (max(0, (15 - pl_num) / 15.0) * 1.5) if pl_num > 0 else 0, 1.5))
        itens.append(("Dividend Yield", min(dy_num / 10.0, 1.0) * 1.5, 1.5))
    elif categoria == 'capital_intensivo':
        itens.append(("CAGR de Lucros", min(cagr_num / 15.0, 1.0) * 2.0, 2.0))
        itens.append(("Consistência do Lucro", consistencia * 1.5, 1.5))
        itens.append(("Dívida Líq/EBITDA", max(0, (4 - div_ebitda_num) / 4.0) * 2.0, 2.0))
        itens.append(("ROE", min(roe_num / 18.0, 1.0) * 1.5, 1.5))
        itens.append(("Dividend Yield", min(dy_num / 10.0, 1.0) * 2.0, 2.0))
        itens.append(("P/L", (max(0, (18 - pl_num) / 18.0) * 1.0) if pl_num > 0 else 0, 1.0))
    elif categoria == 'ciclica':
        itens.append(("ROE", min(roe_num / 20.0, 1.0) * 2.5, 2.5))
        itens.append(("Dívida Líq/EBITDA", max(0, (3 - div_ebitda_num) / 3.0) * 2.0, 2.0))
        itens.append(("CAGR de Lucros", min(cagr_num / 20.0, 1.0) * 1.5, 1.5))
        itens.append(("Consistência do Lucro", consistencia * 1.0, 1.0))
        itens.append(("Dividend Yield", min(dy_num / 10.0, 1.0) * 1.5, 1.5))
        itens.append(("P/VP", (max(0, (2.0 - pvp_num) / 2.0) * 1.0) if pvp_num > 0 else 0, 1.0))
        itens.append(("P/L", (max(0, (15 - pl_num) / 15.0) * 0.5) if pl_num > 0 else 0, 0.5))
    else:
        itens.append(("ROE", min(roe_num / 20.0, 1.0) * 2.5, 2.5))
        itens.append(("CAGR de Lucros", min(cagr_num / 20.0, 1.0) * 2.0, 2.0))
        itens.append(("Consistência do Lucro", consistencia * 1.5, 1.5))
        itens.append(("Dívida Líq/EBITDA", max(0, (5 - div_ebitda_num) / 5.0) * 1.0, 1.0))
        itens.append(("Dividend Yield", min(dy_num / 10.0, 1.0) * 1.5, 1.5))
        itens.append(("P/L", (max(0, (20 - pl_num) / 20.0) * 1.0) if pl_num > 0 else 0, 1.0))
        itens.append(("P/VP", (max(0, (3 - pvp_num) / 3.0) * 0.5) if pvp_num > 0 else 0, 0.5))

    subtotal = sum(i[1] for i in itens)
    pen_gov = penalizacao_governanca(GOVERNANCA.get(ticker, {}).get('nota', 7.0))
    mult_out = penalizacao_outlook(ticker)
    score_fundamentos = round(min(max(0.0, subtotal + pen_gov) * mult_out, 10.0), 1)

    return {
        'categoria': categoria, 'itens': itens, 'subtotal': subtotal,
        'pen_governanca': pen_gov, 'mult_outlook': mult_out,
        'score_fundamentos': score_fundamentos,
    }


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
        "o_que_faz": "A BB Seguridade (BB Seguros) é a maior empresa de seguros da América "
                     "Latina em valor de mercado. Holding que detém 100% da BB Seguros "
                     "(que controla Brasilseg, Brasilprev, Brasilcap e Brasildental) e 100% "
                     "da BB Corretora. Não assume risco de subscrição — distribui produtos "
                     "dos parceiros (Mapfre, Principal Financial Group) pela rede do Banco "
                     "do Brasil, com +91 milhões de clientes. Lucro recorrente R$9,1bi em "
                     "2025 (CAGR +19% em 5 anos). Desde o IPO em 2013, distribuiu "
                     "R$61,6bi em dividendos — 1,8x o valor de mercado. Ação +472% desde "
                     "o IPO vs IBOV +242%.",
        "segmentos": [
            ("Seguro Rural (Brasilseg) — 35,9% do resultado", "Leader absoluta: 62,9% de "
             "market share em seguros rurais. Produtos: agrícola (contra intempéries e queda "
             "de preço), penhor rural (ativo em garantia) e vida produtor rural. CAGR +11% "
             "em prêmios. Contrato até 06/2031. Risco: só 7% da área agrícola tem seguro — "
             "enorme potencial, mas exposição a El Niño e ciclo do agro."),
            ("Previdência (Brasilprev) — 22,6% do resultado", "Maior gestora de previdência "
             "privada do Brasil: 38,4% market share em contribuições e 26,6% em reservas. "
             "Reservas de R$484bi (CAGR +10%). PGBL e VGBL distribuídos na rede BB. "
             "Lucro CAGR +19%. Contrato até 10/2032."),
            ("Prestamista (Brasilseg) — 15,4% do resultado", "12,6% de market share — "
             "líder no segmento. Seguro que garante pagamento de dívida em caso de morte "
             "do mutuário. Cresce com o crédito consignado. Contrato até 06/2031."),
            ("Vida (Brasilseg) — 13,2% do resultado", "9,5% de market share (3º lugar). "
             "Produto não-cumulativo — se o cliente para de pagar, cobertura é suspensa "
             "sem reversão de valor. Sinistralidade caiu 11,6 pp nos últimos 5 anos."),
            ("Capitalização (Brasilcap) — 6,0% do resultado", "25,5% market share em "
             "reservas e 20,7% em arrecadação. Lucro CAGR +208%. Reservas R$11,4bi. "
             "Beneficiado pela Selic alta."),
            ("BB Corretora — distribuição", "Margem líquida de 61,7% no 1T26. Receita "
             "de corretagem CAGR +9%. Contrato até 01/2033. É o 'sistema nervoso' que "
             "conecta os produtos de seguros à rede BB."),
        ],
        "insight_chave": "O 'contrato até 2033' que o mercado teme esconde a realidade: "
                     "os contratos são DIFERENTES por subsidiária. Brasilseg e Prestamista "
                     "vão até 2031, Brasilprev até 2032, BB Corretora até 2033 e "
                     "Brasildental até 2035. A renovação acontece de forma escalonada, "
                     "não de uma vez só — e a empresa já renovou e reestruturou contratos "
                     "historicamente (parceria com Mapfre reformulada em 2019 para focar "
                     "no canal bancário). Além disso, o guidance 2026 projeta queda de "
                     "resultado operacional (-7% a -3%), mas o 1T26 já entregou +1,3% — "
                     "à frente do guidance. O resultado financeiro (Selic rendendo nas "
                     "reservas) foi R$507mi no 1T26, +58,5% A/A — representa 22,8% do "
                     "resultado total e atua como 'colchão' quando o operacional fraqueja.",
        "setor_dinamica": "O Brasil tem uma das menores penetrações de seguros do mundo "
                     "(prêmios/PIB de 3,4% vs 12,7% nos EUA e 11,8% no Reino Unido). "
                     "Apenas 7% da área agrícola está segurada. A combinação de renda "
                     "crescente, formalização do crédito e baixa penetração cria um runway "
                     "secular de crescimento para seguros no Brasil. O modelo bancassurance "
                     "(distribuição via banco) é o mais eficiente: custo de aquisição "
                     "quase zero, já que a rede do BB é paga para servir ao cliente "
                     "de qualquer forma. A receita diferida (R$14,9bi em prêmios + "
                     "R$6,3bi em comissões a apropriar) funciona como colchão: em ciclos "
                     "ruins, a empresa apropia receitas já contratadas.",
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


# Conteúdo qualitativo sobre o negócio — alimentado empresa por empresa.
# Formato: lista de blocos {"titulo": str, "texto": str}.
# Adicione novos tickers aqui à medida que forem sendo estudados.
SOBRE_NEGOCIO = {
    "ABCB4": [
        {"titulo": "Como funciona o negócio", "texto": "O ABC Brasil é o mais puro exemplo de especialização no setor bancário brasileiro. Não tem agência para pessoa física. Não tem conta corrente de varejo. Não tem cartão de crédito PF. Atende exclusivamente médias e grandes empresas (segmento middle market, corporate e large corporate) com crédito, trade finance (financiamento ao comércio exterior), câmbio, derivativos, banco de investimento e seguros corporativos. Controlado pelo Arab Banking Corporation (banco árabe do Barein), tem acesso facilitado a funding internacional e a uma rede de relacionamentos no Oriente Médio que nenhum banco brasileiro replica. A inadimplência histórica abaixo de 1% é o resultado de 35 anos atendendo quem tem balanço para mostrar — empresas com faturamento mínimo de R$30 mi anuais."},
        {"titulo": "De onde vem a receita", "texto": "<b>~55% — Margem com clientes (crédito corporativo):</b> spread sobre carteira de R$32+ bi<br><b>~20% — Margem com mercado e tesouraria:</b> PL remunerado ao CDI + operações de mercado<br><b>~15% — Receitas de serviços:</b> banco de investimento, tarifas, câmbio<br><b>~10% — Seguros e outros:</b> "},
        {"titulo": "Vantagens competitivas", "texto": "✦ Inadimplência histórica < 1% — resultado de 35 anos emprestando apenas para empresas com balanço<br>✦ Sem exposição ao varejo PF: não sofre com inadimplência de cartão, crédito pessoal ou PME de baixa renda<br>✦ Funding internacional (via Arab Banking Corp) com custo menor que captação doméstica — vantagem de spread<br>✦ Modelo de negócio simples, previsível e escalável — sem a complexidade operacional de um banco universal<br>✦ Alta correlação de receitas com o CDI: PL remunerado a CDI + margem com clientes = proteção natural em juro alto"},
        {"titulo": "Riscos principais", "texto": "⚠ Concentração: poucas carteiras grandes — uma inadimplência relevante pontual impacta mais que num banco pulverizado<br>⚠ Crescimento limitado: não tem varejo para escalar rapidamente — cresce no ritmo das empresas que serve<br>⚠ Controlador estrangeiro: decisões podem ser influenciadas por dinâmicas do Arab Banking Corporation<br>⚠ Exposição ao ciclo corporativo: recessão severa aumenta inadimplência mesmo no atacado"},
        {"titulo": "Barreira de entrada", "texto": "🔒 35 anos de relacionamento com o middle e large corporate brasileiro. Empresa de faturamento R$300 mi não troca de banco por conveniência — o relacionamento, o limite de crédito aprovado e as operações estruturadas em curso criam um lock-in real. Mais o funding árabe, que nenhum banco brasileiro vai replicar."},
    ],
    "ALOS3": [
        {"titulo": "Como funciona o negócio", "texto": "A Allos nasceu da fusão entre a Aliansce Shopping Centers e a Sonae Sierra Brasil em 2019, e foi renomeada em 2022 para refletir o reposicionamento estratégico. Com 44 shoppings e mais de 11.000 lojas, é o maior portfólio do Brasil em número de ativos. A estratégia é de escala e diversificação geográfica: presente em todas as regiões, com shoppings de médio e grande porte que atendem diferentes perfis de consumidor. Além do aluguel tradicional, a Allos tem dois vetores de crescimento adicionais: a Helloo (plataforma de mídia em shoppings — painéis, aeroportos, mídia digital), que cresce rápido e tem margens melhores que o aluguel; e um pipeline de expansão via ABL incremental nos shoppings existentes. Em 2026, o incêndio no Shopping Tijuca (janeiro) impactou ~6% da receita de aluguel temporariamente — o ativo operou com capacidade reduzida no 1T26."},
        {"titulo": "De onde vem a receita", "texto": "<b>~55% — Aluguel mínimo garantido:</b> base fixa dos contratos de locação, reajustada por IGP-M/IPCA<br><b>~20% — Aluguel variável (% das vendas):</b> percentual sobre vendas dos lojistas — cresce com SSS<br><b>~12% — Estacionamento e serviços:</b> receita de rotatividade e serviços aos lojistas<br><b>~8% — Helloo (mídia em shoppings e aeroportos):</b> crescimento acelerado; margens superiores ao aluguel<br><b>~5% — Cessão de direito e outros:</b> key money e receitas imobiliárias não recorrentes"},
        {"titulo": "Vantagens competitivas", "texto": "✦ 44 shoppings: maior diversificação geográfica do setor — nenhum ativo representa mais de 10% da receita<br>✦ Helloo: plataforma de mídia em crescimento com margens superiores ao aluguel e receitas crescentes<br>✦ DY de ~9% em 2026: alta distribuição de FCL atrativa para investidores de renda<br>✦ Valuation com desconto (10x FFO) vs Multiplan — potencial de re-rating se qualidade do portfólio melhorar<br>✦ Recompras de ações ativas: programa de buyback aumenta o FFO por ação sem crescimento operacional"},
        {"titulo": "Riscos principais", "texto": "⚠ Portfólio de qualidade média: 58% da receita vem de shoppings com vendas < R$1 bi/ano<br>⚠ Incêndio no Tijuca (jan/2026): impacto temporário mas real de ~6% da receita<br>⚠ Selic alta comprime o valuation: shopping é ativo de duration longa — taxa de desconto importa<br>⚠ Conversão de 9,6%: menor poder de precificação vs Multiplan — lojistas pagam menos por real de venda<br>⚠ Integração ainda em andamento: fusão de 2019 ainda sendo otimizada em sistemas e processos"},
        {"titulo": "Barreira de entrada", "texto": "🔒 44 concessões em pontos estratégicos das cidades. Um shopping bem localizado é inreplicável — não se constrói outro no mesmo quarteirão. O custo de construção de um shopping novo (R$500 mi a R$2 bi) e o tempo de maturação (5-7 anos para atingir ocupação plena) criam uma barreira de entrada altíssima. A Helloo adiciona uma barreira de rede: 44 shoppings + aeroportos criam escala de mídia que anunciantes pagam prêmio para acessar."},
    ],
    "ALUP11": [
        {"titulo": "Como funciona o negócio", "texto": "A Alupar é uma holding privada de controle nacional que opera transmissão e geração no Brasil e na América Latina. No Brasil, detém 9.576 km de linhas de transmissão em 42 sistemas — a terceira maior transmissora privada do país em RAP. No exterior, opera no Peru (6 projetos de transmissão + 1 PCH), na Colômbia (PCH Morro Azul + 2 transmissoras, incluindo concessão VITALÍCIA) e no Chile. O modelo é transmissão como core (~75% do EBITDA, RAP previsível) complementado por geração (4 UHEs, 4 PCHs, 7 eólicos, 1 solar — 798 MW). A geração serve para complementar, não como motor principal. O grande diferencial: com 17% das receitas em USD após os projetos do Peru, a Alupar reduz a exposição à regulação brasileira. Está em ciclo pesado de capex (R$9 bi no ciclo atual), o que comprime o DY hoje mas cria o pipeline de crescimento para os próximos 5-7 anos."},
        {"titulo": "De onde vem a receita", "texto": "<b>~65% — RAP de transmissão Brasil:</b> 42 sistemas; IPCA e IGPM; projetos entrando até 2029<br><b>~20% — Geração renovável Brasil:</b> hídrica, eólica, PCH, solar — 798 MW; PPAs de longo prazo<br><b>~15% — Transmissão e geração América Latina:</b> Peru, Colômbia, Chile — crescente; parte em USD"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Controle 100% nacional: fundadores operam e são donos — alinhamento total de interesses<br>✦ Concessão vitalícia na Colômbia: ativo único no setor — RAP sem prazo de vencimento<br>✦ Expansão em USD (Peru): hedge natural contra depreciação do real<br>✦ Pipeline de entrada operacional: projetos entram até 2029 gerando RAP incremental<br>✦ TIR real implícita de ~8,1%: superior à Taesa (~4,7%) e próxima da ISA (~7,7%)"},
        {"titulo": "Riscos principais", "texto": "⚠ Alavancagem em pico de ~4x: capex de R$9 bi nos próximos anos pressiona o balanço<br>⚠ Risco regulatório externo: Peru, Colômbia e Chile têm marcos menos previsíveis que o Brasil<br>⚠ DY atual baixo (~3%): ciclo de capex comprime dividendo; investidor de renda pode se frustrar<br>⚠ Curtailment na geração eólica: afeta receita do segmento de geração<br>⚠ Execução simultânea: 12 projetos em andamento, 9 fora do Brasil — gestão complexa"},
        {"titulo": "Barreira de entrada", "texto": "🔒 Concessões de 30 anos — e na Colômbia, vitalícia. A capacidade de executar transmissão em países com regulação distinta é expertise que poucos têm e que anos de presença no exterior constroem. A escala de 9.576 km de linhas abre portas em leilões onde operadores menores não conseguem participar. E o controle familiar alinhado garante que o retorno ao acionista é o objetivo, não objetivos políticos."},
    ],
    "AXIA3": [
        {"titulo": "Como funciona o negócio", "texto": "A Axia é a antiga Eletrobras — a maior empresa do setor elétrico brasileiro, com cerca de 30 GW de capacidade instalada e participação em dezenas de concessões de geração e transmissão. A privatização de 2022 foi o maior evento do setor em décadas, mas a transição ainda está sendo digerida. O portfólio tem uma peculiaridade: parte significativa das usinas opera em 'regime de cotas' — um modelo regulatório onde a energia é dividida entre distribuidoras a preço fixo, tirando a geração do mercado livre. O processo de 'descotização' (sair das cotas) está em andamento mas é lento, o que significa que o portfólio ainda é menos lucrativo do que poderia ser. Em 2025 concluiu a migração para o Novo Mercado da B3, simplificou a estrutura acionária e iniciou a venda de ativos não-estratégicos — são os primeiros sinais de que a gestão privada está gerando valor."},
        {"titulo": "De onde vem a receita", "texto": "<b>~50% — Geração hídrica em cotas:</b> preço regulado; menos lucrativo que o mercado livre<br><b>~30% — Geração hídrica em ACL (mercado livre):</b> preço de mercado — potencial de crescimento com descotização<br><b>~15% — Transmissão (RAP):</b> concessões de transmissão em diversas regiões<br><b>~5% — Outros (comercialização, participações):</b> "},
        {"titulo": "Vantagens competitivas", "texto": "✦ Maior empresa do setor — presença em praticamente todos os grandes projetos hídricos do Brasil<br>✦ TIR real implícita de ~10%: bem acima de pares de transmissão (~7-8%)<br>✦ Descotização: cada usina que sai das cotas entra no mercado livre a preço melhor — upside de longo prazo<br>✦ Novo Mercado: governança melhorando, estrutura acionária simplificada<br>✦ Custo de geração entre os mais baixos do mundo (hídrica velha = sem depreciação relevante)"},
        {"titulo": "Riscos principais", "texto": "⚠ Risco político: governo ainda questiona aspectos do acordo de privatização; risco de revisão de termos<br>⚠ Portfólio mais descontratado: menos energia comprometida em contratos de longo prazo vs pares<br>⚠ Descotização é lenta: upside real ainda depende de decisões regulatórias e políticas<br>⚠ Complexidade: dezenas de subsidiárias, concessões e participações — difícil de analisar<br>⚠ GSF: maior exposição hídrica do setor = mais vulnerável à seca"},
        {"titulo": "Barreira de entrada", "texto": "🔒 São décadas de concessões hídrica em rios que já foram inventariados — Tucuruí, Balbina, Itaipu (participação), Angra (nuclear): ativos que jamais serão licenciados de novo. A escala de 30 GW e o papel sistêmico no SIN (o ONS não opera sem a Axia) criam uma barreira que é, na prática, o próprio Brasil."},
    ],
    "BBAS3": [
        {"titulo": "Como funciona o negócio", "texto": "O BB tem três pilares que nenhum banco privado consegue replicar: o crédito rural (53% do crédito agro brasileiro passa pelo BB, com funding subsidiado via FCO e PRONAF), o funcionalismo público (processa metade das folhas do setor público federal e estadual — base de consignado captiva), e o Tesouro Nacional (agente financeiro do governo federal). Fora isso, é um banco universal com seguros (BB Seguridade, controlada listada separadamente) e gestão de ativos. O problema de 2025-2026 é exatamente essa concentração: o agro sofreu com El Niño, preços baixos de grãos e endividamento acumulado. A inadimplência rural saltou de 1% para 6%, o lucro caiu 54% no 1T26 e o ROE colapsou para 7,3%. A BB Seguridade, contudo, continua entregando — o banco dentro do banco que o mercado frequentemente esquece."},
        {"titulo": "De onde vem a receita", "texto": "<b>~45% — Margem financeira (NII):</b> crédito rural + consignado + corporate<br><b>~20% — BB Seguridade (resultado de equivalência patrimonial):</b> seguros, previdência e capitalização<br><b>~20% — Receitas de serviços e tarifas:</b> folha de pagamento, asset management, tarifas<br><b>~15% — Tesouraria e mercado:</b> títulos públicos e operações com o governo"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Monopólio prático no crédito agro — nenhum banco privado tem a rede, o funding subsidiado e a expertise<br>✦ Folha do setor público: base captiva de consignado com inadimplência próxima de zero<br>✦ BB Seguridade: motor de resultado capital-light e recorrente dentro do conglomerado<br>✦ Valuation de desconto (P/L ~4x, P/VP ~0,6x) embute a percepção de risco estatal<br>✦ Gestão de ativos: 24,9% de market share — o maior gestor de recursos do Brasil"},
        {"titulo": "Riscos principais", "texto": "⚠ Interferência política: governo pode forçar crédito subsidiado, reduzir spread e comprometer rentabilidade<br>⚠ Concentração no agro: ciclos negativos (clima, preço de commodities) impactam desproporcionalmente<br>⚠ Inadimplência rural 2025-2026: ainda longe do pico — pode demorar 2-3 anos para normalizar<br>⚠ Menor eficiência operacional que bancos privados — custo de servir é mais alto"},
        {"titulo": "Barreira de entrada", "texto": "🔒 O acesso ao funding subsidiado (FCO, PRONAF, recursos do Tesouro) é uma barreira que nenhum banco privado pode replicar. Quem financia agricultura a taxa de 7-8% a.a. quando o custo de mercado é 14%+ está usando um subsídio que só o banco estatal acessa. Isso cria uma vantagem competitiva no agro que é, literalmente, impossível de replicar sem ser banco público."},
    ],
    "BBDC3": [
        {"titulo": "Como funciona o negócio", "texto": "O Bradesco é o único entre os grandes privados que foi construído de dentro para fora do Brasil — nasceu em Marília (SP) e cresceu pelo interior antes de chegar às capitais. Essa origem explica sua exposição à massa e às PMEs do interior, que são mais vulneráveis a ciclos de juros altos. Em 2022-2024, o banco pagou o preço: inadimplência subindo, provisões estourando, ROE colapsando para abaixo do custo de capital. A reestruturação de Marcelo Noronha (CEO desde 2023) levou o banco a ser mais seletivo no crédito, a fechar agências, digitalizar e focar em alta renda e crédito com garantia. O resultado começou a aparecer em 2025: lucro crescendo, ROE recuperando, ação subindo 60% no ano. Em 2026, a tese é de quanto esse ROE ainda pode subir — e se chegará ao nível de Itaú, ou ficará estacionado nos 15-17%."},
        {"titulo": "De onde vem a receita", "texto": "<b>~50% — Margem financeira (NII):</b> spread de crédito PF + PME + corporativo<br><b>~20% — Seguros (Bradesco Seguros):</b> vida, saúde, automóvel — joint venture com Munich Re<br><b>~18% — Receitas de serviços e tarifas:</b> cartão, previdência, corretagem<br><b>~12% — Outros:</b> mercado de capitais, câmbio, gestão de ativos"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Bradesco Seguros: uma das maiores seguradoras do Brasil — negócio capital-light com margens altas<br>✦ Rede capilar no interior: presença onde grandes bancos e fintechs chegam com mais dificuldade<br>✦ Reestruturação em curso: se o ROE normalizar para 18-20%, o valuation atual (P/L ~6x) está barato<br>✦ Cielo integrada: adquirência + produtos bancários criam potencial de cross-sell"},
        {"titulo": "Riscos principais", "texto": "⚠ Execução: a reestruturação pode demorar mais ou entregar menos que o prometido<br>⚠ Concorrência de fintechs no varejo massificado — o segmento que o Bradesco depende mais<br>⚠ Exposição residual à massa de baixa renda, mais sensível a inadimplência em juro alto<br>⚠ Valuation não é mais óbvio — após alta de 60% em 2025, o desconto já fechou parcialmente"},
        {"titulo": "Barreira de entrada", "texto": "🔒 A rede de distribuição no interior do Brasil é o ativo mais difícil de replicar. Cidades de 30.000 habitantes onde o Bradesco é o único banco presente — e onde a fintech não chega sem agência ou correspondente. Mais a Bradesco Seguros, que tem escala e relacionamento de décadas com corretores."},
    ],
    "BBSE3": [
        {"titulo": "Como funciona o negócio", "texto": "A BB Seguridade não assume risco de seguro. Ela distribui seguros, previdência e capitalização pela rede do Banco do Brasil — 70 milhões de clientes, mais de 3.500 pontos de atendimento — e cobra comissão. O risco de sinistro fica com os parceiros: Mapfre (seguros, JV 74,9% BB + 25,1% Mapfre) e Principal Financial Group (previdência, via Brasilprev). Estrutura capital-light com payout de ~85% — não precisa reter capital para cobrir sinistros. O resultado tem dois motores: operacional (prêmios, corretagem, sinistralidade das parceiras) e financeiro (reservas técnicas da Brasilprev e Brasilcap investidas na Selic). Em juro alto o segundo motor turbina o lucro: no 1T26 foi +58,5% a/a e representou 23% do total. O detalhe que muda tudo: o contrato de distribuição com o BB vai até 2033. O mercado desconta esse risco no valuation — e o P/L de 8x vs. 13-14x histórico do mercado é basicamente o 'preço' que o investidor paga pela incerteza de renovação."},
        {"titulo": "De onde vem a receita", "texto": "<b>~40% — Corretagem e distribuição (BB Corretora):</b> comissão sobre todos os produtos vendidos pela rede BB<br><b>~25% — Previdência (BrasilPrev):</b> taxa de gestão + resultado financeiro das reservas PGBL/VGBL — turbinado pela Selic<br><b>~14% — Seguros rurais (Brasilseg):</b> maior linha individual; sensível ao agro, El Niño e inadimplência rural<br><b>~17% — Seguros vida e prestamista (Brasilseg):</b> prestamista ligado ao consignado — sofre com juro alto; vida é base estável<br><b>~4% — Capitalização (Brasilcap):</b> títulos de capitalização — beneficiado pela Selic alta"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Modelo capital-light: não assume risco de sinistro → payout de 85% → DY de 11-12%<br>✦ Canal exclusivo com 70 milhões de clientes do BB — custo de aquisição praticamente zero<br>✦ Brasilprev: líder em previdência privada no Brasil; reservas crescendo 10% a/a<br>✦ Resultado financeiro expressivo: Selic alta turbina o float das reservas de previdência e capitalização<br>✦ P/L de 8x — desconto histórico vs. média do mercado (13-14x)"},
        {"titulo": "Riscos principais", "texto": "⚠ Contrato 2033: o acordo de distribuição com o BB vence daqui a ~7 anos — renovação, condições e custo são incertos; é o maior risco estrutural<br>⚠ Selic caindo: resultado financeiro (23% do lucro em 1T26) cai imediatamente; recuperação operacional leva trimestres<br>⚠ Seguro rural (~35% dos prêmios): El Niño, seca e inadimplência rural pressionaram a Brasilseg em 2024-2026<br>⚠ Prestamista em queda: ligado ao crédito consignado — juro alto reduz tomada de crédito e, com ela, o seguro<br>⚠ Guidance 2026 conservador: própria empresa projeta resultado operacional de -7% a -3% vs. 2025"},
        {"titulo": "Barreira de entrada", "texto": "🔒 O contrato de exclusividade com o BB e o tamanho da base de clientes são inreplicáveis. Nenhuma seguradora privada tem acesso a 70 milhões de clientes com custo de aquisição zero. Brasilprev é a maior gestora de previdência privada do Brasil — liderança construída em décadas. O problema é que toda essa vantagem depende de um contrato com o estado."},
    ],
    "BMGB4": [
        {"titulo": "Como funciona o negócio", "texto": "O BMG é o banco mais nichado desta lista: 88% da carteira de crédito é formada por aposentados e pensionistas do INSS. O produto central é o empréstimo consignado, onde as parcelas são descontadas diretamente do benefício do INSS — a inadimplência é estruturalmente baixa porque o pagador não é a pessoa, é o governo federal. A distribuição é feita por correspondentes bancários (terceiros que originam o crédito), lojas próprias 'help! Loja de Crédito' (na cor laranja, reconhecível pelo público), e canais digitais. O desafio é que o governo regula a taxa máxima (hoje 1,85%/mês para o empréstimo e 2,46%/mês para o cartão). Quando a Selic sobe, o custo de captação sobe, mas o teto de taxa não — o spread comprime. Em 2025-2026, a CPI do INSS investigando fraudes no consignado criou obrigação de biometria facial para cada contratação — adiciona fricção e pode frear a originação."},
        {"titulo": "De onde vem a receita", "texto": "<b>~55% — Empréstimo consignado INSS:</b> produto principal — taxa máxima 1,85%/mês<br><b>~25% — Cartão consignado INSS:</b> desconto direto no benefício — taxa máxima 2,46%/mês<br><b>~10% — Consignado privado (CLT):</b> iniciado em 2025 — menor escala, maior risco<br><b>~10% — Seguros e outros produtos:</b> Bmg Seguradora — vida, acidentes pessoais"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Inadimplência estruturalmente baixa: parcelas descontadas direto do INSS — o devedor não pode deixar de pagar<br>✦ Base de aposentados é demograficamente crescente — 35 milhões de beneficiários do INSS e crescendo<br>✦ Reconhecimento de marca no público INSS: a cor laranja é sinônimo de consignado no interior do Brasil<br>✦ Correspondentes bancários capilarizados onde bancos tradicionais não chegam"},
        {"titulo": "Riscos principais", "texto": "⚠ Teto regulatório de taxa: Selic sobe, mas o banco não consegue repassar — spread comprime estruturalmente<br>⚠ CPI do INSS e fraudes no consignado: biometria obrigatória adiciona fricção e pode reduzir origação<br>⚠ Concentração extrema em um segmento: qualquer mudança regulatória no consignado INSS impacta 88% da carteira<br>⚠ ROE limitado pelo teto de taxa: difícil escalar margem acima de 12-14% com spread comprimido<br>⚠ Consignado privado (CLT) em expansão — risco maior que o INSS, e o banco ainda está aprendendo o segmento"},
        {"titulo": "Barreira de entrada", "texto": "🔒 O reconhecimento de marca no público INSS e a rede de correspondentes são difíceis de replicar. O aposentado do interior que reconhece a loja laranja e confia no 'consignado BMG' não troca facilmente de banco. Além disso, os correspondentes que originam crédito têm relacionamentos de anos com o BMG — e comissões que constroem lealdade. A barreira não é tecnológica; é de relacionamento e presença física em regiões remotas."},
    ],
    "BPAC11": [
        {"titulo": "Como funciona o negócio", "texto": "O BTG é estruturalmente diferente dos outros: não tem agência, não quer o cliente de massa, não cresce emprestando para pessoa física no cartão. Ele ganha dinheiro sendo o intermediário entre quem tem capital (grandes fortunas, fundos) e quem precisa de capital (grandes empresas, governos). A receita tem seis pilares: corporate lending (crédito para grandes empresas, ~R$2,3 bi/tri), sales & trading (mesa proprietária e corretagem institucional), investment banking (IPOs, M&As, emissões), asset management (R$2,5 tri sob gestão/administração), wealth management (R$1,28 tri — clientes private) e consumer finance (Banco PAN + Too Seguros, consignado privado). No 1T26 entregou lucro de R$4,8 bi (+42% a/a) e ROAE de 26,6%. O modelo de partnership (sócios compram ações — alinhamento total) é um diferencial cultural único."},
        {"titulo": "De onde vem a receita", "texto": "<b>~23% — Corporate Lending:</b> crédito corporativo de alta qualidade — crescimento de 22% a/a<br><b>~15% — Wealth Management:</b> R$ 1,28 tri sob gestão — crescimento recorde<br><b>~19% — Sales & Trading:</b> mesa proprietária + corretagem institucional — volátil<br><b>~12% — Asset Management:</b> R$ 2,5 tri total — taxas de gestão e performance<br><b>~11% — Consumer Finance & Banking:</b> Banco PAN + Too Seguros — consignado privado<br><b>~10% — Investment Banking:</b> IPOs, M&As, emissões de dívida — cíclico<br><b>~10% — Outros (juros e outros):</b> "},
        {"titulo": "Vantagens competitivas", "texto": "✦ Modelo de partnership: sócios são donos — incentivos alinhados, execução consistente há 40 anos<br>✦ Wealth Management: R$1,28 tri em assets com crescimento de 44,6% a/a — receita recorrente e crescente<br>✦ Corporate Lending: inadimplência próxima de zero em crédito para grandes empresas com garantias robustas<br>✦ Marca BTG no mercado de capitais: quando uma empresa quer captar R$1 bi+, o BTG está na lista curta<br>✦ Único entre os grandes a ter ROE acima de 26% de forma sustentada"},
        {"titulo": "Riscos principais", "texto": "⚠ Valuation elevado (P/VP ~9x) não tolera desaceleração — crescimento tem que ser entregue<br>⚠ Investment banking é cíclico — em mercados fechados (sem IPOs, sem M&A), essa linha murcha<br>⚠ Dividend yield baixo (~2%) — não é banco de renda; é banco de crescimento e reinvestimento<br>⚠ Risco-chave concentrado em poucos sócios-chave — risco de sucessão no longo prazo"},
        {"titulo": "Barreira de entrada", "texto": "🔒 A marca e o relacionamento de décadas com os grandes CEOs e CFOs do Brasil. Não é possível construir isso da noite para o dia. Quando a Vale vai emitir uma debênture ou o governo quer estruturar um projeto de infraestrutura, o BTG está na mesa. Isso vem de 40 anos de execução impecável e de uma cultura de partnership que atrai os melhores profissionais do mercado financeiro."},
    ],
    "BRAP4": [
        {"titulo": "Como funciona o negócio", "texto": "A Bradespar é uma holding de participações controlada pelo banco Bradesco. Seu único ativo relevante é uma participação de ~4,5% na Vale. Não opera mina, não tem receita operacional, não tem funcionários de mineração. O resultado é o dividendo recebido da Vale, menos as despesas da holding. A tese de investimento é simples: a Bradespar negocia com desconto de NAV (valor de mercado < valor das ações da Vale que ela possui). Por que o desconto existe? Custos da holding, liquidez menor que a Vale, risco de governança (Bradesco decide o que fazer com a participação) e impostos sobre o dividendo ao longo da cadeia. Quando o desconto se fecha — por buyback, venda de ações ou elevação do dividendo — o acionista da Bradespar captura um retorno extra além da variação da Vale."},
        {"titulo": "De onde vem a receita", "texto": "<b>~95% — Dividendos e JCP da Vale:</b> proporcional à participação de ~4,5% e ao dividendo declarado pela Vale<br><b>~5% — Resultado financeiro e outros:</b> caixa próprio aplicado em renda fixa"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Desconto de NAV: comprar Bradespar = comprar Vale mais barato que o mercado<br>✦ DY amplificado pelo desconto: o yield efetivo sobre o NAV é maior que comprar Vale direto<br>✦ Exposição indireta ao cobre/níquel via Vale: tese de transição energética embutida<br>✦ Simplicidade: não tem risco operacional, ambiental nem de produção — só participação financeira"},
        {"titulo": "Riscos principais", "texto": "⚠ Desconto de NAV pode persistir ou ampliar: holding costuma negociar com desconto estrutural<br>⚠ Custos da holding corroem o NAV: despesas administrativas e impostos reduzem o retorno líquido<br>⚠ Decisão do Bradesco: controlador pode vender a participação na Vale em momento ruim<br>⚠ Dupla tributação: dividendo da Vale → Bradespar → acionista tem mais um passo tributário<br>⚠ Liquidez menor que Vale: spread bid/ask maior; mais difícil de sair em momentos de estresse"},
        {"titulo": "Barreira de entrada", "texto": "🔒 A barreira da Bradespar é o próprio desconto de NAV — quem quer comprar Vale com desconto precisa comprar a Bradespar. Mas não é uma barreira de negócio: qualquer um pode comprar Vale diretamente. A tese funciona enquanto o desconto existir e enquanto a Vale pagar dividendos. Se o desconto fechar, a vantagem da Bradespar desaparece."},
    ],
    "BRAV3": [
        {"titulo": "Como funciona o negócio", "texto": "A Brava Energia nasceu em setembro de 2024 da fusão entre a 3R Petroleum (campos maduros onshore e offshore) e a Enauta (campo de Atlanta). Atlanta é o ativo premium da empresa: óleo leve de altíssima qualidade, offshore no Espírito Santo, com menor desconto no Brent. Os campos de Papa-Terra (óleo pesado, Bacia de Campos) e de gás (Peroá e Manati, offshore) completam o portfólio. Em janeiro de 2026, comprou 50% de Tartaruga Verde e Espadarte por US$450 mi — campos operados pela Petrobras com 14 poços produtores e produção de ~55 kboed a 100%. Em maio de 2026, a Ecopetrol (estatal colombiana) lançou OPA para assumir 51% da empresa a R$23/ação (prêmio de até 28%). A operação aguarda aprovação do CADE e da ANP — e muda completamente o perfil de risco da empresa se concluída."},
        {"titulo": "De onde vem a receita", "texto": "<b>~35% — Atlanta (óleo leve offshore):</b> óleo premium; menor desconto vs Brent; principal ativo da Enauta<br><b>~25% — Papa-Terra (óleo pesado offshore):</b> FPSO P-63; óleo viscoso com maior desconto no Brent<br><b>~15% — Tartaruga Verde + Espadarte (novo):</b> 50% adquiridos em 2026; operado pela Petrobras; 14 poços<br><b>~15% — Gás natural (Peroá, Manati):</b> offshore ES/BA; escoamento via gasodutos<br><b>~10% — Campos onshore 3R:</b> herdados da 3R; menor prioridade estratégica"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Atlanta: óleo leve de alta qualidade — menor desconto vs Brent, maior preço realizado<br>✦ 2ª maior independente em reservas: escala que abre portas em desinvestimentos de grandes petroleiras<br>✦ OPA Ecopetrol a R$23: piso de preço no curto prazo com prêmio de 28%<br>✦ Tartaruga Verde: 14 poços produtores, operado pela Petrobras — produção previsível e já funcionando<br>✦ Diversificação de portfólio: onshore + offshore + gás + óleo leve + óleo pesado"},
        {"titulo": "Riscos principais", "texto": "⚠ Integração pós-fusão não provada: 3R e Enauta tinham culturas e sistemas operacionais distintos<br>⚠ Alavancagem alta: dívida da fusão + US$450 mi de Tartaruga Verde = balanço apertado<br>⚠ OPA Ecopetrol incerta: aprovação de CADE e ANP pode demorar ou não acontecer<br>⚠ Papa-Terra: óleo pesado = maior desconto no Brent e campo operacionalmente mais complexo<br>⚠ FCF neutro em 2026: alta produção, mas capex pesado e dívida consomem o caixa"},
        {"titulo": "Barreira de entrada", "texto": "🔒 Atlanta é o principal ativo de barreira — campo de óleo leve offshore que a Enauta levou anos para desenvolver e que poucos independentes conseguiriam financiar. O know-how da Enauta em desenvolvimento greenfield offshore é raro no Brasil fora da Petrobras. Mas a Brava ainda está construindo sua identidade pós-fusão — a barreira real ainda está sendo testada na execução."},
    ],
    "BRSR6": [
        {"titulo": "Como funciona o negócio", "texto": "O Banrisul é um banco estatal regional — o que significa que seu modelo de negócio é fundamentalmente diferente de todos os outros nesta lista. Ele existe porque o governo do RS quer um banco público estadual. O coração do negócio é a folha de pagamento dos servidores públicos gaúchos: 294 mil servidores ativos, inativos e pensionistas cujo salário passa pelo Banrisul, gerando uma base captiva de consignado, conta corrente e produtos financeiros. Em julho de 2026, renovou esse contrato por R$1,26 bi — pago à vista, reconhecido como intangível e amortizado ao longo de 5 anos. O custo dobrou em relação à renovação anterior (que era de 10 anos). Fora a folha, atende PMEs gaúchas e o varejo do RS. Toda a sua força e seu risco estão concentrados em um único estado."},
        {"titulo": "De onde vem a receita", "texto": "<b>~40% — Crédito consignado público (servidores RS):</b> base captiva da folha estadual<br><b>~35% — Varejo PF e PME gaúcha:</b> clientes pessoas físicas e pequenas empresas do RS<br><b>~15% — Receitas de serviços:</b> tarifas, previdência, seguros<br><b>~10% — Tesouraria:</b> títulos públicos e operações de mercado"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Base captiva de consignado público — 294 mil servidores estaduais com desconto em folha<br>✦ Valuation muito barato (P/VP ~0,5x, P/L ~3x) — desconta o risco político e o ROE baixo<br>✦ Dividend yield alto (~9-11%) — governo precisa do dividendo do banco para compor receitas estaduais<br>✦ Presença capilar no interior do RS onde os grandes bancos privados não chegam"},
        {"titulo": "Riscos principais", "texto": "⚠ 100% concentrado no RS — enchentes, seca, recessão regional batem direto no resultado<br>⚠ Dependência do contrato de folha: renovado a custo crescente (dobrou por ano de contrato na última renovação)<br>⚠ ROE cronicamente baixo (~7-9%) — estruturalmente abaixo do custo de capital<br>⚠ Risco político: troca de governo estadual pode mudar a relação ou condições do contrato<br>⚠ Qualidade de crédito pressionada em PF e PME, com inadimplência subindo em 2026"},
        {"titulo": "Barreira de entrada", "texto": "🔒 O contrato com o governo do RS é a barreira — e também o risco. Nenhum banco privado vai entrar no estado para fazer o que o Banrisul faz sem o benefício do funding barato do servidor e a capilaridade de 500+ agências no interior. Mas essa barreira tem preço: R$1,26 bi a cada 5 anos só para manter o que já tem."},
    ],
    "CMIG4": [
        {"titulo": "Como funciona o negócio", "texto": "A Cemig é uma holding integrada — opera distribuição (Cemig D), geração e transmissão (Cemig GT) e tem participações em outras empresas do setor. É a maior distribuidora do Brasil em número de municípios atendidos e a quarta em transmissão. Controlada pelo Estado de Minas Gerais (50,97% das ONs), sofre com o conflito clássico do estatal: o governo quer dividendos para fechar as contas do estado, mas também quer tarifas baixas para os eleitores. Em 2025, gerou discussão sobre possível federalização como parte do acordo da dívida de MG com o governo federal — um risco que assusta o mercado mas ainda não se concretizou."},
        {"titulo": "De onde vem a receita", "texto": "<b>~55% — Distribuição Minas Gerais (Cemig D):</b> maior distribuidora do Brasil em cobertura geográfica<br><b>~30% — Geração hídrica e eólica (Cemig GT):</b> portfólio diversificado, mas com exposição hídrica<br><b>~10% — Transmissão:</b> 4ª maior do Brasil<br><b>~5% — Participações e comercialização:</b> "},
        {"titulo": "Vantagens competitivas", "texto": "✦ Escala: maior distribuidora em municípios atendidos — MG tem 853 municípios<br>✦ DY alto (8-12%): governo precisa de dividendo para fechar as contas do estado<br>✦ Valuation descontado pelo risco político: quem acredita no desconto pode se beneficiar<br>✦ Portfólio diversificado: geração + transmissão + distribuição reduz concentração em um segmento"},
        {"titulo": "Riscos principais", "texto": "⚠ Risco político: governo MG intervém em gestão, tarifa e alocação de capital<br>⚠ Debate de federalização: dívida de MG com a União pode levar à transferência do controle<br>⚠ Posição vendida em energia: Cemig ficou descoberta em contratos de energia, gerando prejuízo<br>⚠ Alavancagem ~2,3-2,5x: não é crítico mas limita flexibilidade<br>⚠ Eficiência abaixo de privados: custo de servir mais alto por natureza estatal"},
        {"titulo": "Barreira de entrada", "texto": "🔒 A concessão de distribuição em Minas Gerais — o estado mais rico em recursos naturais e o terceiro maior estado em PIB do Brasil. O portfólio de usinas hidrelétricas em rios mineiros é inreplicável. O problema: a barreira é do Estado de MG, não da empresa — e o controlador pode usá-la para objetivos políticos em vez de econômicos."},
    ],
    "CMIN3": [
        {"titulo": "Como funciona o negócio", "texto": "A CSN Mineração é a operação de mineração da CSN (Companhia Siderúrgica Nacional), separada em empresa independente e aberta em IPO em 2021. Opera no Quadrilátero Ferrífero (MG), na mina Casa de Pedra — uma das maiores minas a céu aberto do Brasil. O modelo é simples e direto: extrai minério de ferro (62% Fe), transporta via MRS Logística até o Terminal de Carvão (TECAR) no Porto de Itaguaí (RJ) e exporta, principalmente para a China. Uma parte significativa do minério abastece a própria CSN (que produz aço e precisa de minério) — captivo interno com preço de mercado. Produziu recorde de 45,5 milhões de toneladas em 2025 (+4,6% acima do guidance). Custo C1 de US$23,1/t no 1T26 — competitivo, mas sem o prêmio de qualidade da Vale."},
        {"titulo": "De onde vem a receita", "texto": "<b>~70% — Exportação de minério de ferro (62% Fe):</b> China é o principal destino; preço benchmark 62% Fe CFR<br><b>~20% — Vendas para CSN (mercado interno):</b> captivo — a controladora usa o minério para produzir aço<br><b>~10% — Pelotas e outros produtos:</b> valor agregado sobre o minério bruto"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Custo C1 competitivo (~US$23/t): eficiência operacional que sustenta margem mesmo com minério deprimido<br>✦ Produção recorde em 2025: 45,5 mi t — prova de capacidade operacional crescente<br>✦ Logística integrada via MRS até Itaguaí: escoamento eficiente sem gargalo logístico<br>✦ Captivo interno (CSN): parte da receita não depende do mercado internacional<br>✦ Alavancagem baixa: balanço saudável que permite dividendos mesmo em ciclo fraco"},
        {"titulo": "Riscos principais", "texto": "⚠ Ferro puro sem diversificação: 100% do resultado depende do preço do minério 62% Fe<br>⚠ Sem prêmio de qualidade: vende ao benchmark — não tem o diferencial da Vale em Carajás<br>⚠ Controladora CSN (78%): conflito de interesse potencial — CSN pode extrair caixa da CMIN em detrimento de minoritários<br>⚠ Dependência da China: perfil de exportação muito concentrado no mercado asiático<br>⚠ FCF volátil: capex de crescimento e compras de minério de terceiros criam oscilações no caixa"},
        {"titulo": "Barreira de entrada", "texto": "🔒 Casa de Pedra é uma das maiores reservas de minério de ferro do Quadrilátero Ferrífero. Mas a barreira da CMIN é menor que a da Vale — o minério 62% Fe é mais padronizado e os produtores australianos (Rio Tinto, BHP) têm custo C1 de US$18-20/t, abaixo da CMIN. A barreira real é operacional: a logística via MRS + Itaguaí e a integração com a CSN criam um sistema que funciona há décadas e não é fácil de desmontar."},
    ],
    "CPFE3": [
        {"titulo": "Como funciona o negócio", "texto": "A CPFL é uma das maiores empresas do setor elétrico brasileiro, com presença em distribuição (14% do mercado nacional, 10,3 mi de clientes em 687 municípios), geração (4.411 MW, entre as maiores privadas) e transmissão. Controlada desde 2017 pela State Grid Corporation of China — a maior empresa de energia do mundo, atendendo 1,1 bilhão de pessoas. O controlador quer estabilidade e dividendos, não aventura: o plano de R$29,8 bi para 2025-2029 foca em modernizar a distribuição existente (R$24,7 bi em distribuição), não em crescer por aquisições agressivas. Em maio de 2026, renovou as concessões das três distribuidoras principais (CPFL Paulista, Piratininga, RGE) por mais 30 anos — uma redução relevante de risco de prazo que o mercado subestimou."},
        {"titulo": "De onde vem a receita", "texto": "<b>~65% — Distribuição de energia (CPFL Paulista, Piratininga, RGE, Santa Cruz):</b> 2ª maior distribuidora do Brasil em volume<br><b>~25% — Geração (hídrica + eólica + solar + biomassa):</b> 4.411 MW de capacidade instalada<br><b>~8% — Transmissão (CPFL Transmissão):</b> RAP de linhas de transmissão<br><b>~2% — Comercialização e serviços:</b> "},
        {"titulo": "Vantagens competitivas", "texto": "✦ Concessões renovadas por 30 anos em 2026: risco de prazo eliminado para as principais distribuidoras<br>✦ State Grid como controlador: acesso a capital barato (empréstimo em RMB do NDB), tecnologia chinesa e planejamento de longo prazo<br>✦ 2ª maior distribuidora em volume: escala que poucos concorrentes têm no Sudeste<br>✦ DY consistente de 8-9%: controlador quer dividendo; payout de 78% é sustentável<br>✦ Gestão operacional eficiente: CPFL tem histórico de índices de qualidade acima da média do setor"},
        {"titulo": "Riscos principais", "texto": "⚠ Controlador chinês: geopolítica pode criar ruído regulatório ou político no futuro<br>⚠ Revisão tarifária: WACC regulatório da ANEEL define a rentabilidade da distribuição — risco periódico<br>⚠ Alavancagem moderada e capex de R$29,8 bi: FCF comprometido para crescimento, não para DY extra<br>⚠ Exposição ao Sudeste: crescimento da GD (painéis solares) pode reduzir consumo faturado das distribuidoras<br>⚠ Mercado Livre: migração de grandes clientes para ACL reduz base de consumidores cativos"},
        {"titulo": "Barreira de entrada", "texto": "🔒 687 municípios com concessão exclusiva de distribuição no Sudeste e Sul. Nenhum concorrente entra nesse território — a concessão é de 30 anos, renovada. A combinação de escala, capilaridade e o apoio da maior empresa de energia do mundo como controlador cria uma posição que é inatingível por qualquer novo entrante."},
    ],
    "CPLE3": [
        {"titulo": "Como funciona o negócio", "texto": "A Copel é a empresa integrada de energia do Paraná — geração (hídrica no rio Iguaçu e afluentes), transmissão e distribuição. Em 2023, foi privatizada pelo governo do Paraná, encerrando 70 anos como estatal. A privatização abriu espaço para buscar eficiência operacional, reduzir custos e orientar a gestão para retorno ao acionista em vez de objetivos políticos. Diferente da Cemig (que ainda é estatal), a Copel já não tem o risco de interferência política do governo. Mas ainda está no processo de ajuste pós-privatização: normalização do resultado financeiro, revisão de contratos e alinhamento da cultura organizacional ao modelo privado leva tempo."},
        {"titulo": "De onde vem a receita", "texto": "<b>~55% — Distribuição Paraná (Copel DIS):</b> distribuição regulada em todo o estado do Paraná<br><b>~30% — Geração hídrica + eólica (Copel GeT):</b> Iguaçu, Jordão e complexos eólicos<br><b>~12% — Transmissão (Copel Transmissão):</b> RAP de linhas em todo o Brasil<br><b>~3% — Telecomunicações (Copel Telecom):</b> fibra óptica no Paraná — diferencial único"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Privatização recente: gestão privada ainda capturando eficiência que o estado não priorizou<br>✦ Única utility listada com braço de telecom próprio: Copel Telecom é diferencial raro no setor<br>✦ Paraná: estado com melhor qualidade de crédito e menor inadimplência do Brasil — base de consumidores sólida<br>✦ Geração hídrica no Iguaçu: hidrologia de boa qualidade no Sul (diferente do Sudeste/Nordeste)"},
        {"titulo": "Riscos principais", "texto": "⚠ Resultado pós-privatização ainda normalizando: curva de aprendizado da gestão privada<br>⚠ Alavancagem: ciclo de investimentos pós-privatização pressiona o balanço<br>⚠ Hidrologia Sul: enchentes no RS/SC em 2024 mostraram que o Sul também tem risco climático<br>⚠ Copel Telecom: negócio diferente do core elétrico, exige expertise e capex específicos"},
        {"titulo": "Barreira de entrada", "texto": "🔒 Concessão exclusiva de distribuição em todo o Paraná — um estado de 11 mi de habitantes e PIB relevante. As usinas do rio Iguaçu são um dos maiores sistemas hídricos do Sul e são inreplicáveis. A rede de transmissão de fibra óptica da Copel Telecom seria levada décadas para ser construída por qualquer entrante. Pós-privatização, o risco de interferência política foi eliminado — a barreira ficou mais limpa."},
    ],
    "CSMG3": [
        {"titulo": "Como funciona o negócio", "texto": "A Copasa atende Minas Gerais — o maior estado do Brasil em extensão territorial, com importantes economias agropecuária, industrial e mineral. Em junho de 2026, o governo de MG concluiu a privatização: a Equatorial assumiu ~30% como investidora de referência, em operação estimada em R$8-10 bi. O diferencial estrutural da Copasa vs Sabesp: o WACC regulatório. A ARSAE (agência mineira) fixou WACC real de ~9,42% vs ~7,86% da ARSESP. Isso significa que MG remunera cada real de ativo regulatório a uma taxa 20% maior que São Paulo — mesmo com BRR menor, a rentabilidade por real investido é superior. O playbook é idêntico ao da Sabesp: turnaround operacional (EBITDA projetado de R$3,5 bi em 2026 para R$6,1 bi em 2028, CAGR de 30%+), aceleração de capex (R$3,1 bi em 2026 a R$4,5 bi em 2030) e crescimento da BRR de R$15,5 bi para R$36+ bi até 2030."},
        {"titulo": "De onde vem a receita", "texto": "<b>~60% — Água — tarifa regulada (ARSAE/MG):</b> abastecimento em MG; 3ª revisão tarifária com reajuste de 6,56% em 2026<br><b>~38% — Esgoto — tarifa regulada:</b> cobertura de esgoto ainda abaixo da média nacional — maior espaço de crescimento<br><b>~2% — Resíduos e outros:</b> coleta e tratamento de resíduos industriais; serviços complementares"},
        {"titulo": "Vantagens competitivas", "texto": "✦ WACC regulatório de 9,42% real: 20% maior que Sabesp — maior retorno por real de ativo reconhecido<br>✦ Maior crescimento relativo da BRR: de R$15,5 bi para R$36 bi até 2030 (vs crescimento proporcionalmente menor da Sabesp)<br>✦ Mesmo controlador da Sabesp: Equatorial com playbook comprovado — menos incerteza de execução<br>✦ Valuation ainda atrativo: ação subiu 126% em 12 meses mas ainda negocia abaixo de pares privatizados equivalentes<br>✦ MG tem grande déficit de esgoto: enorme runway de universalização = décadas de crescimento da BRR"},
        {"titulo": "Riscos principais", "texto": "⚠ Turnaround ainda no início: privatização concluída em junho — ganhos de eficiência ainda a capturar<br>⚠ Concessionamento de BH: renovação do contrato com Belo Horizonte foi condição da privatização — qualquer ajuste impacta a base<br>⚠ Regulação mineira: ARSAE pode ser mais conservadora que ARSESP no reconhecimento de investimentos<br>⚠ Risco político residual: Estado de MG retém 5% + golden share — ainda pode interferir em decisões estratégicas<br>⚠ Valuation precificou boa parte: ação já subiu muito com expectativa de privatização; execução precisa corresponder"},
        {"titulo": "Barreira de entrada", "texto": "🔒 Monopólio regulado em Minas Gerais — mesmo modelo da Sabesp. Mas a Copasa tem uma vantagem adicional: o WACC mais alto da ARSAE cria uma 'vantagem regulatória' estrutural que não depende de gestão, mas de metodologia da agência. E com a Equatorial como controladora — que já provou em 7 distribuidoras de energia que consegue transformar ativos ineficientes em geradores de valor — a tese de turnaround tem o executor mais credenciado do setor."},
    ],
    "CURY3": [
        {"titulo": "Como funciona o negócio", "texto": "A Cury é uma das mais puras histórias de foco do mercado imobiliário brasileiro. Em 63 anos de história, atua quase exclusivamente no MCMV — em São Paulo e Rio de Janeiro metropolitano, nas faixas mais altas do programa. O modelo tem três vantagens estruturais que se reforçam mutuamente. Primeiro, o crédito: FGTS a 4-10,5% ao ano não muda com a Selic — quando o mercado de médio padrão desacelera, a Cury continua vendendo. Segundo, a localização: empreendimentos em áreas centrais próximas a metrô e serviços, diferente de concorrentes que vão para a periferia mais barata. Terceiro, o método construtivo: alvenaria estrutural (blocos de concreto) permite flexibilidade de planta, custo controlado e velocidade de entrega. O resultado: ROE de 79,5% no 1T26 — o mais alto do setor — mesmo com caixa líquido positivo, o que demonstra que a geração de caixa é real, não alavancada. Entre 2020 e 2025, multiplicou receita em 5x, VGV em 5,5x e lucro em 5,7x."},
        {"titulo": "De onde vem a receita", "texto": "<b>~65% — MCMV faixas 2, 3 e 4 — São Paulo:</b> principal mercado; áreas centrais com transporte; ticket médio crescente<br><b>~35% — MCMV faixas 2, 3 e 4 — Rio de Janeiro:</b> segundo mercado; expansão acelerada nos últimos 3 anos"},
        {"titulo": "Vantagens competitivas", "texto": "✦ ROE de 79,5% (1T26) — o mais alto do setor, mesmo sendo caixa líquido positivo<br>✦ MCMV imune à Selic: crédito a 4-10,5% via FGTS não muda com a taxa de mercado<br>✦ Localização diferenciada: empreendimentos próximos ao metrô em SP/RJ — demanda captiva<br>✦ Landbank de R$24,9 bi com 3+ anos de visibilidade — crescimento previsível<br>✦ Velocidade de vendas (VSO) de 46% no 1T26 — a mais alta do setor"},
        {"titulo": "Riscos principais", "texto": "⚠ Zero diversificação: qualquer mudança nas regras do MCMV ou FGTS impacta 100% da receita<br>⚠ Concentração em SP e RJ: dois mercados, sem diversificação geográfica<br>⚠ Escassez de mão de obra: causou atrasos em obras em 2025; produtividade em recuperação em 2026<br>⚠ Sucessão executiva: modelo de Co-CEO anunciado em 2026 — transição de gestão é risco de curto prazo<br>⚠ Valuation esticado: P/L de 7-8x para uma empresa de MCMV é acima da média histórica do setor"},
        {"titulo": "Barreira de entrada", "texto": "🔒 63 anos construindo para o mesmo público no mesmo mercado. A Cury conhece cada zona de uso de São Paulo e Rio de Janeiro como ninguém. Sabe onde tem metro previsto, onde vai ter densificação, onde o terreno ainda está barato. Esse banco de dados de décadas de relacionamento com prefeituras, vendedores de terreno e a Caixa Econômica Federal é inreplicável. Qualquer entrante levaria anos para construir a rede de relacionamentos que permite a Cury comprar terreno antes do concorrente saber que está à venda."},
    ],
    "CXSE3": [
        {"titulo": "Como funciona o negócio", "texto": "A lógica da CXSE é idêntica à da BBSE: distribui seguros pela rede da Caixa Econômica Federal e recebe comissão sem assumir o risco de sinistro. Mas o produto-âncora é diferente — e mais defensivo. Todo financiamento imobiliário no Brasil exige por lei dois seguros obrigatórios: MIP (Morte e Invalidez) e DFI (Danos Físicos ao Imóvel). São embutidos na parcela e cobrados por 10 a 35 anos. Cada novo financiamento da Caixa (que detém mais de R$1 tri em carteira imobiliária) gera automaticamente mais um contrato de seguro que dura décadas — é o efeito empilhamento. A base de recorrência cresce enquanto os contratos antigos ainda estão ativos e os novos chegam. No 1T26 entregou lucro de ~R$1,14 bi (+ROE de 65,9%) e DY projetado de ~7-8% para 2026."},
        {"titulo": "De onde vem a receita", "texto": "<b>~55% — Seguro habitacional (MIP + DFI):</b> obrigatório por lei — base recorrente e crescente<br><b>~20% — Prestamista e vida:</b> seguro do crédito consignado e pessoal da Caixa<br><b>~15% — Previdência e capitalização:</b> produtos financeiros da rede Caixa<br><b>~10% — Residencial e outros:</b> seguros patrimoniais para clientes da Caixa"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Efeito empilhamento: cada financiamento gera contrato de 10-35 anos — recorrência que cresce automaticamente<br>✦ Seguro habitacional é obrigatório por lei — não há opção de 'não comprar' para quem financia<br>✦ Mais de 60% de market share em seguro habitacional — posição de dominância que nenhum concorrente replica<br>✦ Canal com 4.000 agências + 13.000 lotéricas — capilaridade ímpar para o público de menor renda<br>✦ ROE de 65,9% no 1T26 — extraordinário para qualquer empresa, de qualquer setor"},
        {"titulo": "Riscos principais", "texto": "⚠ 100% dependente da Caixa como canal e controladora — risco político estatal elevado<br>⚠ Prestamista pressionado: juros altos reduzem crédito consignado e pessoal<br>⚠ Resultado financeiro ajuda hoje (Selic alta), mas perde força quando os juros caírem<br>⚠ Valuation mais esticado que BBSE — P/L de 11-13x já precifica boa parte da qualidade<br>⚠ Qualquer mudança na política habitacional federal (FGTS, Minha Casa) impacta diretamente"},
        {"titulo": "Barreira de entrada", "texto": "🔒 A exclusividade com a Caixa + a lei que obriga o seguro habitacional = monopólio prático. Nenhuma seguradora privada consegue entrar nesse mercado sem ser o parceiro oficial da CEF. E o efeito empilhamento cria uma receita que cresce por décadas sem esforço de vendas adicional — é o modelo mais defensivo e previsível de toda a lista."},
    ],
    "CYRE3": [
        {"titulo": "Como funciona o negócio", "texto": "A Cyrela é a empresa mais complexa do setor listado. Opera com três marcas próprias (Cyrela para alto padrão, Living para médio, Vivaz para MCMV) e tem participação em cinco JVs listadas na B3 (Lavvi, Plano&Plano, Cury, entre outras). O core é o alto padrão em São Paulo — onde projetos de R$2+ bi de VGV como o Epic by Pininfarina (210 metros, maior residencial de SP) definem a marca. A estratégia funciona em ciclos de juros baixos: o comprador de luxo financia parte do imóvel, e com crédito barato aumenta o poder de compra. Em juros altos, o efeito inverte. Em 2026, os lançamentos de alto padrão caíram 71% — o mercado esperou. A Vivaz (MCMV) compensa parcialmente, mas com margem e ROE muito menores. As JVs listadas (especialmente Cury) criam valor que não aparece no P/L da Cyrela."},
        {"titulo": "De onde vem a receita", "texto": "<b>~51% — Alto padrão — marca Cyrela:</b> São Paulo; projetos icônicos de R$500 mil a R$5 mi por unidade<br><b>~23% — Médio padrão — marca Living:</b> classe média SP e outras praças; mais sensível à Selic<br><b>~26% — MCMV — marca Vivaz:</b> parceria com Caixa; crescendo para compensar o alto padrão"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Marca premium de 60 anos: 'Cyrela' é sinônimo de qualidade na cabeça do comprador de alto padrão em SP<br>✦ Projetos icônicos: Epic by Pininfarina (VGV R$2 bi) — não é construção, é obra de arte vendável<br>✦ JVs listadas (Cury, Lavvi): participação em empresas de alto crescimento que criam valor não precificado<br>✦ Diversificação de segmento: quando o alto padrão desacelera, Vivaz sustenta a operação<br>✦ Geração de caixa sólida: mesmo com ROE baixo, converte bem lucro em caixa"},
        {"titulo": "Riscos principais", "texto": "⚠ ROE de 11% no 1T26 — muito abaixo dos pares MCMV (Cury 79%, Direcional 44%)<br>⚠ Alto padrão sensível à Selic: lançamentos caíram 71% no 1T26 com juros altos<br>⚠ Concorrência crescente no luxo: JHSF, Lavvi e incorporadoras internacionais disputam o mesmo público<br>⚠ Vivaz com margem menor: o crescimento que compensa o alto padrão vem com ROE inferior<br>⚠ Mercado concentrado em SP: 60%+ do resultado vem de uma única praça"},
        {"titulo": "Barreira de entrada", "texto": "🔒 A marca Cyrela é a barreira — e é uma barreira cultural, não financeira. Um comprador que paga R$3 mi por um apartamento compra o endereço, o nome do arquiteto e o status da construtora. 60 anos construindo em São Paulo com qualidade consistente criam um ativo intangível que nenhum novo entrante replica em menos de duas décadas. E a carteira de JVs com incorporadoras de crescimento (Cury, Lavvi) cria um portfólio diversificado que o mercado ainda não precifica corretamente."},
    ],
    "DIRR3": [
        {"titulo": "Como funciona o negócio", "texto": "A Direcional tem um modelo operacional de eficiência industrial. Opera em dois segmentos: a marca Direcional (MCMV faixas 2 e 3 — baixa renda) e a marca Riva (médio-baixo padrão, apartamentos até R$500 mil — que passou a ser enquadrada no MCMV faixa 4 em 2026). Presente em 8 estados e no DF, é a maior construtora em área do Brasil. O que diferencia a Direcional dos concorrentes é a combinação de três fatores. Primeiro, o método construtivo industrializado com formas de alumínio — encurta o ciclo de obra, reduz desperdício e viabiliza escala nacional. Segundo, o modelo de permuta: 86% do landbank é adquirido via permuta — o terreno entra como pagamento de unidades futuras, sem desembolso de caixa. Terceiro, o crédito associativo: no MCMV, o risco de inadimplência transfere para o banco financiador na assinatura do contrato — a Direcional recebe sem risco de o comprador não pagar. No 1T26: receita de R$1,2 bi (+30% a/a), lucro de R$200 mi (+27%), margem bruta ajustada de 42,9% — a maior do setor."},
        {"titulo": "De onde vem a receita", "texto": "<b>~55% — Direcional (MCMV faixas 2 e 3):</b> 8 estados e DF; método industrializado; alta escala<br><b>~45% — Riva (médio-baixo, até R$500 mi):</b> enquadrada no MCMV faixa 4 em 2026; VGV +20% no 1T26"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Landbank de R$51,3 bi com 8+ anos de visibilidade — o maior do setor<br>✦ 86% do landbank via permuta: o maior banco de terrenos sem desembolso de caixa<br>✦ Formas de alumínio: método industrializado que reduz prazo de entrega e custo<br>✦ Riva na faixa 4 do MCMV: a subsidiária de médio padrão passou a ter acesso ao crédito subsidiado<br>✦ Maior construtora em área do Brasil — escala que gera poder de negociação com fornecedores"},
        {"titulo": "Riscos principais", "texto": "⚠ Concentração no MCMV: dependência do FGTS e do orçamento público habitacional<br>⚠ Riva sensível à Selic: crédito SBPE mais caro afeta clientes de médio padrão fora do MCMV<br>⚠ INCC pressionando: custo de construção acima da inflação desde 2025<br>⚠ Dois segmentos, dois riscos: gestão de marcas com públicos diferentes exige execução cuidadosa<br>⚠ Alavancagem subindo: geração de caixa sólida mas pagamento de R$804 mi em dividendos em 2025 elevou endividamento"},
        {"titulo": "Barreira de entrada", "texto": "🔒 40 anos de MCMV e o maior landbank do setor formam a barreira. Nenhum novo entrante consegue replicar R$51 bi de terrenos já aprovados e identificados em 8 estados sem anos de trabalho. As formas de alumínio (método construtivo industrializado) vieram de décadas de aprendizado operacional — não se compra só o equipamento, compra-se o know-how de como usá-lo com escala. E o relacionamento de 40 anos com prefeituras do interior do Brasil para aprovação de empreendimentos é impossível de acelerar."},
    ],
    "EGIE3": [
        {"titulo": "Como funciona o negócio", "texto": "A Engie Brasil é a maior empresa privada de geração de energia do país, com ~12,9 GW de capacidade instalada em 145 usinas. O portfólio é 100% renovável: hidrelétricas (~70%), eólicas, solares e biomassa. Além disso, é sócia da TAG — a maior malha de transporte de gás natural do Brasil, com 4.500 km em 10 estados. O modelo de receita combina PPAs (contratos de longo prazo, indexados ao IPCA) com exposição ao mercado livre (PLD spot). O desafio atual: curtailment crescente (26% projetado em 2026, 32% em 2027) — o ONS corta a geração renovável em momentos de sobreoferta. A estratégia de resposta é migrar parte do portfólio para transmissão, que gera RAP previsível e não sofre curtailment. Em 2025, venceu lotes de transmissão nos leilões da ANEEL — a diversificação está em andamento."},
        {"titulo": "De onde vem a receita", "texto": "<b>~60% — PPAs de longo prazo (geração hídrica + eólica):</b> contratos indexados ao IPCA com distribuidoras e grandes consumidores<br><b>~20% — TAG (transporte de gás, participação ~32%):</b> RAP regulada — receita previsível, sem exposição a preço de gás<br><b>~15% — Mercado livre de energia (ACL):</b> preço spot variável — mais volátil<br><b>~5% — Transmissão nascente + outros:</b> RAP de novos projetos em construção (Asa Branca, Graúna)"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Controladora Engie (França): acesso a tecnologia, capital barato e modelo global de energia renovável<br>✦ TAG: ativo de transmissão de gás com receita regulada — reduz a volatilidade da geração<br>✦ 100% renovável: posicionamento ESG premium para contratos com multinacionais exigentes<br>✦ Maior geradora privada: escala garante acesso aos melhores PPAs e aos maiores leilões<br>✦ Expansão em transmissão: diversifica para ativos de menor volatilidade"},
        {"titulo": "Riscos principais", "texto": "⚠ Curtailment: 26-32% projetado para 2026-2027 — energia produzida mas não vendida<br>⚠ Dependência hídrica (~70%): secas ou GSF negativo afetam diretamente a geração<br>⚠ Ciclo de capex pesado: Jirau, Asa Branca, Graúna — R$6 bi investidos em 2025 pressionam o FCF<br>⚠ Payout reduzido para mínimo de 55% no ciclo de capex — DY caiu vs histórico<br>⚠ Selic alta + alavancagem acima de 2,5x: pressão financeira em ciclo de investimento"},
        {"titulo": "Barreira de entrada", "texto": "🔒 Concessões hidrelétricas são praticamente inreplicáveis — os melhores rios já têm dono. Quem tem Itá, Machadinho, Estreito e Jaguara tem ativos que não se licenciam mais hoje. A TAG é a única malha de transporte de gás em 10 estados — monopólio natural regulado. E a marca Engie com 30 anos no Brasil abre portas que novos entrantes levariam décadas para abrir."},
    ],
    "EQTL3": [
        {"titulo": "Como funciona o negócio", "texto": "A Equatorial não é uma distribuidora comum — é uma operadora especializada em turnaround de distribuidoras. O modelo é simples de explicar e difícil de executar: compra distribuidoras com altíssima inadimplência, furto e ineficiência (pagando barato por isso), reduz as perdas, melhora a cobrança, normativa os índices de qualidade e passa a extrair margem de uma operação que estava destruindo valor. Fez isso com a Eletrobras/CEMAR (Maranhão), com a CELPA (Pará), com a COELCE (Ceará), com a CELG-D (Goiás), com a CEA (Amapá) e com a CEPISA (Piauí). Cada aquisição foi uma aposta que o mercado duvidou e a Equatorial executou. Em 2025, entrou no saneamento (15% da Sabesp) e já tem posições em saneamento em outros estados. DY baixo porque reinveste quase tudo — mas valorização histórica é a melhor do setor por décadas."},
        {"titulo": "De onde vem a receita", "texto": "<b>~75% — Distribuição de energia (6 estados):</b> MA, PA, CE, GO, AP, PI — foco em Norte/Nordeste onde havia mais potencial<br><b>~15% — Saneamento (Sabesp 15% + outros):</b> novo vetor de crescimento — mesma lógica de turnaround<br><b>~10% — Geração, transmissão e telecom:</b> ativos complementares vendidos quando maduros"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Track record de turnaround: cada aquisição que o mercado duvidou, a Equatorial executou<br>✦ Gestão de perdas superior: reduz inadimplência e furto nos níveis que distribuidoras estatais nunca conseguiram<br>✦ Regiões de maior potencial: Norte e Nordeste têm mais espaço para redução de perdas que Sudeste já maduro<br>✦ Expansão em saneamento: a mesma lógica de turnaround aplicada a um setor ainda mais ineficiente<br>✦ TIR real de 11,1% implícita: premium justificado pelo histórico e pelo pipeline de crescimento"},
        {"titulo": "Riscos principais", "texto": "⚠ Alavancagem de 3,5x em fase de expansão — cada nova aquisição pressiona mais o balanço<br>⚠ Sabesp (15%): primeira entrada no saneamento de grande escala — execução ainda não provada<br>⚠ Não é banco de renda: DY de 2-4% decepciona investidores que buscam renda mensal<br>⚠ Regulação adversa: WACC regulatório menor ou opex regulatório mais restritivo comprimir margens<br>⚠ Integração de múltiplos ativos simultâneos: complexidade operacional cresce com o portfólio"},
        {"titulo": "Barreira de entrada", "texto": "🔒 A capacidade de executar turnaround é a barreira — e ela não se compra, se constrói em décadas. A Equatorial tem um playbook testado, uma equipe que já fez isso 6 vezes e relacionamentos com reguladores e comunidades locais que constroem confiança. Nenhum concorrente combina o histórico de execução com o acesso a capital e a disposição de atuar em regiões que outros evitam. É o modelo mais difícil de imitar no setor."},
    ],
    "IRBR3": [
        {"titulo": "Como funciona o negócio", "texto": "O IRB é uma resseguradora — uma categoria completamente diferente das outras três. Quando a Porto vende um seguro de carro de R$200.000, ela pode não querer carregar 100% desse risco no balanço. Então ela 'cede' parte do risco ao IRB, pagando um prêmio de resseguro. Se o carro for roubado, a Porto paga ao cliente e o IRB ressarce parte para a Porto. O IRB não tem cliente pessoa física. Seus clientes são as seguradoras (chamadas de 'cedentes'). A métrica-rei é o Combined Ratio — se for abaixo de 100%, a operação de subscrição dá lucro. O IRB passou por uma crise grave em 2020 (fraude contábil, Combined Ratio de 140%+). Desde 2022 está em turnaround: Combined Ratio voltou para ~85-90%, resultado de subscrição cresceu 74,5% no 1T26, sinistralidade doméstica caiu para 35%. Em 2026 anunciou expansão para seguro direto (criação de duas seguradoras próprias) — é uma mudança estrutural do modelo que o mercado ainda está digerindo."},
        {"titulo": "De onde vem a receita", "texto": "<b>~53% — Resultado de subscrição (prêmios - sinistros - despesas):</b> coração do negócio — R$180 mi no 1T26, +74,5% a/a<br><b>~47% — Resultado financeiro (float das reservas):</b> reservas técnicas investidas rendendo a Selic"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Único ressegurador de grande porte listado na B3 — sem comparável doméstico<br>✦ Turnaround concluído: Combined Ratio de 140%+ em 2020 para ~85-90% em 2026<br>✦ Solvência regulatória de 287% — capital de sobra para crescer e distribuir dividendos<br>✦ Mercado de resseguro no Brasil cresceu 7,1% no 1T26 — vento a favor estrutural<br>✦ A partir de 2027, reforma tributária (CBS/IBS) zera alíquota do resseguro — potencial ganho de rentabilidade<br>✦ Base de dados técnicos de 80+ anos de riscos brasileiros — vantagem de subscrição inreplicável"},
        {"titulo": "Riscos principais", "texto": "⚠ Catástrofes de grande escala: enchente, furacão, acidente de aviação podem gerar perda pontual enorme<br>⚠ Histórico de fraude contábil em 2020 — credibilidade ainda em reconstrução com investidores institucionais<br>⚠ Expansão para seguro direto em 2026 é aposta não provada — pode consumir capital e desviar foco<br>⚠ Sinistralidade internacional elevada (~93%) — mercado externo é menos lucrativo que o doméstico<br>⚠ Dividend yield baixo (~3%) — turnaround recente limita distribuição; ainda não é banco de renda"},
        {"titulo": "Barreira de entrada", "texto": "🔒 80 anos de base de dados técnicos de risco no Brasil. Uma resseguradora nova levaria décadas para ter a confiança técnica para assumir resseguros de aviação, petróleo ou grandes riscos industriais. O IRB sabe exatamente quanto custa um incêndio numa plataforma de petróleo no Brasil — e essa informação vale mais do que qualquer capital. Mais o oligopólio regulatório: a SUSEP controla a abertura de novas resseguradoras."},
    ],
    "ISAE4": [
        {"titulo": "Como funciona o negócio", "texto": "A ISA Energia é a segunda maior transmissora privada do Brasil, com foco no Sudeste. Controlada pela ISA Interconexión Eléctrica S.A. (Colombia), uma das maiores empresas de transmissão da América Latina. O diferencial da ISA vs Taesa está na qualidade do portfólio: as concessões são predominantemente de categoria II e III, com metodologia regulatória mais moderna e transparente — menos risco de surpresas na revisão de RAP. Menor alavancagem que a Taesa, TIR real implícita de ~7,7%, o que a coloca em posição mais defensiva no setor. Também tem participação minoritária da Axia Energia (ex-Eletrobras) em algumas concessões, o que cria uma relação estratégica com a maior geradora do país."},
        {"titulo": "De onde vem a receita", "texto": "<b>~98% — RAP de transmissão:</b> receita contratada por 30 anos, predominantemente indexada ao IPCA<br><b>~2% — Outros serviços:</b> operação e manutenção de terceiros"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Portfólio de concessões modernas (cat. II/III): menor risco regulatório vs Taesa<br>✦ Menor alavancagem: mais espaço para novos leilões sem pressionar o balanço<br>✦ TIR real implícita de ~7,7% — bem acima da NTN-B de prazo semelhante<br>✦ Controlador com track record: ISA Colombia opera transmissão em 6 países com excelência<br>✦ Zero risco climático — mesmo modelo de receita da Taesa"},
        {"titulo": "Riscos principais", "texto": "⚠ Controlador colombiano: decisões vêm de fora do Brasil — alinhamento com minoritários nem sempre é total<br>⚠ Selic alta comprime valuation como em qualquer transmissora de duration longa<br>⚠ Menor liquidez que Taesa na B3 — spread bid/ask maior para investidores institucionais<br>⚠ Depende de novos leilões para crescer — mercado de transmissão é competitivo"},
        {"titulo": "Barreira de entrada", "texto": "🔒 Idem à Taesa: exclusividade regulatória de 30 anos e custo proibitivo de infraestrutura. Adicionalmente, o relacionamento com a Axia e a presença no Sudeste (onde está a maior demanda do país) são vantagens geográficas e de relacionamento difíceis de replicar."},
    ],
    "ITUB4": [
        {"titulo": "Como funciona o negócio", "texto": "O Itaú opera em quatro frentes: varejo (conta corrente, cartão, crédito e seguros para pessoas físicas), atacado (crédito para grandes empresas, mercado de capitais, tesouraria), gestão de ativos (fundos, previdência) e atividades internacionais (América Latina). O diferencial não é o tamanho — é a seletividade. O Itaú deliberadamente abandonou segmentos de menor renda e maior inadimplência, concentrando a carteira em alta e média renda. 6 de cada 10 brasileiros de alta renda têm relacionamento com o banco. Isso gera spreads melhores, inadimplência menor e fee de serviços mais alto (asset management, corretagem, seguros). No 1T26 entregou lucro recorrente de R$ 12,3 bi e ROE de 24,8% — o mais alto entre os incumbentes."},
        {"titulo": "De onde vem a receita", "texto": "<b>~50% — Margem financeira (NII):</b> spread de crédito e resultado de tesouraria<br><b>~25% — Receitas de serviços e tarifas:</b> cartão, asset management, advisory, corretagem<br><b>~12% — Seguros:</b> Itaú Seguros — vida, prestamista, imobiliário<br><b>~13% — Outros:</b> câmbio, derivativos, international"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Melhor ROE entre os bancões incumbentes (~24-26%) — sustentado por décadas, não é pico de ciclo<br>✦ Foco na alta renda cria um flywheel: menor inadimplência → menor provisão → mais capital disponível para crescer<br>✦ Escala de distribuição: rede própria + parcerias + digital permitem cross-sell sem aumentar custo proporcional<br>✦ Transformação digital avançada — 75% das transações já são digitais, com meta de 75% dos clientes em modelo digital-first até 2027<br>✦ Seguros e asset management são negócios capital-light dentro do banco, com margens muito mais altas que o crédito"},
        {"titulo": "Riscos principais", "texto": "⚠ Valuation premium (P/L ~8x, P/VP ~2x) não tolera decepções — qualquer deterioração é punida<br>⚠ Competição crescente de BTG no wealth management e de fintechs no varejo digital<br>⚠ Regulação bancária pode aumentar requisitos de capital, pressionando distribuição de dividendos<br>⚠ Expansão na América Latina (Chile, Argentina, Colômbia) adiciona risco cambial e político"},
        {"titulo": "Barreira de entrada", "texto": "🔒 A combinação de marca, rede de distribuição, base de dados de clientes e capital regulatório cria uma barreira de entrada que nenhuma fintech conseguiu transpor em décadas. Nubank chegou a 100 milhões de clientes — mas em rentabilidade por cliente ainda está longe do Itaú."},
    ],
    "KEPL3": [
        {"titulo": "Como funciona o negócio", "texto": "A Kepler Weber não é autopeça — é uma empresa de bens de capital para o agronegócio. Fabrica silos (metálicos e de concreto), secadores de grãos, transportadores (elevadores de canecas, correias) e sistemas de controle para armazenagem de soja, milho, trigo e outros grãos. É líder absoluta no Brasil com ~80% de market share em silos metálicos — o produto mais vendido do portfólio. O mercado-alvo são produtores rurais individuais, cooperativas e tradings (Bunge, ADM, Cargill, LDC). O diferencial do modelo: o Brasil tem grave déficit de armazenagem. A capacidade estática nacional é de ~175 milhões de toneladas, enquanto a produção de grãos superou 320 milhões em 2025. Cada tonelada de grão produzida sem armazém adequado é prejuízo para o produtor. Isso cria demanda estrutural que não depende do ciclo econômico convencional — depende do ciclo do agronegócio."},
        {"titulo": "De onde vem a receita", "texto": "<b>~55% — Silos metálicos e acessórios:</b> produto principal; liderança de 80% de mercado; vende a produtores e cooperativas<br><b>~20% — Secadores de grãos:</b> equipamento crítico pós-colheita; crescimento com qualidade exigida para exportação<br><b>~15% — Sistemas de transporte (elevadores, correias):</b> logística interna do silo — cross-sell natural com a venda do silo<br><b>~10% — Exportação e serviços:</b> América do Sul, África e outros; instalação e manutenção"},
        {"titulo": "Vantagens competitivas", "texto": "✦ 80% de market share em silos: nenhum concorrente chega perto — liderança consolidada em décadas<br>✦ Déficit estrutural de armazenagem: Brasil produz 320 mi t de grãos com capacidade de 175 mi t — runway de crescimento secular<br>✦ Câmbio positivo por proxy: cliente rural vende soja em dólar — dólar alto dá mais poder de compra para investir em armazenagem<br>✦ Carteira de pedidos de 12+ meses: visibilidade de receita acima da média industrial<br>✦ Panambi como polo: 100 anos de know-how em equipamentos agroindustriais no RS — cluster com fornecedores especializados"},
        {"titulo": "Riscos principais", "texto": "⚠ Ciclicidade do agro: safra ruim + queda de commodity = produtor adia investimento em armazenagem<br>⚠ Aço como matéria-prima: preço internacional afeta custo dos silos; repasse ao cliente tem defasagem<br>⚠ Concentração geográfica: RS como base industrial — enchentes de 2024 impactaram operações<br>⚠ Concorrência de importados: silos chineses entram via dumping em períodos de câmbio apreciado"},
        {"titulo": "Barreira de entrada", "texto": "🔒 100 anos de know-how e 80% de mercado criam uma barreira quase intransponível. O produtor rural que vai comprar um silo de R$500 mil não arrisca com um fornecedor desconhecido — ele quer quem estará lá para dar assistência em 10 anos. A Kepler tem rede de revendedores e assistência técnica em todo o Brasil agrícola — um entrante precisaria de décadas para construir esse canal. E a posição de liderança cria um efeito de rede: cooperativa que já tem silos Kepler compra mais Kepler porque os sistemas são integrados."},
    ],
    "KLBN4": [
        {"titulo": "Como funciona o negócio", "texto": "A Klabin é a empresa mais complexa do trio. Planta pinus (fibra longa) e eucalipto (fibra curta), produz celulose, papel e embalagens — e converte parte em produtos acabados como sacos industriais, caixas de papelão e cartões. Vende celulose para exportação, mas uma fatia relevante da receita é embalagem doméstica, o que amortece o ciclo de commodity. É a maior produtora e exportadora de papel para embalagem do Brasil."},
        {"titulo": "De onde vem a receita", "texto": "<b>~45% — Embalagens (papelão ondulado, caixas):</b> mercado doméstico, relativamente estável<br><b>~25% — Papel para embalagem (kraft, cartão):</b> Brasil e exportação<br><b>~20% — Celulose (fibra longa e fluff):</b> exportação, commodity<br><b>~10% — Sacos industriais:</b> cimento, fertilizante, Brasil"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Única produtora de pinus em escala industrial no Brasil — fibra longa que ninguém mais tem<br>✦ Diversificação de produto: embalagem amorte o ciclo de celulose<br>✦ Integração vertical completa: da floresta ao produto acabado<br>✦ Celulose fluff (para fraldas e absorventes) — nicho de margem alta e demanda crescente"},
        {"titulo": "Riscos principais", "texto": "⚠ Capex intensivo e constante — projetos de expansão pressionam caixa por anos seguidos<br>⚠ Alavancagem historicamente alta (4–5x EBITDA em fases de investimento)<br>⚠ Complexidade operacional: 23 plantas, múltiplos produtos, margens diferentes por linha<br>⚠ Pinus tem ciclo de 15 anos — planejamento florestal é de altíssimo prazo"},
        {"titulo": "Barreira de entrada", "texto": "🔒 O pinus. Ninguém mais tem floresta de pinus em escala no Brasil. Plantar hoje para colher em 15 anos é uma barreira de entrada que efetivamente fecha o mercado para novos entrantes na fibra longa."},
    ],
    "LEVE3": [
        {"titulo": "Como funciona o negócio", "texto": "A Mahle Metal Leve é a subsidiária brasileira do grupo Mahle — um dos maiores fabricantes de componentes automotivos do mundo, com sede em Stuttgart, Alemanha. No Brasil, fabrica pistões, anéis de segmento, buchas, filtros (óleo, ar, combustível) e velas de ignição. O modelo tem duas frentes: OEM (~30%), onde vende diretamente para GM, Ford, Stellantis e Volkswagen que montam os carros novos; e aftermarket (~70%), onde vende para distribuidores e mecânicas que trocam peças em carros usados. O aftermarket é o diferencial: com frota média de 11+ anos no Brasil, cada motor exige troca de pistão, filtro ou vela em média a cada 2-3 anos. Quanto mais velha a frota, mais demanda — é anticíclico por natureza. A controladora alemã custeia o P&D global (€1 bi/ano em inovação) e o Brasil se beneficia do know-how sem pagar por isso diretamente. Exporta componentes para Europa e América do Norte, capturando o câmbio favorável."},
        {"titulo": "De onde vem a receita", "texto": "<b>~55% — Aftermarket Brasil:</b> mecânicas, distribuidores, varejo de autopeças — anticíclico e recorrente<br><b>~25% — OEM Brasil (montadoras):</b> GM, Ford, Stellantis, VW — segue produção de veículos novos<br><b>~20% — Exportação (OEM global):</b> componentes para Europa e EUA; dólar alto melhora margens"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Aftermarket anticíclico: frota velha gera demanda constante independente do PIB<br>✦ P&D financiado pela matriz: Mahle alemã investe €1 bi/ano em inovação — LEVE3 acessa sem pagar<br>✦ Margem bruta de 38-40%: entre as mais altas do setor industrial — brand reconhecido pelo mecânico<br>✦ Exportação em dólar: ~20% das receitas em moeda forte protege em desvalorizações do real<br>✦ Único papel do grupo Mahle listado fora da Alemanha: acesso a gestão global com liquidez local"},
        {"titulo": "Riscos principais", "texto": "⚠ Eletrificação da frota: carro elétrico não tem pistão, filtro de óleo nem vela — ameaça estrutural de 10-20 anos<br>⚠ Concentração no motor a combustão: 90%+ das receitas dependem de tecnologia em transição<br>⚠ OEM sujeito ao ciclo automotivo: montadoras param produção em crise e afeta 25% da receita<br>⚠ Controladora estrangeira: dividendo certo, mas decisões estratégicas vêm de Stuttgart — potencial de conflito com minoritários"},
        {"titulo": "Barreira de entrada", "texto": "🔒 Marca reconhecida pelo mecânico. No aftermarket, quem decide a peça é o mecânico — não o dono do carro. E o mecânico de Franca, Uberlândia ou Manaus conhece e confia na Mahle há décadas. Construir essa confiança com 50.000 mecânicos no Brasil inteiro é um ativo invisível que nenhum concorrente recompra. Mais o know-how técnico da matriz alemã: qualidade de produto que importados asiáticos ainda não replicam no motor."},
    ],
    "MDNE3": [
        {"titulo": "Como funciona o negócio", "texto": "A Moura Dubeux tem um modelo diferente de todas as outras incorporadoras listadas. Além da incorporação tradicional, opera o chamado 'modelo de condomínio': os clientes compram cotas do terreno coletivamente, formam um condomínio, e a MD constrói por conta do condomínio cobrando taxa de administração mensal. Isso gera receita recorrente durante a obra e reduz o risco de crédito (o cliente paga mensalmente conforme a obra avança). Em 2026, reorganizou-se como holding MDNE com três marcas: Moura Dubeux (alto padrão e luxo + segunda residência), Mood (médio padrão, lançada em 2023) e Ún1ca (MCMV no Nordeste, em parceria com a Direcional — joint venture chamada Ún1ca para o segmento econômico nordestino). Opera em 7 estados nordestinos, com liderança de mercado absoluta na região — 260 empreendimentos entregues em 42 anos e VGV lançado de R$5,5 bi projetados para 2026."},
        {"titulo": "De onde vem a receita", "texto": "<b>~55% — Alto padrão e luxo — marca Moura Dubeux:</b> Recife, Fortaleza, Natal, João Pessoa; segunda residência na costa nordestina<br><b>~30% — Médio padrão — marca Mood:</b> lançada em 2023; crescendo rápido; primeira residência classe média<br><b>~15% — MCMV — marca Ún1ca (JV com Direcional):</b> iniciada em 2025; em crescimento acelerado; acesso ao FGTS"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Monopólio regional: 42 anos de liderança no Nordeste — nenhum concorrente nacional tem a mesma escala regional<br>✦ Modelo de condomínio: receita recorrente durante a obra + risco de crédito menor<br>✦ DY de 17%: alta distribuição de lucros; P/L de 5,79x — um dos mais baratos do setor<br>✦ Nordeste com demanda reprimida: menos saturado que SP; cliente de alto padrão regional tem menos opções<br>✦ Ún1ca (MCMV): diversificação que protege em ciclo de juro alto; JV com Direcional traz expertise"},
        {"titulo": "Riscos principais", "texto": "⚠ Concentração no Nordeste: PIB regional mais fraco — recessão nacional impacta mais<br>⚠ Três marcas recentes: Mood (2023) e Ún1ca (2025) ainda em maturação — execução simultânea é risco<br>⚠ Alto padrão sensível à Selic: o core do negócio sofre quando crédito encarece<br>⚠ Small cap: liquidez menor (R$8 mi/dia) — spread bid/ask maior, menos cobertura de analistas<br>⚠ Dependência familiar: empresa fundada pela família Dubeux — risco de governança em eventual transição"},
        {"titulo": "Barreira de entrada", "texto": "🔒 42 anos de presença dominante no Nordeste. O comprador de alto padrão em Recife não compra da Cyrela — compra da Moura Dubeux. Essa confiança de marca regional, construída empreendimento a empreendimento em uma região onde poucos nacionais apostaram, é inreplicável no curto prazo. O modelo de condomínio é outro diferencial que os concorrentes não dominam — o cliente nordestino está habituado a esse modelo e o prefere. E o banco de terrenos de décadas na costa nordestina, em regiões que valorizaram com o turismo interno pós-pandemia, é uma posição que nenhum novo entrante vai encontrar disponível."},
    ],
    "MULT3": [
        {"titulo": "Como funciona o negócio", "texto": "A Multiplan foi fundada por José Isaac Peres em 1974 e construiu ao longo de 50 anos um portfólio de 20 shoppings concentrados em localidades premium: BarraShopping (RJ), MorumbiShopping (SP), ParkShopping (BSB), BH Shopping (MG), entre outros. A estratégia é o oposto da Allos: poucos ativos, mas os melhores. 73% do portfólio tem vendas anuais superiores a R$1 bilhão — o melhor índice do setor. Isso se traduz na maior conversão de vendas em aluguel: 10,5% vs 9,6% da Allos. Em termos práticos: para cada R$100 que o lojista vende, a Multiplan captura R$10,50 em aluguel. Esse poder de precificação vem da qualidade — lojista que está no MorumbiShopping não tem alternativa de mesma qualidade próxima. A Multiplan também tem um componente imobiliário relevante: desenvolve apartamentos e escritórios no entorno dos shoppings — o projeto de cidade completa ao redor do shopping (multimix)."},
        {"titulo": "De onde vem a receita", "texto": "<b>~52% — Aluguel mínimo garantido:</b> base fixa reajustada por IGP-DI/IPCA; portfólio premium permite mínimos maiores<br><b>~22% — Aluguel variável (% das vendas):</b> maior percentual variável que os pares — reflexo da qualidade do lojista<br><b>~13% — Estacionamento:</b> alto fluxo de veículos em shoppings premium — receita relevante<br><b>~8% — Desenvolvimento imobiliário (multimix):</b> apartamentos e escritórios no entorno dos shoppings — ciclo mais longo<br><b>~5% — Cessão de direito e outros:</b> key money e receitas não recorrentes"},
        {"titulo": "Vantagens competitivas", "texto": "✦ 73% do portfólio com vendas > R$1 bi/ano: qualidade de ativo incomum — lojistas pagam prêmio para estar lá<br>✦ 10,5% de conversão: maior poder de precificação do setor — cada real de venda gera mais aluguel<br>✦ Vendas/m² cresceram 10,9% em 2025: maior taxa de crescimento entre os pares<br>✦ 50 anos de track record: Multiplan construiu shoppings que viraram referência de consumo nas suas cidades<br>✦ Multimix: desenvolvimento imobiliário ao redor cria ecossistema de valor que valoriza o próprio shopping"},
        {"titulo": "Riscos principais", "texto": "⚠ Valuation de prêmio (12x FFO): não tolera decepção — qualquer desaceleração é punida no preço<br>⚠ Concentração geográfica: forte em SP, RJ e Sul — recessão regional impacta mais que portfólio nacional<br>⚠ Selic alta é o maior inimigo: duration longa do ativo = valuation comprimido em cenário de juro alto<br>⚠ DY mais baixo (~5-6%): reinveste mais; para investidores de renda pura, a Allos é mais atrativa<br>⚠ Expansão limitada: portfólio premium tem menos oportunidades de crescimento via novos shoppings"},
        {"titulo": "Barreira de entrada", "texto": "🔒 50 anos de curadoria de localização e de mix de lojistas. O MorumbiShopping em São Paulo ou o BarraShopping no Rio têm listas de espera de lojistas que querem entrar. Quando o Zara, a Apple ou a Nike quer estar em São Paulo, o MorumbiShopping está na lista curta — e a Multiplan sabe negociar esse poder de escassez em aluguel. Isso é uma vantagem competitiva de marca que levou meio século para construir e que nenhum shopping novo replica mesmo com capital infinito."},
    ],
    "PETR4": [
        {"titulo": "Como funciona o negócio", "texto": "A Petrobras é uma empresa integrada de petróleo e gás — extrai no pré-sal, refina nas suas refinarias e vende combustível e derivados para o mercado brasileiro e para exportação. Com meta de 3,4 milhões de boed até 2028 e custo de extração abaixo de US$6/barril, é uma das operações de mais baixo custo do planeta. O pré-sal brasileiro — especialmente Búzios, com reservas gigantescas na Bacia de Santos — é o coração do negócio: óleo leve de alta qualidade, em águas profundas, com FPSOs que chegam a produzir 200 mil barris/dia cada. O plano 2026-2030 prevê US$109 bi de investimento, 62% no pré-sal, com 8 novos sistemas de produção até 2030, sendo 7 já contratados. A integração com o refino funciona como amortecedor: quando o Brent cai, o refino compra petróleo barato e sustenta margens. O custo total médio de produção (incluindo royalties e participações governamentais) é de US$30,4/boe no quinquênio — muito abaixo do preço de equilíbrio do mercado."},
        {"titulo": "De onde vem a receita", "texto": "<b>~60% — E&P (exploração e produção):</b> pré-sal é o motor; <US$6/bbl de lifting cost; 8 novos FPSOs até 2030<br><b>~30% — Refino, Transporte e Comercialização:</b> 1,8 mi bpd de capacidade; expansão para 2,1 mi até 2030<br><b>~7% — Gás natural e energia:</b> TAG, transporte de gás, termelétricas<br><b>~3% — Outros (fertilizantes, biocombustíveis):</b> biorrefino em expansão; US$1,2 bi aprovado em 2026"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Pré-sal: custo <US$6/bbl — um dos mais baixos do mundo; óleo leve de alta qualidade<br>✦ Búzios: maior reservatório offshore fora do Oriente Médio — reservas imensas, produção crescente por décadas<br>✦ Integração E&P + refino: proteção natural quando o Brent cai (refino compra barato)<br>✦ Dividendo garantido: política de 45% do FCF; governo precisa do dividendo — alinhamento forçado<br>✦ Escala operacional: única operadora de FPSOs em águas ultra-profundas no Brasil; know-how inreplicável"},
        {"titulo": "Riscos principais", "texto": "⚠ Risco político: CEO indicado pelo governo; preços de combustíveis como instrumento político<br>⚠ Refino pressionado: governo quer gasolina barata — comprime margens do segmento<br>⚠ Margem Equatorial: nova fronteira exploratória com licenciamento ambiental incerto (IBAMA)<br>⚠ Brent estruturalmente mais baixo: plano assume US$63/bbl em 2026; abaixo disso, capex é revisto<br>⚠ Transição energética: portfólio de longo prazo concentrado em hidrocarbonetos"},
        {"titulo": "Barreira de entrada", "texto": "🔒 O pré-sal é a barreira mais alta do setor de petróleo no mundo. Operar FPSOs em águas de 2.000-3.000 metros, perfurar poços de 6.000-7.000 metros passando pela camada de sal, é um desafio de engenharia que só meia dúzia de empresas no planeta domina — e a Petrobras é operadora de praticamente todos. Ninguém entra no pré-sal sem ela, e ela tem mais de 70 anos de know-how local."},
    ],
    "POMO4": [
        {"titulo": "Como funciona o negócio", "texto": "A Marcopolo não fabrica o chassi do ônibus — fabrica a carroceria. O chassi vem da Volvo, Mercedes ou Scania; a Marcopolo coloca em cima a estrutura de passageiros (o que o passageiro vê e sente). É a maior fabricante de carrocerias de ônibus do mundo em volume. Opera em dois mercados distintos: Brasil (~50% da receita), onde os clientes são prefeituras (ônibus urbano), empresas de turismo e fretamento; e exterior (~50%), onde exporta para América Latina, África, Índia, Austrália e Europa, com fabricação local em alguns países. O produto é customizado — cada pedido tem especificações diferentes. Isso cria barreiras de engenharia e relacionamento com o cliente que produtos padronizados não têm. Em 2025-2026, o BRT (Bus Rapid Transit) nas capitais brasileiras e o programa de eletrificação de frotas municipais são os maiores catalisadores. A Marcopolo já fabrica carrocerias para ônibus elétricos — é uma das poucas do setor que mitigou o risco de eletrificação."},
        {"titulo": "De onde vem a receita", "texto": "<b>~30% — Ônibus urbano — Brasil:</b> prefeituras e operadoras; BRT e eletrificação são catalisadores 2025-2026<br><b>~20% — Ônibus rodoviário e turismo — Brasil:</b> empresas de fretamento e turismo; ciclo ligado à economia<br><b>~35% — Exportação (América Latina + África + outros):</b> dólar/euro nas receitas; margens melhores que o mercado doméstico<br><b>~15% — Fabricação local no exterior (JVs):</b> Índia, Austrália, Colômbia — receita em moeda local"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Líder mundial em carrocerias de ônibus: escala que nenhum concorrente brasileiro alcança<br>✦ 50% de exportação: diversificação geográfica que suaviza o ciclo doméstico<br>✦ Produto customizado: cada ônibus é um projeto — barreiras de engenharia e relacionamento<br>✦ Já fabrica para elétricos: adaptação estratégica que evita a armadilha da eletrificação<br>✦ Caxias do Sul: cluster industrial gaúcho com fornecedores especializados e mão de obra qualificada"},
        {"titulo": "Riscos principais", "texto": "⚠ Dependência de orçamento público: prefeituras compram quando têm verba — ciclo político afeta demanda doméstica<br>⚠ Eletrificação em andamento: BYD e Volvo Elétrico competem pela carroceria de ônibus elétrico<br>⚠ Câmbio de dois gumes: exportação beneficia margem, mas matéria-prima importada sobe junto<br>⚠ Enchentes RS (2024): sede em Caxias do Sul sofreu impacto operacional — risco geográfico concentrado"},
        {"titulo": "Barreira de entrada", "texto": "🔒 75 anos de know-how em engenharia de carrocerias de ônibus. O ônibus urbano de São Paulo, de Lagos, de Melbourne e de Montevidéu pode ser da Marcopolo — e cada cidade tem normas técnicas, dimensões e especificações diferentes. Dominar isso em 100+ países é uma barreira de conhecimento técnico e relacionamento institucional que nenhum entrante replica em menos de décadas."},
    ],
    "PRIO3": [
        {"titulo": "Como funciona o negócio", "texto": "A PRIO tem um modelo único e comprovado: compra campos de petróleo maduros que grandes petroleiras decidiram abandonar, assume a operação, corta custos e aumenta a recuperação dos reservatórios. Fez isso com Frade (da Chevron), Albacora Leste (da Petrobras), cluster Polvo+Tubarão Martelo (da Dommo) e, mais recentemente, Peregrino (da Equinor) — o maior campo da empresa, 100% adquirido em 2025. O resultado: de 5 mil barris/dia e custo de US$35/bbl em 2015 para +190 mil barris/dia e custo de US$9/bbl em 2026. Wahoo é o próximo capítulo: primeiro campo desenvolvido do zero pela PRIO, conectado ao FPSO Valente via tieback de Frade, com custo marginal de apenas US$1/bbl (usa infraestrutura existente) e capacidade de 40 kboed. Peregrino, que a Equinor operava a US$500 mi/ano de custo, já está sendo operado pela PRIO a US$370 mi e deve chegar a US$250 mi quando o gasoduto de gás for reativado em 2026 — US$250 mi de ganho anual."},
        {"titulo": "De onde vem a receita", "texto": "<b>~40% — Peregrino:</b> campo pesado da Equinor; PRIO cortou custo de US$500 mi para meta US$250 mi/ano<br><b>~30% — Frade + Wahoo:</b> Wahoo a 40 kboed com custo marginal de US$1/bbl — maior catalisador de 2026<br><b>~15% — Albacora Leste:</b> campo da Petrobras revendido; PRIO aumentou produção e eficiência<br><b>~15% — Polvo + Tubarão Martelo + outros:</b> cluster offshore menor na Bacia de Campos"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Modelo de revitalização comprovado: compra barato, corta custo, aumenta produção — 100% de execução<br>✦ Lifting cost ~US$9/bbl (meta US$7): margem expressiva mesmo com Brent a US$50<br>✦ Zero risco político: privada, independente, sem governo determinando preços ou CEO<br>✦ Wahoo: custo marginal de US$1/bbl por usar infraestrutura do Frade — puro upside<br>✦ Peregrino: sinergias de US$250 mi/ano vs Equinor — maior captura de valor de campo único"},
        {"titulo": "Riscos principais", "texto": "⚠ Brent é tudo: sem refino para amortecer — cada US$1 de queda vai direto no EBITDA<br>⚠ Alavancagem pós-Peregrino: US$3 bi de aquisição; meta 1x dívida/EBITDA até 2027 a US$60<br>⚠ Declínio natural: campos maduros declinam — precisa de perfurações contínuas (Albacora Leste+30 kboed)<br>⚠ Ramp-up de Wahoo: GOR (razão gás-óleo) alto; cada poço precisa de 10 dias de estabilização<br>⚠ Concentração na Bacia de Campos: todos os ativos offshore no RJ — risco operacional concentrado"},
        {"titulo": "Barreira de entrada", "texto": "🔒 O know-how de revitalização de campos maduros é a barreira. A PRIO desenvolveu metodologias próprias para extrair mais petróleo de reservatórios dados como esgotados. Isso se combina com uma cultura de custo obsessiva — cortou o OpEx de Peregrino pela metade em menos de um ano. E a reputação junto às grandes petroleiras que querem desinvestir é a maior vantagem competitiva: quando a Chevron, Equinor ou Petrobras quer vender um campo, a PRIO está na lista curta dos compradores."},
    ],
    "PSSA3": [
        {"titulo": "Como funciona o negócio", "texto": "A Porto é a única seguradora real desta lista — ela assume risco, subscreve apólices, paga sinistros. Não é distribuidora de banco. Nasceu em 1945 como seguradora de automóveis e por décadas foi sinônimo de 'seguro de carro'. O problema: auto tinha sinistralidade alta e margens comprimidas. A virada estratégica foi deliberada: diluir o auto (que era 90% da receita) e crescer nas verticais mais rentáveis. Em 2025, auto era apenas 39%. Hoje opera em quatro verticais: Porto Seguro (auto, residencial, empresarial), Porto Saúde (planos de saúde e odonto, crescendo forte), Porto Bank (cartão de crédito, consórcio) e Porto Serviços (assistências). A parceria com o Itaú (exclusividade para auto e residencial nos canais do banco) é uma alavanca de distribuição que nenhum concorrente tem — o Itaú Seguro de Auto é, na prática, operado pela Porto."},
        {"titulo": "De onde vem a receita", "texto": "<b>~39% — Auto (Porto Seguro + Itaú + Azul Seguros):</b> era 90% em 2010 — deliberadamente diluído; sinistralidade alta e margens comprimidas<br><b>~25% — Porto Saúde (planos de saúde e odonto):</b> vertical mais rentável e em crescimento — margens superiores ao auto<br><b>~15% — Residencial e empresarial:</b> cross-sell com auto e parceria Itaú — sinistralidade mais baixa<br><b>~12% — Porto Bank (cartão, consórcio, financiamento):</b> crescendo via base de 18 mi de clientes — sem custo de aquisição<br><b>~9% — Porto Serviços (assistências):</b> assistências 24h e serviços domésticos — fidelização e receita recorrente"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Diversificação real: auto 39% da receita — se o mercado de carros parar, a Porto não para<br>✦ Porto Saúde crescendo com margens superiores ao auto — driver estrutural dos próximos anos<br>✦ Exclusividade nos canais do Itaú: acesso a mais de 50 milhões de clientes com custo de aquisição reduzido<br>✦ Taxa de renovação 10 pp acima da média do mercado — fidelidade de cliente acima da concorrência<br>✦ 18 milhões de clientes únicos — base para cross-sell de saúde, banco e serviços"},
        {"titulo": "Riscos principais", "texto": "⚠ Sinistralidade alta: ela paga o que a natureza e os acidentes custam — granizo, enchente, fraude<br>⚠ Competição agressiva em auto: concorrentes praticando preços baixos para ganhar mercado<br>⚠ Porto Saúde: custo dos planos de saúde cresce sistematicamente acima da inflação<br>⚠ DY menor (~5-6%) — reinveste mais para crescer; não é banco de renda no curto prazo<br>⚠ Valuation mais alto (P/L ~10x) após forte valorização — margem de segurança menor"},
        {"titulo": "Barreira de entrada", "texto": "🔒 A exclusividade no Itaú + 80 anos de marca + rede de 46.000 corretores. Um novo entrante levaria décadas para construir a confiança que um corretor tem com a Porto. O contrato com o Itaú é uma alavanca que qualquer outra seguradora pagaria bilhões para ter. E a liderança em auto (com a sinistralidade controlada que têm) cria um banco de dados de risco que é vantagem competitiva de subscrição."},
    ],
    "RANI3": [
        {"titulo": "Como funciona o negócio", "texto": "A Irani não é uma produtora de celulose de mercado. É uma fabricante de embalagens que produz sua própria celulose — e usa tudo internamente. Pega aparas (papel reciclado descartado por supermercados, e-commerce e frigoríficos), transforma em papel kraft e papelão ondulado, e vende para o mercado doméstico. Também tem florestas próprias de pinus no Sul (SC e RS), de onde extrai fibra virgem para complementar a produção e resina de terebintina como subproduto (usada em tintas a óleo)."},
        {"titulo": "De onde vem a receita", "texto": "<b>~57% — Embalagens de papelão ondulado:</b> frigoríficos, agro, e-commerce, alimentos<br><b>~37% — Papel para embalagens (kraft):</b> sacolas, sacos, papel multiwall — Brasil e 15% exportação<br><b>~6% — Resinas e madeira:</b> terebintina e venda de madeira — subproduto do pinus"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Zero exposição ao câmbio e ao ciclo global de celulose — negócio 100% doméstico<br>✦ Demanda por embalagem de papelão cresceu 2–5%/ano mesmo em recessão — setor defensivo<br>✦ Floresta própria de pinus garante parte do custo estável e previsível<br>✦ Capacidade de repasse de preço: quem compra caixa de papelão não tem substituto fácil<br>✦ Plataforma Gaia (>R$1 bi investido): ganhos de eficiência ainda sendo colhidos"},
        {"titulo": "Riscos principais", "texto": "⚠ Preço das aparas (OCC): insumo externo que representa ~30% do custo — variou de R$610 a R$1.300/t<br>⚠ Eventos climáticos no Sul (enchentes RS/SC) disruptam o fornecimento de aparas<br>⚠ Small cap — menor liquidez, menor cobertura de analistas, mais suscetível a humor de mercado<br>⚠ Capex pesado recente (Gaia) ainda sendo digerido; FCF pressiona no curto prazo"},
        {"titulo": "Barreira de entrada", "texto": "🔒 Integração + localização + relacionamento com clientes industriais. No mercado de embalagens, o cliente (frigorífico, agro) não troca de fornecedor facilmente — logística, especificação técnica e volume criam um lock-in operacional relevante."},
    ],
    "SANB3": [
        {"titulo": "Como funciona o negócio", "texto": "O Santander é um banco universal (PF + PME + atacado), mas com uma particularidade: é subsidiária de um grupo global espanhol. Isso tem vantagens (acesso a tecnologia, melhores práticas globais, plataforma de câmbio internacional) e desvantagens (decisões estratégicas feitas em Madri podem não se adaptar à realidade brasileira, e parte do lucro 'vaza' para a matriz). Historicamente, o Santander teve dificuldade de encontrar seu nicho no Brasil: não tem o foco em alta renda do Itaú, não tem o agro do BB, não tem o interior do Bradesco, não tem o atacado do BTG. Em 2026, está buscando diferenciação em crédito imobiliário, alta renda e PME. O ROE ainda é o mais baixo entre os grandes privados — o mercado cobra prova."},
        {"titulo": "De onde vem a receita", "texto": "<b>~52% — Margem financeira (NII):</b> crédito PF + PME + corporate<br><b>~22% — Receitas de serviços e tarifas:</b> cartão, seguros, corretagem<br><b>~12% — Seguros e previdência:</b> <br><b>~14% — Mercado de capitais e câmbio:</b> "},
        {"titulo": "Vantagens competitivas", "texto": "✦ Plataforma global: câmbio, trade finance e operações internacionais para clientes com negócios no exterior<br>✦ Acesso à tecnologia e melhores práticas do grupo global — Openbank (banco digital do grupo) chegando ao Brasil<br>✦ Valuation descontado em relação aos pares: se o ROE normalizar, há upside relevante<br>✦ Histórico consistente de pagamento de JCP — yield atrativo dado o valuation baixo"},
        {"titulo": "Riscos principais", "texto": "⚠ ROE estruturalmente mais baixo que os pares privados — sem nicho definido que justifique prêmio<br>⚠ Decisões estratégicas dependem da matriz espanhola — nem sempre otimizadas para o Brasil<br>⚠ Exposição a PME e varejo de menor renda em ciclo de juro alto e inadimplência elevada<br>⚠ Competição intensa: Itaú na alta renda, BTG no atacado, Nubank/Inter no varejo digital"},
        {"titulo": "Barreira de entrada", "texto": "🔒 A plataforma global é a barreira real. Para uma empresa brasileira que exporta, importa ou tem sócios internacionais, ter um banco com presença em 10 países na mesa é conveniente. Mas no varejo PF doméstico, essa vantagem não aparece — o que explica o ROE mais baixo: a barreira não se traduz em rentabilidade no negócio principal."},
    ],
    "SAPR4": [
        {"titulo": "Como funciona o negócio", "texto": "A Sanepar é a empresa de saneamento do Paraná — controlada pelo governo estadual. Opera 346 concessões municipais, com cobertura de água já alta historicamente (Paraná tem índices acima da média nacional). O foco atual é expansão de esgoto e modernização das redes. Diferente das pares privatizadas, a Sanepar não passou por turnaround — já era uma empresa relativamente eficiente. O grande evento de 2026 foi a decisão da AGEPAR sobre os R$4 bi de precatórios (dinheiro recebido via vitória judicial): a agência regulatória determinou que o valor será repassado aos consumidores via redução de tarifa, e não distribuído como dividendo extraordinário. O mercado frustrado explica a queda de ~8% das ações em 2026. Também em 2026, a revisão tarifária entregou apenas 2,49% (IRT) — bem abaixo da inflação — comprimindo margens e frustrou as expectativas."},
        {"titulo": "De onde vem a receita", "texto": "<b>~55% — Água — tarifa regulada (AGEPAR/PR):</b> cobertura histórica alta no PR; crescimento via novos usuários e reajuste tarifário<br><b>~43% — Esgoto — tarifa regulada:</b> déficit de esgoto no Paraná ainda a ser endereçado — maior runway de crescimento<br><b>~2% — Outros serviços:</b> resíduos industriais; serviços técnicos para municípios"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Operação madura e eficiente: sem o 'mato alto' das estatais que vão para privatização — base operacional sólida<br>✦ Cobertura alta de água: menor risco operacional e de qualidade; Paraná tem melhores indicadores do setor<br>✦ Dívida controlada: dívida líquida/EBITDA de 0,71x — folga para investimento sem comprometer a estrutura financeira<br>✦ P/VP abaixo de 1x: negocia abaixo do valor patrimonial — piso de proteção para o investidor<br>✦ Estado do Paraná: melhor qualidade de crédito entre os estados brasileiros — menor risco de interferência política irresponsável"},
        {"titulo": "Riscos principais", "texto": "⚠ Precatórios para consumidores: R$4 bi que o mercado esperava como dividendo foram para os usuários — frustrou a tese de dividendo extraordinário<br>⚠ Revisão tarifária conservadora: IRT 2026 de 2,49% (abaixo da inflação) comprime receita real<br>⚠ Sem catalisador de privatização: governo do PR não sinaliza privatização; sem repricing de múltiplo no horizonte<br>⚠ Crescimento limitado: empresa mais madura = menor crescimento de BRR = menor expansão de receita vs pares<br>⚠ Lucro pressionado: 1T26 com queda de 70,8% (efeito base de comparação alta + itens não recorrentes de 2025)"},
        {"titulo": "Barreira de entrada", "texto": "🔒 346 concessões municipais no Paraná — o mesmo monopólio regulado dos pares. A Sanepar tem uma vantagem específica: décadas de relacionamento com os municípios paranaenses e um histórico de qualidade de serviço que reduz o risco de revogação de concessões. O Paraná tem o melhor perfil de pagadores do Brasil — inadimplência menor, consumo per capita maior, renda acima da média. A barreira aqui é mais operacional do que de turnaround: quem tentasse entrar não teria como competir por concessões já consolidadas."},
    ],
    "SBSP3": [
        {"titulo": "Como funciona o negócio", "texto": "A Sabesp é um monopólio de saneamento no estado de São Paulo — atende 375 municípios, incluindo a capital e a Grande São Paulo, que sozinhas concentram 22% da população brasileira e 31% do PIB nacional. Em julho de 2024, o governo de SP vendeu 32% das ações por R$14,8 bi — a maior oferta de saneamento da história do Brasil (demanda de R$187 bi). A Equatorial pagou R$6,9 bi por 15% e assumiu como investidora de referência. O modelo pós-privatização tem três vetores: (1) turnaround operacional (opex cortou R$3 bi em 2025 — de R$11,8 para R$8,8 bi); (2) aceleração de capex (R$20 bi em 2026, quase 3x o histórico anual); (3) universalização e crescimento da BRR. Cada real investido e reconhecido pela ARSESP vira receita regulatória futura — o motor de valorização de longo prazo. O CEO Carlos Piani (ex-Equatorial Maranhão) declarou: 'Estamos à frente das metas, o que nos permite sonhar' — sinalizando possível expansão para outras concessões."},
        {"titulo": "De onde vem a receita", "texto": "<b>~65% — Água — tarifa regulada:</b> distribuição de água tratada para 375 municípios paulistas<br><b>~33% — Esgoto — tarifa regulada:</b> coleta e tratamento; meta de 90% de cobertura até 2033<br><b>~2% — Outros serviços:</b> resíduos, construção para terceiros, serviços técnicos"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Melhor área de concessão do Brasil: SP concentra 22% da população e 31% do PIB — demanda e renda acima da média<br>✦ Turnaround comprovado: R$3 bi de opex cortados em 1 ano — a Equatorial provou que consegue fazer em saneamento o que fez em energia<br>✦ BRR crescendo de R$88 bi para R$158 bi até 2030 — cada real de capex vira receita regulatória futura<br>✦ Política de dividendos crescente: 50% do lucro em 2026-27, chegando a 100% a partir de 2030<br>✦ Revisão tarifária anual até 2030 — ciclo curto reduz o risco de investimento não reconhecido"},
        {"titulo": "Riscos principais", "texto": "⚠ Execução do capex de R$70 bi: quase 3x o histórico — escassez de empreiteiros, licenças e pessoal capacitado<br>⚠ Revisão tarifária politicamente sensível: Tarcísio de Freitas com agenda eleitoral em 2026 pode pressionar tarifas<br>⚠ Residências irregulares incluídas na universalização: custo e operacionalização incertos<br>⚠ Valuation já captura parte da transformação: ação subiu muito desde a privatização — margem de segurança menor<br>⚠ Lock-up da Equatorial até 2029: limitação de liquidez do controlador no curto prazo"},
        {"titulo": "Barreira de entrada", "texto": "🔒 O monopólio regulado é a barreira definitiva. Nenhuma empresa entra em São Paulo para concorrer com a Sabesp — a concessão vai até 2060 em contrato único com 375 municípios. Quem quer saneamento na região metropolitana de SP, paga para a Sabesp. E com a aceleração do capex e o reconhecimento tarifário anual, cada ano que passa aumenta os ativos da base regulatória — criando uma barreira de ativos que vai crescendo com o tempo."},
    ],
    "SHUL4": [
        {"titulo": "Como funciona o negócio", "texto": "A Schuler é uma OEM pura — fabrica exclusivamente para montadoras. O produto são peças estampadas de aço: portas, capôs, para-lamas, reforços estruturais de chassi, componentes de suspensão. É o que o cliente nunca vê, mas que está em todo veículo. A demanda segue diretamente a produção de veículos no Brasil — quando as montadoras produzem mais, a Schuler fatura mais; quando param (crise de semicondutores, recessão), a Schuler para junto. A matéria-prima principal é o aço plano — cujo preço é cotado internacionalmente e tem componente de câmbio, criando risco de margem quando o real desvaloriza sem que o cliente (montadora) aceite reajuste imediato. Opera em Santa Catarina, com uma estrutura industrial robusta e relacionamento de décadas com as principais montadoras do Brasil."},
        {"titulo": "De onde vem a receita", "texto": "<b>~60% — Peças estampadas para carros de passeio:</b> GM, Ford, Stellantis, VW, Toyota — clientes concentrados<br><b>~30% — Peças para veículos comerciais e pesados:</b> caminhões e ônibus — ciclo diferente do passeio<br><b>~10% — Ferramental e outros serviços:</b> matrizes e ferramentas para clientes industriais"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Relacionamento de décadas com montadoras: trocam de fornecedor raramente — custo de mudança é enorme<br>✦ Santa Catarina: polo industrial consolidado com fornecedores especializados e logística para portos<br>✦ Especialização técnica: estampagem de alta precisão é barreira de processo que startups não replicam<br>✦ Veículos comerciais: diversificação com caminhões e ônibus que têm ciclo diferente do passeio"},
        {"titulo": "Riscos principais", "texto": "⚠ OEM 100%: qualquer queda na produção de veículos impacta diretamente a receita<br>⚠ Concentração de clientes: poucos clientes grandes — perder um é perder fatia relevante<br>⚠ Aço como risco: commodity internacional com componente cambial; repricing com montadora é lento<br>⚠ Eletrificação: carros elétricos têm menos peças estampadas de aço (estrutura diferente) — risco de médio prazo"},
        {"titulo": "Barreira de entrada", "texto": "🔒 O processo de qualificação de um novo fornecedor numa montadora leva 2-3 anos de testes, auditorias e certificações. A Schuler já passou por esse processo com todos os clientes — a barreira de entrada não é o equipamento (pode-se comprar uma prensa), mas o histórico de qualidade que dá confiança à montadora para homologar. E São Bento do Sul concentra um cluster de indústrias de metal-mecânica que cria um ambiente de fornecedores especializados difícil de replicar."},
    ],
    "SLCE3": [
        {"titulo": "Como funciona o negócio", "texto": "Produtora pura de commodities — não beneficia nem exporta diretamente. Opera ~18 fazendas em 7 estados do Cerrado. ~70% das áreas são arrendadas em sacos de soja/hectare: quando o preço cai, o custo cai junto — proteção automática de margem. Em 2025-2026, queda de ~20% no preço da soja e câmbio mais forte pressionaram margens vs o pico de 2022-2023."},
        {"titulo": "De onde vem a receita", "texto": "<b>~55% — Soja:</b> principal cultura; exportada via tradings<br><b>~30% — Algodão:</b> maior margem unitária; demanda global crescente<br><b>~15% — Milho (safrinha):</b> segunda safra no mesmo solo — custo marginal menor"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Maior produtora listada: escala de 700 mil ha gera poder de negociação com fornecedores<br>✦ Arrendamento como hedge: custo em sacos de soja cai quando preço cai automaticamente<br>✦ Cerrado: produtividade acima da média nacional; logística para exportação otimizada<br>✦ Diversificação: soja + milho + algodão suaviza dependência de uma única commodity"},
        {"titulo": "Riscos principais", "texto": "⚠ Preço de soja: queda de 20% no preço reduz receita proporcionalmente<br>⚠ Câmbio apreciado: real forte comprime margens da receita em dólar<br>⚠ Clima: seca ou excesso de chuva impacta produção nas 18 fazendas<br>⚠ Arrendamento renovável: risco de não renovação ou aumento de custo pelo dono da terra"},
        {"titulo": "Barreira de entrada", "texto": "🔒 40 anos de relacionamento com donos de terra para arrendamento de longo prazo. Gestão de 18 fazendas em 7 estados com agricultura de precisão é operação que levou décadas para construir. Novo entrante precisaria de capital, terra disponível e reputação ao mesmo tempo."},
    ],
    "SUZB3": [
        {"titulo": "Como funciona o negócio", "texto": "A Suzano planta eucalipto, processa em celulose de fibra curta (BHKP) e exporta praticamente tudo em dólar. O produto é commodity global — o preço é dado pelo mercado internacional, não pela empresa. Sua vantagem é ser a produtora de menor custo do mundo, graças à produtividade do eucalipto brasileiro (o mais rápido do planeta — 7 anos do plantio ao corte) e à escala das operações após a fusão com a Fibria em 2019."},
        {"titulo": "De onde vem a receita", "texto": "<b>~85% — Celulose BHKP:</b> fibra curta de eucalipto, commodity global<br><b>~10% — Papel:</b> papel para imprimir/escrever e tissue<br><b>~5% — Outros:</b> energia, madeira, derivados"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Menor custo de produção de celulose do mundo — floresta tropical de crescimento ultrarrápido<br>✦ Escala de 10,9 milhões de toneladas/ano — nenhum concorrente chega perto no eucalipto<br>✦ Hedge natural: receita em dólar vs. custos em real<br>✦ Certificação FSC de toda a base florestal — acesso a mercados premium na Europa"},
        {"titulo": "Riscos principais", "texto": "⚠ Preço da celulose cai 30–40% num ciclo negativo — resultado despenca junto<br>⚠ Dívida em dólar: variação cambial pode gerar prejuízo contábil mesmo com caixa saudável<br>⚠ Projeto Cerrado (nova fábrica em GO) aumentou alavancagem — deleveraging levará anos<br>⚠ Produto único: sem diversificação que amortize o ciclo"},
        {"titulo": "Barreira de entrada", "texto": "🔒 Escala e custo. Construir uma fábrica de celulose de 2 milhões de toneladas custa ~US$ 5 bilhões e leva 5 anos. Nenhum novo entrante consegue competir no custo sem décadas de plantio próprio."},
    ],
    "TAEE11": [
        {"titulo": "Como funciona o negócio", "texto": "A Taesa é a transmissora pura mais conhecida da B3. Opera mais de 13.000 km de linhas de transmissão e 109 subestações em 18 estados. O modelo é simples e poderoso: vence um leilão da ANEEL, constrói a linha e passa a receber a RAP (Receita Anual Permitida) por 30 anos. A RAP não depende de quanto energia flui pela linha — só de a linha estar disponível dentro dos parâmetros técnicos (parâmetros de indisponibilidade geram desconto na RAP, chamado de Parcela Variável). Com receita indexada à inflação (60% IGPM + 40% IPCA), payout de 100% e sem risco climático, a Taesa é comparada a uma NTN-B de longo prazo. O que diferencia dos títulos públicos: risco de renovação de concessões antigas com metodologia menos favorável, e alavancagem de 4,7x que limita novos investimentos."},
        {"titulo": "De onde vem a receita", "texto": "<b>~95% — RAP de transmissão:</b> receita contratada por 30 anos, reajustada por IGPM/IPCA<br><b>~5% — Reforços e melhorias autorizados:</b> RAP adicional por obras autorizadas na concessão"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Zero risco climático: transmissão não gera energia — chuva, seca, vento não importam<br>✦ RAP indexada à inflação: receita do próximo ano é basicamente conhecida hoje<br>✦ Payout de ~100% do lucro regulatório: quem compra recebe praticamente todo o lucro<br>✦ Portfólio de categoria II/III (mais transparente): menor risco de surpresa regulatória nas concessões novas<br>✦ Quando o IGPM supera o IPCA: receita cresce mais que os custos — assimetria positiva"},
        {"titulo": "Riscos principais", "texto": "⚠ Alavancagem de 4,7x dívida líquida/EBITDA — a maior entre as transmissoras da B3<br>⚠ Concessões antigas têm metodologia diferente: revisão pode reduzir 15-20% da RAP dessas linhas<br>⚠ Capex pendente de R$2,2 bi em projetos — a empresa precisa captar e construir<br>⚠ IGPM negativo (já aconteceu em 2017) reduz a receita das concessões indexadas a esse índice<br>⚠ Selic alta eleva o custo da dívida e comprime o valuation (duration muito longa)"},
        {"titulo": "Barreira de entrada", "texto": "🔒 Uma vez vencido o leilão, a concessão é exclusiva por 30 anos. Ninguém constrói uma linha de transmissão paralela — o regulador não autoriza. O custo de construção da infraestrutura e a exclusividade regulatória criam um monopólio natural de altíssima barreira. O desafio não é a concorrência — é vencer o próximo leilão a uma RAP que ainda dê retorno."},
    ],
    "VALE3": [
        {"titulo": "Como funciona o negócio", "texto": "A Vale é uma das cinco maiores empresas de mineração do mundo e a maior exportadora de minério de ferro do planeta. Opera em dois grandes segmentos: Metais Ferrosos (~70% do EBITDA) e Metais Básicos (~15%). O coração do negócio é o Sistema Norte — a mina de Carajás, no Pará. Carajás tem o maior depósito de minério de ferro de alta qualidade do mundo: reservas de ~7 bilhões de toneladas com teor médio de 67% Fe (benchmark é 62%). A qualidade superior gera prêmio de preço de US$5-15/t. A logística é integrada: ferrovia EFC (Estrada de Ferro Carajás, 892 km) leva o minério diretamente ao Porto do Itaqui (MA) — sem baldeação, sem intermediário, menor custo. Em metais básicos, a Vale tem níquel no Canadá (Voisey's Bay) e cobre em projetos de desenvolvimento. Com a transição energética, cobre e níquel ganham relevância — o Sossego e o Salobo (cobre no PA) são apostas de longo prazo."},
        {"titulo": "De onde vem a receita", "texto": "<b>~55% — Minério de ferro e pelotas (Sistema Norte — Carajás):</b> 67% Fe; premium sobre benchmark; EFC + Porto Itaqui<br><b>~20% — Minério de ferro (Sistema Sudeste — MG):</b> 62-63% Fe; Quadrilátero Ferrífero; sistema mais antigo e caro<br><b>~12% — Níquel e subprodutos (cobre, cobalto, platina):</b> Canadá, Brasil, Indonesia; metal da bateria EV<br><b>~8% — Cobre (Sossego, Salobo — PA):</b> crescimento acelerado; apoio da transição energética<br><b>~5% — Outros (manganês, ferroligas, logística):</b> "},
        {"titulo": "Vantagens competitivas", "texto": "✦ Carajás: o melhor minério do mundo em qualidade e reservas — inreplicável em qualquer outra jurisdição<br>✦ Custo C1 entre os mais baixos do planeta: ~US$23-25/t vs produtores marginais a US$80+/t<br>✦ Logística própria (EFC + Porto Itaqui): controle do custo de ponta a ponta sem dependência de terceiros<br>✦ Diversificação em metais da transição: cobre e níquel crescem em relevância com veículos elétricos<br>✦ Sem controlador majoritário: gestão profissional com foco em retorno ao acionista"},
        {"titulo": "Riscos principais", "texto": "⚠ China: 70% das exportações vão para a China — qualquer desaceleração afeta diretamente<br>⚠ Brumadinho: passivo ambiental e reputacional em curso desde 2019 — provisões continuam pesando<br>⚠ Metais básicos: cobre e níquel ainda não são escala suficiente para compensar volatilidade do ferro<br>⚠ Produção de Carajás com metas ambiciosas: execução de S11D a plena capacidade é desafio logístico<br>⚠ Câmbio apreciado comprime margens em reais mesmo sem queda do preço do minério"},
        {"titulo": "Barreira de entrada", "texto": "🔒 Carajás é a barreira definitiva. O depósito foi descoberto em 1967 por geólogos da Vale e da US Steel — e nunca se encontrou outro igual no mundo em qualidade e escala. Quem não tem Carajás não tem o mesmo produto. Adicione a ferrovia de 892 km e o porto próprio: construir essa logística hoje custaria US$15-20 bi e levaria 10-15 anos. A Vale tem isso funcionando há décadas."},
    ],
    "VULC3": [
        {"titulo": "Como funciona o negócio", "texto": "A Vulcabras é a maior fabricante de calçados esportivos do Brasil — em volume de produção, não em receita de marca. Opera com duas marcas: Olympikus (própria, focada em performance popular) e Under Armour (licença exclusiva para o Brasil — fabrica, distribui e vende). A fábrica principal fica em Horizonte (CE) — maior complexo industrial de calçados do hemisfério sul, com mais de 13.000 funcionários. O Nordeste tem dois benefícios estruturais: custo de mão de obra menor e incentivos fiscais do estado do Ceará. O modelo de licença da Under Armour é o diferencial: a Vulcabras paga royalty (em dólar, um custo), mas recebe o brand premium de uma marca global de alta performance que ela não precisaria construir do zero. Vende via varejo (Renner, Riachuelo), e-commerce e lojas multimarcas."},
        {"titulo": "De onde vem a receita", "texto": "<b>~48% — Under Armour Brasil (licença):</b> marca premium — maior ticket médio; paga royalty em dólar; contrato vigente<br><b>~40% — Olympikus:</b> marca própria — boa penetração no interior e classes B/C; maior margem líquida<br><b>~12% — Outros (exportação, private label):</b> exportação para América Latina; produção para terceiros"},
        {"titulo": "Vantagens competitivas", "texto": "✦ Maior complexo industrial de calçados do hemisfério sul: escala de 50 mi de pares/ano gera custo unitário imbatível<br>✦ Under Armour: brand premium sem o risco de construir uma marca global do zero<br>✦ Nordeste: custo de mão de obra menor + incentivos fiscais do Ceará = estrutura de custo competitiva<br>✦ Margem bruta 42-45%: a mais alta do grupo — mix de marca premium com produção eficiente<br>✦ Olympikus como proteção: marca própria cresce sem depender de contrato de licença"},
        {"titulo": "Riscos principais", "texto": "⚠ Renovação do contrato Under Armour: se perder a licença, perde ~48% da receita do dia para a noite<br>⚠ Royalty em dólar: custo da licença sobe com o dólar — margem comprimida em desvalorizações do real<br>⚠ Importados asiáticos: concorrência de calçados chineses e vietnamitas comprime preços no varejo<br>⚠ Exposição à renda da classe C: Olympikus e Under Armour entry-level sensíveis a crises de renda"},
        {"titulo": "Barreira de entrada", "texto": "🔒 Escala industrial e a licença Under Armour. Construir um complexo de 13.000 funcionários especializados em calçados esportivos leva décadas — e criar o conhecimento técnico de solado, espuma de amortecimento e cabedal esportivo é barreira de processo. A Under Armour escolheu a Vulcabras porque ela é a única no Brasil com capacidade de produzir em escala e qualidade para uma marca premium global."},
    ],
}
PERFIL_EMPRESA = {
    "ABCB4": {
        "nome": "ABC Brasil",
        "fundacao": "1989",
        "sede": "São Paulo, SP",
        "tagline": "O banco que nunca atendeu pessoa física. 100% atacado, 100% foco em empresa — e a menor inadimplência do setor.",
        "modelo": "O ABC Brasil é o mais puro exemplo de especialização no setor bancário brasileiro.  Não tem agência para pessoa física. Não tem conta corrente de varejo. Não tem cartão de crédito PF.  Atende exclusivamente médias e grandes empresas (segmento middle market, corporate e large corporate)  com crédito, trade finance (financiamento ao comércio exterior), câmbio, derivativos,  banco de investimento e seguros corporativos.  Controlado pelo Arab Banking Corporation (banco árabe do Barein), tem acesso facilitado  a funding internacional e a uma rede de relacionamentos no Oriente Médio que  nenhum banco brasileiro replica.  A inadimplência histórica abaixo de 1% é o resultado de 35 anos atendendo quem  tem balanço para mostrar — empresas com faturamento mínimo de R$30 mi anuais.",
        "receita": [
            ("Margem com clientes (crédito corporativo)", "~55%", "spread sobre carteira de R$32+ bi"),
            ("Margem com mercado e tesouraria", "~20%", "PL remunerado ao CDI + operações de mercado"),
            ("Receitas de serviços", "~15%", "banco de investimento, tarifas, câmbio"),
        ],
        "vantagens": [
            "Inadimplência histórica < 1% — resultado de 35 anos emprestando apenas para empresas com balanço",
            "Sem exposição ao varejo PF: não sofre com inadimplência de cartão, crédito pessoal ou PME de baixa renda",
            "Funding internacional (via Arab Banking Corp) com custo menor que captação doméstica — vantagem de spread",
            "Modelo de negócio simples, previsível e escalável — sem a complexidade operacional de um banco universal",
            "Alta correlação de receitas com o CDI: PL remunerado a CDI + margem com clientes = proteção natural em juro alto",
        ],
        "riscos": [
            "Concentração: poucas carteiras grandes — uma inadimplência relevante pontual impacta mais que num banco pulverizado",
            "Crescimento limitado: não tem varejo para escalar rapidamente — cresce no ritmo das empresas que serve",
            "Controlador estrangeiro: decisões podem ser influenciadas por dinâmicas do Arab Banking Corporation",
            "Exposição ao ciclo corporativo: recessão severa aumenta inadimplência mesmo no atacado",
        ],
        "barreira": "35 anos de relacionamento com o middle e large corporate brasileiro.  Empresa de faturamento R$300 mi não troca de banco por conveniência —  o relacionamento, o limite de crédito aprovado e as operações estruturadas em curso  criam um lock-in real. Mais o funding árabe, que nenhum banco brasileiro vai replicar.",
    },
    "ALOS3": {
        "nome": "Allos S.A.",
        "fundacao": "2019 (fusão Aliansce + Sonae Sierra Brasil; renomeada Allos em 2022)",
        "sede": "Rio de Janeiro, RJ",
        "tagline": "A maior plataforma de shoppings do Brasil em número de ativos. 44 shoppings, diversificação nacional e a Helloo como motor de receita de mídia.",
        "modelo": "A Allos nasceu da fusão entre a Aliansce Shopping Centers e a Sonae Sierra Brasil em 2019,  e foi renomeada em 2022 para refletir o reposicionamento estratégico.  Com 44 shoppings e mais de 11.000 lojas, é o maior portfólio do Brasil em número de ativos.  A estratégia é de escala e diversificação geográfica: presente em todas as regiões,  com shoppings de médio e grande porte que atendem diferentes perfis de consumidor.  Além do aluguel tradicional, a Allos tem dois vetores de crescimento adicionais:  a Helloo (plataforma de mídia em shoppings — painéis, aeroportos, mídia digital),  que cresce rápido e tem margens melhores que o aluguel;  e um pipeline de expansão via ABL incremental nos shoppings existentes.  Em 2026, o incêndio no Shopping Tijuca (janeiro) impactou ~6% da receita de aluguel  temporariamente — o ativo operou com capacidade reduzida no 1T26.",
        "receita": [
            ("Aluguel mínimo garantido", "~55%", "base fixa dos contratos de locação, reajustada por IGP-M/IPCA"),
            ("Aluguel variável (% das vendas)", "~20%", "percentual sobre vendas dos lojistas — cresce com SSS"),
            ("Estacionamento e serviços", "~12%", "receita de rotatividade e serviços aos lojistas"),
            ("Helloo (mídia em shoppings e aeroportos)", "~8%", "crescimento acelerado; margens superiores ao aluguel"),
            ("Cessão de direito e outros", "~5%", "key money e receitas imobiliárias não recorrentes"),
        ],
        "vantagens": [
            "44 shoppings: maior diversificação geográfica do setor — nenhum ativo representa mais de 10% da receita",
            "Helloo: plataforma de mídia em crescimento com margens superiores ao aluguel e receitas crescentes",
            "DY de ~9% em 2026: alta distribuição de FCL atrativa para investidores de renda",
            "Valuation com desconto (10x FFO) vs Multiplan — potencial de re-rating se qualidade do portfólio melhorar",
            "Recompras de ações ativas: programa de buyback aumenta o FFO por ação sem crescimento operacional",
        ],
        "riscos": [
            "Portfólio de qualidade média: 58% da receita vem de shoppings com vendas < R$1 bi/ano",
            "Incêndio no Tijuca (jan/2026): impacto temporário mas real de ~6% da receita",
            "Selic alta comprime o valuation: shopping é ativo de duration longa — taxa de desconto importa",
            "Conversão de 9,6%: menor poder de precificação vs Multiplan — lojistas pagam menos por real de venda",
            "Integração ainda em andamento: fusão de 2019 ainda sendo otimizada em sistemas e processos",
        ],
        "barreira": "44 concessões em pontos estratégicos das cidades.  Um shopping bem localizado é inreplicável — não se constrói outro no mesmo quarteirão.  O custo de construção de um shopping novo (R$500 mi a R$2 bi) e o tempo de maturação  (5-7 anos para atingir ocupação plena) criam uma barreira de entrada altíssima.  A Helloo adiciona uma barreira de rede: 44 shoppings + aeroportos criam escala de mídia  que anunciantes pagam prêmio para acessar.",
    },
    "ALUP11": {
        "nome": "Alupar Investimento",
        "fundacao": "2000 (holding formalizada em 2007)",
        "sede": "São Paulo, SP",
        "tagline": "A transmissora com ambição latino-americana. Controle 100% nacional, expansão no Peru e Colômbia, e a única com concessão vitalícia no exterior.",
        "modelo": "A Alupar é uma holding privada de controle nacional que opera transmissão e geração  no Brasil e na América Latina. No Brasil, detém 9.576 km de linhas de transmissão  em 42 sistemas — a terceira maior transmissora privada do país em RAP.  No exterior, opera no Peru (6 projetos de transmissão + 1 PCH), na Colômbia  (PCH Morro Azul + 2 transmissoras, incluindo concessão VITALÍCIA) e no Chile.  O modelo é transmissão como core (~75% do EBITDA, RAP previsível)  complementado por geração (4 UHEs, 4 PCHs, 7 eólicos, 1 solar — 798 MW).  A geração serve para complementar, não como motor principal.  O grande diferencial: com 17% das receitas em USD após os projetos do Peru,  a Alupar reduz a exposição à regulação brasileira.  Está em ciclo pesado de capex (R$9 bi no ciclo atual), o que comprime o DY  hoje mas cria o pipeline de crescimento para os próximos 5-7 anos.",
        "receita": [
            ("RAP de transmissão Brasil", "~65%", "42 sistemas; IPCA e IGPM; projetos entrando até 2029"),
            ("Geração renovável Brasil", "~20%", "hídrica, eólica, PCH, solar — 798 MW; PPAs de longo prazo"),
            ("Transmissão e geração América Latina", "~15%", "Peru, Colômbia, Chile — crescente; parte em USD"),
        ],
        "vantagens": [
            "Controle 100% nacional: fundadores operam e são donos — alinhamento total de interesses",
            "Concessão vitalícia na Colômbia: ativo único no setor — RAP sem prazo de vencimento",
            "Expansão em USD (Peru): hedge natural contra depreciação do real",
            "Pipeline de entrada operacional: projetos entram até 2029 gerando RAP incremental",
            "TIR real implícita de ~8,1%: superior à Taesa (~4,7%) e próxima da ISA (~7,7%)",
        ],
        "riscos": [
            "Alavancagem em pico de ~4x: capex de R$9 bi nos próximos anos pressiona o balanço",
            "Risco regulatório externo: Peru, Colômbia e Chile têm marcos menos previsíveis que o Brasil",
            "DY atual baixo (~3%): ciclo de capex comprime dividendo; investidor de renda pode se frustrar",
            "Curtailment na geração eólica: afeta receita do segmento de geração",
            "Execução simultânea: 12 projetos em andamento, 9 fora do Brasil — gestão complexa",
        ],
        "barreira": "Concessões de 30 anos — e na Colômbia, vitalícia.  A capacidade de executar transmissão em países com regulação distinta é expertise  que poucos têm e que anos de presença no exterior constroem.  A escala de 9.576 km de linhas abre portas em leilões onde operadores menores  não conseguem participar. E o controle familiar alinhado  garante que o retorno ao acionista é o objetivo, não objetivos políticos.",
    },
    "AXIA3": {
        "nome": "Axia Energia (ex-Eletrobras)",
        "fundacao": "1961 (como Eletrobras); privatizada em 2022; renomeada Axia Energia em 2025",
        "sede": "Rio de Janeiro, RJ",
        "tagline": "A maior empresa do setor elétrico brasileiro. Privatizada em 2022, ainda digerindo a transição. TIR implícita de 10% real.",
        "modelo": "A Axia é a antiga Eletrobras — a maior empresa do setor elétrico brasileiro,  com cerca de 30 GW de capacidade instalada e participação em dezenas de  concessões de geração e transmissão. A privatização de 2022 foi o maior evento  do setor em décadas, mas a transição ainda está sendo digerida.  O portfólio tem uma peculiaridade: parte significativa das usinas opera em 'regime de cotas'  — um modelo regulatório onde a energia é dividida entre distribuidoras a preço fixo,  tirando a geração do mercado livre. O processo de 'descotização' (sair das cotas)  está em andamento mas é lento, o que significa que o portfólio ainda é menos  lucrativo do que poderia ser.  Em 2025 concluiu a migração para o Novo Mercado da B3, simplificou a estrutura  acionária e iniciou a venda de ativos não-estratégicos — são os primeiros sinais  de que a gestão privada está gerando valor.",
        "receita": [
            ("Geração hídrica em cotas", "~50%", "preço regulado; menos lucrativo que o mercado livre"),
            ("Geração hídrica em ACL (mercado livre)", "~30%", "preço de mercado — potencial de crescimento com descotização"),
            ("Transmissão (RAP)", "~15%", "concessões de transmissão em diversas regiões"),
        ],
        "vantagens": [
            "Maior empresa do setor — presença em praticamente todos os grandes projetos hídricos do Brasil",
            "TIR real implícita de ~10%: bem acima de pares de transmissão (~7-8%)",
            "Descotização: cada usina que sai das cotas entra no mercado livre a preço melhor — upside de longo prazo",
            "Novo Mercado: governança melhorando, estrutura acionária simplificada",
            "Custo de geração entre os mais baixos do mundo (hídrica velha = sem depreciação relevante)",
        ],
        "riscos": [
            "Risco político: governo ainda questiona aspectos do acordo de privatização; risco de revisão de termos",
            "Portfólio mais descontratado: menos energia comprometida em contratos de longo prazo vs pares",
            "Descotização é lenta: upside real ainda depende de decisões regulatórias e políticas",
            "Complexidade: dezenas de subsidiárias, concessões e participações — difícil de analisar",
            "GSF: maior exposição hídrica do setor = mais vulnerável à seca",
        ],
        "barreira": "São décadas de concessões hídrica em rios que já foram inventariados —  Tucuruí, Balbina, Itaipu (participação), Angra (nuclear): ativos que jamais serão  licenciados de novo. A escala de 30 GW e o papel sistêmico no SIN  (o ONS não opera sem a Axia) criam uma barreira que é, na prática, o próprio Brasil.",
    },
    "BBAS3": {
        "nome": "Banco do Brasil",
        "fundacao": "1808 (fundado por Dom João VI)",
        "sede": "Brasília, DF",
        "tagline": "O banco do agro e do funcionalismo. Líder incontestável no crédito rural, mas pagando o preço de uma carteira concentrada.",
        "modelo": "O BB tem três pilares que nenhum banco privado consegue replicar: o crédito rural (53% do crédito  agro brasileiro passa pelo BB, com funding subsidiado via FCO e PRONAF), o funcionalismo público  (processa metade das folhas do setor público federal e estadual — base de consignado captiva), e o  Tesouro Nacional (agente financeiro do governo federal). Fora isso, é um banco universal com  seguros (BB Seguridade, controlada listada separadamente) e gestão de ativos. O problema de 2025-2026  é exatamente essa concentração: o agro sofreu com El Niño, preços baixos de grãos e endividamento  acumulado. A inadimplência rural saltou de 1% para 6%, o lucro caiu 54% no 1T26 e o ROE colapsou  para 7,3%. A BB Seguridade, contudo, continua entregando — o banco dentro do banco que o mercado  frequentemente esquece.",
        "receita": [
            ("Margem financeira (NII)", "~45%", "crédito rural + consignado + corporate"),
            ("BB Seguridade (resultado de equivalência patrimonial)", "~20%", "seguros, previdência e capitalização"),
            ("Receitas de serviços e tarifas", "~20%", "folha de pagamento, asset management, tarifas"),
            ("Tesouraria e mercado", "~15%", "títulos públicos e operações com o governo"),
        ],
        "vantagens": [
            "Monopólio prático no crédito agro — nenhum banco privado tem a rede, o funding subsidiado e a expertise",
            "Folha do setor público: base captiva de consignado com inadimplência próxima de zero",
            "BB Seguridade: motor de resultado capital-light e recorrente dentro do conglomerado",
            "Valuation de desconto (P/L ~4x, P/VP ~0,6x) embute a percepção de risco estatal",
            "Gestão de ativos: 24,9% de market share — o maior gestor de recursos do Brasil",
        ],
        "riscos": [
            "Interferência política: governo pode forçar crédito subsidiado, reduzir spread e comprometer rentabilidade",
            "Concentração no agro: ciclos negativos (clima, preço de commodities) impactam desproporcionalmente",
            "Inadimplência rural 2025-2026: ainda longe do pico — pode demorar 2-3 anos para normalizar",
            "Menor eficiência operacional que bancos privados — custo de servir é mais alto",
        ],
        "barreira": "O acesso ao funding subsidiado (FCO, PRONAF, recursos do Tesouro) é uma barreira que nenhum banco  privado pode replicar. Quem financia agricultura a taxa de 7-8% a.a. quando o custo de mercado é 14%+  está usando um subsídio que só o banco estatal acessa. Isso cria uma vantagem competitiva no agro  que é, literalmente, impossível de replicar sem ser banco público.",
    },
    "BBDC3": {
        "nome": "Bradesco",
        "fundacao": "1943",
        "sede": "Osasco, SP",
        "tagline": "O gigante em reestruturação. Construído no interior do Brasil, foi o maior banco privado por décadas — agora recupera a rentabilidade.",
        "modelo": "O Bradesco é o único entre os grandes privados que foi construído de dentro para fora do Brasil —  nasceu em Marília (SP) e cresceu pelo interior antes de chegar às capitais. Essa origem explica  sua exposição à massa e às PMEs do interior, que são mais vulneráveis a ciclos de juros altos.  Em 2022-2024, o banco pagou o preço: inadimplência subindo, provisões estourando, ROE colapsando  para abaixo do custo de capital. A reestruturação de Marcelo Noronha (CEO desde 2023) levou o banco  a ser mais seletivo no crédito, a fechar agências, digitalizar e focar em alta renda e crédito  com garantia. O resultado começou a aparecer em 2025: lucro crescendo, ROE recuperando, ação  subindo 60% no ano. Em 2026, a tese é de quanto esse ROE ainda pode subir — e se chegará ao  nível de Itaú, ou ficará estacionado nos 15-17%.",
        "receita": [
            ("Margem financeira (NII)", "~50%", "spread de crédito PF + PME + corporativo"),
            ("Seguros (Bradesco Seguros)", "~20%", "vida, saúde, automóvel — joint venture com Munich Re"),
            ("Receitas de serviços e tarifas", "~18%", "cartão, previdência, corretagem"),
            ("Outros", "~12%", "mercado de capitais, câmbio, gestão de ativos"),
        ],
        "vantagens": [
            "Bradesco Seguros: uma das maiores seguradoras do Brasil — negócio capital-light com margens altas",
            "Rede capilar no interior: presença onde grandes bancos e fintechs chegam com mais dificuldade",
            "Reestruturação em curso: se o ROE normalizar para 18-20%, o valuation atual (P/L ~6x) está barato",
            "Cielo integrada: adquirência + produtos bancários criam potencial de cross-sell",
        ],
        "riscos": [
            "Execução: a reestruturação pode demorar mais ou entregar menos que o prometido",
            "Concorrência de fintechs no varejo massificado — o segmento que o Bradesco depende mais",
            "Exposição residual à massa de baixa renda, mais sensível a inadimplência em juro alto",
            "Valuation não é mais óbvio — após alta de 60% em 2025, o desconto já fechou parcialmente",
        ],
        "barreira": "A rede de distribuição no interior do Brasil é o ativo mais difícil de replicar.  Cidades de 30.000 habitantes onde o Bradesco é o único banco presente — e onde  a fintech não chega sem agência ou correspondente. Mais a Bradesco Seguros, que tem  escala e relacionamento de décadas com corretores.",
    },
    "BBSE3": {
        "nome": "BB Seguridade",
        "fundacao": "2012 (IPO)",
        "sede": "Brasília, DF",
        "tagline": "O maior pagador de dividendos do setor. Uma distribuidora de seguros disfarçada de seguradora — e isso é exatamente o que a torna tão lucrativa.",
        "modelo": "A BB Seguridade não assume risco de seguro. Ela distribui seguros, previdência e capitalização  pela rede do Banco do Brasil — 70 milhões de clientes, mais de 3.500 pontos de atendimento —  e cobra comissão. O risco de sinistro fica com os parceiros: Mapfre (seguros, JV 74,9% BB + 25,1% Mapfre)  e Principal Financial Group (previdência, via Brasilprev).  Estrutura capital-light com payout de ~85% — não precisa reter capital para cobrir sinistros.  O resultado tem dois motores: operacional (prêmios, corretagem, sinistralidade das parceiras)  e financeiro (reservas técnicas da Brasilprev e Brasilcap investidas na Selic).  Em juro alto o segundo motor turbina o lucro: no 1T26 foi +58,5% a/a e representou 23% do total.  O detalhe que muda tudo: o contrato de distribuição com o BB vai até 2033.  O mercado desconta esse risco no valuation — e o P/L de 8x vs. 13-14x histórico do mercado  é basicamente o 'preço' que o investidor paga pela incerteza de renovação.",
        "receita": [
            ("Seguro Rural (Brasilseg)", "~36%", "maior fatia do lucro — exposto ao agro, El Niño e inadimplência rural; líder com 62,9% de market share no seguro agrícola"),
            ("Previdência (Brasilprev)", "~23%", "maior gestora de previdência privada do Brasil; R$484 bi em reservas; turbinada pela Selic alta"),
            ("Prestamista (Brasilseg)", "~15%", "seguro que protege operações de crédito — cresce com o crédito consignado; sofre quando juros altos travam o crédito"),
            ("Vida (Brasilseg)", "~13%", "segmento mais estável e diversificador — menor volatilidade que rural ou prestamista"),
            ("Capitalização (Brasilcap)", "~6%", "títulos de capitalização — beneficiado pela Selic alta; cresce com ticket único"),
        ],
        "vantagens": [
            "Modelo capital-light: não assume risco de sinistro → payout de 85% → DY de 11-12%",
            "Canal exclusivo com 70 milhões de clientes do BB — custo de aquisição praticamente zero",
            "Brasilprev: líder em previdência privada no Brasil; reservas crescendo 10% a/a",
            "Resultado financeiro expressivo: Selic alta turbina o float das reservas de previdência e capitalização",
            "P/L de 8x — desconto histórico vs. média do mercado (13-14x)",
        ],
        "riscos": [
            "Contrato 2033: o acordo de distribuição com o BB vence daqui a ~7 anos — renovação, condições e custo são incertos; é o maior risco estrutural",
            "Selic caindo: resultado financeiro (23% do lucro em 1T26) cai imediatamente; recuperação operacional leva trimestres",
            "Seguro rural (~35% dos prêmios): El Niño, seca e inadimplência rural pressionaram a Brasilseg em 2024-2026",
            "Prestamista em queda: ligado ao crédito consignado — juro alto reduz tomada de crédito e, com ela, o seguro",
            "Guidance 2026 conservador: própria empresa projeta resultado operacional de -7% a -3% vs. 2025",
        ],
        "barreira": "O contrato de exclusividade com o BB e o tamanho da base de clientes são inreplicáveis.  Nenhuma seguradora privada tem acesso a 70 milhões de clientes com custo de aquisição zero.  Brasilprev é a maior gestora de previdência privada do Brasil — liderança construída em décadas.  O problema é que toda essa vantagem depende de um contrato com o estado.",
    },
    "BMGB4": {
        "nome": "Banco BMG",
        "fundacao": "1930 (família Pentagna Guimarães)",
        "sede": "Belo Horizonte, MG",
        "tagline": "O especialista em consignado INSS. Enquanto outros bancões atendem todo mundo, o BMG só atende aposentado — e isso é sua maior força.",
        "modelo": "O BMG é o banco mais nichado desta lista: 88% da carteira de crédito é formada  por aposentados e pensionistas do INSS.  O produto central é o empréstimo consignado, onde as parcelas são descontadas  diretamente do benefício do INSS — a inadimplência é estruturalmente baixa porque  o pagador não é a pessoa, é o governo federal.  A distribuição é feita por correspondentes bancários (terceiros que originam o crédito),  lojas próprias 'help! Loja de Crédito' (na cor laranja, reconhecível pelo público),  e canais digitais.  O desafio é que o governo regula a taxa máxima (hoje 1,85%/mês para o empréstimo e  2,46%/mês para o cartão). Quando a Selic sobe, o custo de captação sobe,  mas o teto de taxa não — o spread comprime.  Em 2025-2026, a CPI do INSS investigando fraudes no consignado criou obrigação de  biometria facial para cada contratação — adiciona fricção e pode frear a originação.",
        "receita": [
            ("Empréstimo consignado INSS", "~55%", "produto principal — taxa máxima 1,85%/mês"),
            ("Cartão consignado INSS", "~25%", "desconto direto no benefício — taxa máxima 2,46%/mês"),
            ("Consignado privado (CLT)", "~10%", "iniciado em 2025 — menor escala, maior risco"),
            ("Seguros e outros produtos", "~10%", "Bmg Seguradora — vida, acidentes pessoais"),
        ],
        "vantagens": [
            "Inadimplência estruturalmente baixa: parcelas descontadas direto do INSS — o devedor não pode deixar de pagar",
            "Base de aposentados é demograficamente crescente — 35 milhões de beneficiários do INSS e crescendo",
            "Reconhecimento de marca no público INSS: a cor laranja é sinônimo de consignado no interior do Brasil",
            "Correspondentes bancários capilarizados onde bancos tradicionais não chegam",
        ],
        "riscos": [
            "Teto regulatório de taxa: Selic sobe, mas o banco não consegue repassar — spread comprime estruturalmente",
            "CPI do INSS e fraudes no consignado: biometria obrigatória adiciona fricção e pode reduzir origação",
            "Concentração extrema em um segmento: qualquer mudança regulatória no consignado INSS impacta 88% da carteira",
            "ROE limitado pelo teto de taxa: difícil escalar margem acima de 12-14% com spread comprimido",
            "Consignado privado (CLT) em expansão — risco maior que o INSS, e o banco ainda está aprendendo o segmento",
        ],
        "barreira": "O reconhecimento de marca no público INSS e a rede de correspondentes são difíceis de replicar.  O aposentado do interior que reconhece a loja laranja e confia no 'consignado BMG'  não troca facilmente de banco. Além disso, os correspondentes que originam crédito  têm relacionamentos de anos com o BMG — e comissões que constroem lealdade.  A barreira não é tecnológica; é de relacionamento e presença física em regiões remotas.",
    },
    "BPAC11": {
        "nome": "BTG Pactual",
        "fundacao": "1983",
        "sede": "São Paulo, SP",
        "tagline": "O maior banco de investimento da América Latina. Não é um banco de varejo — é uma máquina de alocar capital.",
        "modelo": "O BTG é estruturalmente diferente dos outros: não tem agência, não quer o cliente de massa,  não cresce emprestando para pessoa física no cartão. Ele ganha dinheiro sendo o intermediário  entre quem tem capital (grandes fortunas, fundos) e quem precisa de capital (grandes empresas, governos).  A receita tem seis pilares: corporate lending (crédito para grandes empresas, ~R$2,3 bi/tri),  sales & trading (mesa proprietária e corretagem institucional), investment banking (IPOs, M&As, emissões),  asset management (R$2,5 tri sob gestão/administração), wealth management (R$1,28 tri — clientes private)  e consumer finance (Banco PAN + Too Seguros, consignado privado).  No 1T26 entregou lucro de R$4,8 bi (+42% a/a) e ROAE de 26,6%.  O modelo de partnership (sócios compram ações — alinhamento total) é um diferencial cultural único.",
        "receita": [
            ("Corporate Lending", "~23%", "crédito corporativo de alta qualidade — crescimento de 22% a/a"),
            ("Wealth Management", "~15%", "R$ 1,28 tri sob gestão — crescimento recorde"),
            ("Sales & Trading", "~19%", "mesa proprietária + corretagem institucional — volátil"),
            ("Asset Management", "~12%", "R$ 2,5 tri total — taxas de gestão e performance"),
            ("Consumer Finance & Banking", "~11%", "Banco PAN + Too Seguros — consignado privado"),
            ("Investment Banking", "~10%", "IPOs, M&As, emissões de dívida — cíclico"),
        ],
        "vantagens": [
            "Modelo de partnership: sócios são donos — incentivos alinhados, execução consistente há 40 anos",
            "Wealth Management: R$1,28 tri em assets com crescimento de 44,6% a/a — receita recorrente e crescente",
            "Corporate Lending: inadimplência próxima de zero em crédito para grandes empresas com garantias robustas",
            "Marca BTG no mercado de capitais: quando uma empresa quer captar R$1 bi+, o BTG está na lista curta",
            "Único entre os grandes a ter ROE acima de 26% de forma sustentada",
        ],
        "riscos": [
            "Valuation elevado (P/VP ~9x) não tolera desaceleração — crescimento tem que ser entregue",
            "Investment banking é cíclico — em mercados fechados (sem IPOs, sem M&A), essa linha murcha",
            "Dividend yield baixo (~2%) — não é banco de renda; é banco de crescimento e reinvestimento",
            "Risco-chave concentrado em poucos sócios-chave — risco de sucessão no longo prazo",
        ],
        "barreira": "A marca e o relacionamento de décadas com os grandes CEOs e CFOs do Brasil.  Não é possível construir isso da noite para o dia. Quando a Vale vai emitir uma debênture  ou o governo quer estruturar um projeto de infraestrutura, o BTG está na mesa.  Isso vem de 40 anos de execução impecável e de uma cultura de partnership que  atrai os melhores profissionais do mercado financeiro.",
    },
    "BRAP4": {
        "nome": "Bradespar S.A.",
        "fundacao": "2000 (spin-off do Bradesco para concentrar participações industriais)",
        "sede": "São Paulo, SP",
        "tagline": "A forma de ter Vale com desconto. Holding que detém ~4,5% da Vale — sem operar uma única mina. O rendimento é o dividendo da Vale amplificado pelo desconto de NAV.",
        "modelo": "A Bradespar é uma holding de participações controlada pelo banco Bradesco.  Seu único ativo relevante é uma participação de ~4,5% na Vale.  Não opera mina, não tem receita operacional, não tem funcionários de mineração.  O resultado é o dividendo recebido da Vale, menos as despesas da holding.  A tese de investimento é simples: a Bradespar negocia com desconto de NAV  (valor de mercado < valor das ações da Vale que ela possui).  Por que o desconto existe? Custos da holding, liquidez menor que a Vale,  risco de governança (Bradesco decide o que fazer com a participação)  e impostos sobre o dividendo ao longo da cadeia.  Quando o desconto se fecha — por buyback, venda de ações ou elevação do dividendo —  o acionista da Bradespar captura um retorno extra além da variação da Vale.",
        "receita": [
            ("Dividendos e JCP da Vale", "~95%", "proporcional à participação de ~4,5% e ao dividendo declarado pela Vale"),
            ("Resultado financeiro e outros", "~5%", "caixa próprio aplicado em renda fixa"),
        ],
        "vantagens": [
            "Desconto de NAV: comprar Bradespar = comprar Vale mais barato que o mercado",
            "DY amplificado pelo desconto: o yield efetivo sobre o NAV é maior que comprar Vale direto",
            "Exposição indireta ao cobre/níquel via Vale: tese de transição energética embutida",
            "Simplicidade: não tem risco operacional, ambiental nem de produção — só participação financeira",
        ],
        "riscos": [
            "Desconto de NAV pode persistir ou ampliar: holding costuma negociar com desconto estrutural",
            "Custos da holding corroem o NAV: despesas administrativas e impostos reduzem o retorno líquido",
            "Decisão do Bradesco: controlador pode vender a participação na Vale em momento ruim",
            "Dupla tributação: dividendo da Vale → Bradespar → acionista tem mais um passo tributário",
            "Liquidez menor que Vale: spread bid/ask maior; mais difícil de sair em momentos de estresse",
        ],
        "barreira": "A barreira da Bradespar é o próprio desconto de NAV —  quem quer comprar Vale com desconto precisa comprar a Bradespar.  Mas não é uma barreira de negócio:  qualquer um pode comprar Vale diretamente.  A tese funciona enquanto o desconto existir e enquanto a Vale pagar dividendos.  Se o desconto fechar, a vantagem da Bradespar desaparece.",
    },
    "BRAV3": {
        "nome": "Brava Energia",
        "fundacao": "2024 (fusão 3R Petroleum + Enauta)",
        "sede": "Rio de Janeiro, RJ",
        "tagline": "A junior oil em consolidação. Nasceu da fusão de dois modelos distintos — ainda provando que o todo vale mais que as partes. OPA da Ecopetrol coloca o horizonte em suspenso.",
        "modelo": "A Brava Energia nasceu em setembro de 2024 da fusão entre a 3R Petroleum  (campos maduros onshore e offshore) e a Enauta (campo de Atlanta).  Atlanta é o ativo premium da empresa: óleo leve de altíssima qualidade,  offshore no Espírito Santo, com menor desconto no Brent.  Os campos de Papa-Terra (óleo pesado, Bacia de Campos) e de gás  (Peroá e Manati, offshore) completam o portfólio.  Em janeiro de 2026, comprou 50% de Tartaruga Verde e Espadarte por US$450 mi  — campos operados pela Petrobras com 14 poços produtores e produção  de ~55 kboed a 100%.  Em maio de 2026, a Ecopetrol (estatal colombiana) lançou OPA  para assumir 51% da empresa a R$23/ação (prêmio de até 28%).  A operação aguarda aprovação do CADE e da ANP — e muda completamente  o perfil de risco da empresa se concluída.",
        "receita": [
            ("Atlanta (óleo leve offshore)", "~35%", "óleo premium; menor desconto vs Brent; principal ativo da Enauta"),
            ("Papa-Terra (óleo pesado offshore)", "~25%", "FPSO P-63; óleo viscoso com maior desconto no Brent"),
            ("Tartaruga Verde + Espadarte (novo)", "~15%", "50% adquiridos em 2026; operado pela Petrobras; 14 poços"),
            ("Gás natural (Peroá, Manati)", "~15%", "offshore ES/BA; escoamento via gasodutos"),
            ("Campos onshore 3R", "~10%", "herdados da 3R; menor prioridade estratégica"),
        ],
        "vantagens": [
            "Atlanta: óleo leve de alta qualidade — menor desconto vs Brent, maior preço realizado",
            "2ª maior independente em reservas: escala que abre portas em desinvestimentos de grandes petroleiras",
            "OPA Ecopetrol a R$23: piso de preço no curto prazo com prêmio de 28%",
            "Tartaruga Verde: 14 poços produtores, operado pela Petrobras — produção previsível e já funcionando",
            "Diversificação de portfólio: onshore + offshore + gás + óleo leve + óleo pesado",
        ],
        "riscos": [
            "Integração pós-fusão não provada: 3R e Enauta tinham culturas e sistemas operacionais distintos",
            "Alavancagem alta: dívida da fusão + US$450 mi de Tartaruga Verde = balanço apertado",
            "OPA Ecopetrol incerta: aprovação de CADE e ANP pode demorar ou não acontecer",
            "Papa-Terra: óleo pesado = maior desconto no Brent e campo operacionalmente mais complexo",
            "FCF neutro em 2026: alta produção, mas capex pesado e dívida consomem o caixa",
        ],
        "barreira": "Atlanta é o principal ativo de barreira — campo de óleo leve offshore  que a Enauta levou anos para desenvolver e que poucos independentes  conseguiriam financiar.  O know-how da Enauta em desenvolvimento greenfield offshore  é raro no Brasil fora da Petrobras.  Mas a Brava ainda está construindo sua identidade pós-fusão —  a barreira real ainda está sendo testada na execução.",
    },
    "BRSR6": {
        "nome": "Banrisul",
        "fundacao": "1928",
        "sede": "Porto Alegre, RS",
        "tagline": "O banco do Rio Grande do Sul. Seu destino é o destino do RS — e do contrato com o governo estadual.",
        "modelo": "O Banrisul é um banco estatal regional — o que significa que seu modelo de negócio  é fundamentalmente diferente de todos os outros nesta lista.  Ele existe porque o governo do RS quer um banco público estadual.  O coração do negócio é a folha de pagamento dos servidores públicos gaúchos:  294 mil servidores ativos, inativos e pensionistas cujo salário passa pelo Banrisul,  gerando uma base captiva de consignado, conta corrente e produtos financeiros.  Em julho de 2026, renovou esse contrato por R$1,26 bi — pago à vista, reconhecido como  intangível e amortizado ao longo de 5 anos. O custo dobrou em relação à renovação  anterior (que era de 10 anos). Fora a folha, atende PMEs gaúchas e o varejo do RS.  Toda a sua força e seu risco estão concentrados em um único estado.",
        "receita": [
            ("Crédito consignado público (servidores RS)", "~40%", "base captiva da folha estadual"),
            ("Varejo PF e PME gaúcha", "~35%", "clientes pessoas físicas e pequenas empresas do RS"),
            ("Receitas de serviços", "~15%", "tarifas, previdência, seguros"),
            ("Tesouraria", "~10%", "títulos públicos e operações de mercado"),
        ],
        "vantagens": [
            "Base captiva de consignado público — 294 mil servidores estaduais com desconto em folha",
            "Valuation muito barato (P/VP ~0,5x, P/L ~3x) — desconta o risco político e o ROE baixo",
            "Dividend yield alto (~9-11%) — governo precisa do dividendo do banco para compor receitas estaduais",
            "Presença capilar no interior do RS onde os grandes bancos privados não chegam",
        ],
        "riscos": [
            "100% concentrado no RS — enchentes, seca, recessão regional batem direto no resultado",
            "Dependência do contrato de folha: renovado a custo crescente (dobrou por ano de contrato na última renovação)",
            "ROE cronicamente baixo (~7-9%) — estruturalmente abaixo do custo de capital",
            "Risco político: troca de governo estadual pode mudar a relação ou condições do contrato",
            "Qualidade de crédito pressionada em PF e PME, com inadimplência subindo em 2026",
        ],
        "barreira": "O contrato com o governo do RS é a barreira — e também o risco.  Nenhum banco privado vai entrar no estado para fazer o que o Banrisul faz  sem o benefício do funding barato do servidor e a capilaridade de 500+ agências no interior.  Mas essa barreira tem preço: R$1,26 bi a cada 5 anos só para manter o que já tem.",
    },
    "CMIG4": {
        "nome": "Cemig",
        "fundacao": "1952 (por Juscelino Kubitschek)",
        "sede": "Belo Horizonte, MG",
        "tagline": "A estatal integrada de Minas Gerais. Maior distribuidora do Brasil, com risco político que o mercado desconta no preço.",
        "modelo": "A Cemig é uma holding integrada — opera distribuição (Cemig D),  geração e transmissão (Cemig GT) e tem participações em outras empresas do setor.  É a maior distribuidora do Brasil em número de municípios atendidos e a quarta  em transmissão. Controlada pelo Estado de Minas Gerais (50,97% das ONs),  sofre com o conflito clássico do estatal: o governo quer dividendos para fechar  as contas do estado, mas também quer tarifas baixas para os eleitores.  Em 2025, gerou discussão sobre possível federalização como parte do acordo  da dívida de MG com o governo federal — um risco que assusta o mercado  mas ainda não se concretizou.",
        "receita": [
            ("Distribuição Minas Gerais (Cemig D)", "~55%", "maior distribuidora do Brasil em cobertura geográfica"),
            ("Geração hídrica e eólica (Cemig GT)", "~30%", "portfólio diversificado, mas com exposição hídrica"),
            ("Transmissão", "~10%", "4ª maior do Brasil"),
        ],
        "vantagens": [
            "Escala: maior distribuidora em municípios atendidos — MG tem 853 municípios",
            "DY alto (8-12%): governo precisa de dividendo para fechar as contas do estado",
            "Valuation descontado pelo risco político: quem acredita no desconto pode se beneficiar",
            "Portfólio diversificado: geração + transmissão + distribuição reduz concentração em um segmento",
        ],
        "riscos": [
            "Risco político: governo MG intervém em gestão, tarifa e alocação de capital",
            "Debate de federalização: dívida de MG com a União pode levar à transferência do controle",
            "Posição vendida em energia: Cemig ficou descoberta em contratos de energia, gerando prejuízo",
            "Alavancagem ~2,3-2,5x: não é crítico mas limita flexibilidade",
            "Eficiência abaixo de privados: custo de servir mais alto por natureza estatal",
        ],
        "barreira": "A concessão de distribuição em Minas Gerais — o estado mais rico em recursos naturais  e o terceiro maior estado em PIB do Brasil.  O portfólio de usinas hidrelétricas em rios mineiros é inreplicável.  O problema: a barreira é do Estado de MG, não da empresa —  e o controlador pode usá-la para objetivos políticos em vez de econômicos.",
    },
    "CMIN3": {
        "nome": "CSN Mineração S.A.",
        "fundacao": "1977 (como área de mineração da CSN; IPO em 2021)",
        "sede": "São Paulo, SP",
        "tagline": "A segunda maior mineradora de ferro do Brasil. Operação concentrada no Quadrilátero Ferrífero — puro jogo de preço do minério, câmbio e custo C1.",
        "modelo": "A CSN Mineração é a operação de mineração da CSN (Companhia Siderúrgica Nacional),  separada em empresa independente e aberta em IPO em 2021.  Opera no Quadrilátero Ferrífero (MG), na mina Casa de Pedra —  uma das maiores minas a céu aberto do Brasil.  O modelo é simples e direto: extrai minério de ferro (62% Fe),  transporta via MRS Logística até o Terminal de Carvão (TECAR) no Porto de Itaguaí (RJ)  e exporta, principalmente para a China.  Uma parte significativa do minério abastece a própria CSN  (que produz aço e precisa de minério) — captivo interno com preço de mercado.  Produziu recorde de 45,5 milhões de toneladas em 2025 (+4,6% acima do guidance).  Custo C1 de US$23,1/t no 1T26 — competitivo, mas sem o prêmio de qualidade da Vale.",
        "receita": [
            ("Exportação de minério de ferro (62% Fe)", "~70%", "China é o principal destino; preço benchmark 62% Fe CFR"),
            ("Vendas para CSN (mercado interno)", "~20%", "captivo — a controladora usa o minério para produzir aço"),
            ("Pelotas e outros produtos", "~10%", "valor agregado sobre o minério bruto"),
        ],
        "vantagens": [
            "Custo C1 competitivo (~US$23/t): eficiência operacional que sustenta margem mesmo com minério deprimido",
            "Produção recorde em 2025: 45,5 mi t — prova de capacidade operacional crescente",
            "Logística integrada via MRS até Itaguaí: escoamento eficiente sem gargalo logístico",
            "Captivo interno (CSN): parte da receita não depende do mercado internacional",
            "Alavancagem baixa: balanço saudável que permite dividendos mesmo em ciclo fraco",
        ],
        "riscos": [
            "Ferro puro sem diversificação: 100% do resultado depende do preço do minério 62% Fe",
            "Sem prêmio de qualidade: vende ao benchmark — não tem o diferencial da Vale em Carajás",
            "Controladora CSN (78%): conflito de interesse potencial — CSN pode extrair caixa da CMIN em detrimento de minoritários",
            "Dependência da China: perfil de exportação muito concentrado no mercado asiático",
            "FCF volátil: capex de crescimento e compras de minério de terceiros criam oscilações no caixa",
        ],
        "barreira": "Casa de Pedra é uma das maiores reservas de minério de ferro do Quadrilátero Ferrífero.  Mas a barreira da CMIN é menor que a da Vale —  o minério 62% Fe é mais padronizado e os produtores australianos  (Rio Tinto, BHP) têm custo C1 de US$18-20/t, abaixo da CMIN.  A barreira real é operacional: a logística via MRS + Itaguaí  e a integração com a CSN criam um sistema que funciona  há décadas e não é fácil de desmontar.",
    },
    "CPFE3": {
        "nome": "CPFL Energia",
        "fundacao": "1912",
        "sede": "Campinas, SP",
        "tagline": "A distribuidora integrada com a maior capilaridade do Sudeste. DY consistente de 8-9% e controlador chinês que quer estabilidade.",
        "modelo": "A CPFL é uma das maiores empresas do setor elétrico brasileiro, com presença  em distribuição (14% do mercado nacional, 10,3 mi de clientes em 687 municípios),  geração (4.411 MW, entre as maiores privadas) e transmissão.  Controlada desde 2017 pela State Grid Corporation of China — a maior empresa  de energia do mundo, atendendo 1,1 bilhão de pessoas.  O controlador quer estabilidade e dividendos, não aventura: o plano de R$29,8 bi  para 2025-2029 foca em modernizar a distribuição existente (R$24,7 bi em distribuição),  não em crescer por aquisições agressivas.  Em maio de 2026, renovou as concessões das três distribuidoras principais  (CPFL Paulista, Piratininga, RGE) por mais 30 anos — uma redução relevante de  risco de prazo que o mercado subestimou.",
        "receita": [
            ("Distribuição de energia (CPFL Paulista, Piratininga, RGE, Santa Cruz)", "~65%", "2ª maior distribuidora do Brasil em volume"),
            ("Geração (hídrica + eólica + solar + biomassa)", "~25%", "4.411 MW de capacidade instalada"),
            ("Transmissão (CPFL Transmissão)", "~8%", "RAP de linhas de transmissão"),
        ],
        "vantagens": [
            "Concessões renovadas por 30 anos em 2026: risco de prazo eliminado para as principais distribuidoras",
            "State Grid como controlador: acesso a capital barato (empréstimo em RMB do NDB), tecnologia chinesa e planejamento de longo prazo",
            "2ª maior distribuidora em volume: escala que poucos concorrentes têm no Sudeste",
            "DY consistente de 8-9%: controlador quer dividendo; payout de 78% é sustentável",
            "Gestão operacional eficiente: CPFL tem histórico de índices de qualidade acima da média do setor",
        ],
        "riscos": [
            "Controlador chinês: geopolítica pode criar ruído regulatório ou político no futuro",
            "Revisão tarifária: WACC regulatório da ANEEL define a rentabilidade da distribuição — risco periódico",
            "Alavancagem moderada e capex de R$29,8 bi: FCF comprometido para crescimento, não para DY extra",
            "Exposição ao Sudeste: crescimento da GD (painéis solares) pode reduzir consumo faturado das distribuidoras",
            "Mercado Livre: migração de grandes clientes para ACL reduz base de consumidores cativos",
        ],
        "barreira": "687 municípios com concessão exclusiva de distribuição no Sudeste e Sul.  Nenhum concorrente entra nesse território — a concessão é de 30 anos, renovada.  A combinação de escala, capilaridade e o apoio da maior empresa de energia do  mundo como controlador cria uma posição que é inatingível por qualquer novo entrante.",
    },
    "CPLE3": {
        "nome": "Copel",
        "fundacao": "1954",
        "sede": "Curitiba, PR",
        "tagline": "A ex-estatal do Paraná. Privatizada em 2023, agora sob gestão privada buscando eficiência que o Estado nunca priorizou.",
        "modelo": "A Copel é a empresa integrada de energia do Paraná — geração (hídrica no rio Iguaçu  e afluentes), transmissão e distribuição. Em 2023, foi privatizada pelo governo do Paraná,  encerrando 70 anos como estatal. A privatização abriu espaço para buscar eficiência  operacional, reduzir custos e orientar a gestão para retorno ao acionista  em vez de objetivos políticos.  Diferente da Cemig (que ainda é estatal), a Copel já não tem o risco  de interferência política do governo. Mas ainda está no processo de ajuste  pós-privatização: normalização do resultado financeiro, revisão de contratos  e alinhamento da cultura organizacional ao modelo privado leva tempo.",
        "receita": [
            ("Distribuição Paraná (Copel DIS)", "~55%", "distribuição regulada em todo o estado do Paraná"),
            ("Geração hídrica + eólica (Copel GeT)", "~30%", "Iguaçu, Jordão e complexos eólicos"),
            ("Transmissão (Copel Transmissão)", "~12%", "RAP de linhas em todo o Brasil"),
            ("Telecomunicações (Copel Telecom)", "~3%", "fibra óptica no Paraná — diferencial único"),
        ],
        "vantagens": [
            "Privatização recente: gestão privada ainda capturando eficiência que o estado não priorizou",
            "Única utility listada com braço de telecom próprio: Copel Telecom é diferencial raro no setor",
            "Paraná: estado com melhor qualidade de crédito e menor inadimplência do Brasil — base de consumidores sólida",
            "Geração hídrica no Iguaçu: hidrologia de boa qualidade no Sul (diferente do Sudeste/Nordeste)",
        ],
        "riscos": [
            "Resultado pós-privatização ainda normalizando: curva de aprendizado da gestão privada",
            "Alavancagem: ciclo de investimentos pós-privatização pressiona o balanço",
            "Hidrologia Sul: enchentes no RS/SC em 2024 mostraram que o Sul também tem risco climático",
            "Copel Telecom: negócio diferente do core elétrico, exige expertise e capex específicos",
        ],
        "barreira": "Concessão exclusiva de distribuição em todo o Paraná — um estado de 11 mi de habitantes  e PIB relevante. As usinas do rio Iguaçu são um dos maiores sistemas hídricos do Sul  e são inreplicáveis. A rede de transmissão de fibra óptica da Copel Telecom  seria levada décadas para ser construída por qualquer entrante.  Pós-privatização, o risco de interferência política foi eliminado —  a barreira ficou mais limpa.",
    },
    "CSMG3": {
        "nome": "Copasa (Companhia de Saneamento de Minas Gerais)",
        "fundacao": "1963 (como COMAG; Copasa desde 1974)",
        "sede": "Belo Horizonte, MG",
        "tagline": "A segunda maior privatização de saneamento do Brasil — concluída em junho de 2026. Mesma Equatorial, mesmo playbook, maior WACC regulatório. O turnaround começa agora.",
        "modelo": "A Copasa atende Minas Gerais — o maior estado do Brasil em extensão territorial,  com importantes economias agropecuária, industrial e mineral.  Em junho de 2026, o governo de MG concluiu a privatização:  a Equatorial assumiu ~30% como investidora de referência,  em operação estimada em R$8-10 bi.  O diferencial estrutural da Copasa vs Sabesp: o WACC regulatório.  A ARSAE (agência mineira) fixou WACC real de ~9,42% vs ~7,86% da ARSESP.  Isso significa que MG remunera cada real de ativo regulatório a uma taxa 20% maior  que São Paulo — mesmo com BRR menor, a rentabilidade por real investido é superior.  O playbook é idêntico ao da Sabesp: turnaround operacional  (EBITDA projetado de R$3,5 bi em 2026 para R$6,1 bi em 2028, CAGR de 30%+),  aceleração de capex (R$3,1 bi em 2026 a R$4,5 bi em 2030)  e crescimento da BRR de R$15,5 bi para R$36+ bi até 2030.",
        "receita": [
            ("Água — tarifa regulada (ARSAE/MG)", "~60%", "abastecimento em MG; 3ª revisão tarifária com reajuste de 6,56% em 2026"),
            ("Esgoto — tarifa regulada", "~38%", "cobertura de esgoto ainda abaixo da média nacional — maior espaço de crescimento"),
            ("Resíduos e outros", "~2%", "coleta e tratamento de resíduos industriais; serviços complementares"),
        ],
        "vantagens": [
            "WACC regulatório de 9,42% real: 20% maior que Sabesp — maior retorno por real de ativo reconhecido",
            "Maior crescimento relativo da BRR: de R$15,5 bi para R$36 bi até 2030 (vs crescimento proporcionalmente menor da Sabesp)",
            "Mesmo controlador da Sabesp: Equatorial com playbook comprovado — menos incerteza de execução",
            "Valuation ainda atrativo: ação subiu 126% em 12 meses mas ainda negocia abaixo de pares privatizados equivalentes",
            "MG tem grande déficit de esgoto: enorme runway de universalização = décadas de crescimento da BRR",
        ],
        "riscos": [
            "Turnaround ainda no início: privatização concluída em junho — ganhos de eficiência ainda a capturar",
            "Concessionamento de BH: renovação do contrato com Belo Horizonte foi condição da privatização — qualquer ajuste impacta a base",
            "Regulação mineira: ARSAE pode ser mais conservadora que ARSESP no reconhecimento de investimentos",
            "Risco político residual: Estado de MG retém 5% + golden share — ainda pode interferir em decisões estratégicas",
            "Valuation precificou boa parte: ação já subiu muito com expectativa de privatização; execução precisa corresponder",
        ],
        "barreira": "Monopólio regulado em Minas Gerais — mesmo modelo da Sabesp.  Mas a Copasa tem uma vantagem adicional: o WACC mais alto da ARSAE  cria uma 'vantagem regulatória' estrutural que não depende de gestão,  mas de metodologia da agência.  E com a Equatorial como controladora — que já provou em 7 distribuidoras de energia  que consegue transformar ativos ineficientes em geradores de valor —  a tese de turnaround tem o executor mais credenciado do setor.",
    },
    "CURY3": {
        "nome": "Cury Construtora e Incorporadora",
        "fundacao": "1963 (por Elias Cury em São Paulo)",
        "sede": "São Paulo, SP",
        "tagline": "A incorporadora de MCMV com o maior ROE do Brasil. Em 63 anos, nunca vendeu um imóvel fora do programa habitacional — e é exatamente isso que a torna tão rentável.",
        "modelo": "A Cury é uma das mais puras histórias de foco do mercado imobiliário brasileiro.  Em 63 anos de história, atua quase exclusivamente no MCMV —  em São Paulo e Rio de Janeiro metropolitano, nas faixas mais altas do programa.  O modelo tem três vantagens estruturais que se reforçam mutuamente.  Primeiro, o crédito: FGTS a 4-10,5% ao ano não muda com a Selic —  quando o mercado de médio padrão desacelera, a Cury continua vendendo.  Segundo, a localização: empreendimentos em áreas centrais próximas a metrô e  serviços, diferente de concorrentes que vão para a periferia mais barata.  Terceiro, o método construtivo: alvenaria estrutural (blocos de concreto)  permite flexibilidade de planta, custo controlado e velocidade de entrega.  O resultado: ROE de 79,5% no 1T26 — o mais alto do setor — mesmo com caixa líquido  positivo, o que demonstra que a geração de caixa é real, não alavancada.  Entre 2020 e 2025, multiplicou receita em 5x, VGV em 5,5x e lucro em 5,7x.",
        "receita": [
            ("MCMV faixas 2, 3 e 4 — São Paulo", "~65%", "principal mercado; áreas centrais com transporte; ticket médio crescente"),
            ("MCMV faixas 2, 3 e 4 — Rio de Janeiro", "~35%", "segundo mercado; expansão acelerada nos últimos 3 anos"),
        ],
        "vantagens": [
            "ROE de 79,5% (1T26) — o mais alto do setor, mesmo sendo caixa líquido positivo",
            "MCMV imune à Selic: crédito a 4-10,5% via FGTS não muda com a taxa de mercado",
            "Localização diferenciada: empreendimentos próximos ao metrô em SP/RJ — demanda captiva",
            "Landbank de R$24,9 bi com 3+ anos de visibilidade — crescimento previsível",
            "Velocidade de vendas (VSO) de 46% no 1T26 — a mais alta do setor",
        ],
        "riscos": [
            "Zero diversificação: qualquer mudança nas regras do MCMV ou FGTS impacta 100% da receita",
            "Concentração em SP e RJ: dois mercados, sem diversificação geográfica",
            "Escassez de mão de obra: causou atrasos em obras em 2025; produtividade em recuperação em 2026",
            "Sucessão executiva: modelo de Co-CEO anunciado em 2026 — transição de gestão é risco de curto prazo",
            "Valuation esticado: P/L de 7-8x para uma empresa de MCMV é acima da média histórica do setor",
        ],
        "barreira": "63 anos construindo para o mesmo público no mesmo mercado.  A Cury conhece cada zona de uso de São Paulo e Rio de Janeiro como ninguém.  Sabe onde tem metro previsto, onde vai ter densificação, onde o terreno ainda está barato.  Esse banco de dados de décadas de relacionamento com prefeituras,  vendedores de terreno e a Caixa Econômica Federal é inreplicável.  Qualquer entrante levaria anos para construir a rede de relacionamentos  que permite a Cury comprar terreno antes do concorrente saber que está à venda.",
    },
    "CXSE3": {
        "nome": "Caixa Seguridade",
        "fundacao": "2015 (IPO em 2021)",
        "sede": "Brasília, DF",
        "tagline": "A distribuidora do crédito habitacional. Onde tem financiamento da Caixa, tem seguro da CXSE — e por lei.",
        "modelo": "A lógica da CXSE é idêntica à da BBSE: distribui seguros pela rede da Caixa Econômica Federal  e recebe comissão sem assumir o risco de sinistro. Mas o produto-âncora é diferente — e mais defensivo.  Todo financiamento imobiliário no Brasil exige por lei dois seguros obrigatórios: MIP (Morte e Invalidez)  e DFI (Danos Físicos ao Imóvel). São embutidos na parcela e cobrados por 10 a 35 anos.  Cada novo financiamento da Caixa (que detém mais de R$1 tri em carteira imobiliária)  gera automaticamente mais um contrato de seguro que dura décadas — é o efeito empilhamento.  A base de recorrência cresce enquanto os contratos antigos ainda estão ativos e os novos chegam.  No 1T26 entregou lucro de ~R$1,14 bi (+ROE de 65,9%) e DY projetado de ~7-8% para 2026.",
        "receita": [
            ("Seguro habitacional (MIP + DFI)", "~55%", "obrigatório por lei — base recorrente e crescente"),
            ("Prestamista e vida", "~20%", "seguro do crédito consignado e pessoal da Caixa"),
            ("Previdência e capitalização", "~15%", "produtos financeiros da rede Caixa"),
            ("Residencial e outros", "~10%", "seguros patrimoniais para clientes da Caixa"),
        ],
        "vantagens": [
            "Efeito empilhamento: cada financiamento gera contrato de 10-35 anos — recorrência que cresce automaticamente",
            "Seguro habitacional é obrigatório por lei — não há opção de 'não comprar' para quem financia",
            "Mais de 60% de market share em seguro habitacional — posição de dominância que nenhum concorrente replica",
            "Canal com 4.000 agências + 13.000 lotéricas — capilaridade ímpar para o público de menor renda",
            "ROE de 65,9% no 1T26 — extraordinário para qualquer empresa, de qualquer setor",
        ],
        "riscos": [
            "100% dependente da Caixa como canal e controladora — risco político estatal elevado",
            "Prestamista pressionado: juros altos reduzem crédito consignado e pessoal",
            "Resultado financeiro ajuda hoje (Selic alta), mas perde força quando os juros caírem",
            "Valuation mais esticado que BBSE — P/L de 11-13x já precifica boa parte da qualidade",
            "Qualquer mudança na política habitacional federal (FGTS, Minha Casa) impacta diretamente",
        ],
        "barreira": "A exclusividade com a Caixa + a lei que obriga o seguro habitacional = monopólio prático.  Nenhuma seguradora privada consegue entrar nesse mercado sem ser o parceiro oficial da CEF.  E o efeito empilhamento cria uma receita que cresce por décadas sem esforço de vendas adicional —  é o modelo mais defensivo e previsível de toda a lista.",
    },
    "CYRE3": {
        "nome": "Cyrela Brazil Realty",
        "fundacao": "1962 (por Elie Horn em São Paulo)",
        "sede": "São Paulo, SP",
        "tagline": "A maior incorporadora de alto padrão de São Paulo. Três marcas, três segmentos, uma cidade que concentra 60% do mercado de luxo do Brasil.",
        "modelo": "A Cyrela é a empresa mais complexa do setor listado.  Opera com três marcas próprias (Cyrela para alto padrão, Living para médio,  Vivaz para MCMV) e tem participação em cinco JVs listadas na B3  (Lavvi, Plano&Plano, Cury, entre outras).  O core é o alto padrão em São Paulo — onde projetos de R$2+ bi de VGV  como o Epic by Pininfarina (210 metros, maior residencial de SP)  definem a marca. A estratégia funciona em ciclos de juros baixos:  o comprador de luxo financia parte do imóvel, e com crédito barato  aumenta o poder de compra. Em juros altos, o efeito inverte.  Em 2026, os lançamentos de alto padrão caíram 71% — o mercado esperou.  A Vivaz (MCMV) compensa parcialmente, mas com margem e ROE muito menores.  As JVs listadas (especialmente Cury) criam valor que não aparece no P/L da Cyrela.",
        "receita": [
            ("Alto padrão — marca Cyrela", "~51%", "São Paulo; projetos icônicos de R$500 mil a R$5 mi por unidade"),
            ("Médio padrão — marca Living", "~23%", "classe média SP e outras praças; mais sensível à Selic"),
            ("MCMV — marca Vivaz", "~26%", "parceria com Caixa; crescendo para compensar o alto padrão"),
        ],
        "vantagens": [
            "Marca premium de 60 anos: 'Cyrela' é sinônimo de qualidade na cabeça do comprador de alto padrão em SP",
            "Projetos icônicos: Epic by Pininfarina (VGV R$2 bi) — não é construção, é obra de arte vendável",
            "JVs listadas (Cury, Lavvi): participação em empresas de alto crescimento que criam valor não precificado",
            "Diversificação de segmento: quando o alto padrão desacelera, Vivaz sustenta a operação",
            "Geração de caixa sólida: mesmo com ROE baixo, converte bem lucro em caixa",
        ],
        "riscos": [
            "ROE de 11% no 1T26 — muito abaixo dos pares MCMV (Cury 79%, Direcional 44%)",
            "Alto padrão sensível à Selic: lançamentos caíram 71% no 1T26 com juros altos",
            "Concorrência crescente no luxo: JHSF, Lavvi e incorporadoras internacionais disputam o mesmo público",
            "Vivaz com margem menor: o crescimento que compensa o alto padrão vem com ROE inferior",
            "Mercado concentrado em SP: 60%+ do resultado vem de uma única praça",
        ],
        "barreira": "A marca Cyrela é a barreira — e é uma barreira cultural, não financeira.  Um comprador que paga R$3 mi por um apartamento compra o endereço,  o nome do arquiteto e o status da construtora.  60 anos construindo em São Paulo com qualidade consistente  criam um ativo intangível que nenhum novo entrante replica em menos de duas décadas.  E a carteira de JVs com incorporadoras de crescimento  (Cury, Lavvi) cria um portfólio diversificado que o mercado ainda não precifica corretamente.",
    },
    "DIRR3": {
        "nome": "Direcional Engenharia",
        "fundacao": "1981 (por Ricardo Valadares Gontijo em Belo Horizonte)",
        "sede": "Belo Horizonte, MG",
        "tagline": "A maior construtora do Brasil em área. Dois segmentos, dois clientes, oito estados — e um modelo de permuta que deixa o caixa livre enquanto o landbank cresce.",
        "modelo": "A Direcional tem um modelo operacional de eficiência industrial.  Opera em dois segmentos: a marca Direcional (MCMV faixas 2 e 3 — baixa renda)  e a marca Riva (médio-baixo padrão, apartamentos até R$500 mil —  que passou a ser enquadrada no MCMV faixa 4 em 2026).  Presente em 8 estados e no DF, é a maior construtora em área do Brasil.  O que diferencia a Direcional dos concorrentes é a combinação de três fatores.  Primeiro, o método construtivo industrializado com formas de alumínio —  encurta o ciclo de obra, reduz desperdício e viabiliza escala nacional.  Segundo, o modelo de permuta: 86% do landbank é adquirido via permuta —  o terreno entra como pagamento de unidades futuras, sem desembolso de caixa.  Terceiro, o crédito associativo: no MCMV, o risco de inadimplência transfere  para o banco financiador na assinatura do contrato — a Direcional recebe  sem risco de o comprador não pagar.  No 1T26: receita de R$1,2 bi (+30% a/a), lucro de R$200 mi (+27%),  margem bruta ajustada de 42,9% — a maior do setor.",
        "receita": [
            ("Direcional (MCMV faixas 2 e 3)", "~55%", "8 estados e DF; método industrializado; alta escala"),
            ("Riva (médio-baixo, até R$500 mi)", "~45%", "enquadrada no MCMV faixa 4 em 2026; VGV +20% no 1T26"),
        ],
        "vantagens": [
            "Landbank de R$51,3 bi com 8+ anos de visibilidade — o maior do setor",
            "86% do landbank via permuta: o maior banco de terrenos sem desembolso de caixa",
            "Formas de alumínio: método industrializado que reduz prazo de entrega e custo",
            "Riva na faixa 4 do MCMV: a subsidiária de médio padrão passou a ter acesso ao crédito subsidiado",
            "Maior construtora em área do Brasil — escala que gera poder de negociação com fornecedores",
        ],
        "riscos": [
            "Concentração no MCMV: dependência do FGTS e do orçamento público habitacional",
            "Riva sensível à Selic: crédito SBPE mais caro afeta clientes de médio padrão fora do MCMV",
            "INCC pressionando: custo de construção acima da inflação desde 2025",
            "Dois segmentos, dois riscos: gestão de marcas com públicos diferentes exige execução cuidadosa",
            "Alavancagem subindo: geração de caixa sólida mas pagamento de R$804 mi em dividendos em 2025 elevou endividamento",
        ],
        "barreira": "40 anos de MCMV e o maior landbank do setor formam a barreira.  Nenhum novo entrante consegue replicar R$51 bi de terrenos já aprovados e identificados  em 8 estados sem anos de trabalho.  As formas de alumínio (método construtivo industrializado) vieram de décadas  de aprendizado operacional — não se compra só o equipamento,  compra-se o know-how de como usá-lo com escala.  E o relacionamento de 40 anos com prefeituras do interior do Brasil  para aprovação de empreendimentos é impossível de acelerar.",
    },
    "EGIE3": {
        "nome": "Engie Brasil Energia",
        "fundacao": "1994 (como Nacional Energética; marca Engie desde 2016)",
        "sede": "Florianópolis, SC",
        "tagline": "A maior geradora privada do Brasil. 100% renovável, controlada pela Engie francesa. O desafio é o curtailment crescente e o capex pesado.",
        "modelo": "A Engie Brasil é a maior empresa privada de geração de energia do país, com ~12,9 GW  de capacidade instalada em 145 usinas. O portfólio é 100% renovável: hidrelétricas (~70%),  eólicas, solares e biomassa. Além disso, é sócia da TAG — a maior malha de transporte  de gás natural do Brasil, com 4.500 km em 10 estados.  O modelo de receita combina PPAs (contratos de longo prazo, indexados ao IPCA)  com exposição ao mercado livre (PLD spot).  O desafio atual: curtailment crescente (26% projetado em 2026, 32% em 2027)  — o ONS corta a geração renovável em momentos de sobreoferta.  A estratégia de resposta é migrar parte do portfólio para transmissão,  que gera RAP previsível e não sofre curtailment. Em 2025, venceu lotes  de transmissão nos leilões da ANEEL — a diversificação está em andamento.",
        "receita": [
            ("PPAs de longo prazo (geração hídrica + eólica)", "~60%", "contratos indexados ao IPCA com distribuidoras e grandes consumidores"),
            ("TAG (transporte de gás, participação ~32%)", "~20%", "RAP regulada — receita previsível, sem exposição a preço de gás"),
            ("Mercado livre de energia (ACL)", "~15%", "preço spot variável — mais volátil"),
            ("Transmissão nascente + outros", "~5%", "RAP de novos projetos em construção (Asa Branca, Graúna)"),
        ],
        "vantagens": [
            "Controladora Engie (França): acesso a tecnologia, capital barato e modelo global de energia renovável",
            "TAG: ativo de transmissão de gás com receita regulada — reduz a volatilidade da geração",
            "100% renovável: posicionamento ESG premium para contratos com multinacionais exigentes",
            "Maior geradora privada: escala garante acesso aos melhores PPAs e aos maiores leilões",
            "Expansão em transmissão: diversifica para ativos de menor volatilidade",
        ],
        "riscos": [
            "Curtailment: 26-32% projetado para 2026-2027 — energia produzida mas não vendida",
            "Dependência hídrica (~70%): secas ou GSF negativo afetam diretamente a geração",
            "Ciclo de capex pesado: Jirau, Asa Branca, Graúna — R$6 bi investidos em 2025 pressionam o FCF",
            "Payout reduzido para mínimo de 55% no ciclo de capex — DY caiu vs histórico",
            "Selic alta + alavancagem acima de 2,5x: pressão financeira em ciclo de investimento",
        ],
        "barreira": "Concessões hidrelétricas são praticamente inreplicáveis — os melhores rios já têm dono.  Quem tem Itá, Machadinho, Estreito e Jaguara tem ativos que não se licenciam mais hoje.  A TAG é a única malha de transporte de gás em 10 estados — monopólio natural regulado.  E a marca Engie com 30 anos no Brasil abre portas que novos entrantes levariam décadas para abrir.",
    },
    "EQTL3": {
        "nome": "Equatorial Energia",
        "fundacao": "2004",
        "sede": "São Luís, MA",
        "tagline": "A melhor alocadora de capital do setor elétrico. Compra distribuidoras caóticas, enxuga, recupera e gera retorno acima de qualquer par.",
        "modelo": "A Equatorial não é uma distribuidora comum — é uma operadora especializada em  turnaround de distribuidoras. O modelo é simples de explicar e difícil de executar:  compra distribuidoras com altíssima inadimplência, furto e ineficiência  (pagando barato por isso), reduz as perdas, melhora a cobrança, normativa  os índices de qualidade e passa a extrair margem de uma operação que  estava destruindo valor. Fez isso com a Eletrobras/CEMAR (Maranhão),  com a CELPA (Pará), com a COELCE (Ceará), com a CELG-D (Goiás), com a CEA (Amapá)  e com a CEPISA (Piauí). Cada aquisição foi uma aposta que o mercado duvidou  e a Equatorial executou. Em 2025, entrou no saneamento (15% da Sabesp)  e já tem posições em saneamento em outros estados.  DY baixo porque reinveste quase tudo — mas valorização histórica  é a melhor do setor por décadas.",
        "receita": [
            ("Distribuição de energia (6 estados)", "~75%", "MA, PA, CE, GO, AP, PI — foco em Norte/Nordeste onde havia mais potencial"),
            ("Saneamento (Sabesp 15% + outros)", "~15%", "novo vetor de crescimento — mesma lógica de turnaround"),
            ("Geração, transmissão e telecom", "~10%", "ativos complementares vendidos quando maduros"),
        ],
        "vantagens": [
            "Track record de turnaround: cada aquisição que o mercado duvidou, a Equatorial executou",
            "Gestão de perdas superior: reduz inadimplência e furto nos níveis que distribuidoras estatais nunca conseguiram",
            "Regiões de maior potencial: Norte e Nordeste têm mais espaço para redução de perdas que Sudeste já maduro",
            "Expansão em saneamento: a mesma lógica de turnaround aplicada a um setor ainda mais ineficiente",
            "TIR real de 11,1% implícita: premium justificado pelo histórico e pelo pipeline de crescimento",
        ],
        "riscos": [
            "Alavancagem de 3,5x em fase de expansão — cada nova aquisição pressiona mais o balanço",
            "Sabesp (15%): primeira entrada no saneamento de grande escala — execução ainda não provada",
            "Não é banco de renda: DY de 2-4% decepciona investidores que buscam renda mensal",
            "Regulação adversa: WACC regulatório menor ou opex regulatório mais restritivo comprimir margens",
            "Integração de múltiplos ativos simultâneos: complexidade operacional cresce com o portfólio",
        ],
        "barreira": "A capacidade de executar turnaround é a barreira — e ela não se compra, se constrói em décadas.  A Equatorial tem um playbook testado, uma equipe que já fez isso 6 vezes e  relacionamentos com reguladores e comunidades locais que constroem confiança.  Nenhum concorrente combina o histórico de execução com o acesso a capital  e a disposição de atuar em regiões que outros evitam.  É o modelo mais difícil de imitar no setor.",
    },
    "IRBR3": {
        "nome": "IRB Brasil Re",
        "fundacao": "1939 (Governo Vargas)",
        "sede": "Rio de Janeiro, RJ",
        "tagline": "O seguro das seguradoras. O único papel da B3 que nenhum consumidor final conhece — e que é fundamental para que todo o mercado de seguros funcione.",
        "modelo": "O IRB é uma resseguradora — uma categoria completamente diferente das outras três.  Quando a Porto vende um seguro de carro de R$200.000, ela pode não querer carregar 100% desse risco  no balanço. Então ela 'cede' parte do risco ao IRB, pagando um prêmio de resseguro.  Se o carro for roubado, a Porto paga ao cliente e o IRB ressarce parte para a Porto.  O IRB não tem cliente pessoa física. Seus clientes são as seguradoras (chamadas de 'cedentes').  A métrica-rei é o Combined Ratio — se for abaixo de 100%, a operação de subscrição dá lucro.  O IRB passou por uma crise grave em 2020 (fraude contábil, Combined Ratio de 140%+).  Desde 2022 está em turnaround: Combined Ratio voltou para ~85-90%, resultado de subscrição  cresceu 74,5% no 1T26, sinistralidade doméstica caiu para 35%.  Em 2026 anunciou expansão para seguro direto (criação de duas seguradoras próprias) —  é uma mudança estrutural do modelo que o mercado ainda está digerindo.",
        "receita": [
            ("Resultado de subscrição (prêmios - sinistros - despesas)", "~53%", "coração do negócio — R$180 mi no 1T26, +74,5% a/a"),
            ("Resultado financeiro (float das reservas)", "~47%", "reservas técnicas investidas rendendo a Selic"),
        ],
        "vantagens": [
            "Único ressegurador de grande porte listado na B3 — sem comparável doméstico",
            "Turnaround concluído: Combined Ratio de 140%+ em 2020 para ~85-90% em 2026",
            "Solvência regulatória de 287% — capital de sobra para crescer e distribuir dividendos",
            "Mercado de resseguro no Brasil cresceu 7,1% no 1T26 — vento a favor estrutural",
            "A partir de 2027, reforma tributária (CBS/IBS) zera alíquota do resseguro — potencial ganho de rentabilidade",
            "Base de dados técnicos de 80+ anos de riscos brasileiros — vantagem de subscrição inreplicável",
        ],
        "riscos": [
            "Catástrofes de grande escala: enchente, furacão, acidente de aviação podem gerar perda pontual enorme",
            "Histórico de fraude contábil em 2020 — credibilidade ainda em reconstrução com investidores institucionais",
            "Expansão para seguro direto em 2026 é aposta não provada — pode consumir capital e desviar foco",
            "Sinistralidade internacional elevada (~93%) — mercado externo é menos lucrativo que o doméstico",
            "Dividend yield baixo (~3%) — turnaround recente limita distribuição; ainda não é banco de renda",
        ],
        "barreira": "80 anos de base de dados técnicos de risco no Brasil.  Uma resseguradora nova levaria décadas para ter a confiança técnica para assumir  resseguros de aviação, petróleo ou grandes riscos industriais.  O IRB sabe exatamente quanto custa um incêndio numa plataforma de petróleo no Brasil —  e essa informação vale mais do que qualquer capital.  Mais o oligopólio regulatório: a SUSEP controla a abertura de novas resseguradoras.",
    },
    "ISAE4": {
        "nome": "ISA Energia Brasil (ex-Transmissão Paulista)",
        "fundacao": "1999 (Transmissão Paulista) / controladora ISA Colombia fundada 1967",
        "sede": "São Paulo, SP",
        "tagline": "A transmissora com o melhor portfólio de novas concessões. Mais previsível que a Taesa, menor alavancagem, controlador colombiano.",
        "modelo": "A ISA Energia é a segunda maior transmissora privada do Brasil, com foco no Sudeste.  Controlada pela ISA Interconexión Eléctrica S.A. (Colombia), uma das maiores empresas  de transmissão da América Latina. O diferencial da ISA vs Taesa está na qualidade  do portfólio: as concessões são predominantemente de categoria II e III,  com metodologia regulatória mais moderna e transparente — menos risco de surpresas  na revisão de RAP. Menor alavancagem que a Taesa, TIR real implícita de ~7,7%,  o que a coloca em posição mais defensiva no setor. Também tem participação minoritária  da Axia Energia (ex-Eletrobras) em algumas concessões, o que cria uma relação  estratégica com a maior geradora do país.",
        "receita": [
            ("RAP de transmissão", "~98%", "receita contratada por 30 anos, predominantemente indexada ao IPCA"),
            ("Outros serviços", "~2%", "operação e manutenção de terceiros"),
        ],
        "vantagens": [
            "Portfólio de concessões modernas (cat. II/III): menor risco regulatório vs Taesa",
            "Menor alavancagem: mais espaço para novos leilões sem pressionar o balanço",
            "TIR real implícita de ~7,7% — bem acima da NTN-B de prazo semelhante",
            "Controlador com track record: ISA Colombia opera transmissão em 6 países com excelência",
            "Zero risco climático — mesmo modelo de receita da Taesa",
        ],
        "riscos": [
            "Controlador colombiano: decisões vêm de fora do Brasil — alinhamento com minoritários nem sempre é total",
            "Selic alta comprime valuation como em qualquer transmissora de duration longa",
            "Menor liquidez que Taesa na B3 — spread bid/ask maior para investidores institucionais",
            "Depende de novos leilões para crescer — mercado de transmissão é competitivo",
        ],
        "barreira": "Idem à Taesa: exclusividade regulatória de 30 anos e custo proibitivo de infraestrutura.  Adicionalmente, o relacionamento com a Axia e a presença no Sudeste (onde está a maior  demanda do país) são vantagens geográficas e de relacionamento difíceis de replicar.",
    },
    "ITUB4": {
        "nome": "Itaú Unibanco",
        "fundacao": "1945 (fusão Itaú+Unibanco em 2008)",
        "sede": "São Paulo, SP",
        "tagline": "O maior banco privado da América Latina. Disciplina de capital, foco em alta renda e o melhor ROE entre os incumbentes.",
        "modelo": "O Itaú opera em quatro frentes: varejo (conta corrente, cartão, crédito e seguros para pessoas físicas),  atacado (crédito para grandes empresas, mercado de capitais, tesouraria), gestão de ativos (fundos, previdência)  e atividades internacionais (América Latina). O diferencial não é o tamanho — é a seletividade. O Itaú  deliberadamente abandonou segmentos de menor renda e maior inadimplência, concentrando a carteira em alta e  média renda. 6 de cada 10 brasileiros de alta renda têm relacionamento com o banco. Isso gera spreads  melhores, inadimplência menor e fee de serviços mais alto (asset management, corretagem, seguros).  No 1T26 entregou lucro recorrente de R$ 12,3 bi e ROE de 24,8% — o mais alto entre os incumbentes.",
        "receita": [
            ("Margem financeira (NII)", "~50%", "spread de crédito e resultado de tesouraria"),
            ("Receitas de serviços e tarifas", "~25%", "cartão, asset management, advisory, corretagem"),
            ("Seguros", "~12%", "Itaú Seguros — vida, prestamista, imobiliário"),
            ("Outros", "~13%", "câmbio, derivativos, international"),
        ],
        "vantagens": [
            "Melhor ROE entre os bancões incumbentes (~24-26%) — sustentado por décadas, não é pico de ciclo",
            "Foco na alta renda cria um flywheel: menor inadimplência → menor provisão → mais capital disponível para crescer",
            "Escala de distribuição: rede própria + parcerias + digital permitem cross-sell sem aumentar custo proporcional",
            "Transformação digital avançada — 75% das transações já são digitais, com meta de 75% dos clientes em modelo digital-first até 2027",
            "Seguros e asset management são negócios capital-light dentro do banco, com margens muito mais altas que o crédito",
        ],
        "riscos": [
            "Valuation premium (P/L ~8x, P/VP ~2x) não tolera decepções — qualquer deterioração é punida",
            "Competição crescente de BTG no wealth management e de fintechs no varejo digital",
            "Regulação bancária pode aumentar requisitos de capital, pressionando distribuição de dividendos",
            "Expansão na América Latina (Chile, Argentina, Colômbia) adiciona risco cambial e político",
        ],
        "barreira": "A combinação de marca, rede de distribuição, base de dados de clientes e capital regulatório  cria uma barreira de entrada que nenhuma fintech conseguiu transpor em décadas.  Nubank chegou a 100 milhões de clientes — mas em rentabilidade por cliente ainda está longe do Itaú.",
    },
    "KEPL3": {
        "nome": "Kepler Weber S.A.",
        "fundacao": "1925 (em Panambi, RS)",
        "sede": "Panambi, RS",
        "tagline": "O líder absoluto em armazenagem de grãos no Brasil. 80% de market share em silos — e a safra recorde do agro brasileiro ainda está criando demanda por mais capacidade.",
        "modelo": "A Kepler Weber não é autopeça — é uma empresa de bens de capital para o agronegócio.  Fabrica silos (metálicos e de concreto), secadores de grãos,  transportadores (elevadores de canecas, correias) e sistemas de controle  para armazenagem de soja, milho, trigo e outros grãos.  É líder absoluta no Brasil com ~80% de market share em silos metálicos —  o produto mais vendido do portfólio.  O mercado-alvo são produtores rurais individuais, cooperativas e tradings  (Bunge, ADM, Cargill, LDC).  O diferencial do modelo: o Brasil tem grave déficit de armazenagem.  A capacidade estática nacional é de ~175 milhões de toneladas,  enquanto a produção de grãos superou 320 milhões em 2025.  Cada tonelada de grão produzida sem armazém adequado é prejuízo para o produtor.  Isso cria demanda estrutural que não depende do ciclo econômico convencional —  depende do ciclo do agronegócio.",
        "receita": [
            ("Silos metálicos e acessórios", "~55%", "produto principal; liderança de 80% de mercado; vende a produtores e cooperativas"),
            ("Secadores de grãos", "~20%", "equipamento crítico pós-colheita; crescimento com qualidade exigida para exportação"),
            ("Sistemas de transporte (elevadores, correias)", "~15%", "logística interna do silo — cross-sell natural com a venda do silo"),
            ("Exportação e serviços", "~10%", "América do Sul, África e outros; instalação e manutenção"),
        ],
        "vantagens": [
            "80% de market share em silos: nenhum concorrente chega perto — liderança consolidada em décadas",
            "Déficit estrutural de armazenagem: Brasil produz 320 mi t de grãos com capacidade de 175 mi t — runway de crescimento secular",
            "Câmbio positivo por proxy: cliente rural vende soja em dólar — dólar alto dá mais poder de compra para investir em armazenagem",
            "Carteira de pedidos de 12+ meses: visibilidade de receita acima da média industrial",
            "Panambi como polo: 100 anos de know-how em equipamentos agroindustriais no RS — cluster com fornecedores especializados",
        ],
        "riscos": [
            "Ciclicidade do agro: safra ruim + queda de commodity = produtor adia investimento em armazenagem",
            "Aço como matéria-prima: preço internacional afeta custo dos silos; repasse ao cliente tem defasagem",
            "Concentração geográfica: RS como base industrial — enchentes de 2024 impactaram operações",
            "Concorrência de importados: silos chineses entram via dumping em períodos de câmbio apreciado",
        ],
        "barreira": "100 anos de know-how e 80% de mercado criam uma barreira quase intransponível.  O produtor rural que vai comprar um silo de R$500 mil  não arrisca com um fornecedor desconhecido —  ele quer quem estará lá para dar assistência em 10 anos.  A Kepler tem rede de revendedores e assistência técnica em todo o Brasil agrícola —  um entrante precisaria de décadas para construir esse canal.  E a posição de liderança cria um efeito de rede:  cooperativa que já tem silos Kepler compra mais Kepler  porque os sistemas são integrados.",
    },
    "KLBN4": {
        "nome": "Klabin",
        "fundacao": "1899",
        "sede": "São Paulo, SP",
        "tagline": "A única produtora brasileira com pinus em escala. Integração do bosque à caixa.",
        "modelo": "A Klabin é a empresa mais complexa do trio. Planta pinus (fibra longa) e eucalipto  (fibra curta), produz celulose, papel e embalagens — e converte parte em produtos  acabados como sacos industriais, caixas de papelão e cartões. Vende celulose para  exportação, mas uma fatia relevante da receita é embalagem doméstica, o que amortece  o ciclo de commodity. É a maior produtora e exportadora de papel para embalagem do Brasil.",
        "receita": [
            ("Embalagens (papelão ondulado, caixas)", "~45%", "mercado doméstico, relativamente estável"),
            ("Papel para embalagem (kraft, cartão)", "~25%", "Brasil e exportação"),
            ("Celulose (fibra longa e fluff)", "~20%", "exportação, commodity"),
            ("Sacos industriais", "~10%", "cimento, fertilizante, Brasil"),
        ],
        "vantagens": [
            "Única produtora de pinus em escala industrial no Brasil — fibra longa que ninguém mais tem",
            "Diversificação de produto: embalagem amorte o ciclo de celulose",
            "Integração vertical completa: da floresta ao produto acabado",
            "Celulose fluff (para fraldas e absorventes) — nicho de margem alta e demanda crescente",
        ],
        "riscos": [
            "Capex intensivo e constante — projetos de expansão pressionam caixa por anos seguidos",
            "Alavancagem historicamente alta (4–5x EBITDA em fases de investimento)",
            "Complexidade operacional: 23 plantas, múltiplos produtos, margens diferentes por linha",
            "Pinus tem ciclo de 15 anos — planejamento florestal é de altíssimo prazo",
        ],
        "barreira": "",
    },
    "LEVE3": {
        "nome": "Mahle Metal Leve S.A.",
        "fundacao": "1950 (como Metal Leve; controlada pela Mahle alemã desde 1996)",
        "sede": "São Paulo, SP",
        "tagline": "O negócio que prospera quando o carro envelhece. Aftermarket anticíclico, controladora alemã que financia o P&D, e a única empresa do grupo que a Mahle listou fora da Alemanha.",
        "modelo": "A Mahle Metal Leve é a subsidiária brasileira do grupo Mahle —  um dos maiores fabricantes de componentes automotivos do mundo,  com sede em Stuttgart, Alemanha.  No Brasil, fabrica pistões, anéis de segmento, buchas,  filtros (óleo, ar, combustível) e velas de ignição.  O modelo tem duas frentes: OEM (~30%), onde vende diretamente para  GM, Ford, Stellantis e Volkswagen que montam os carros novos;  e aftermarket (~70%), onde vende para distribuidores e mecânicas  que trocam peças em carros usados.  O aftermarket é o diferencial: com frota média de 11+ anos no Brasil,  cada motor exige troca de pistão, filtro ou vela em média a cada 2-3 anos.  Quanto mais velha a frota, mais demanda — é anticíclico por natureza.  A controladora alemã custeia o P&D global (€1 bi/ano em inovação)  e o Brasil se beneficia do know-how sem pagar por isso diretamente.  Exporta componentes para Europa e América do Norte, capturando o câmbio favorável.",
        "receita": [
            ("Aftermarket Brasil", "~55%", "mecânicas, distribuidores, varejo de autopeças — anticíclico e recorrente"),
            ("OEM Brasil (montadoras)", "~25%", "GM, Ford, Stellantis, VW — segue produção de veículos novos"),
            ("Exportação (OEM global)", "~20%", "componentes para Europa e EUA; dólar alto melhora margens"),
        ],
        "vantagens": [
            "Aftermarket anticíclico: frota velha gera demanda constante independente do PIB",
            "P&D financiado pela matriz: Mahle alemã investe €1 bi/ano em inovação — LEVE3 acessa sem pagar",
            "Margem bruta de 38-40%: entre as mais altas do setor industrial — brand reconhecido pelo mecânico",
            "Exportação em dólar: ~20% das receitas em moeda forte protege em desvalorizações do real",
            "Único papel do grupo Mahle listado fora da Alemanha: acesso a gestão global com liquidez local",
        ],
        "riscos": [
            "Eletrificação da frota: carro elétrico não tem pistão, filtro de óleo nem vela — ameaça estrutural de 10-20 anos",
            "Concentração no motor a combustão: 90%+ das receitas dependem de tecnologia em transição",
            "OEM sujeito ao ciclo automotivo: montadoras param produção em crise e afeta 25% da receita",
            "Controladora estrangeira: dividendo certo, mas decisões estratégicas vêm de Stuttgart — potencial de conflito com minoritários",
        ],
        "barreira": "Marca reconhecida pelo mecânico. No aftermarket, quem decide a peça é o mecânico —  não o dono do carro. E o mecânico de Franca, Uberlândia ou Manaus  conhece e confia na Mahle há décadas.  Construir essa confiança com 50.000 mecânicos no Brasil inteiro  é um ativo invisível que nenhum concorrente recompra.  Mais o know-how técnico da matriz alemã:  qualidade de produto que importados asiáticos ainda não replicam no motor.",
    },
    "MDNE3": {
        "nome": "MDNE (Moura Dubeux Engenharia)",
        "fundacao": "1983 (em Recife, PE — por Jorge Moura e Dubeux)",
        "sede": "Recife, PE",
        "tagline": "O maior grupo imobiliário do Nordeste. 42 anos, 260 empreendimentos, três marcas e um modelo de condomínio que não existe em São Paulo.",
        "modelo": "A Moura Dubeux tem um modelo diferente de todas as outras incorporadoras listadas.  Além da incorporação tradicional, opera o chamado 'modelo de condomínio':  os clientes compram cotas do terreno coletivamente, formam um condomínio,  e a MD constrói por conta do condomínio cobrando taxa de administração mensal.  Isso gera receita recorrente durante a obra e reduz o risco de crédito  (o cliente paga mensalmente conforme a obra avança).  Em 2026, reorganizou-se como holding MDNE com três marcas:  Moura Dubeux (alto padrão e luxo + segunda residência),  Mood (médio padrão, lançada em 2023) e  Ún1ca (MCMV no Nordeste, em parceria com a Direcional —  joint venture chamada Ún1ca para o segmento econômico nordestino).  Opera em 7 estados nordestinos, com liderança de mercado absoluta na região —  260 empreendimentos entregues em 42 anos e VGV lançado de R$5,5 bi projetados para 2026.",
        "receita": [
            ("Alto padrão e luxo — marca Moura Dubeux", "~55%", "Recife, Fortaleza, Natal, João Pessoa; segunda residência na costa nordestina"),
            ("Médio padrão — marca Mood", "~30%", "lançada em 2023; crescendo rápido; primeira residência classe média"),
            ("MCMV — marca Ún1ca (JV com Direcional)", "~15%", "iniciada em 2025; em crescimento acelerado; acesso ao FGTS"),
        ],
        "vantagens": [
            "Monopólio regional: 42 anos de liderança no Nordeste — nenhum concorrente nacional tem a mesma escala regional",
            "Modelo de condomínio: receita recorrente durante a obra + risco de crédito menor",
            "DY de 17%: alta distribuição de lucros; P/L de 5,79x — um dos mais baratos do setor",
            "Nordeste com demanda reprimida: menos saturado que SP; cliente de alto padrão regional tem menos opções",
            "Ún1ca (MCMV): diversificação que protege em ciclo de juro alto; JV com Direcional traz expertise",
        ],
        "riscos": [
            "Concentração no Nordeste: PIB regional mais fraco — recessão nacional impacta mais",
            "Três marcas recentes: Mood (2023) e Ún1ca (2025) ainda em maturação — execução simultânea é risco",
            "Alto padrão sensível à Selic: o core do negócio sofre quando crédito encarece",
            "Small cap: liquidez menor (R$8 mi/dia) — spread bid/ask maior, menos cobertura de analistas",
            "Dependência familiar: empresa fundada pela família Dubeux — risco de governança em eventual transição",
        ],
        "barreira": "42 anos de presença dominante no Nordeste.  O comprador de alto padrão em Recife não compra da Cyrela — compra da Moura Dubeux.  Essa confiança de marca regional, construída empreendimento a empreendimento  em uma região onde poucos nacionais apostaram, é inreplicável no curto prazo.  O modelo de condomínio é outro diferencial que os concorrentes não dominam —  o cliente nordestino está habituado a esse modelo e o prefere.  E o banco de terrenos de décadas na costa nordestina,  em regiões que valorizaram com o turismo interno pós-pandemia,  é uma posição que nenhum novo entrante vai encontrar disponível.",
    },
    "MULT3": {
        "nome": "Multiplan Empreendimentos Imobiliários",
        "fundacao": "1974 (por José Isaac Peres)",
        "sede": "Rio de Janeiro, RJ",
        "tagline": "A shopping premium do Brasil. 20 shoppings, 73% com vendas acima de R$1 bilhão — e a maior conversão de vendas em aluguel do setor. Qualidade justifica o prêmio de múltiplo.",
        "modelo": "A Multiplan foi fundada por José Isaac Peres em 1974 e construiu ao longo de 50 anos  um portfólio de 20 shoppings concentrados em localidades premium:  BarraShopping (RJ), MorumbiShopping (SP), ParkShopping (BSB), BH Shopping (MG),  entre outros. A estratégia é o oposto da Allos: poucos ativos, mas os melhores.  73% do portfólio tem vendas anuais superiores a R$1 bilhão — o melhor índice do setor.  Isso se traduz na maior conversão de vendas em aluguel: 10,5% vs 9,6% da Allos.  Em termos práticos: para cada R$100 que o lojista vende,  a Multiplan captura R$10,50 em aluguel. Esse poder de precificação vem da qualidade  — lojista que está no MorumbiShopping não tem alternativa de mesma qualidade próxima.  A Multiplan também tem um componente imobiliário relevante:  desenvolve apartamentos e escritórios no entorno dos shoppings —  o projeto de cidade completa ao redor do shopping (multimix).",
        "receita": [
            ("Aluguel mínimo garantido", "~52%", "base fixa reajustada por IGP-DI/IPCA; portfólio premium permite mínimos maiores"),
            ("Aluguel variável (% das vendas)", "~22%", "maior percentual variável que os pares — reflexo da qualidade do lojista"),
            ("Estacionamento", "~13%", "alto fluxo de veículos em shoppings premium — receita relevante"),
            ("Desenvolvimento imobiliário (multimix)", "~8%", "apartamentos e escritórios no entorno dos shoppings — ciclo mais longo"),
            ("Cessão de direito e outros", "~5%", "key money e receitas não recorrentes"),
        ],
        "vantagens": [
            "73% do portfólio com vendas > R$1 bi/ano: qualidade de ativo incomum — lojistas pagam prêmio para estar lá",
            "10,5% de conversão: maior poder de precificação do setor — cada real de venda gera mais aluguel",
            "Vendas/m² cresceram 10,9% em 2025: maior taxa de crescimento entre os pares",
            "50 anos de track record: Multiplan construiu shoppings que viraram referência de consumo nas suas cidades",
            "Multimix: desenvolvimento imobiliário ao redor cria ecossistema de valor que valoriza o próprio shopping",
        ],
        "riscos": [
            "Valuation de prêmio (12x FFO): não tolera decepção — qualquer desaceleração é punida no preço",
            "Concentração geográfica: forte em SP, RJ e Sul — recessão regional impacta mais que portfólio nacional",
            "Selic alta é o maior inimigo: duration longa do ativo = valuation comprimido em cenário de juro alto",
            "DY mais baixo (~5-6%): reinveste mais; para investidores de renda pura, a Allos é mais atrativa",
            "Expansão limitada: portfólio premium tem menos oportunidades de crescimento via novos shoppings",
        ],
        "barreira": "50 anos de curadoria de localização e de mix de lojistas.  O MorumbiShopping em São Paulo ou o BarraShopping no Rio  têm listas de espera de lojistas que querem entrar.  Quando o Zara, a Apple ou a Nike quer estar em São Paulo,  o MorumbiShopping está na lista curta — e a Multiplan sabe  negociar esse poder de escassez em aluguel.  Isso é uma vantagem competitiva de marca que levou meio século para construir  e que nenhum shopping novo replica mesmo com capital infinito.",
    },
    "PETR4": {
        "nome": "Petrobras",
        "fundacao": "1953 (fundada por Getúlio Vargas)",
        "sede": "Rio de Janeiro, RJ",
        "tagline": "A empresa mais lucrativa do Brasil. O pré-sal é o ativo; a política é o risco permanente.",
        "modelo": "A Petrobras é uma empresa integrada de petróleo e gás — extrai no pré-sal,  refina nas suas refinarias e vende combustível e derivados para o mercado  brasileiro e para exportação. Com meta de 3,4 milhões de boed até 2028 e  custo de extração abaixo de US$6/barril, é uma das operações de mais baixo custo  do planeta. O pré-sal brasileiro — especialmente Búzios, com reservas gigantescas  na Bacia de Santos — é o coração do negócio: óleo leve de alta qualidade,  em águas profundas, com FPSOs que chegam a produzir 200 mil barris/dia cada.  O plano 2026-2030 prevê US$109 bi de investimento, 62% no pré-sal,  com 8 novos sistemas de produção até 2030, sendo 7 já contratados.  A integração com o refino funciona como amortecedor: quando o Brent cai,  o refino compra petróleo barato e sustenta margens.  O custo total médio de produção (incluindo royalties e participações governamentais)  é de US$30,4/boe no quinquênio — muito abaixo do preço de equilíbrio do mercado.",
        "receita": [
            ("E&P (exploração e produção)", "~60%", "pré-sal é o motor; <US$6/bbl de lifting cost; 8 novos FPSOs até 2030"),
            ("Refino, Transporte e Comercialização", "~30%", "1,8 mi bpd de capacidade; expansão para 2,1 mi até 2030"),
            ("Gás natural e energia", "~7%", "TAG, transporte de gás, termelétricas"),
            ("Outros (fertilizantes, biocombustíveis)", "~3%", "biorrefino em expansão; US$1,2 bi aprovado em 2026"),
        ],
        "vantagens": [
            "Pré-sal: custo <US$6/bbl — um dos mais baixos do mundo; óleo leve de alta qualidade",
            "Búzios: maior reservatório offshore fora do Oriente Médio — reservas imensas, produção crescente por décadas",
            "Integração E&P + refino: proteção natural quando o Brent cai (refino compra barato)",
            "Dividendo garantido: política de 45% do FCF; governo precisa do dividendo — alinhamento forçado",
            "Escala operacional: única operadora de FPSOs em águas ultra-profundas no Brasil; know-how inreplicável",
        ],
        "riscos": [
            "Risco político: CEO indicado pelo governo; preços de combustíveis como instrumento político",
            "Refino pressionado: governo quer gasolina barata — comprime margens do segmento",
            "Margem Equatorial: nova fronteira exploratória com licenciamento ambiental incerto (IBAMA)",
            "Brent estruturalmente mais baixo: plano assume US$63/bbl em 2026; abaixo disso, capex é revisto",
            "Transição energética: portfólio de longo prazo concentrado em hidrocarbonetos",
        ],
        "barreira": "O pré-sal é a barreira mais alta do setor de petróleo no mundo.  Operar FPSOs em águas de 2.000-3.000 metros, perfurar poços de 6.000-7.000 metros  passando pela camada de sal, é um desafio de engenharia que só meia dúzia de  empresas no planeta domina — e a Petrobras é operadora de praticamente todos.  Ninguém entra no pré-sal sem ela, e ela tem mais de 70 anos de know-how local.",
    },
    "POMO4": {
        "nome": "Marcopolo S.A.",
        "fundacao": "1949 (em Caxias do Sul, RS — por Reinaldo Pasa)",
        "sede": "Caxias do Sul, RS",
        "tagline": "O maior fabricante de carrocerias de ônibus do mundo. Exporta para 100+ países, e cada ônibus é um projeto de engenharia — não uma linha de produção em série.",
        "modelo": "A Marcopolo não fabrica o chassi do ônibus — fabrica a carroceria.  O chassi vem da Volvo, Mercedes ou Scania; a Marcopolo coloca em cima  a estrutura de passageiros (o que o passageiro vê e sente).  É a maior fabricante de carrocerias de ônibus do mundo em volume.  Opera em dois mercados distintos: Brasil (~50% da receita),  onde os clientes são prefeituras (ônibus urbano), empresas de turismo  e fretamento; e exterior (~50%), onde exporta para América Latina,  África, Índia, Austrália e Europa, com fabricação local em alguns países.  O produto é customizado — cada pedido tem especificações diferentes.  Isso cria barreiras de engenharia e relacionamento com o cliente  que produtos padronizados não têm.  Em 2025-2026, o BRT (Bus Rapid Transit) nas capitais brasileiras  e o programa de eletrificação de frotas municipais são os maiores catalisadores.  A Marcopolo já fabrica carrocerias para ônibus elétricos —  é uma das poucas do setor que mitigou o risco de eletrificação.",
        "receita": [
            ("Ônibus urbano — Brasil", "~30%", "prefeituras e operadoras; BRT e eletrificação são catalisadores 2025-2026"),
            ("Ônibus rodoviário e turismo — Brasil", "~20%", "empresas de fretamento e turismo; ciclo ligado à economia"),
            ("Exportação (América Latina + África + outros)", "~35%", "dólar/euro nas receitas; margens melhores que o mercado doméstico"),
            ("Fabricação local no exterior (JVs)", "~15%", "Índia, Austrália, Colômbia — receita em moeda local"),
        ],
        "vantagens": [
            "Líder mundial em carrocerias de ônibus: escala que nenhum concorrente brasileiro alcança",
            "50% de exportação: diversificação geográfica que suaviza o ciclo doméstico",
            "Produto customizado: cada ônibus é um projeto — barreiras de engenharia e relacionamento",
            "Já fabrica para elétricos: adaptação estratégica que evita a armadilha da eletrificação",
            "Caxias do Sul: cluster industrial gaúcho com fornecedores especializados e mão de obra qualificada",
        ],
        "riscos": [
            "Dependência de orçamento público: prefeituras compram quando têm verba — ciclo político afeta demanda doméstica",
            "Eletrificação em andamento: BYD e Volvo Elétrico competem pela carroceria de ônibus elétrico",
            "Câmbio de dois gumes: exportação beneficia margem, mas matéria-prima importada sobe junto",
            "Enchentes RS (2024): sede em Caxias do Sul sofreu impacto operacional — risco geográfico concentrado",
        ],
        "barreira": "75 anos de know-how em engenharia de carrocerias de ônibus.  O ônibus urbano de São Paulo, de Lagos, de Melbourne e de Montevidéu  pode ser da Marcopolo — e cada cidade tem normas técnicas,  dimensões e especificações diferentes.  Dominar isso em 100+ países é uma barreira de conhecimento técnico e  relacionamento institucional que nenhum entrante replica em menos de décadas.",
    },
    "PRIO3": {
        "nome": "PRIO (PetroRio)",
        "fundacao": "2010 (como HRT Petroleum; virou PetroRio em 2014; PRIO em 2021)",
        "sede": "Rio de Janeiro, RJ",
        "tagline": "A maior independente do Brasil. Compra o que a Chevron, Equinor e Petrobras descartaram — e extrai mais petróleo com menos custo.",
        "modelo": "A PRIO tem um modelo único e comprovado: compra campos de petróleo maduros  que grandes petroleiras decidiram abandonar, assume a operação, corta custos  e aumenta a recuperação dos reservatórios.  Fez isso com Frade (da Chevron), Albacora Leste (da Petrobras),  cluster Polvo+Tubarão Martelo (da Dommo) e, mais recentemente,  Peregrino (da Equinor) — o maior campo da empresa, 100% adquirido em 2025.  O resultado: de 5 mil barris/dia e custo de US$35/bbl em 2015  para +190 mil barris/dia e custo de US$9/bbl em 2026.  Wahoo é o próximo capítulo: primeiro campo desenvolvido do zero pela PRIO,  conectado ao FPSO Valente via tieback de Frade, com custo marginal de  apenas US$1/bbl (usa infraestrutura existente) e capacidade de 40 kboed.  Peregrino, que a Equinor operava a US$500 mi/ano de custo,  já está sendo operado pela PRIO a US$370 mi e deve chegar a US$250 mi  quando o gasoduto de gás for reativado em 2026 — US$250 mi de ganho anual.",
        "receita": [
            ("Peregrino", "~40%", "campo pesado da Equinor; PRIO cortou custo de US$500 mi para meta US$250 mi/ano"),
            ("Frade + Wahoo", "~30%", "Wahoo a 40 kboed com custo marginal de US$1/bbl — maior catalisador de 2026"),
            ("Albacora Leste", "~15%", "campo da Petrobras revendido; PRIO aumentou produção e eficiência"),
            ("Polvo + Tubarão Martelo + outros", "~15%", "cluster offshore menor na Bacia de Campos"),
        ],
        "vantagens": [
            "Modelo de revitalização comprovado: compra barato, corta custo, aumenta produção — 100% de execução",
            "Lifting cost ~US$9/bbl (meta US$7): margem expressiva mesmo com Brent a US$50",
            "Zero risco político: privada, independente, sem governo determinando preços ou CEO",
            "Wahoo: custo marginal de US$1/bbl por usar infraestrutura do Frade — puro upside",
            "Peregrino: sinergias de US$250 mi/ano vs Equinor — maior captura de valor de campo único",
        ],
        "riscos": [
            "Brent é tudo: sem refino para amortecer — cada US$1 de queda vai direto no EBITDA",
            "Alavancagem pós-Peregrino: US$3 bi de aquisição; meta 1x dívida/EBITDA até 2027 a US$60",
            "Declínio natural: campos maduros declinam — precisa de perfurações contínuas (Albacora Leste+30 kboed)",
            "Ramp-up de Wahoo: GOR (razão gás-óleo) alto; cada poço precisa de 10 dias de estabilização",
            "Concentração na Bacia de Campos: todos os ativos offshore no RJ — risco operacional concentrado",
        ],
        "barreira": "O know-how de revitalização de campos maduros é a barreira.  A PRIO desenvolveu metodologias próprias para extrair mais petróleo  de reservatórios dados como esgotados.  Isso se combina com uma cultura de custo obsessiva —  cortou o OpEx de Peregrino pela metade em menos de um ano.  E a reputação junto às grandes petroleiras que querem desinvestir  é a maior vantagem competitiva: quando a Chevron, Equinor ou Petrobras  quer vender um campo, a PRIO está na lista curta dos compradores.",
    },
    "PSSA3": {
        "nome": "Porto",
        "fundacao": "1945",
        "sede": "São Paulo, SP",
        "tagline": "A maior seguradora não-vida do Brasil. Saiu do risco de ser 'só auto' e virou um ecossistema de seguros, serviços e finanças.",
        "modelo": "A Porto é a única seguradora real desta lista — ela assume risco, subscreve apólices,  paga sinistros. Não é distribuidora de banco. Nasceu em 1945 como seguradora de automóveis  e por décadas foi sinônimo de 'seguro de carro'. O problema: auto tinha sinistralidade alta  e margens comprimidas. A virada estratégica foi deliberada: diluir o auto (que era 90% da receita)  e crescer nas verticais mais rentáveis. Em 2025, auto era apenas 39%.  Hoje opera em quatro verticais: Porto Seguro (auto, residencial, empresarial),  Porto Saúde (planos de saúde e odonto, crescendo forte), Porto Bank (cartão de crédito, consórcio)  e Porto Serviços (assistências).  A parceria com o Itaú (exclusividade para auto e residencial nos canais do banco)  é uma alavanca de distribuição que nenhum concorrente tem — o Itaú Seguro de Auto é,  na prática, operado pela Porto.",
        "receita": [
            ("Auto (Porto Seguro + Itaú + Azul Seguros)", "~39%", "era 90% em 2010 — deliberadamente diluído; sinistralidade alta e margens comprimidas"),
            ("Porto Saúde (planos de saúde e odonto)", "~25%", "vertical mais rentável e em crescimento — margens superiores ao auto"),
            ("Residencial e empresarial", "~15%", "cross-sell com auto e parceria Itaú — sinistralidade mais baixa"),
            ("Porto Bank (cartão, consórcio, financiamento)", "~12%", "crescendo via base de 18 mi de clientes — sem custo de aquisição"),
            ("Porto Serviços (assistências)", "~9%", "assistências 24h e serviços domésticos — fidelização e receita recorrente"),
        ],
        "vantagens": [
            "Diversificação real: auto 39% da receita — se o mercado de carros parar, a Porto não para",
            "Porto Saúde crescendo com margens superiores ao auto — driver estrutural dos próximos anos",
            "Exclusividade nos canais do Itaú: acesso a mais de 50 milhões de clientes com custo de aquisição reduzido",
            "Taxa de renovação 10 pp acima da média do mercado — fidelidade de cliente acima da concorrência",
            "18 milhões de clientes únicos — base para cross-sell de saúde, banco e serviços",
        ],
        "riscos": [
            "Sinistralidade alta: ela paga o que a natureza e os acidentes custam — granizo, enchente, fraude",
            "Competição agressiva em auto: concorrentes praticando preços baixos para ganhar mercado",
            "Porto Saúde: custo dos planos de saúde cresce sistematicamente acima da inflação",
            "DY menor (~5-6%) — reinveste mais para crescer; não é banco de renda no curto prazo",
            "Valuation mais alto (P/L ~10x) após forte valorização — margem de segurança menor",
        ],
        "barreira": "A exclusividade no Itaú + 80 anos de marca + rede de 46.000 corretores.  Um novo entrante levaria décadas para construir a confiança que um corretor tem com a Porto.  O contrato com o Itaú é uma alavanca que qualquer outra seguradora pagaria bilhões para ter.  E a liderança em auto (com a sinistralidade controlada que têm) cria um banco de dados de risco  que é vantagem competitiva de subscrição.",
    },
    "RANI3": {
        "nome": "Irani (Celulose Irani)",
        "fundacao": "1941",
        "sede": "Campina da Alegria, SC",
        "tagline": "A única empresa de embalagens sustentáveis pura listada na B3. Brasil puro, sem câmbio.",
        "modelo": "A Irani não é uma produtora de celulose de mercado. É uma fabricante de embalagens  que produz sua própria celulose — e usa tudo internamente. Pega aparas (papel  reciclado descartado por supermercados, e-commerce e frigoríficos), transforma em  papel kraft e papelão ondulado, e vende para o mercado doméstico. Também tem florestas  próprias de pinus no Sul (SC e RS), de onde extrai fibra virgem para complementar  a produção e resina de terebintina como subproduto (usada em tintas a óleo).",
        "receita": [
            ("Embalagens de papelão ondulado", "~57%", "frigoríficos, agro, e-commerce, alimentos"),
            ("Papel para embalagens (kraft)", "~37%", "sacolas, sacos, papel multiwall — Brasil e 15% exportação"),
            ("Resinas e madeira", "~6%", "terebintina e venda de madeira — subproduto do pinus"),
        ],
        "vantagens": [
            "Zero exposição ao câmbio e ao ciclo global de celulose — negócio 100% doméstico",
            "Demanda por embalagem de papelão cresceu 2–5%/ano mesmo em recessão — setor defensivo",
            "Floresta própria de pinus garante parte do custo estável e previsível",
            "Capacidade de repasse de preço: quem compra caixa de papelão não tem substituto fácil",
            "Plataforma Gaia (>R$1 bi investido): ganhos de eficiência ainda sendo colhidos",
        ],
        "riscos": [
            "Preço das aparas (OCC): insumo externo que representa ~30% do custo — variou de R$610 a R$1.300/t",
            "Eventos climáticos no Sul (enchentes RS/SC) disruptam o fornecimento de aparas",
            "Small cap — menor liquidez, menor cobertura de analistas, mais suscetível a humor de mercado",
            "Capex pesado recente (Gaia) ainda sendo digerido; FCF pressiona no curto prazo",
        ],
        "barreira": "",
    },
    "SANB3": {
        "nome": "Santander Brasil",
        "fundacao": "1982 (chegou ao Brasil)",
        "sede": "São Paulo, SP",
        "tagline": "O único banco internacional com escala no Brasil. Terceiro maior privado, mas ainda procurando o modelo certo para o mercado local.",
        "modelo": "O Santander é um banco universal (PF + PME + atacado), mas com uma particularidade:  é subsidiária de um grupo global espanhol. Isso tem vantagens (acesso a tecnologia,  melhores práticas globais, plataforma de câmbio internacional) e desvantagens  (decisões estratégicas feitas em Madri podem não se adaptar à realidade brasileira,  e parte do lucro 'vaza' para a matriz). Historicamente, o Santander teve dificuldade  de encontrar seu nicho no Brasil: não tem o foco em alta renda do Itaú, não tem o  agro do BB, não tem o interior do Bradesco, não tem o atacado do BTG.  Em 2026, está buscando diferenciação em crédito imobiliário, alta renda e PME.  O ROE ainda é o mais baixo entre os grandes privados — o mercado cobra prova.",
        "receita": [
            ("Margem financeira (NII)", "~52%", "crédito PF + PME + corporate"),
            ("Receitas de serviços e tarifas", "~22%", "cartão, seguros, corretagem"),
        ],
        "vantagens": [
            "Plataforma global: câmbio, trade finance e operações internacionais para clientes com negócios no exterior",
            "Acesso à tecnologia e melhores práticas do grupo global — Openbank (banco digital do grupo) chegando ao Brasil",
            "Valuation descontado em relação aos pares: se o ROE normalizar, há upside relevante",
            "Histórico consistente de pagamento de JCP — yield atrativo dado o valuation baixo",
        ],
        "riscos": [
            "ROE estruturalmente mais baixo que os pares privados — sem nicho definido que justifique prêmio",
            "Decisões estratégicas dependem da matriz espanhola — nem sempre otimizadas para o Brasil",
            "Exposição a PME e varejo de menor renda em ciclo de juro alto e inadimplência elevada",
            "Competição intensa: Itaú na alta renda, BTG no atacado, Nubank/Inter no varejo digital",
        ],
        "barreira": "A plataforma global é a barreira real. Para uma empresa brasileira que exporta,  importa ou tem sócios internacionais, ter um banco com presença em 10 países na mesa  é conveniente. Mas no varejo PF doméstico, essa vantagem não aparece — o que explica  o ROE mais baixo: a barreira não se traduz em rentabilidade no negócio principal.",
    },
    "SAPR4": {
        "nome": "Sanepar (Companhia de Saneamento do Paraná)",
        "fundacao": "1963",
        "sede": "Curitiba, PR",
        "tagline": "O saneamento do Paraná — eficiente, estatal e sem catalisador. Operação madura, tarifa conservadora, precatórios que foram para o consumidor em vez do acionista.",
        "modelo": "A Sanepar é a empresa de saneamento do Paraná — controlada pelo governo estadual.  Opera 346 concessões municipais, com cobertura de água já alta historicamente  (Paraná tem índices acima da média nacional). O foco atual é expansão de esgoto  e modernização das redes.  Diferente das pares privatizadas, a Sanepar não passou por turnaround —  já era uma empresa relativamente eficiente.  O grande evento de 2026 foi a decisão da AGEPAR sobre os R$4 bi de precatórios  (dinheiro recebido via vitória judicial): a agência regulatória determinou  que o valor será repassado aos consumidores via redução de tarifa,  e não distribuído como dividendo extraordinário.  O mercado frustrado explica a queda de ~8% das ações em 2026.  Também em 2026, a revisão tarifária entregou apenas 2,49% (IRT) —  bem abaixo da inflação — comprimindo margens e frustrou as expectativas.",
        "receita": [
            ("Água — tarifa regulada (AGEPAR/PR)", "~55%", "cobertura histórica alta no PR; crescimento via novos usuários e reajuste tarifário"),
            ("Esgoto — tarifa regulada", "~43%", "déficit de esgoto no Paraná ainda a ser endereçado — maior runway de crescimento"),
            ("Outros serviços", "~2%", "resíduos industriais; serviços técnicos para municípios"),
        ],
        "vantagens": [
            "Operação madura e eficiente: sem o 'mato alto' das estatais que vão para privatização — base operacional sólida",
            "Cobertura alta de água: menor risco operacional e de qualidade; Paraná tem melhores indicadores do setor",
            "Dívida controlada: dívida líquida/EBITDA de 0,71x — folga para investimento sem comprometer a estrutura financeira",
            "P/VP abaixo de 1x: negocia abaixo do valor patrimonial — piso de proteção para o investidor",
            "Estado do Paraná: melhor qualidade de crédito entre os estados brasileiros — menor risco de interferência política irresponsável",
        ],
        "riscos": [
            "Precatórios para consumidores: R$4 bi que o mercado esperava como dividendo foram para os usuários — frustrou a tese de dividendo extraordinário",
            "Revisão tarifária conservadora: IRT 2026 de 2,49% (abaixo da inflação) comprime receita real",
            "Sem catalisador de privatização: governo do PR não sinaliza privatização; sem repricing de múltiplo no horizonte",
            "Crescimento limitado: empresa mais madura = menor crescimento de BRR = menor expansão de receita vs pares",
            "Lucro pressionado: 1T26 com queda de 70,8% (efeito base de comparação alta + itens não recorrentes de 2025)",
        ],
        "barreira": "346 concessões municipais no Paraná — o mesmo monopólio regulado dos pares.  A Sanepar tem uma vantagem específica: décadas de relacionamento com os municípios paranaenses  e um histórico de qualidade de serviço que reduz o risco de revogação de concessões.  O Paraná tem o melhor perfil de pagadores do Brasil —  inadimplência menor, consumo per capita maior, renda acima da média.  A barreira aqui é mais operacional do que de turnaround:  quem tentasse entrar não teria como competir por concessões já consolidadas.",
    },
    "SBSP3": {
        "nome": "Sabesp (Companhia de Saneamento Básico do Estado de SP)",
        "fundacao": "1973",
        "sede": "São Paulo, SP",
        "tagline": "A maior empresa de saneamento da América Latina. Privatizada em 2024 pela maior oferta de saneamento da história — e o turnaround mais ambicioso do setor começa agora.",
        "modelo": "A Sabesp é um monopólio de saneamento no estado de São Paulo —  atende 375 municípios, incluindo a capital e a Grande São Paulo,  que sozinhas concentram 22% da população brasileira e 31% do PIB nacional.  Em julho de 2024, o governo de SP vendeu 32% das ações por R$14,8 bi —  a maior oferta de saneamento da história do Brasil (demanda de R$187 bi).  A Equatorial pagou R$6,9 bi por 15% e assumiu como investidora de referência.  O modelo pós-privatização tem três vetores: (1) turnaround operacional  (opex cortou R$3 bi em 2025 — de R$11,8 para R$8,8 bi);  (2) aceleração de capex (R$20 bi em 2026, quase 3x o histórico anual);  (3) universalização e crescimento da BRR.  Cada real investido e reconhecido pela ARSESP vira receita regulatória futura —  o motor de valorização de longo prazo.  O CEO Carlos Piani (ex-Equatorial Maranhão) declarou: 'Estamos à frente das metas,  o que nos permite sonhar' — sinalizando possível expansão para outras concessões.",
        "receita": [
            ("Água — tarifa regulada", "~65%", "distribuição de água tratada para 375 municípios paulistas"),
            ("Esgoto — tarifa regulada", "~33%", "coleta e tratamento; meta de 90% de cobertura até 2033"),
            ("Outros serviços", "~2%", "resíduos, construção para terceiros, serviços técnicos"),
        ],
        "vantagens": [
            "Melhor área de concessão do Brasil: SP concentra 22% da população e 31% do PIB — demanda e renda acima da média",
            "Turnaround comprovado: R$3 bi de opex cortados em 1 ano — a Equatorial provou que consegue fazer em saneamento o que fez em energia",
            "BRR crescendo de R$88 bi para R$158 bi até 2030 — cada real de capex vira receita regulatória futura",
            "Política de dividendos crescente: 50% do lucro em 2026-27, chegando a 100% a partir de 2030",
            "Revisão tarifária anual até 2030 — ciclo curto reduz o risco de investimento não reconhecido",
        ],
        "riscos": [
            "Execução do capex de R$70 bi: quase 3x o histórico — escassez de empreiteiros, licenças e pessoal capacitado",
            "Revisão tarifária politicamente sensível: Tarcísio de Freitas com agenda eleitoral em 2026 pode pressionar tarifas",
            "Residências irregulares incluídas na universalização: custo e operacionalização incertos",
            "Valuation já captura parte da transformação: ação subiu muito desde a privatização — margem de segurança menor",
            "Lock-up da Equatorial até 2029: limitação de liquidez do controlador no curto prazo",
        ],
        "barreira": "O monopólio regulado é a barreira definitiva.  Nenhuma empresa entra em São Paulo para concorrer com a Sabesp —  a concessão vai até 2060 em contrato único com 375 municípios.  Quem quer saneamento na região metropolitana de SP, paga para a Sabesp.  E com a aceleração do capex e o reconhecimento tarifário anual,  cada ano que passa aumenta os ativos da base regulatória —  criando uma barreira de ativos que vai crescendo com o tempo.",
    },
    "SHUL4": {
        "nome": "Schuler S.A.",
        "fundacao": "1937 (em São Bento do Sul, SC)",
        "sede": "São Bento do Sul, SC",
        "tagline": "A maior estamparia de aço do Brasil. Fabrica as partes metálicas que ninguém vê — mas que todo carro tem. Puro OEM, puro ciclo automotivo.",
        "modelo": "A Schuler é uma OEM pura — fabrica exclusivamente para montadoras.  O produto são peças estampadas de aço: portas, capôs, para-lamas,  reforços estruturais de chassi, componentes de suspensão.  É o que o cliente nunca vê, mas que está em todo veículo.  A demanda segue diretamente a produção de veículos no Brasil —  quando as montadoras produzem mais, a Schuler fatura mais;  quando param (crise de semicondutores, recessão), a Schuler para junto.  A matéria-prima principal é o aço plano — cujo preço é cotado internacionalmente  e tem componente de câmbio, criando risco de margem quando o real desvaloriza  sem que o cliente (montadora) aceite reajuste imediato.  Opera em Santa Catarina, com uma estrutura industrial robusta  e relacionamento de décadas com as principais montadoras do Brasil.",
        "receita": [
            ("Peças estampadas para carros de passeio", "~60%", "GM, Ford, Stellantis, VW, Toyota — clientes concentrados"),
            ("Peças para veículos comerciais e pesados", "~30%", "caminhões e ônibus — ciclo diferente do passeio"),
            ("Ferramental e outros serviços", "~10%", "matrizes e ferramentas para clientes industriais"),
        ],
        "vantagens": [
            "Relacionamento de décadas com montadoras: trocam de fornecedor raramente — custo de mudança é enorme",
            "Santa Catarina: polo industrial consolidado com fornecedores especializados e logística para portos",
            "Especialização técnica: estampagem de alta precisão é barreira de processo que startups não replicam",
            "Veículos comerciais: diversificação com caminhões e ônibus que têm ciclo diferente do passeio",
        ],
        "riscos": [
            "OEM 100%: qualquer queda na produção de veículos impacta diretamente a receita",
            "Concentração de clientes: poucos clientes grandes — perder um é perder fatia relevante",
            "Aço como risco: commodity internacional com componente cambial; repricing com montadora é lento",
            "Eletrificação: carros elétricos têm menos peças estampadas de aço (estrutura diferente) — risco de médio prazo",
        ],
        "barreira": "O processo de qualificação de um novo fornecedor numa montadora leva 2-3 anos  de testes, auditorias e certificações.  A Schuler já passou por esse processo com todos os clientes —  a barreira de entrada não é o equipamento (pode-se comprar uma prensa),  mas o histórico de qualidade que dá confiança à montadora para homologar.  E São Bento do Sul concentra um cluster de indústrias de metal-mecânica  que cria um ambiente de fornecedores especializados difícil de replicar.",
    },
    "SLCE3": {
        "nome": "SLC Agrícola S.A.",
        "fundacao": "1977",
        "sede": "Porto Alegre, RS",
        "tagline": "A maior produtora agrícola listada do Brasil. 700 mil hectares, soja + milho + algodão, tudo vendido em dólar.",
        "modelo": "Produtora pura de commodities — não beneficia nem exporta diretamente.  Opera ~18 fazendas em 7 estados do Cerrado.  ~70% das áreas são arrendadas em sacos de soja/hectare:  quando o preço cai, o custo cai junto — proteção automática de margem.  Em 2025-2026, queda de ~20% no preço da soja e câmbio mais forte  pressionaram margens vs o pico de 2022-2023.",
        "receita": [
            ("Soja", "~55%", "principal cultura; exportada via tradings"),
            ("Algodão", "~30%", "maior margem unitária; demanda global crescente"),
            ("Milho (safrinha)", "~15%", "segunda safra no mesmo solo — custo marginal menor"),
        ],
        "vantagens": [
            "Maior produtora listada: escala de 700 mil ha gera poder de negociação com fornecedores",
            "Arrendamento como hedge: custo em sacos de soja cai quando preço cai automaticamente",
            "Cerrado: produtividade acima da média nacional; logística para exportação otimizada",
            "Diversificação: soja + milho + algodão suaviza dependência de uma única commodity",
        ],
        "riscos": [
            "Preço de soja: queda de 20% no preço reduz receita proporcionalmente",
            "Câmbio apreciado: real forte comprime margens da receita em dólar",
            "Clima: seca ou excesso de chuva impacta produção nas 18 fazendas",
            "Arrendamento renovável: risco de não renovação ou aumento de custo pelo dono da terra",
        ],
        "barreira": "40 anos de relacionamento com donos de terra para arrendamento de longo prazo.  Gestão de 18 fazendas em 7 estados com agricultura de precisão é operação  que levou décadas para construir.  Novo entrante precisaria de capital, terra disponível e reputação ao mesmo tempo.",
    },
    "SUZB3": {
        "nome": "Suzano",
        "fundacao": "1924",
        "sede": "São Paulo, SP",
        "tagline": "A maior produtora mundial de celulose de eucalipto. Puro jogo de escala, custo e câmbio.",
        "modelo": "A Suzano planta eucalipto, processa em celulose de fibra curta (BHKP) e exporta  praticamente tudo em dólar. O produto é commodity global — o preço é dado pelo mercado  internacional, não pela empresa. Sua vantagem é ser a produtora de menor custo do  mundo, graças à produtividade do eucalipto brasileiro (o mais rápido do planeta —  7 anos do plantio ao corte) e à escala das operações após a fusão com a Fibria em 2019.",
        "receita": [
            ("Celulose BHKP", "~85%", "fibra curta de eucalipto, commodity global"),
            ("Papel", "~10%", "papel para imprimir/escrever e tissue"),
            ("Outros", "~5%", "energia, madeira, derivados"),
        ],
        "vantagens": [
            "Menor custo de produção de celulose do mundo — floresta tropical de crescimento ultrarrápido",
            "Escala de 10,9 milhões de toneladas/ano — nenhum concorrente chega perto no eucalipto",
            "Hedge natural: receita em dólar vs. custos em real",
            "Certificação FSC de toda a base florestal — acesso a mercados premium na Europa",
        ],
        "riscos": [
            "Preço da celulose cai 30–40% num ciclo negativo — resultado despenca junto",
            "Dívida em dólar: variação cambial pode gerar prejuízo contábil mesmo com caixa saudável",
            "Projeto Cerrado (nova fábrica em GO) aumentou alavancagem — deleveraging levará anos",
            "Produto único: sem diversificação que amortize o ciclo",
        ],
        "barreira": "",
    },
    "TAEE11": {
        "nome": "Taesa (Transmissora Aliança de Energia Elétrica)",
        "fundacao": "2009 (parceria Cemig + ISA Colombia)",
        "sede": "Belo Horizonte, MG",
        "tagline": "A NTN-B da bolsa. Receita de longo prazo indexada à inflação, payout de 100%, sem risco climático. O preço que se paga é a alavancagem.",
        "modelo": "A Taesa é a transmissora pura mais conhecida da B3. Opera mais de 13.000 km de linhas de  transmissão e 109 subestações em 18 estados. O modelo é simples e poderoso:  vence um leilão da ANEEL, constrói a linha e passa a receber a RAP (Receita Anual Permitida)  por 30 anos. A RAP não depende de quanto energia flui pela linha — só de a linha estar disponível  dentro dos parâmetros técnicos (parâmetros de indisponibilidade geram desconto na RAP,  chamado de Parcela Variável). Com receita indexada à inflação (60% IGPM + 40% IPCA),  payout de 100% e sem risco climático, a Taesa é comparada a uma NTN-B de longo prazo.  O que diferencia dos títulos públicos: risco de renovação de concessões antigas  com metodologia menos favorável, e alavancagem de 4,7x que limita novos investimentos.",
        "receita": [
            ("RAP de transmissão", "~95%", "receita contratada por 30 anos, reajustada por IGPM/IPCA"),
            ("Reforços e melhorias autorizados", "~5%", "RAP adicional por obras autorizadas na concessão"),
        ],
        "vantagens": [
            "Zero risco climático: transmissão não gera energia — chuva, seca, vento não importam",
            "RAP indexada à inflação: receita do próximo ano é basicamente conhecida hoje",
            "Payout de ~100% do lucro regulatório: quem compra recebe praticamente todo o lucro",
            "Portfólio de categoria II/III (mais transparente): menor risco de surpresa regulatória nas concessões novas",
            "Quando o IGPM supera o IPCA: receita cresce mais que os custos — assimetria positiva",
        ],
        "riscos": [
            "Alavancagem de 4,7x dívida líquida/EBITDA — a maior entre as transmissoras da B3",
            "Concessões antigas têm metodologia diferente: revisão pode reduzir 15-20% da RAP dessas linhas",
            "Capex pendente de R$2,2 bi em projetos — a empresa precisa captar e construir",
            "IGPM negativo (já aconteceu em 2017) reduz a receita das concessões indexadas a esse índice",
            "Selic alta eleva o custo da dívida e comprime o valuation (duration muito longa)",
        ],
        "barreira": "Uma vez vencido o leilão, a concessão é exclusiva por 30 anos.  Ninguém constrói uma linha de transmissão paralela — o regulador não autoriza.  O custo de construção da infraestrutura e a exclusividade regulatória criam  um monopólio natural de altíssima barreira.  O desafio não é a concorrência — é vencer o próximo leilão a uma RAP que ainda dê retorno.",
    },
    "VALE3": {
        "nome": "Vale S.A.",
        "fundacao": "1942 (como Companhia Vale do Rio Doce, estatal; privatizada em 1997)",
        "sede": "Rio de Janeiro, RJ",
        "tagline": "A maior mineradora de ferro do mundo. Carajás é o maior e melhor depósito de minério de ferro do planeta — e a Vale tem ele há 80 anos.",
        "modelo": "A Vale é uma das cinco maiores empresas de mineração do mundo e a maior exportadora  de minério de ferro do planeta. Opera em dois grandes segmentos:  Metais Ferrosos (~70% do EBITDA) e Metais Básicos (~15%).  O coração do negócio é o Sistema Norte — a mina de Carajás, no Pará.  Carajás tem o maior depósito de minério de ferro de alta qualidade do mundo:  reservas de ~7 bilhões de toneladas com teor médio de 67% Fe  (benchmark é 62%). A qualidade superior gera prêmio de preço de US$5-15/t.  A logística é integrada: ferrovia EFC (Estrada de Ferro Carajás, 892 km)  leva o minério diretamente ao Porto do Itaqui (MA) —  sem baldeação, sem intermediário, menor custo.  Em metais básicos, a Vale tem níquel no Canadá (Voisey's Bay)  e cobre em projetos de desenvolvimento.  Com a transição energética, cobre e níquel ganham relevância —  o Sossego e o Salobo (cobre no PA) são apostas de longo prazo.",
        "receita": [
            ("Minério de ferro e pelotas (Sistema Norte — Carajás)", "~55%", "67% Fe; premium sobre benchmark; EFC + Porto Itaqui"),
            ("Minério de ferro (Sistema Sudeste — MG)", "~20%", "62-63% Fe; Quadrilátero Ferrífero; sistema mais antigo e caro"),
            ("Níquel e subprodutos (cobre, cobalto, platina)", "~12%", "Canadá, Brasil, Indonesia; metal da bateria EV"),
            ("Cobre (Sossego, Salobo — PA)", "~8%", "crescimento acelerado; apoio da transição energética"),
        ],
        "vantagens": [
            "Carajás: o melhor minério do mundo em qualidade e reservas — inreplicável em qualquer outra jurisdição",
            "Custo C1 entre os mais baixos do planeta: ~US$23-25/t vs produtores marginais a US$80+/t",
            "Logística própria (EFC + Porto Itaqui): controle do custo de ponta a ponta sem dependência de terceiros",
            "Diversificação em metais da transição: cobre e níquel crescem em relevância com veículos elétricos",
            "Sem controlador majoritário: gestão profissional com foco em retorno ao acionista",
        ],
        "riscos": [
            "China: 70% das exportações vão para a China — qualquer desaceleração afeta diretamente",
            "Brumadinho: passivo ambiental e reputacional em curso desde 2019 — provisões continuam pesando",
            "Metais básicos: cobre e níquel ainda não são escala suficiente para compensar volatilidade do ferro",
            "Produção de Carajás com metas ambiciosas: execução de S11D a plena capacidade é desafio logístico",
            "Câmbio apreciado comprime margens em reais mesmo sem queda do preço do minério",
        ],
        "barreira": "Carajás é a barreira definitiva.  O depósito foi descoberto em 1967 por geólogos da Vale e da US Steel —  e nunca se encontrou outro igual no mundo em qualidade e escala.  Quem não tem Carajás não tem o mesmo produto.  Adicione a ferrovia de 892 km e o porto próprio:  construir essa logística hoje custaria US$15-20 bi e levaria 10-15 anos.  A Vale tem isso funcionando há décadas.",
    },
    "VULC3": {
        "nome": "Vulcabras Azaleia S.A.",
        "fundacao": "1952 (como Calçados Azaleia; Vulcabras desde 2011)",
        "sede": "Jundiaí, SP",
        "tagline": "O maior fabricante de calçados esportivos do Brasil. Faz Under Armour para o Brasil e Olympikus — 50 milhões de pares por ano, saindo de Horizonte (CE).",
        "modelo": "A Vulcabras é a maior fabricante de calçados esportivos do Brasil —  em volume de produção, não em receita de marca.  Opera com duas marcas: Olympikus (própria, focada em performance popular)  e Under Armour (licença exclusiva para o Brasil — fabrica, distribui e vende).  A fábrica principal fica em Horizonte (CE) — maior complexo industrial  de calçados do hemisfério sul, com mais de 13.000 funcionários.  O Nordeste tem dois benefícios estruturais: custo de mão de obra menor  e incentivos fiscais do estado do Ceará.  O modelo de licença da Under Armour é o diferencial:  a Vulcabras paga royalty (em dólar, um custo),  mas recebe o brand premium de uma marca global de alta performance  que ela não precisaria construir do zero.  Vende via varejo (Renner, Riachuelo), e-commerce e lojas multimarcas.",
        "receita": [
            ("Under Armour Brasil (licença)", "~48%", "marca premium — maior ticket médio; paga royalty em dólar; contrato vigente"),
            ("Olympikus", "~40%", "marca própria — boa penetração no interior e classes B/C; maior margem líquida"),
            ("Outros (exportação, private label)", "~12%", "exportação para América Latina; produção para terceiros"),
        ],
        "vantagens": [
            "Maior complexo industrial de calçados do hemisfério sul: escala de 50 mi de pares/ano gera custo unitário imbatível",
            "Under Armour: brand premium sem o risco de construir uma marca global do zero",
            "Nordeste: custo de mão de obra menor + incentivos fiscais do Ceará = estrutura de custo competitiva",
            "Margem bruta 42-45%: a mais alta do grupo — mix de marca premium com produção eficiente",
            "Olympikus como proteção: marca própria cresce sem depender de contrato de licença",
        ],
        "riscos": [
            "Renovação do contrato Under Armour: se perder a licença, perde ~48% da receita do dia para a noite",
            "Royalty em dólar: custo da licença sobe com o dólar — margem comprimida em desvalorizações do real",
            "Importados asiáticos: concorrência de calçados chineses e vietnamitas comprime preços no varejo",
            "Exposição à renda da classe C: Olympikus e Under Armour entry-level sensíveis a crises de renda",
        ],
        "barreira": "Escala industrial e a licença Under Armour.  Construir um complexo de 13.000 funcionários especializados em calçados esportivos  leva décadas — e criar o conhecimento técnico de solado,  espuma de amortecimento e cabedal esportivo é barreira de processo.  A Under Armour escolheu a Vulcabras porque ela é a única no Brasil  com capacidade de produzir em escala e qualidade para uma marca premium global.",
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


# ---- P/FCO e P/FCL via Fundamentei (página de Valuation, sem login) ------
# NUNCA TESTADO contra o HTML de verdade -- a página parece ser um app
# Next.js (componentes React), não uma tabela HTML tradicional como o
# Fundamentus, então a extração aqui é por busca de texto em sequência
# (acha "P/FCO"/"P/FCL" no DOM e pega o número que vem imediatamente antes),
# resistente a mudança de tag (div/h2/h4) mas sensível a mudança de classe
# CSS que reordene o conteúdo. Validar com Diego antes de confiar.
@st.cache_data(ttl=86400, show_spinner=False)
def get_fluxo_caixa_fundamentei(ticker):
    """Busca P/FCO (preço ÷ fluxo de caixa operacional) e P/FCL (preço ÷
    fluxo de caixa livre) na página pública de Valuation do Fundamentei --
    métricas de geração de caixa real, não disponíveis no Fundamentus.
    Retorna (dict_ou_None, erro_ou_None). dict tem 'p_fco' e 'p_fcl'
    (ambos float ou None se não encontrados)."""
    try:
        url = f"https://fundamentei.com/br/{ticker.lower()}/valuation?tab=VALUATION"
        r = requests.get(url, timeout=12, headers=_FUNDAMENTUS_HEADERS)
        if r.status_code != 200:
            return None, f"HTTP {r.status_code} ao acessar Fundamentei"

        soup = BeautifulSoup(r.text, 'html.parser')
        # Pega todo o texto visível, em ordem, quebrado por elemento --
        # assim a busca não depende de qual tag específica (h2, h4, div)
        # envolve cada número/rótulo.
        textos = [t.strip() for t in soup.stripped_strings]

        def _achar_valor_antes_do_rotulo(rotulo_exato):
            for i, txt in enumerate(textos):
                if txt == rotulo_exato:
                    # Procura pra trás o primeiro texto que parece um número
                    for j in range(i - 1, max(i - 4, -1), -1):
                        candidato = textos[j].replace('.', '').replace(',', '.')
                        try:
                            return float(candidato)
                        except ValueError:
                            continue
            return None

        p_fco = _achar_valor_antes_do_rotulo('P/FCO')
        p_fcl = _achar_valor_antes_do_rotulo('P/FCL')

        if p_fco is None and p_fcl is None:
            return None, "P/FCO e P/FCL não encontrados na página (estrutura pode ter mudado)"

        return {'p_fco': p_fco, 'p_fcl': p_fcl}, None
    except Exception as e:
        return None, str(e)


# Rótulos EXATOS de cada aba de Valuation do Fundamentei (o valor aparece
# ANTES do rótulo na página). Confirmados na estrutura pública do site.
_FUNDAMENTEI_ABAS = {
    "VALUATION": ["P/R", "P/EBITDA"],
    "PROFITABILITY": ["Margem EBITDA", "Margem EBIT", "D&A/EBITDA",
                      "Capex/Receita", "Capex/D&A", "Capex/FCO"],
    "GROWTH": ["CAGR Receita 5 anos", "CAGR Lucro Op. 5 anos",
               "CAGR LPA 5 anos", "CAGR FCO 5 anos"],
}


def _fmei_num(txt):
    """Converte texto do Fundamentei ('8,2%', '12,5', '—', '1.234,5') em
    float ou None. Trata '%', traço de indisponível e formato BR."""
    if txt is None:
        return None
    s = str(txt).strip().replace('%', '').replace('R$', '').strip()
    if s in ('—', '-', '', 'N/A', 'n/a', 'nan'):
        return None
    s = s.replace('.', '').replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None


@st.cache_data(ttl=86400, show_spinner=False)
def get_indicadores_fundamentei(ticker):
    """Raspa os indicadores das 4 abas de Valuation do Fundamentei (Valuation,
    Lucratividade, Crescimento, Alavancagem). Retorna (dict rótulo->float|None,
    erro). O valor vem ANTES do rótulo na página, então buscamos pra trás nos
    1-2 elementos anteriores (evita pegar número de outro indicador)."""
    resultado = {}
    erro = None
    for aba, rotulos in _FUNDAMENTEI_ABAS.items():
        try:
            url = f"https://fundamentei.com/br/{ticker.lower()}/valuation?tab={aba}"
            r = requests.get(url, timeout=12, headers=_FUNDAMENTUS_HEADERS)
            if r.status_code != 200:
                erro = f"HTTP {r.status_code} ({aba})"
                for rot in rotulos:
                    resultado.setdefault(rot, None)
                continue
            soup = BeautifulSoup(r.text, 'html.parser')
            textos = [t.strip() for t in soup.stripped_strings]
            for rotulo in rotulos:
                valor = None
                for i, txt in enumerate(textos):
                    if txt == rotulo:
                        for j in range(i - 1, max(i - 3, -1), -1):
                            v = _fmei_num(textos[j])
                            if v is not None:
                                valor = v
                                break
                        break
                resultado[rotulo] = valor
        except Exception as e:
            erro = str(e)
            for rot in rotulos:
                resultado.setdefault(rot, None)

    if not any(v is not None for v in resultado.values()):
        return None, (erro or "nenhum indicador encontrado")
    return resultado, erro


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
        # Valor de mercado — busca a coluna independente de capitalização
        _col_vm = next((c for c in df.columns if c.strip().upper() == 'VALOR DE MERCADO'), None)
        if _col_vm:
            df['vl_mercado'] = df[_col_vm].apply(lambda v: limpar_valor(str(v)) / 1e9 if limpar_valor(str(v)) else 0)
        else:
            df['vl_mercado'] = 0

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

    _NOMES_ABAS = ["📊 Visão Geral", "💰 Valuation", "📈 Dividendos",
                   "👤 Movimentação", "📑 Resultado", "🧠 Tese"]
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

        with st.expander("🔍 Ver de onde vem esse Score, ponto a ponto"):
            _dy_brk = ativo_data.get('dy_num', 0) if isinstance(ativo_data, dict) else 0
            _pl_brk = ativo_data.get('pl_num', 0) if isinstance(ativo_data, dict) else 0
            _roe_brk = ativo_data.get('roe_num_raw', 0) if isinstance(ativo_data, dict) else 0
            _marg_brk = ativo_data.get('margem_num_raw', 0) if isinstance(ativo_data, dict) else 0
            _pvp_brk = ativo_data.get('pvp_num_raw', 0) if isinstance(ativo_data, dict) else 0
            _div_eb_brk = limpar_valor(row.get('Dívida líquida/EBITDA', 0))
            _cagr_brk = limpar_valor(row.get('CAGR lucros (últ. 5 anos)', 0))
            _hist_brk = ativo_data.get('historico_lucro', {}) if isinstance(ativo_data, dict) else {}

            _det = explicar_score(_dy_brk, _pl_brk, _div_eb_brk, _cagr_brk, _roe_brk, _marg_brk,
                                  pvp_num=_pvp_brk, setor=row.get('SETOR', ''), ticker=ticker,
                                  historico_lucro=_hist_brk)

            st.caption(f"Categoria de setor usada: **{_det['categoria']}**")
            for label, obtido, possivel in _det['itens']:
                pct_barra = int((obtido / possivel) * 100) if possivel > 0 else 0
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;font-size:0.85em;"
                    f"margin-bottom:2px;'><span>{label}</span>"
                    f"<span style='color:#D4AF37;font-weight:700;'>{obtido:.2f} / {possivel:.1f}</span></div>"
                    f"<div style='background:rgba(255,255,255,0.08);border-radius:4px;height:6px;"
                    f"margin-bottom:10px;overflow:hidden;'>"
                    f"<div style='background:#D4AF37;height:100%;width:{pct_barra}%;'></div></div>",
                    unsafe_allow_html=True
                )
            st.markdown(
                f"**Subtotal qualidade + valuation: {_det['subtotal']:.2f} / 10,0**  \n"
                f"Ajuste de governança: {_det['pen_governanca']:+.2f}  \n"
                f"Multiplicador de outlook 2026: ×{_det['mult_outlook']:.2f}  \n"
                f"**= Score de fundamentos: {_det['score_fundamentos']}/10** "
                f"(depois disso ainda entra o ajuste de preço vs. teto, se houver, pra "
                f"chegar no Score de Momento mostrado acima)."
            )
            st.caption(
                "Compare esse detalhamento com o de outro ativo do mesmo setor pra entender "
                "exatamente qual componente está pesando mais — em vez de só confiar no número "
                "final."
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

        # ---- Volatilidade Implícita / IV Rank / IV Percentil ----
        st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)
        st.markdown(
            "<span style='font-size:0.8em;color:#D4AF37;font-weight:bold;"
            "text-transform:uppercase;letter-spacing:0.5px;'>Volatilidade Implícita</span>",
            unsafe_allow_html=True,
        )
        with st.spinner(""):
            _vol_vg, _erro_vg = get_volatilidade_ticker(ticker)
        if _vol_vg is not None:
            _vi  = _vol_vg['vol_implicita']
            _rnk = _vol_vg['iv_rank']
            _pct = _vol_vg['iv_percentil']
            _cor_vg = "#EF4444" if (_rnk or 0) >= 70 else ("#D4AF37" if (_rnk or 0) >= 30 else "#22C55E")
            _vc1, _vc2, _vc3 = st.columns(3)
            for _col_vg, _lbl_vg, _val_vg in [
                (_vc1, "Vol. Implícita", f"{_vi:.2f}%".replace(".", ",") if _vi is not None else "—"),
                (_vc2, "IV Rank",        f"{_rnk:.0f}%".replace(".", ",") if _rnk is not None else "—"),
                (_vc3, "IV Percentil",   f"{_pct:.0f}%".replace(".", ",") if _pct is not None else "—"),
            ]:
                _col_vg.markdown(
                    "<div style='{base}text-align:center;'>"
                    "<div style='font-size:0.75em;color:#ccc;text-transform:uppercase;'>{lbl}</div>"
                    "<div style='font-size:1.4em;font-weight:900;color:{cor};'>{val}</div>"
                    "</div>".format(base=card_style, cor=_cor_vg, lbl=_lbl_vg, val=_val_vg),
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Volatilidade implícita indisponível para este ativo.")

    # ════════════════════════════════════════════════════════════════════
    # ABA: TESE (qualitativo: sobre o negócio, governança, outlook,
    # estudo específico, panorama da empresa, par-a-par)
    # ════════════════════════════════════════════════════════════════════
    if aba_ativa == "🧠 Tese":
        # ════════════════════════════════════════════════════════════
        # PERFIL DO DOSSIÊ — estilo idêntico ao app de estudo
        # Cobre: modelo, receita, vantagens, riscos, barreira
        # ════════════════════════════════════════════════════════════
        _perfil = PERFIL_EMPRESA.get(ticker)
        if _perfil:
            # Cabeçalho com tagline
            _cor_tese = {"Bancos": "#60A5FA", "Seguros": "#A78BFA",
                         "Energia Elétrica": "#FCD34D", "Petróleo": "#FB923C",
                         "Mineração": "#FBBF24", "Agronegócio": "#86EFAC",
                         "Shoppings": "#E879F9", "Saneamento": "#38BDF8",
                         "Telecom": "#60A5FA"}.get(row.get("SETOR",""), "#D4AF37")

            st.markdown(
                f"<div style='{card_style}border-left:4px solid {_cor_tese};margin-bottom:18px;'>"
                f"<div style='font-size:0.7em;color:#aaa;text-transform:uppercase;"
                f"letter-spacing:1px;margin-bottom:4px;'>"
                f"{_perfil.get('nome',ticker)} · {_perfil.get('fundacao','')} · {_perfil.get('sede','')}</div>"
                f"<div style='font-size:0.95em;color:{_cor_tese};font-style:italic;"
                f"font-weight:600;line-height:1.5;'>{_perfil.get('tagline','')}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

            # Como funciona o negócio
            st.markdown(
                "<span style='font-size:0.75em;color:#D4AF37;font-weight:700;"
                "text-transform:uppercase;letter-spacing:0.8px;'>Como funciona o negócio</span>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='{card_style}margin-bottom:16px;'>"
                f"<div style='font-size:0.91em;color:#ddd;line-height:1.75;'>"
                f"{_perfil.get('modelo','')}</div></div>",
                unsafe_allow_html=True,
            )

            # De onde vem a receita
            if _perfil.get('receita'):
                st.markdown(
                    "<span style='font-size:0.75em;color:#D4AF37;font-weight:700;"
                    "text-transform:uppercase;letter-spacing:0.8px;margin-top:4px;display:block;'>"
                    "De onde vem a receita</span>",
                    unsafe_allow_html=True,
                )
                for _seg, _pct, _det in _perfil['receita']:
                    st.markdown(
                        f"<div style='display:flex;align-items:flex-start;gap:14px;"
                        f"padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.06);'>"
                        f"<div style='min-width:52px;text-align:right;font-size:1.05em;"
                        f"font-weight:800;color:#D4AF37;'>{_pct}</div>"
                        f"<div><div style='font-size:0.88em;font-weight:600;color:#eee;"
                        f"margin-bottom:2px;'>{_seg}</div>"
                        f"<div style='font-size:0.80em;color:#aaa;'>{_det}</div></div></div>",
                        unsafe_allow_html=True,
                    )
                st.markdown("<div style='margin-bottom:14px;'></div>", unsafe_allow_html=True)

            # Vantagens e Riscos lado a lado
            _tc1, _tc2 = st.columns(2)
            with _tc1:
                if _perfil.get('vantagens'):
                    st.markdown(
                        "<span style='font-size:0.75em;color:#22C55E;font-weight:700;"
                        "text-transform:uppercase;letter-spacing:0.8px;'>Vantagens competitivas</span>",
                        unsafe_allow_html=True,
                    )
                    for _v in _perfil['vantagens']:
                        st.markdown(
                            f"<div style='background:rgba(34,197,94,0.07);border-left:3px solid #22C55E;"
                            f"border-radius:0 8px 8px 0;padding:9px 13px;margin-bottom:7px;"
                            f"font-size:0.87em;color:#d1fae5;line-height:1.5;'>✦ {_v}</div>",
                            unsafe_allow_html=True,
                        )
            with _tc2:
                if _perfil.get('riscos'):
                    st.markdown(
                        "<span style='font-size:0.75em;color:#EF4444;font-weight:700;"
                        "text-transform:uppercase;letter-spacing:0.8px;'>Riscos principais</span>",
                        unsafe_allow_html=True,
                    )
                    for _r in _perfil['riscos']:
                        st.markdown(
                            f"<div style='background:rgba(239,68,68,0.07);border-left:3px solid #EF4444;"
                            f"border-radius:0 8px 8px 0;padding:9px 13px;margin-bottom:7px;"
                            f"font-size:0.87em;color:#fee2e2;line-height:1.5;'>⚠ {_r}</div>",
                            unsafe_allow_html=True,
                        )

            # Barreira de entrada
            if _perfil.get('barreira'):
                st.markdown(
                    "<span style='font-size:0.75em;color:#D4AF37;font-weight:700;"
                    "text-transform:uppercase;letter-spacing:0.8px;margin-top:4px;display:block;'>"
                    "Barreira de entrada</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div style='background:rgba(212,175,55,0.07);border-left:3px solid #D4AF37;"
                    f"border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:16px;"
                    f"font-size:0.87em;color:#fef3c7;line-height:1.5;'>🔒 {_perfil['barreira']}</div>",
                    unsafe_allow_html=True,
                )

            st.markdown("---")

        # ---- Governança e Outlook (mantidos abaixo do perfil) ----
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

        # ---- Estudo Específico ----
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

        # PANORAMA_EMPRESA sempre exibido quando existir — é conteúdo diferente do PERFIL
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

        # ---- Earnings Yield (1/P-L Atual) + TIR REAL por arquétipo ----
        st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
        if pl_atual_val and pl_atual_val > 0:
            ey_val = (1 / pl_atual_val) * 100
            ey_str = f"{ey_val:.1f}%".replace(".", ",")
            ey_cor = "#22C55E" if ey_val >= 10 else ("#D4AF37" if ey_val >= 6 else "#EF4444")
        else:
            ey_str, ey_cor = "—", "#888"

        eytir1, eytir2, eytir3 = st.columns(3)
        _card_metric(eytir1, "Earnings Yield", ey_str, cor_valor=ey_cor)
        render_tir(st, eytir2, eytir3, ticker, row, ativo_data, pl_atual_val, dy_num, card_style, limpar_valor)

        st.caption(
            "Earnings Yield = 1 ÷ P/L Atual. TIR REAL = retorno anual real (nominal "
            "descontado o IPCA base de 6%), no formato IPCA + X%, pelo método do arquétipo "
            "do ativo — o botão ao lado abre a memória de cálculo, passo a passo."
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

        # ---- Indicadores unificados, agrupados por categoria ----
        def _f1(v, suf="", pre=""):
            return (pre + f"{v:.1f}{suf}").replace(".", ",") if v is not None else "\u2014"

        def _f2(v, suf="", pre=""):
            return (pre + f"{v:.2f}{suf}").replace(".", ",") if v is not None else "\u2014"

        _sem_ebitda = _setor_cat in ('banco', 'seguradora', 'holding')

        _fdm_dados = None
        if not _sem_ebitda:
            _fdm_dados, _fdm_erro = get_fluxo_caixa_fundamentei(ticker)
        _fco = (_fdm_dados or {}).get('p_fco')
        _fcl = (_fdm_dados or {}).get('p_fcl')

        _ind_add, _ = get_indicadores_fundamentei(ticker)
        _ia = _ind_add or {}

        _grupos_ind = [
            ("Valuation", [
                ("P/VP", pvp_str if pvp_str != "-" else "\u2014", _destaca_pvp_roe, True),
                ("P/R", _f1(_ia.get('P/R'), "x"), False, True),
                ("P/EBIT", _f1(p_ebit_val, "x"), False, not _sem_ebitda),
                ("P/EBITDA", _f1(_ia.get('P/EBITDA'), "x"), False, not _sem_ebitda),
                ("EV/EBITDA", _f1(ev_ebitda_val, "x"), False, not _sem_ebitda),
                ("P/FCO", _f1(_fco, "x"), False, not _sem_ebitda),
                ("P/FCL", _f1(_fcl, "x"), False, not _sem_ebitda),
                ("PEG Ratio", _f1(peg_val, "x"), False, True),
                ("VPA", _f2(vpa_val, "", "R$ "), False, True),
            ]),
            ("Rentabilidade", [
                ("ROE", roe, _destaca_pvp_roe, True),
                ("ROIC", _f1(roic_val, "%"), False, True),
                ("ROA", _f1(roa_val, "%"), False, True),
                ("Margem Liq.", margem, False, True),
                ("Margem EBITDA", _f1(_ia.get('Margem EBITDA'), "%"), False, not _sem_ebitda),
                ("Margem EBIT", _f1(_ia.get('Margem EBIT'), "%"), False, not _sem_ebitda),
            ]),
            ("Capex & Fluxo de Caixa", [
                ("D&A/EBITDA", _f1(_ia.get('D&A/EBITDA'), "%"), False, not _sem_ebitda),
                ("Capex/Receita", _f1(_ia.get('Capex/Receita'), "%"), False, not _sem_ebitda),
                ("Capex/D&A", _f1(_ia.get('Capex/D&A'), "%"), False, not _sem_ebitda),
                ("Capex/FCO", _f1(_ia.get('Capex/FCO'), "%"), False, not _sem_ebitda),
            ]),
            ("Crescimento (5 anos)", [
                ("CAGR Lucros", row.get('CAGR lucros (\u00faltimos 5 anos)', row.get('CAGR lucros (\u00falt. 5 anos)', '-')), False, True),
                ("CAGR Receita", _f1(_ia.get('CAGR Receita 5 anos'), "%"), False, True),
                ("CAGR Lucro Op.", _f1(_ia.get('CAGR Lucro Op. 5 anos'), "%"), False, True),
                ("CAGR LPA", _f1(_ia.get('CAGR LPA 5 anos'), "%"), False, True),
                ("CAGR FCO", _f1(_ia.get('CAGR FCO 5 anos'), "%"), False, True),
            ]),
            ("Endividamento & Risco", [
                ("Divida Liq/EBITDA", row.get('D\u00edvida l\u00edquida/EBITDA', '-'), _destaca_div_ebitda, True),
                ("Divida/Patrim.", _f2(div_liq_patrim_val), False, True),
                ("Beta (vs IBOV)", beta, False, True),
            ]),
        ]

        for _nome_g, _cards in _grupos_ind:
            _vis = [c for c in _cards if c[3]]
            if not _vis:
                continue
            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            st.markdown(
                f"<span style='font-size:0.8em;color:#D4AF37;font-weight:bold;"
                f"text-transform:uppercase;letter-spacing:0.5px;'>{_nome_g}</span>",
                unsafe_allow_html=True,
            )
            for _k in range(0, len(_vis), 4):
                _linha = _vis[_k:_k + 4]
                _cols = st.columns(4)
                for _idx, (_tit, _txt, _dest, _) in enumerate(_linha):
                    _card_metric(_cols[_idx], _tit, _txt, destaque=_dest)

        st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)
        if _sem_ebitda:
            st.caption(
                "Para bancos, seguradoras e holdings, os m\u00faltiplos e margens baseados em "
                "EBITDA/Capex s\u00e3o omitidos de prop\u00f3sito \u2014 n\u00e3o fazem sentido para o modelo "
                "de neg\u00f3cio desses setores (sairiam valores sem significado real)."
            )
        st.caption(
            "PEG Ratio = P/L Projetado \u00f7 CAGR de Lucros. Abaixo de 1x costuma indicar "
            "crescimento barato frente ao pre\u00e7o; acima de 2x, pre\u00e7o esticado."
        )
        if not ind_extras and erro_ind:
            st.caption(f"Alguns indicadores (ROIC, VPA, etc.) est\u00e3o indispon\u00edveis agora ({erro_ind}).")

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
    if False:  # Vol./Gráfico removido -- vol está na Visão Geral
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


@st.cache_data(ttl=86400, show_spinner=False)
def get_fluxo_caixa_livre(ticker):
    """Busca o Fluxo de Caixa Livre (TTM) via brapi.dev, módulo financialData
    (fonte: CVM -- demonstrações financeiras oficiais, não Yahoo). Retorna
    (valor_ou_None, json_bruto_ou_None, erro_ou_None) -- o json_bruto é só
    pra diagnóstico, pra ver a resposta completa caso o nome do campo não
    seja o que eu chutei.

    NUNCA TESTADO contra o token de verdade -- além do nome do campo ser
    incerto, a documentação da brapi.dev sugere que Fluxo de Caixa pode
    exigir plano pago (Startup/Pro), não disponível no plano básico. Se
    falhar, o erro retornado deve indicar o motivo (sem token, HTTP 402
    'Payment Required' = precisa de upgrade de plano, campo ausente, etc.)."""
    token = st.secrets.get("BRAPI_TOKEN", "")
    if not token:
        return None, None, "BRAPI_TOKEN não configurado"
    try:
        url = f"https://brapi.dev/api/quote/{ticker}?modules=financialData&token={token}"
        r = requests.get(url, timeout=8)
        if r.status_code == 402:
            return None, None, "HTTP 402 (Payment Required) — esse dado provavelmente exige upgrade do plano na brapi.dev"
        if r.status_code != 200:
            return None, None, f"HTTP {r.status_code}"
        dados_json = r.json()
        resultados = dados_json.get('results', [])
        if not resultados:
            return None, dados_json, "resposta sem 'results'"
        fin_data = resultados[0].get('financialData', {})
        if not fin_data:
            return None, dados_json, "ticker encontrado, mas sem o módulo financialData na resposta"
        # Nome exato do campo é uma estimativa -- tentamos algumas variantes
        # comuns (camelCase em inglês, padrão Yahoo-like que a brapi.dev
        # costuma seguir na nomenclatura dos campos).
        for chave in ('freeCashflow', 'freeCashFlow', 'fluxoCaixaLivre'):
            if chave in fin_data and fin_data[chave] is not None:
                return float(fin_data[chave]), dados_json, None
        return None, dados_json, "módulo financialData veio, mas nenhum campo de FCL conhecido foi encontrado dentro dele"
    except Exception as e:
        return None, None, str(e)


def get_taxa_real_referencia():
    """Wrapper com fallback: tenta a busca live; se falhar, usa o valor
    manual. Sempre retorna um número usável."""
    taxa, _, _ = get_taxa_ipca_longa()
    return taxa if taxa is not None else TAXA_IPCA_LONGA_MANUAL


ibov_val, ibov_var = get_ibov()
selic_val = get_selic()

# Cabeçalho (Total/Filtrados/Ibovespa/Selic/destaques) só aparece na tela
# principal em modo Cards -- esconde ao abrir um ativo (mais espaço pra
# ver o detalhe) e no modo Tabela (mais espaço pra ver mais empresas).
_mostrar_cabecalho = (not st.session_state.ativo_selecionado
                      and st.session_state.modo_exibicao != 'Tabela')
card_filtrados = card_menor_pl = card_maior_score = None

# ---- Linha 1: Total+Filtrados (juntas = largura de 1 caixa de baixo);
# Ibovespa+Selic (juntas = largura de 2 caixas de baixo, centralizadas) ----
if _mostrar_cabecalho:
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
    tcol2, tcol3, tcol4, tcol5, tcol6 = st.columns([1, 1, 1, 1.4, 5])
    with tcol2:
        if st.button("⊞ Cards", use_container_width=True,
                     type="primary" if st.session_state.modo_exibicao == 'Cards' else "secondary"):
            st.session_state.modo_exibicao = 'Cards'
            st.rerun()
    with tcol3:
        if st.button("📋 Tabela", use_container_width=True,
                     type="primary" if st.session_state.modo_exibicao == 'Tabela' else "secondary"):
            st.session_state.modo_exibicao = 'Tabela'
            st.rerun()
    with tcol4:
        if st.button("⚖ Comparar", use_container_width=True,
                     type="primary" if st.session_state.modo_exibicao == 'Comparar' else "secondary"):
            st.session_state.modo_exibicao = 'Comparar'
            st.rerun()
    with tcol5:
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

        # ROE, Margem Líquida e Mínima/Máxima de 12 meses: prioriza
        # Fundamentus sobre Yahoo -- o Yahoo é inconsistente pra ações da B3
        # (campos vazios com frequência, principalmente fora do horário de
        # mercado aberto), enquanto o Fundamentus é a mesma fonte já usada
        # pra ROIC/P-L/VPA em outras partes do app. Yahoo só entra como
        # respaldo se o Fundamentus não tiver o dado.
        ind_extras_lote, _ = get_indicadores_fundamentus(row['CÓDIGO'])
        if ind_extras_lote:
            roe_fund = _ind_buscar(ind_extras_lote, 'roe')
            marg_liq_fund = _ind_buscar(ind_extras_lote, 'marg. l', 'margem l')
            min_52_fund = _ind_buscar(ind_extras_lote, 'min 52', 'mín 52', 'min. 52')
            max_52_fund = _ind_buscar(ind_extras_lote, 'max 52', 'máx 52', 'max. 52')
            if roe_fund is not None:
                roe_num_raw = roe_fund
                roe = f"{roe_fund:.2f}%".replace('.', ',')
            if marg_liq_fund is not None:
                margem_num_raw = marg_liq_fund
                margem = f"{marg_liq_fund:.2f}%".replace('.', ',')
            if min_52_fund is not None:
                low = f"R$ {min_52_fund:.2f}".replace('.', ',')
            if max_52_fund is not None:
                high = f"R$ {max_52_fund:.2f}".replace('.', ',')

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

        earnings_yield_lote = (1 / pl_num * 100) if pl_num > 0 else None

        ativos_com_score.append({
            'row': row, 'score': score,
            'score_fundamentos': score_fundamentos, 'pct_acima_teto': pct_acima_teto,
            'score_estrutural': score_estrutural,
            'earnings_yield': earnings_yield_lote,
            'dy_num': dy_num, 'dy_clean': dy_clean, 'pl_num': pl_num,
            'progresso': progresso, 'porcentagem': porcentagem,
            'dt': dt, 'val': val, 'roe': roe, 'margem': margem,
            'low': low, 'high': high,
            'roe_num_raw': roe_num_raw, 'margem_num_raw': margem_num_raw, 'pvp_num_raw': pvp_num_raw,
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
            'vl_mercado': row.get('vl_mercado', 0) or 0,
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

    # Pré-carregar Fundamentei em background para que a tabela abra rápido.
    # Como get_fluxo_caixa_fundamentei tem cache de 24h, a segunda chamada
    # (na tabela) retorna instantaneamente do cache.
    for a in ativos_com_score:
        try:
            get_fluxo_caixa_fundamentei(a['row']['CÓDIGO'])
        except Exception:
            pass

    return ativos_com_score


if df_f.empty:
    if card_filtrados is not None:
        card_filtrados.markdown("""<div class='top-card'>
            <div class='label'>🔍 Ativos Filtrados</div>
            <div class='value'>0</div>
        </div>""", unsafe_allow_html=True)
    st.warning("Nenhum ativo encontrado.")
else:
    ativos_com_score = _construir_ativos_com_score(df_f, _min_score_efetivo, filtro_status_val)

    if card_filtrados is not None:
        card_filtrados.markdown(f"""<div class='top-card'>
            <div class='label'>🔍 Ativos Filtrados</div>
            <div class='value'>{len(ativos_com_score)}</div>
        </div>""", unsafe_allow_html=True)

    if card_maior_score is not None:
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

    if card_menor_pl is not None:
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

        # Modo Tabela — grade completa, ordenável por coluna (clicando no
        # cabeçalho), igual o screener do Fundamentei que o Diego mostrou.
        # Mostra muitos ativos e muitos números ao mesmo tempo -- o que os
        # Cards não conseguem fazer bem.
        if st.session_state.modo_exibicao == 'Tabela':

            # Helper: lê Valor de Mercado do df_f, tolerante ao formato do Google Sheets
            def _get_vm(df_src, ticker):
                try:
                    col = next((c for c in df_src.columns if 'mercado' in c.lower()), None)
                    if col is None:
                        return None
                    mask = df_src['CÓDIGO'] == ticker
                    if not mask.any():
                        return None
                    raw = df_src.loc[mask, col].values[0]
                    s = str(raw).strip().replace('R$', '').replace(' ', '')
                    if s in ('', 'nan', 'None', '-', '0'):
                        return None
                    # Google Sheets pode exportar como número puro (486807436382.97)
                    # ou como brasileiro (486.807.436.382,97)
                    if ',' in s:
                        s = s.replace('.', '').replace(',', '.')
                    else:
                        pass  # já está no formato float padrão
                    v = float(s)
                    return round(v / 1e9, 2) if v > 0 else None
                except Exception:
                    return None
            st.markdown("#### 📋 Tabela Completa")
            st.caption(
                "Clique no cabeçalho de qualquer coluna pra ordenar. Use o seletor abaixo "
                "pra abrir o detalhe de um ativo."
            )

            # Vol. Implícita vem de uma busca única que já traz todos os
            # ativos de uma vez (cache compartilhado) -- não precisa de uma
            # chamada por ticker.
            _vol_dados_tabela, _ = get_volatilidade_oplab()
            _vol_dados_tabela = _vol_dados_tabela or {}

            linhas_tabela = []
            for a in ativos_com_score:
                r = a['row']
                tk = r['CÓDIGO']
                _fdm_tab, _ = get_fluxo_caixa_fundamentei(tk)
                # P/L já está em a['pl_num'] — sem chamar Fundamentus de novo
                _pl_at_tab = a.get('pl_num') or None
                if _pl_at_tab is not None and (_pl_at_tab <= 0 or _pl_at_tab > 300):
                    _pl_at_tab = None
                _vol_tab = _vol_dados_tabela.get(tk, {})
                linhas_tabela.append({
                    'Logo': a.get('logo_url', '') or None,
                    'Ticker': tk,
                    'Setor': r.get('SETOR', '-'),
                    'Cotação': limpar_valor(str(r.get('Cotação atual', 0))),
                    'Var. Dia (%)': a.get('variacao_dia', 0.0),
                    'Score': a.get('score', 0),
                    'P/L': a.get('pl_num', 0) or None,
                    'P/VP': a.get('pvp_str', '-'),
                    'DY (%)': a.get('dy_num', 0) or None,
                    'ROE (%)': a.get('roe_num_raw', 0) or None,
                    'CAGR Lucros (%)': limpar_valor(r.get('CAGR lucros (últ. 5 anos)', 0)) or None,
                    'Earnings Yield (%)': a.get('earnings_yield') or None,
                    'TIR Real (%)': tir_real_valor(tk, r, a, limpar_valor, pl_atual_val=_pl_at_tab),
                    'Valor de Mercado': _get_vm(df_f, tk),
                    '_confirmada': tk in TICKERS_TIR_CONFIRMADA,
                    'Dívida Líq/EBITDA': limpar_valor(r.get('Dívida líquida/EBITDA', 0)) or None,
                    'P/FCO': (_fdm_tab or {}).get('p_fco'),
                    'P/FCL': (_fdm_tab or {}).get('p_fcl'),
                    'Vol. Implícita (%)': _vol_tab.get('vol_implicita'),
                })
            df_tabela = pd.DataFrame(linhas_tabela)

            def _cor_variacao_tabela(v):
                if pd.isna(v):
                    return ''
                cor = "#22C55E" if v > 0 else ("#EF4444" if v < 0 else "#D4AF37")
                return f"color: {cor}; font-weight: 700;"

            confirmadas_mask = df_tabela['_confirmada'] & df_tabela['TIR Real (%)'].notna()
            styler_tabela = df_tabela.drop(columns=['_confirmada']).style.map(
                _cor_variacao_tabela, subset=['Var. Dia (%)'])
            if confirmadas_mask.any():
                styler_tabela = styler_tabela.map(
                    lambda v: "color: #22C55E; font-weight: 700;",
                    subset=pd.IndexSlice[confirmadas_mask[confirmadas_mask].index, ['TIR Real (%)']]
                )

            st.dataframe(
                styler_tabela,
                use_container_width=True,
                hide_index=True,
                height=min(740, 70 + 35 * len(df_tabela)),
                column_config={
                    'Logo': st.column_config.ImageColumn(width="small"),
                    'Cotação': st.column_config.NumberColumn(format="R$ %.2f"),
                    'Var. Dia (%)': st.column_config.NumberColumn(format="%.2f%%"),
                    'Score': st.column_config.NumberColumn(format="%.1f"),
                    'P/L': st.column_config.NumberColumn(format="%.1fx"),
                    'DY (%)': st.column_config.NumberColumn(format="%.1f%%"),
                    'ROE (%)': st.column_config.NumberColumn(format="%.1f%%"),
                    'CAGR Lucros (%)': st.column_config.NumberColumn(format="%.1f%%"),
                    'Earnings Yield (%)': st.column_config.NumberColumn(format="%.1f%%"),
                    'TIR Real (%)': st.column_config.NumberColumn(format="IPCA + %.1f%%"),
                    'Valor de Mercado': st.column_config.NumberColumn("Val. Mercado (R$ bi)", format="R$ %.1f bi"),
                    'Dívida Líq/EBITDA': st.column_config.NumberColumn(format="%.1fx"),
                    'P/FCO': st.column_config.NumberColumn(format="%.1fx"),
                    'P/FCL': st.column_config.NumberColumn(format="%.1fx"),
                    'Vol. Implícita (%)': st.column_config.NumberColumn(format="%.1f%%"),
                },
            )
            st.caption(
                "Score mostrado é o 'De Momento' (considera preço atual vs. teto). P/FCO e "
                "P/FCL vêm do Fundamentei — vazios podem indicar geração de caixa fraca/"
                "negativa no momento, ou que o dado não se aplica ao tipo de negócio "
                "(bancos, seguradoras e holdings não têm essas métricas calculadas)."
            )

            st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
            ticker_aberto = st.selectbox(
                "Abrir detalhe de um ativo:",
                options=[""] + sorted(df_tabela['Ticker'].tolist()),
                index=0,
            )
            if ticker_aberto:
                st.session_state.ativo_selecionado = ticker_aberto
                st.session_state.aba_ativa = "📊 Visão Geral"
                st.rerun()

            st.download_button(
                "⬇ Baixar tabela em CSV",
                data=df_tabela.to_csv(index=False).encode('utf-8-sig'),
                file_name="radar_fundamentalista.csv",
                mime="text/csv",
            )
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
