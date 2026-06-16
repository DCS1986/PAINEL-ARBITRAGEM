import pandas as pd
import streamlit as st
import yfinance as yf
import requests

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Radar Fundamentalista", layout="wide")

# ---- Controle de acesso ----
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# --- CONFIGURAÇÃO DO FUNDO ---
link_da_imagem = "https://raw.githubusercontent.com/DCS1986/PAINEL-ARBITRAGEM/main/1500x500.png"

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

/* Topo limpo mantendo botões visíveis */
[data-testid="stHeader"] {{
    background: rgba(0,0,0,0.3) !important;
}}
.block-container {{
    padding-top: 28px !important;
    padding-bottom: 0px !important;
}}
[data-testid="stSidebar"] {{
    background: rgba(10, 12, 18, 0.95) !important;
    border-right: 1px solid rgba(255,255,255,0.08) !important;
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
    color: #ccc;
    font-weight: 600;
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

# ---- Página de entrada ----
if not st.session_state.autenticado:

    # CSS: botão turquesa igual ao toggle Lista/Cards
    st.markdown("""
<style>
div[data-testid="stButton"] button[kind="primary"] {
    background-color: #00BCD4 !important;
    color: #ffffff !important;
    border: none !important;
    font-weight: 700 !important;
    font-size: 1em !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
    background-color: #00ACC1 !important;
}
</style>
""", unsafe_allow_html=True)

    st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)

    # Texto centralizado em coluna larga
    tl, tc, tr = st.columns([1, 2, 1])
    with tc:
        st.markdown(
            "<h1 style='text-align:center; font-size:2.8em; font-weight:900; "
            "letter-spacing:3px; text-transform:uppercase; color:#ffffff; "
            "white-space:nowrap; margin:0 0 6px 0;'>Radar Fundamentalista</h1>"
            "<p style='text-align:center; font-size:0.85em; color:rgba(255,255,255,0.4); "
            "letter-spacing:3px; text-transform:uppercase; margin:0 0 32px 0;'>Diego Castro</p>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='text-align:center; font-size:0.9em; color:#ccc; "
            "line-height:1.8; margin:0 0 20px 0;'>"
            "Ferramenta de análise quantitativa e qualitativa de ações brasileiras "
            "desenvolvida para apoiar o processo de tomada de decisão em investimentos "
            "de longo prazo.</p>"
            "<p style='text-align:center; font-size:0.85em; color:#aaa; "
            "line-height:1.8; margin:0 0 20px 0;'>"
            "O score proprietário combina múltiplos critérios com pesos diferenciados "
            "por setor: qualidade operacional, crescimento e consistência dos resultados, "
            "solidez financeira, valuation relativo, retorno ao acionista e "
            "governança corporativa — avaliada de forma qualitativa e aplicada "
            "como penalizador.</p>"
            "<p style='text-align:center; font-size:0.78em; color:#888; "
            "line-height:1.7; margin:0 0 32px 0;'>"
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
        return "#39FF14"
    elif porcentagem >= 25:
        return "#FFD700"
    else:
        return "#FF4444"

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
}

OUTLOOK_2026 = {
    "BBSE3":  {"icone": "⚠️", "cor": "#FFD700", "texto": "Atenção: exposição ao agro (granizo, seca, El Niño) pode pressionar sinistros em 2026. Monitorar sinistralidade agrícola no 1T26 antes de ampliar posição."},
    "ITUB4":  {"icone": "✅", "cor": "#39FF14", "texto": "Ciclo de crédito favorável, inadimplência sob controle, ROE elevado. Um dos melhores momentos operacionais da história. Perspectiva positiva para 2026."},
    "BBAS3":  {"icone": "🔴", "cor": "#FF4444", "texto": "Risco elevado: carteira agro sob pressão com alta inadimplência. Guidance revisado sem aviso. Aguardar 2T26 para avaliar se deterioração foi pontual ou estrutural antes de aportar."},
    "BBDC3":  {"icone": "🟡", "cor": "#FFD700", "texto": "Recuperação em curso após anos difíceis. Lucro voltando a crescer mas abaixo dos pares. Posição especulativa de melhora — cautela com alocação."},
    "ABCB4":  {"icone": "✅", "cor": "#39FF14", "texto": "Carteira corporativa de alta qualidade, inadimplência estruturalmente baixa. Perspectiva positiva, menos sensível ao ciclo de varejo."},
    "BRSR6":  {"icone": "⚠️", "cor": "#FFD700", "texto": "Exposição significativa ao agro gaúcho e reflexos das enchentes de 2024. Monitorar evolução da carteira de crédito rural em 2026."},
    "SANB3":  {"icone": "✅", "cor": "#39FF14", "texto": "Ciclo de melhora operacional. ROE subindo, foco em eficiência. Perspectiva moderadamente positiva para 2026."},
    "BMGB4":  {"icone": "⚠️", "cor": "#FFD700", "texto": "Nicho de consignado INSS sob pressão regulatória. Teto de juros pode impactar margens. Monitorar evolução da regulação em 2026."},
    "BPAC11": {"icone": "✅", "cor": "#39FF14", "texto": "Forte expansão de receitas recorrentes. Menos dependente do ciclo de crédito. Uma das melhores perspectivas do setor financeiro para 2026."},
    "IRBR3":  {"icone": "⚠️", "cor": "#FFD700", "texto": "Ressegurador em recuperação pós-fraude. Resultados melhorando, mas histórico exige cautela. El Niño e eventos climáticos extremos são risco relevante."},
    "PSSA3":  {"icone": "✅", "cor": "#39FF14", "texto": "Momento operacional sólido. Seguros auto e residencial com bons resultados. Perspectiva positiva, mas monitorar sinistralidade climática."},
    "CXSE3":  {"icone": "✅", "cor": "#39FF14", "texto": "Crescimento consistente de prêmios via rede da Caixa. Vantagem competitiva de distribuição enorme. Perspectiva positiva para 2026."},
    "ITSA4":  {"icone": "✅", "cor": "#39FF14", "texto": "Holding do Itaú — resultado acompanha o banco. Desconto histórico pode se fechar. Perspectiva positiva com menor volatilidade que o banco diretamente."},
    "PETR4":  {"icone": "⚠️", "cor": "#FFD700", "texto": "Petróleo em patamar moderado (~$70-75). Risco fiscal e de interferência na política de dividendos. Monitorar anúncio de investimentos e possível revisão da remuneração em 2026."},
    "VALE3":  {"icone": "🔴", "cor": "#FF4444", "texto": "Minério de ferro pressionado pela desaceleração chinesa. Acordo de Mariana ainda em negociação (provisão bilionária). 2026 desafiador — aguardar estabilização do cenário China."},
    "BRAP4":  {"icone": "⚠️", "cor": "#FFD700", "texto": "Herda o cenário desafiador da Vale com desconto adicional de holding. Monitorar acordo de Mariana e preço do minério."},
    "CMIN3":  {"icone": "⚠️", "cor": "#FFD700", "texto": "Sensível ao preço do minério e desaceleração chinesa. Perspectiva cautelosa para 2026."},
    "GGBR3":  {"icone": "⚠️", "cor": "#FFD700", "texto": "Dependente do ciclo de construção civil. Perspectiva neutra — programa de infraestrutura pode ser catalisador positivo em 2026."},
    "KLBN4":  {"icone": "✅", "cor": "#39FF14", "texto": "Celulose e papel com demanda resiliente. Expansão Puma II maturando. Perspectiva positiva para 2026, menos cíclica que pares do setor."},
    "UNIP6":  {"icone": "⚠️", "cor": "#FFD700", "texto": "Margens pressionadas pelo ciclo químico global e dumping chinês de petroquímicos. Perspectiva neutra a negativa para 2026."},
    "LEVE3":  {"icone": "✅", "cor": "#39FF14", "texto": "Reposição automotiva resiliente. Transição para elétricos é risco de longo prazo, irrelevante para 2026. Perspectiva positiva."},
    "SHUL4":  {"icone": "✅", "cor": "#39FF14", "texto": "Compressores industriais com demanda estável. Nicho protegido e bem gerido. Perspectiva positiva para 2026."},
    "VULC3":  {"icone": "✅", "cor": "#39FF14", "texto": "Marca consolidada no esportivo. Expansão de margens em curso. Perspectiva positiva, dependente do consumo doméstico."},
    "TIMS3":  {"icone": "✅", "cor": "#39FF14", "texto": "Crescimento consistente de receita e margens. Mercado consolidado favorece rentabilidade. Excelente perspectiva para 2026."},
    "ALOS3":  {"icone": "✅", "cor": "#39FF14", "texto": "Shoppings em ciclo favorável. Consumo aquecido e vacância baixa. Integração da fusão gerando sinergias. Perspectiva positiva para 2026."},
    "KEPL3":  {"icone": "✅", "cor": "#39FF14", "texto": "Armazenagem agrícola com demanda estrutural crescente. Perspectiva positiva, pouco sensível ao preço das commodities."},
    "SLCE3":  {"icone": "⚠️", "cor": "#FFD700", "texto": "Exposta à cotação de soja/algodão e câmbio. El Niño traz incerteza climática para 2ª safra. Cautela — aguardar definição do clima antes de ampliar posição."},
    "RANI3":  {"icone": "✅", "cor": "#39FF14", "texto": "Embalagens de papel com demanda resiliente e crescente. Expansão de capacidade em andamento. Perspectiva positiva para 2026."},
    "CMIG4":  {"icone": "⚠️", "cor": "#FFD700", "texto": "Distribuição e geração reguladas, mas gestão pública limita eficiência. Perspectiva neutra. Atenção ao processo de renovação de concessões."},
    "CPLE3":  {"icone": "✅", "cor": "#39FF14", "texto": "Privatização trazendo eficiência. Perspectiva positiva com potencial de redução de custos e melhora de margens em 2026."},
    "EGIE3":  {"icone": "✅", "cor": "#39FF14", "texto": "Geração renovável com contratos longos. Menor exposição a risco hidrológico por mix diversificado. Perspectiva excelente para 2026."},
    "TAEE11": {"icone": "✅", "cor": "#39FF14", "texto": "Transmissão com RAP garantido — completamente independente de hidrologia. Perspectiva muito positiva e previsível para 2026."},
    "ISAE4":  {"icone": "✅", "cor": "#39FF14", "texto": "Transmissão regulada, receita previsível. Perspectiva positiva similar à Taesa, com ciclo de revisão tarifária favorável."},
    "CPFE3":  {"icone": "✅", "cor": "#39FF14", "texto": "Mix equilibrado de distribuição e geração. Perspectiva positiva beneficiada por revisão tarifária e expansão renovável em 2026."},
    "SBSP3":  {"icone": "✅", "cor": "#39FF14", "texto": "Pós-privatização acelerando investimentos. Perspectiva positiva de médio prazo, mas 2026 ainda é ano de transição e reorganização."},
    "SAPR4":  {"icone": "✅", "cor": "#39FF14", "texto": "Saneamento com demanda inelástica. Perspectiva estável. Revisão tarifária pendente pode ser catalisador positivo em 2026."},
    "CSMG3":  {"icone": "⚠️", "cor": "#FFD700", "texto": "Ainda pública. Privatização em discussão pode ser catalisador, mas risco político de MG é relevante. Perspectiva neutra."},
    "AXIA3":  {"icone": "✅", "cor": "#39FF14", "texto": "Fibra óptica em expansão acelerada. Demanda por conectividade crescente e estrutural. Perspectiva positiva para 2026."},
    "B3SA3":  {"icone": "⚠️", "cor": "#FFD700", "texto": "Dependente do volume de negociação. Juros altos reduzem fluxo para renda variável. Melhora depende de queda de juros e volta do PF — perspectiva neutra para 2026."},
    "BRBI11": {"icone": "✅", "cor": "#39FF14", "texto": "Banco de investimento em crescimento. Perspectiva positiva dependente do ambiente de M&A e mercado de capitais em 2026."},
}

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
            return ('acima_target', '#FF4444', '🔴',
                    f"Acima do target (+{pct_acima:.1f}%) — considerar redução")

        elif cot > preco_teto:
            # Entre teto e target — zona de atenção
            pct = ((cot - preco_teto) / preco_teto) * 100
            return ('acima_teto', '#FF8C00', '🟠',
                    f"Acima do preço teto (+{pct:.1f}%) — aguardar recuo")

        else:
            # Abaixo do teto — zona de compra
            pct_teto   = ((preco_teto - cot) / preco_teto) * 100
            pct_target = ((target - cot) / target) * 100
            if pct_teto >= 15:
                return ('oportunidade', '#39FF14', '🟢',
                        f"Forte oportunidade — {pct_teto:.1f}% abaixo do teto / {pct_target:.1f}% abaixo do target")
            else:
                return ('compra', '#00BCD4', '🔵',
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
        df['preco_teto']  = df['PREÇO TETO'].apply(limpar_valor) if 'PREÇO TETO' in df.columns else 0
        df['target']      = df['TARGET'].apply(limpar_valor) if 'TARGET' in df.columns else 0

        return df
    except:
        return pd.DataFrame()

df = carregar_dados()

# --- SIDEBAR ---
st.sidebar.markdown("""
<div style="padding:4px 0 12px 0; border-bottom:1px solid rgba(255,255,255,0.08);
            margin-bottom:16px;">
    <span style="font-size:1.1em; font-weight:800; color:#fff; letter-spacing:1px;">
        🎯 Filtros
    </span>
</div>
""", unsafe_allow_html=True)

# Busca rápida sempre visível
busca_ticker = st.sidebar.text_input("🔍 Buscar ticker:", placeholder="ex: BBSE3").strip().upper()

# Filtro por setor
setores_disponiveis = sorted(df['SETOR'].unique().tolist()) if not df.empty else []
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

    # ---- Governança + Outlook lado a lado ----
    gov = GOVERNANCA.get(ticker, {})
    out = OUTLOOK_2026.get(ticker, {})
    nota_gov = gov.get('nota', None)
    obs_gov  = gov.get('obs', '')

    st.markdown("<div style='margin-top:32px;'></div>", unsafe_allow_html=True)

    gcol1, gcol2 = st.columns(2)

    card_style = (
        "display:flex; flex-direction:column; padding:20px 22px; border-radius:12px; "
        "background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.12); "
        "min-height:120px; box-sizing:border-box; "
    )

    with gcol1:
        if nota_gov is not None:
            if nota_gov >= 8:
                gov_cor, gov_label = "#39FF14", "Alta"
            elif nota_gov >= 6:
                gov_cor, gov_label = "#FFD700", "Média"
            else:
                gov_cor, gov_label = "#FF4444", "Baixa"
            st.markdown(
                "<div style='{base}'>"
                "<div style='font-size:0.82em;color:#888;font-weight:600;letter-spacing:0.5px;"
                "text-transform:uppercase;margin-bottom:12px;'>🏛️ Governança Corporativa</div>"
                "<div style='display:flex;align-items:center;gap:14px;margin-bottom:12px;'>"
                "<span style='font-size:2.4em;font-weight:900;color:{cor};line-height:1;'>{nota}</span>"
                "<span style='font-size:0.95em;color:{cor};font-weight:700;'>{label}</span>"
                "</div>"
                "<div style='font-size:0.83em;color:#bbb;line-height:1.65;'>{obs}</div>"
                "</div>".format(base=card_style, cor=gov_cor, nota=nota_gov,
                                label=gov_label, obs=obs_gov),
                unsafe_allow_html=True
            )

    with gcol2:
        if out:
            if out['cor'] == "#39FF14":
                out_label_cor = "#39FF14"
            elif out['cor'] == "#FFD700":
                out_label_cor = "#FFD700"
            else:
                out_label_cor = "#FF4444"
            st.markdown(
                "<div style='{base}'>"
                "<div style='font-size:0.82em;font-weight:600;color:#888;letter-spacing:0.5px;"
                "text-transform:uppercase;margin-bottom:12px;'>{icone} Outlook 2026</div>"
                "<div style='font-size:0.83em;color:#ccc;line-height:1.65;'>{texto}</div>"
                "</div>".format(base=card_style, icone=out['icone'], texto=out['texto']),
                unsafe_allow_html=True
            )

    # ---- Teto / Target / Status ----
    gov2  = GOVERNANCA.get(ticker, {})
    pt_v  = ativo_data.get('preco_teto_val', 0) if isinstance(ativo_data, dict) else 0
    tg_v  = ativo_data.get('target_val', 0)      if isinstance(ativo_data, dict) else 0
    s_st  = ativo_data.get('st_status', 'neutro') if isinstance(ativo_data, dict) else 'neutro'
    s_cor = ativo_data.get('st_cor', '#888')      if isinstance(ativo_data, dict) else '#888'
    s_ico = ativo_data.get('st_icone', '⚪')      if isinstance(ativo_data, dict) else '⚪'
    s_desc= ativo_data.get('st_desc', '')         if isinstance(ativo_data, dict) else ''
    cot_v = limpar_valor(str(ativo_data.get('row', {}).get('Cotação atual', 0) if isinstance(ativo_data, dict) else 0).replace('R$',''))

    if pt_v > 0 and tg_v > 0:
        pct_teto   = ((pt_v - cot_v) / pt_v * 100) if cot_v < pt_v else -((cot_v - pt_v) / pt_v * 100)
        pct_target = ((tg_v - cot_v) / tg_v * 100) if cot_v < tg_v else -((cot_v - tg_v) / tg_v * 100)

        st.markdown(
            f"<div style='padding:16px 20px;border-radius:12px;margin-bottom:16px;"
            f"background:rgba(255,255,255,0.04);border:2px solid {s_cor};'>"
            f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:12px;'>"
            f"<span style='font-size:1.6em;'>{s_ico}</span>"
            f"<span style='font-size:1.0em;font-weight:700;color:{s_cor};'>{s_desc}</span>"
            f"</div>"
            f"<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;text-align:center;'>"
            f"<div><div style='font-size:0.75em;color:#888;margin-bottom:4px;'>COTAÇÃO ATUAL</div>"
            f"<div style='font-size:1.3em;font-weight:800;color:#fff;'>R$ {cot_v:.2f}</div></div>"
            f"<div><div style='font-size:0.75em;color:#888;margin-bottom:4px;'>PREÇO TETO</div>"
            f"<div style='font-size:1.3em;font-weight:800;color:#FFD700;'>R$ {pt_v:.2f}</div>"
            f"<div style='font-size:0.78em;color:#aaa;'>{'▼' if pct_teto > 0 else '▲'} {abs(pct_teto):.1f}%</div></div>"
            f"<div><div style='font-size:0.75em;color:#888;margin-bottom:4px;'>TARGET</div>"
            f"<div style='font-size:1.3em;font-weight:800;color:#39FF14;'>R$ {tg_v:.2f}</div>"
            f"<div style='font-size:0.78em;color:#aaa;'>{'▼' if pct_target > 0 else '▲'} {abs(pct_target):.1f}%</div></div>"
            f"</div></div>",
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-top:32px;'></div>", unsafe_allow_html=True)
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
               text-transform:uppercase; color:#fff; line-height:1.1;">
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

st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

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
                               pvp_num=pvp_num_raw, setor=row.get('SETOR', ''),
                               ticker=row.get('CÓDIGO', ''), historico_lucro=historico_lucro)

        preco_teto_val = row.get('preco_teto', 0) if 'preco_teto' in row.index else limpar_valor(str(row.get('PREÇO TETO', 0)))
        target_val     = row.get('target', 0) if 'target' in row.index else limpar_valor(str(row.get('TARGET', 0)))
        st_status, st_cor, st_icone, st_desc = status_aporte(row.get('Cotação atual', 0), preco_teto_val, target_val)

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
            'st_status': st_status,
            'st_cor': st_cor,
            'st_icone': st_icone,
            'st_desc': st_desc,
            'preco_teto_val': preco_teto_val,
            'target_val': target_val,
        })

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
                              f"<div style='font-size:0.92em;font-weight:800;color:#fff;'>{dy_c}%</div></div>"
                            + f"<div style='text-align:center;'>"
                              f"<div style='font-size:0.68em;color:#bbb;font-weight:600;'>P/L</div>"
                              f"<div style='font-size:0.92em;font-weight:800;color:#fff;'>{pl_c}x</div></div>"
                            + f"<div style='text-align:center;'>"
                              f"<div style='font-size:0.68em;color:#bbb;font-weight:600;'>Score</div>"
                              f"<div style='font-size:0.92em;font-weight:800;color:#FFD700;'>⭐{score_c}</div></div>"
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
                            st.rerun()
            st.stop()

        # Modo Lista — duas colunas para ver mais ativos na tela
        metade     = len(ativos_com_score) // 2 + len(ativos_com_score) % 2
        lista_col1 = ativos_com_score[:metade]
        lista_col2 = ativos_com_score[metade:]
        lcol1, lcol2 = st.columns(2)

        def render_ativo(ativo):
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
            st_status       = ativo['st_status']
            st_cor          = ativo['st_cor']
            st_icone        = ativo['st_icone']
            st_desc         = ativo['st_desc']
            preco_teto_val  = ativo['preco_teto_val']
            target_val      = ativo['target_val']

            dy_icone = "🔷" if dy_num > 8 else ""
            cot      = formatar_cotacao(row.get('Cotação atual', 0))
            pl       = f"{row.get('P/L PROJETADO', '0')}x"
            ic_setor = icone_setor(row['SETOR'])
            if variacao_dia > 0:
                var_str = f"🟢 +{variacao_dia:.2f}%"
            elif variacao_dia < 0:
                var_str = f"🔴 {variacao_dia:.2f}%"
            else:
                var_str = f"🟡 {variacao_dia:.2f}%"
            iv_label = f"IV: {iv_str}" if iv_str != "-" else ""
            titulo = (
                f"{st_icone} {ic_setor} :orange[**{row['CÓDIGO']}**] | {cot} {var_str} | P/L: {pl} | "
                f"DY: {dy_icone} {dy_clean}% | {iv_label} | ⭐ Score: {score}/10 | Setor: {row['SETOR']}"
            )
            st.markdown("<div class='ativo-sep'></div>", unsafe_allow_html=True)
            with st.expander(titulo):
                if logo_url:
                    st.markdown(
                        f"<div style='display:flex;align-items:center;gap:12px;"
                        f"margin-bottom:14px;padding-bottom:10px;"
                        f"border-bottom:1px solid rgba(255,255,255,0.07);'>"
                        f"<img src='{logo_url}' style='height:36px;width:auto;"
                        f"border-radius:6px;background:#fff;padding:3px;'/>"
                        f"<span style='font-size:1.1em;font-weight:700;color:#FFD700;"
                        f"letter-spacing:1px;'>{row['CÓDIGO']}</span>"
                        f"<span style='font-size:0.85em;color:#888;'>{row.get('SETOR','-')}</span>"
                        f"</div>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown("#### 📊 Valuation")
                    st.markdown(f"**P/L Médio (10 anos):** {row.get('P/L médio (últ. 10 anos)', '-')}x")
                    st.markdown(f"**P/VP:** {pvp_str}")
                    st.markdown(f"**Valor de Mercado:** {row.get('VALOR DE MERCADO', '-')}")
                    st.markdown(f"**RESULTADO PROJETADO:** {row.get('LL PROJETADO', '-')}")
                    st.markdown(
                        f"**⭐ RESULTADO ENTREGUE (1/4):** "
                        f"<span style='color:#39FF14;font-weight:bold;'>{row.get('RESULTADO 2026 (1/4)', '-')}</span>",
                        unsafe_allow_html=True)
                    cor = cor_progresso(porcentagem)
                    st.markdown(
                        f"<div style='background:#222;border-radius:6px;height:12px;width:100%;margin:6px 0;'>"
                        f"<div style='background:{cor};width:{porcentagem}%;height:12px;border-radius:6px;'></div></div>",
                        unsafe_allow_html=True)
                    st.markdown(f"<span style='color:{cor};font-weight:bold;'>Status: {porcentagem}% do resultado projetado</span>", unsafe_allow_html=True)
                    if historico_lucro:
                        st.markdown("<span style='font-size:0.85em;color:#aaa;font-weight:bold;'>📈 Lucro Líquido (5 anos)</span>", unsafe_allow_html=True)
                        st.markdown(mini_grafico_linha(historico_lucro, "#39FF14"), unsafe_allow_html=True)
                with c2:
                    st.markdown("#### 💰 Dividendos")
                    style_dy = "color:#39FF14;font-weight:bold;" if dy_num > 8 else ""
                    st.markdown(f"**Dividend Yield:** <span style='{style_dy}'>{dy_clean}%</span>", unsafe_allow_html=True)
                    st.markdown(f"**Payout:** {row.get('PAYOUT', '-')}")
                    st.markdown(f"**LPA Est.:** {row.get('LPA ESTIMADO', '-')}")
                    st.markdown(f"**Div. Projetado:** {row.get('Dividendo por ação bruto projetado', '-')}")
                    st.markdown(f"**Data Ex (último):** {dt}")
                    st.markdown(f"**Valor Último Div.:** {val}")
                    if proximo_provento_data != "-":
                        st.markdown(
                            f"<div style='margin-top:10px;padding:8px 12px;border-radius:8px;"
                            f"background:#1a3a1a;border:1px solid #39FF14;'>"
                            f"<span style='color:#39FF14;font-weight:bold;'>📅 Próximo Provento em Aberto</span><br>"
                            f"<span style='color:#fff;'>Data COM: <b>{proximo_provento_data}</b>"
                            f" | Valor Est.: <b>{proximo_provento_valor}</b></span></div>",
                            unsafe_allow_html=True)
                    else:
                        st.markdown(
                            "<div style='margin-top:10px;padding:6px 12px;border-radius:8px;"
                            "background:#2a2a2a;border:1px solid #555;color:#888;font-size:0.85em;'>"
                            "📅 Nenhum provento futuro identificado</div>",
                            unsafe_allow_html=True)
                    st.markdown("**Histórico DY (5 anos):**")
                    st.markdown(mini_grafico_dy(historico_dy), unsafe_allow_html=True)
                with c3:
                    st.markdown("#### ⚙️ Operacional")
                    pl_proj = row.get('P/L PROJETADO', '-')
                    st.markdown(f"**P/L Projetado:** <span style='color:#FFD700;font-weight:bold;font-size:1.1em;'>{pl_proj}x</span>", unsafe_allow_html=True)
                    st.markdown(f"**Dívida Líq/EBITDA:** {row.get('Dívida líquida/EBITDA', '-')}")
                    st.markdown(f"**CAGR Lucros:** {row.get('CAGR lucros (últ. 5 anos)', '-')}")
                    st.markdown(f"**ROE:** {roe}")
                    st.markdown(f"**Margem Líq.:** {margem}")
                    st.markdown(f"**Beta (vs IBOV):** {beta}")
                    if historico_pl:
                        st.markdown("<span style='font-size:0.85em;color:#aaa;font-weight:bold;'>📈 P/L Histórico (5 anos)</span>", unsafe_allow_html=True)
                        st.markdown(mini_grafico_linha(historico_pl, "#1E90FF", label_suffix="x"), unsafe_allow_html=True)

        with lcol1:
            for ativo in lista_col1:
                render_ativo(ativo)
        with lcol2:
            for ativo in lista_col2:
                render_ativo(ativo)
