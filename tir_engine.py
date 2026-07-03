"""
Motor de calculo de TIR por arquetipo de negocio - RADAR Fundamentalista.

Ideia central: nao existe formula unica de TIR para acao. Cada empresa cai em um
arquetipo que define o metodo correto. O motor identifica o arquetipo, aplica o
metodo e devolve a TIR ja com a memoria de calculo aberta, passo a passo, para
exibicao no card (botao "Ver calculo") e validacao manual.

Convencao: tudo em termos NOMINAIS (comparavel ao CDI).
Convencao de entrada: passe dy, roe e pvp em DECIMAL (0.086, nao 8.6).

Premissas ficam centralizadas em PREMISSAS / HOLDINGS / NORMALIZACAO_CICLICA.
Ajuste ali e a TIR de todos os ativos do arquetipo se recalibra.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ==========================================================================
# PREMISSAS CENTRAIS (edite aqui - valem para todos os ativos do arquetipo)
# ==========================================================================
PREMISSAS = {
    "inflacao_lp":   0.045,   # inflacao de longo prazo
    "premio_risco":  0.045,   # equity risk premium
    "g_teto":        0.15,    # teto do crescimento (so corta absurdo; projecao conservadora fala)
    "g_piso":        0.00,    # piso (projecao/CAGR negativo nao vira encolhimento perpetuo)
}

# Inflacao base pra converter a TIR NOMINAL em TIR REAL (formato "IPCA + X%",
# igual o mercado apresenta uma NTN-B). Conversao composta:
#   TIR real = (1 + TIR nominal) / (1 + IPCA_BASE) - 1
IPCA_BASE = 0.06

# Carimbo de versao - aparece na caixa de calculo. Se o app nao mostrar esta
# versao, o engine novo NAO esta no ar (arquivo duplicado ou cache do deploy).
VERSION = "v9 (formula por setor: banco/seguradora/qualidade/ciclica/utility/holding)"

# Holdings: desconto de NAV e peso das contingencias sobre o NAV.
# O desconto e a opcionalidade (kicker se fechar); a contingencia e o risco.
# Sao mostrados na memoria, nao embutidos num numero unico (timing incerto).
HOLDINGS = {
    "ITSA4":  {"desconto": 0.20, "contingencia_nav": 0.00, "g_subjacente": 0.06},
    "BRAP4":  {"desconto": 0.37, "contingencia_nav": 0.28, "g_subjacente": 0.045},
    "BRBI11": {"desconto": 0.15, "contingencia_nav": 0.00, "g_subjacente": 0.06},
}

# Ciclicas: fator de normalizacao do lucro (mid-cycle / trailing).
# > 1 quando o lucro atual esta deprimido (vale do ciclo); < 1 quando no pico.
# ESTE e o input mais sensivel do modelo - calibre por nome a cada resultado.
NORMALIZACAO_CICLICA = {
    "VALE3": 1.0, "PETR4": 1.0, "PRIO3": 1.0, "CMIN3": 1.0,
    "KLBN4": 1.0, "RANI3": 1.0, "SLCE3": 1.0, "KEPL3": 1.0,
    "FESA4": 2.0,   # 1T26 no prejuizo; trailing deprimido
}

# Ressalvas por ativo (aparecem no alerta do card).
ALERTAS = {
    "FESA4": "Clausula de financiamento trava payout em 25%: TIR de caixa << TIR economica.",
    "AXIA3": "Reestruturacao em curso: base de lucro ainda nao normalizou.",
    "ALOS3": "Operador de shopping (renda recorrente de aluguel) - avaliar como utility/FFO.",
}


# ==========================================================================
# MAPA DE ARQUETIPOS
# ==========================================================================
ARQUETIPO_POR_TICKER = {
    # 1) Banco -> DY + ROE x retencao (cresce retendo capital)
    **{t: "banco" for t in [
        "ITUB4", "BBDC3", "BBAS3", "BPAC11", "ABCB4", "BRSR6", "SANB3", "BMGB4",
    ]},
    # 2) Seguradora -> DY + crescimento projetado (capital-light, payout ~100%)
    **{t: "seguradora" for t in ["BBSE3", "PSSA3", "CXSE3", "IRBR3"]},
    # 3) Qualidade / crescimento -> DY + crescimento projetado (motor: reinvestir)
    **{t: "qualidade" for t in [
        "WEGE3", "B3SA3", "GRND3", "LEVE3", "POMO4", "VULC3", "SHUL4",
        "CGRA4", "LREN3",
    ]},
    # 4) Utility / contratada -> DY + inflacao (receita regulada indexada)
    **{t: "utility" for t in [
        "SBSP3", "CSMG3", "SAPR4", "TAEE11", "EGIE3", "CPFE3", "CPLE3",
        "CMIG4", "EQTL3", "TIMS3", "ISAE4", "AXIA3",
    ]},
    # 5) Ciclica de commodity -> DY + inflacao (lucro/FCL nao extrapolado)
    **{t: "ciclica" for t in [
        "VALE3", "PETR4", "PRIO3", "CMIN3", "KLBN4", "RANI3", "SLCE3",
        "KEPL3", "FESA4", "SUZB3",
    ]},
    # 6) Holding -> look-through + desconto de NAV
    **{t: "holding" for t in ["ITSA4", "BRAP4", "BRBI11"]},
    # 7) Incorporadora / imobiliario -> DY + crescimento projetado
    **{t: "incorporadora" for t in [
        "CYRE3", "CURY3", "DIRR3", "JHSF3", "MDNE3", "ALOS3",
    ]},
}

NOME_METODO = {
    "banco":         "DY + ROE x retencao (cresce retendo capital)",
    "seguradora":    "DY + crescimento projetado (capital-light, payout alto)",
    "qualidade":     "DY + crescimento projetado (motor: reinvestimento)",
    "utility":       "DY + inflacao (receita regulada; real ~= DY)",
    "ciclica":       "DY + inflacao (lucro/FCL ciclico nao extrapolado)",
    "holding":       "DY look-through + inflacao (desconto de NAV a parte)",
    "incorporadora": "DY + crescimento projetado",
}


# ==========================================================================
# ESTRUTURAS DE RETORNO
# ==========================================================================
@dataclass
class Passo:
    rotulo: str
    valor: str


@dataclass
class ResultadoTIR:
    tir: Optional[float]          # nominal, em decimal (ex.: 0.15 = 15%)
    arquetipo: str
    metodo: str
    memoria: list = field(default_factory=list)
    alerta: str = ""

    @property
    def tir_pct(self) -> str:
        return "n/d" if self.tir is None else f"{self.tir * 100:.1f}%"


# ==========================================================================
# HELPERS
# ==========================================================================
def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(x, hi))


def _dec(x: Optional[float]) -> Optional[float]:
    """Normaliza para decimal: se vier > 1.5 assume que veio em % (8.6 -> 0.086)."""
    if x is None:
        return None
    return x / 100.0 if x > 1.5 else x


def _p(v: float) -> str:
    return f"{v * 100:.1f}%"


# ==========================================================================
# METODOS POR ARQUETIPO
# ==========================================================================
def _g_projetado(dados: dict):
    """Crescimento a partir da SUA projecao (conservadora): implicito no P/L
    atual vs P/L projetado -> g = P/L atual / P/L projetado - 1. Se voce projeta
    o lucro caindo (ex.: BBSE), o g sai baixo/zero sozinho. Fallback: CAGR."""
    pl_atual = dados.get("pl_atual")
    pl_proj = dados.get("pl")            # P/L PROJETADO da planilha
    if pl_atual and pl_atual > 0 and pl_proj and pl_proj > 0:
        g = pl_atual / pl_proj - 1
        return _clamp(g, PREMISSAS["g_piso"], PREMISSAS["g_teto"]), "projecao (P/L atual vs projetado)"
    cagr = _dec(dados.get("cagr"))
    if cagr is not None:
        return _clamp(cagr, PREMISSAS["g_piso"], PREMISSAS["g_teto"]), "CAGR de lucros (fallback)"
    return IPCA_BASE, "inflacao (sem projecao)"


def _tir_banco(dados: dict) -> ResultadoTIR:
    dy = _dec(dados.get("dy")) or 0.0
    roe = _dec(dados.get("roe"))
    payout_real = dados.get("payout")
    r = ResultadoTIR(None, "banco", NOME_METODO["banco"])
    if roe is None:
        r.alerta = "Sem ROE - metodo de banco depende do ROE."
        return r
    payout = _clamp(payout_real, 0, 1) if (payout_real and payout_real > 0) else 0.40
    fonte = "planilha" if (payout_real and payout_real > 0) else "default 40%"
    retencao = max(0.0, 1 - payout)
    g = _clamp(roe * retencao, PREMISSAS["g_piso"], PREMISSAS["g_teto"])
    tir = dy + g
    r.tir = tir
    r.memoria = [
        Passo("Dividend yield (DY)", _p(dy)),
        Passo("ROE", _p(roe)),
        Passo(f"Payout ({fonte})", _p(payout)),
        Passo("Retencao (1 - payout)", _p(retencao)),
        Passo(f"g = ROE x retencao (teto {_p(PREMISSAS['g_teto'])})", _p(g)),
        Passo("TIR nominal = DY + g", _p(tir)),
    ]
    return r


def _tir_seguradora(dados: dict, ticker: str) -> ResultadoTIR:
    dy = _dec(dados.get("dy")) or 0.0
    r = ResultadoTIR(None, "seguradora", NOME_METODO["seguradora"])
    g, fonte_g = _g_projetado(dados)
    tir = dy + g
    r.tir = tir
    r.memoria = [
        Passo("Dividend yield (DY)", _p(dy)),
        Passo(f"g projetado ({fonte_g}, teto {_p(PREMISSAS['g_teto'])})", _p(g)),
        Passo("TIR nominal = DY + g", _p(tir)),
        Passo("Obs.", "Capital-light: cresce sem reter. Sua projecao ja embute o cenario."),
    ]
    r.alerta = ALERTAS.get(ticker, "")
    return r


def _tir_qualidade(dados: dict) -> ResultadoTIR:
    dy = _dec(dados.get("dy")) or 0.0
    r = ResultadoTIR(None, "qualidade", NOME_METODO["qualidade"])
    g, fonte_g = _g_projetado(dados)
    tir = dy + g
    r.tir = tir
    r.memoria = [
        Passo("Dividend yield (DY)", _p(dy)),
        Passo(f"g projetado ({fonte_g}, teto {_p(PREMISSAS['g_teto'])})", _p(g)),
        Passo("TIR nominal = DY + g", _p(tir)),
        Passo("Obs.", "Motor e o crescimento (reinvestimento), nao o dividendo."),
    ]
    return r


def _tir_incorporadora(dados: dict, ticker: str) -> ResultadoTIR:
    dy = _dec(dados.get("dy")) or 0.0
    r = ResultadoTIR(None, "incorporadora", NOME_METODO["incorporadora"])
    g, fonte_g = _g_projetado(dados)
    tir = dy + g
    r.tir = tir
    r.memoria = [
        Passo("Dividend yield (DY)", _p(dy)),
        Passo(f"g projetado ({fonte_g}, teto {_p(PREMISSAS['g_teto'])})", _p(g)),
        Passo("TIR nominal = DY + g", _p(tir)),
        Passo("Cuidado", "Lucro (P/L) distorcido por PoC; a projecao capta o crescimento real."),
    ]
    r.alerta = ALERTAS.get(ticker, "")
    return r


def _tir_ciclica(dados: dict, ticker: str) -> ResultadoTIR:
    dy = _dec(dados.get("dy")) or 0.0
    r = ResultadoTIR(None, "ciclica", NOME_METODO["ciclica"])
    g = IPCA_BASE   # nao extrapola lucro/FCL de commodity; assume manter valor real
    tir = dy + g
    r.tir = tir
    r.memoria = [
        Passo("Dividend yield (DY)", _p(dy)),
        Passo("g = inflacao (nao extrapola lucro ciclico)", _p(g)),
        Passo("TIR nominal = DY + inflacao", _p(tir)),
        Passo("Cuidado", "Ciclica: P/L e CAGR de lucro ignorados - enganam no pico/vale. Real ~= DY."),
    ]
    r.alerta = ALERTAS.get(ticker, "")
    return r


def _tir_utility(dados: dict, ticker: str) -> ResultadoTIR:
    dy = _dec(dados.get("dy")) or 0.0
    r = ResultadoTIR(None, "utility", NOME_METODO["utility"])
    g = IPCA_BASE   # receita regulada indexada a inflacao: crescimento real ~ 0
    tir = dy + g
    r.tir = tir
    r.memoria = [
        Passo("Dividend yield (DY)", _p(dy)),
        Passo("g = inflacao (receita regulada indexada)", _p(g)),
        Passo("TIR nominal = DY + inflacao", _p(tir)),
        Passo("Obs.", "Real ~= DY. Ideal futuro: DCF do fluxo regulado (WACC vs TIR indexada)."),
    ]
    r.alerta = ALERTAS.get(ticker, "")
    return r


def _tir_holding(dados: dict, ticker: str) -> ResultadoTIR:
    dy = _dec(dados.get("dy")) or 0.0
    info = HOLDINGS.get(ticker, {"desconto": 0.0, "contingencia_nav": 0.0,
                                 "g_subjacente": IPCA_BASE})
    r = ResultadoTIR(None, "holding", NOME_METODO["holding"])
    if dy <= 0:
        r.alerta = "Sem DY - holding depende do dividendo look-through."
        return r
    g = info.get("g_subjacente", IPCA_BASE)
    tir = dy + g
    r.tir = tir
    r.memoria = [
        Passo("DY reportado (ja amplificado pelo desconto)", _p(dy)),
        Passo("g da controlada", _p(g)),
        Passo("TIR de renda = DY + g", _p(tir)),
        Passo("Desconto de NAV (kicker se fechar)", _p(info["desconto"])),
        Passo("Contingencias / NAV (risco, cauda esquerda)", _p(info["contingencia_nav"])),
        Passo("Obs.", "P/L contabil ignorado - contaminado por equivalencia patrimonial."),
    ]
    r.alerta = ALERTAS.get(ticker, "")
    return r


# ==========================================================================
# API PUBLICA
# ==========================================================================
def classificar(ticker: str) -> Optional[str]:
    return ARQUETIPO_POR_TICKER.get((ticker or "").upper())


def _arquetipo_por_setor(setor: str) -> Optional[str]:
    """Fallback quando o ticker nao esta no mapa: classifica pelo texto do
    SETOR (mesma logica de setores do RADAR), pra nunca deixar um ticker
    novo sem TIR."""
    s = str(setor or "").lower()
    if not s:
        return None
    if "holding" in s:
        return "holding"
    if any(x in s for x in ("constru", "incorpora", "imobili")):
        return "incorporadora"
    if any(x in s for x in ("elétric", "eletric", "energia", "saneamento",
                            "transmiss", "utilities", "água", "agua", "gás", "gas")):
        return "utility"
    if any(x in s for x in ("papel", "celulose", "mineraç", "minera", "petról",
                            "petro", "óleo", "oleo", "cíclic", "ciclic", "químic",
                            "quimic", "siderur", "metalur", "borracha", "commodit",
                            "agro", "agr")):
        return "ciclica"
    if any(x in s for x in ("seguro", "segur", "previd", "capitaliz", "resseg")):
        return "seguradora"
    if any(x in s for x in ("banco", "banc", "financeir", "cred")):
        return "banco"
    # varejo, industrial, telecom, bens, etc. -> qualidade (crescimento projetado)
    return "qualidade"


def calcular_tir(ticker: str, dados: dict) -> ResultadoTIR:
    """
    ticker: codigo B3 (ex.: 'BBAS3').
    dados : dict com preco, pl, dy, roe, pvp (dy/roe/pvp em decimal).
            Opcional: 'setor' (usado como fallback de classificacao) e,
            para ciclicas, 'lucro_normalizado_pa'.
    """
    ticker = (ticker or "").upper()
    arq = classificar(ticker) or _arquetipo_por_setor(dados.get("setor"))

    if arq == "banco":
        return _tir_banco(dados)
    if arq == "seguradora":
        return _tir_seguradora(dados, ticker)
    if arq == "qualidade":
        return _tir_qualidade(dados)
    if arq == "utility":
        return _tir_utility(dados, ticker)
    if arq == "ciclica":
        return _tir_ciclica(dados, ticker)
    if arq == "holding":
        return _tir_holding(dados, ticker)
    if arq == "incorporadora":
        return _tir_incorporadora(dados, ticker)

    r = ResultadoTIR(None, "nao_classificado", "-")
    r.alerta = f"Ticker {ticker} sem arquetipo (nem por setor) - adicione ao mapa."
    return r


def tir_real_de(res: ResultadoTIR):
    """Converte a TIR nominal do resultado em TIR REAL (decimal), descontando
    o IPCA_BASE de forma composta. Retorna None se nao houver TIR."""
    if res.tir is None:
        return None
    return (1 + res.tir) / (1 + IPCA_BASE) - 1


# ==========================================================================
# RENDER STREAMLIT - caixa da TIR REAL (identica ao _card_metric) + botao
# ==========================================================================
def render_tir_real(st, col_box, col_botao, res: ResultadoTIR, card_style: str):
    """Desenha a caixa 'TIR REAL' (mesmo markup do _card_metric do app, pra
    ficar identica a caixa de Earnings Yield) na col_box, e o botao 'Ver
    calculo' (popover com a memoria) na col_botao. Formato: IPCA + X%."""
    tir_real = tir_real_de(res)
    if tir_real is not None:
        p = tir_real * 100
        texto = f"IPCA + {p:.1f}%".replace(".", ",")
        cor = "#22C55E" if p >= 8 else ("#D4AF37" if p >= 4 else "#EF4444")
    else:
        texto, cor = "—", "#888"

    col_box.markdown(
        "<div style='{base}text-align:center;'>"
        "<div style='font-size:0.72em;color:#ccc;text-transform:uppercase;'>TIR REAL</div>"
        "<div style='font-size:1.25em;font-weight:900;color:{cor};'>{texto}</div>"
        "</div>".format(base=card_style, cor=cor, texto=texto),
        unsafe_allow_html=True
    )

    with col_botao:
        with st.popover("🔍 Ver cálculo da TIR", use_container_width=True):
            st.markdown(f"**Arquétipo:** {res.arquetipo}")
            st.markdown(f"**Método:** {res.metodo}")
            st.markdown("---")
            for passo in res.memoria:
                st.markdown(f"**{passo.rotulo}:** {passo.valor}")
            if res.tir is not None:
                st.markdown("---")
                st.markdown(
                    ("**Conversão pra real:** (1 + {nom:.1f}%) ÷ (1 + {ipca:.0f}%) − 1 "
                     "= **IPCA + {real:.1f}%**").format(
                        nom=res.tir * 100, ipca=IPCA_BASE * 100, real=tir_real * 100
                    ).replace(".", ",")
                )
            if res.alerta:
                st.warning(res.alerta)
            if res.tir is None and not res.memoria:
                st.caption("Sem dados suficientes para calcular a TIR deste ativo.")
            st.caption(f"engine {VERSION}")


def montar_dados_tir(row, ativo_data, limpar_valor, pl_atual_val=None, dy_num=None):
    """Monta o dict de entrada da TIR a partir do row (planilha) e do
    ativo_data. Fonte unica, usada tanto pelo card quanto pela tabela, pra
    os dois nunca divergirem."""
    roe_raw = ativo_data.get('roe_num_raw', 0) if isinstance(ativo_data, dict) else 0
    pvp_raw = ativo_data.get('pvp_num_raw', 0) if isinstance(ativo_data, dict) else 0
    if dy_num is None:
        dy_num = ativo_data.get('dy_num', 0) if isinstance(ativo_data, dict) else 0
    payout_raw = row.get('PAYOUT', '-')
    payout_num = limpar_valor(payout_raw) if payout_raw not in (None, '-', '') else None
    cagr_raw = row.get('CAGR lucros (últ. 5 anos)', row.get('CAGR lucros (últimos 5 anos)', None))
    cagr_num = limpar_valor(cagr_raw) if cagr_raw not in (None, '-', '') else None
    # P/L da planilha (PROJETADO) e a fonte confiavel; pl_atual_val (Fundamentus)
    # so como fallback quando o projetado nao existir.
    pl_proj = limpar_valor(row.get('P/L PROJETADO', 0))
    pl_para_tir = pl_proj if (pl_proj and pl_proj > 0) else pl_atual_val
    return {
        "preco": limpar_valor(str(row.get('Cotação atual', 0)).replace('R$', '')) or None,
        "pl": pl_para_tir,
        "pl_atual": pl_atual_val,
        "dy": (dy_num / 100) if dy_num else None,
        "roe": (roe_raw / 100) if roe_raw else None,
        "pvp": pvp_raw or None,
        "payout": (payout_num / 100) if payout_num else None,
        "cagr": (cagr_num / 100) if cagr_num is not None else None,
        "setor": row.get('SETOR', ''),
    }


def tir_real_valor(ticker, row, ativo_data, limpar_valor, pl_atual_val=None, dy_num=None):
    """Retorna a TIR REAL em pontos percentuais (ex.: 12.3) ou None.
    Para uso na Tabela Completa (coluna numerica, ordenavel)."""
    dados = montar_dados_tir(row, ativo_data, limpar_valor, pl_atual_val, dy_num)
    res = calcular_tir(ticker, dados)
    tr = tir_real_de(res)
    return round(tr * 100, 1) if tr is not None else None


def render_tir(st, col_box, col_botao, ticker, row, ativo_data,
               pl_atual_val, dy_num, card_style, limpar_valor):
    """Tudo em um: monta os dados a partir do row/ativo_data, calcula a TIR
    pelo arquetipo e desenha a caixa 'TIR REAL' + o botao da memoria.
    Basta uma unica linha de chamada no app.py."""
    dados = montar_dados_tir(row, ativo_data, limpar_valor, pl_atual_val, dy_num)
    res = calcular_tir(ticker, dados)
    render_tir_real(st, col_box, col_botao, res, card_style)
    return res
