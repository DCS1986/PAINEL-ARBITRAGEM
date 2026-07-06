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
    "g_piso":        0.06,    # piso = inflacao: todo negocio ao menos mantem valor real
    #                          (com isso a TIR real nunca cai abaixo do proprio DY)
}

# Inflacao base pra converter a TIR NOMINAL em TIR REAL (formato "IPCA + X%",
# igual o mercado apresenta uma NTN-B). Conversao composta:
#   TIR real = (1 + TIR nominal) / (1 + IPCA_BASE) - 1
IPCA_BASE = 0.06

# Carimbo de versao - aparece na caixa de calculo. Se o app nao mostrar esta
# versao, o engine novo NAO esta no ar (arquivo duplicado ou cache do deploy).
VERSION = "v13 (incorporadoras: ROE medio 3 anos + teto g=12%; bancos/PSSA: ROE atual)"

# Tickers com TIR calculada com formula validada — exibidos em verde na tabela
TICKERS_TIR_CONFIRMADA = {
    # Bancos: formula EY*payout=DY, g=ROE*retencao
    "ITUB4", "BBAS3", "BBDC3", "BPAC11", "SANB3", "ABCB4", "BRSR6", "BMGB4",
    # Seguradoras com formula individual validada
    "BBSE3",   # yield-only (g=inflacao, TIR real = DY)
    "CXSE3",   # DY + 10% de crescimento
    "PSSA3",   # Porto: EY*payout=DY, g=ROE*retencao (formula banco — validada no print)
    # Telecom
    "TIMS3",   # cenario medio: DY + 7% crescimento
    # Incorporadoras: formula banco com ROE medio 3 anos + teto g=12%
    "CURY3", "DIRR3", "MDNE3", "CYRE3",
    # Utilities elétricas: DY atual × g travado por subsetor
    "TAEE11","ISAE4","ALUP11","EGIE3","AXIA3","CPFE3","EQTL3","CMIG4","CPLE3",
}

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
        "PSSA3",  # Porto: payout 50%, g=ROE*retencao — mesma formula dos bancos
        # Incorporadoras: mesma formula, ROE medio 3 anos, teto g=12%
        "CURY3", "DIRR3", "MDNE3", "CYRE3",
    ]},
    # 2) Seguradora -> DY + crescimento especifico (capital-light, payout alto)
    **{t: "seguradora" for t in ["BBSE3", "CXSE3", "IRBR3"]},
    # 3) Qualidade / crescimento -> DY + crescimento projetado (motor: reinvestir)
    **{t: "qualidade" for t in [
        "WEGE3", "B3SA3", "GRND3", "LEVE3", "POMO4", "VULC3", "SHUL4",
        "CGRA4", "LREN3",
    ]},
    # 4) Utility / contratada -> DY + inflacao (receita regulada indexada)
    **{t: "utility" for t in [
        "SBSP3", "CSMG3", "SAPR4", "TAEE11", "EGIE3", "CPFE3", "CPLE3",
        "CMIG4", "EQTL3", "TIMS3", "ISAE4", "AXIA3", "ALUP11",
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
        "JHSF3", "ALOS3",
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
    """Crescimento a partir da SUA projecao: implicito no P/L atual vs P/L
    projetado -> g = P/L atual / P/L projetado - 1. So vale quando os dois P/L
    estao na MESMA base (ambos por lucro liquido). Se a razao explode, e sinal
    de base diferente (ex.: projetado por EBITDA numa ciclica, ou P/L atual
    distorcido por LL negativo/cambio) -> a comparacao nao vale, cai no CAGR."""
    pl_atual = dados.get("pl_atual")
    pl_proj = dados.get("pl")            # P/L PROJETADO da planilha
    if pl_atual and pl_atual > 0 and pl_proj and pl_proj > 0:
        g_raw = pl_atual / pl_proj - 1
        # Trava de sanidade: crescimento anual plausivel entre -40% e +80%.
        # Fora disso os dois P/L nao sao comparaveis (bases distintas).
        if -0.40 <= g_raw <= 0.80:
            return _clamp(g_raw, PREMISSAS["g_piso"], PREMISSAS["g_teto"]), "projecao (P/L atual vs projetado)"
    cagr = _dec(dados.get("cagr"))
    if cagr is not None:
        return _clamp(cagr, PREMISSAS["g_piso"], PREMISSAS["g_teto"]), "CAGR de lucros (fallback)"
    return IPCA_BASE, "inflacao (sem projecao confiavel)"


def _tir_nominal(dy: float, g: float) -> float:
    """Retorno nominal composto: (1+DY) x (1+g) - 1.
    Matematicamente correto — DY+g e apenas aproximacao para numeros pequenos."""
    return (1 + dy) * (1 + g) - 1


def _tir_banco(dados: dict, ticker: str = "") -> ResultadoTIR:
    """Formula do print: EY = 1/PL_projetado, DY = EY x payout, g = (1-payout) x ROE_atual."""
    pl   = dados.get("pl")       # P/L PROJETADO da planilha
    roe  = _dec(dados.get("roe"))
    payout_real = dados.get("payout")
    r = ResultadoTIR(None, "banco", NOME_METODO["banco"])
    if not pl or pl <= 0:
        r.alerta = "Falta P/L projetado."
        return r
    # Incorporadoras: usa ROE médio 3 anos + teto específico do setor
    if ticker in _ROE_MEDIO_INCORPORADORA:
        roe_calc  = _ROE_MEDIO_INCORPORADORA[ticker]
        g_teto    = _G_TETO_INCORPORADORA
        fonte_roe = f"ROE médio 3 anos ({int(roe_calc*100)}% — suaviza pico do ciclo)"
        # Payout e P/L também travados para evitar distorção do PoC e dividendos extraordinários
        payout_real = _PAYOUT_INCORPORADORA[ticker]
        pl = _PL_REF_INCORPORADORA[ticker]   # P/L de referência validado
        fonte_p = f"payout sustentável fixo ({int(payout_real*100)}%)"
    else:
        if roe is None:
            r.alerta = "Faltam PL projetado e/ou ROE."
            return r
        roe_calc  = roe
        g_teto    = PREMISSAS["g_teto"]
        fonte_roe = "ROE atual"
    payout   = _clamp(payout_real, 0, 1) if (payout_real and payout_real > 0) else 0.40
    fonte_p  = "planilha" if (payout_real and payout_real > 0) else "default 40%"
    ey       = 1.0 / pl
    dy       = ey * payout
    retencao = max(0.0, 1 - payout)
    g        = _clamp(roe_calc * retencao, PREMISSAS["g_piso"], g_teto)
    tir = _tir_nominal(dy, g)
    r.tir = tir
    r.memoria = [
        Passo("P/L projetado (planilha)", f"{pl:.1f}x".replace(".", ",")),
        Passo("Earning yield (EY = 1/PL)", _p(ey)),
        Passo(f"Payout ({fonte_p})", _p(payout)),
        Passo("Dividend yield = EY x payout", _p(dy)),
        Passo(fonte_roe, _p(roe_calc)),
        Passo("Retencao (1 - payout)", _p(retencao)),
        Passo(f"g = ROE x retencao (teto {_p(PREMISSAS['g_teto'])})", _p(g)),
        Passo("TIR nominal = (1+DY) x (1+g) - 1", _p(tir)),
    ]
    return r


# Crescimento fixo por ticker para seguradoras com formula validada
_G_OVERRIDE_SEGURADORA = {
    "BBSE3": IPCA_BASE,   # g = inflacao → TIR real = DY (sem crescimento real projetado)
    "CXSE3": 0.10,        # g = 10% (crescimento validado pelo modelo do analista)
}


def _tir_seguradora(dados: dict, ticker: str) -> ResultadoTIR:
    dy = _dec(dados.get("dy")) or 0.0
    r = ResultadoTIR(None, "seguradora", NOME_METODO["seguradora"])
    # Override: BBSE e CXSE usam crescimento fixo validado
    if ticker in _G_OVERRIDE_SEGURADORA:
        g = _G_OVERRIDE_SEGURADORA[ticker]
        if ticker == "BBSE3":
            fonte_g = "inflacao (sem crescimento real projetado para 2026)"
        else:
            fonte_g = "10% (crescimento validado)"
    else:
        g, fonte_g = _g_projetado(dados)
    tir = _tir_nominal(dy, g)
    r.tir = tir
    r.memoria = [
        Passo("Dividend yield (DY)", _p(dy)),
        Passo(f"g ({fonte_g})", _p(g)),
        Passo("TIR nominal = (1+DY) x (1+g) - 1", _p(tir)),
        Passo("Obs.", "Capital-light: cresce sem reter capital."),
    ]
    r.alerta = ALERTAS.get(ticker, "")
    return r


def _tir_qualidade(dados: dict) -> ResultadoTIR:
    dy = _dec(dados.get("dy")) or 0.0
    r = ResultadoTIR(None, "qualidade", NOME_METODO["qualidade"])
    g, fonte_g = _g_projetado(dados)
    tir = _tir_nominal(dy, g)
    r.tir = tir
    r.memoria = [
        Passo("Dividend yield (DY)", _p(dy)),
        Passo(f"g projetado ({fonte_g}, teto {_p(PREMISSAS['g_teto'])})", _p(g)),
        Passo("TIR nominal = (1+DY) x (1+g) - 1", _p(tir)),
        Passo("Obs.", "Motor e o crescimento (reinvestimento), nao o dividendo."),
    ]
    return r


def _tir_incorporadora(dados: dict, ticker: str) -> ResultadoTIR:
    dy_atual = _dec(dados.get("dy")) or 0.0
    dy_norm  = dados.get("dy_norm")
    dy       = dy_norm if dy_norm is not None else dy_atual
    r = ResultadoTIR(None, "incorporadora", NOME_METODO["incorporadora"])
    g, fonte_g = _g_projetado(dados)
    tir = _tir_nominal(dy, g)
    r.tir = tir
    fonte_dy = "DY normalizado (media 2-3 anos)" if dy_norm is not None else "DY atual"
    r.memoria = [
        Passo(f"DY usado ({fonte_dy})", _p(dy)),
        Passo("DY atual (referencia)", _p(dy_atual)),
        Passo(f"g projetado ({fonte_g}, teto {_p(PREMISSAS['g_teto'])})", _p(g)),
        Passo("TIR nominal = (1+DY) x (1+g) - 1", _p(tir)),
        Passo("Cuidado", "Dividendo suavizado para nao creditar pico de ciclo como recorrente."),
    ]
    r.alerta = ALERTAS.get(ticker, "")
    return r


def _tir_ciclica(dados: dict, ticker: str) -> ResultadoTIR:
    dy = _dec(dados.get("dy")) or 0.0
    r = ResultadoTIR(None, "ciclica", NOME_METODO["ciclica"])
    g = IPCA_BASE
    tir = _tir_nominal(dy, g)
    r.tir = tir
    r.memoria = [
        Passo("Dividend yield (DY)", _p(dy)),
        Passo("g = inflacao (nao extrapola lucro ciclico)", _p(g)),
        Passo("TIR nominal = (1+DY) x (1+g) - 1", _p(tir)),
        Passo("Cuidado", "Ciclica: P/L e CAGR ignorados — enganam no pico/vale. Real ~= DY."),
    ]
    r.alerta = ALERTAS.get(ticker, "")
    return r


# ROE médio 3 anos para incorporadoras (suaviza pico do ciclo)
# Fonte: histórico de releases 2022-2025, arredondado de forma conservadora
_ROE_MEDIO_INCORPORADORA = {
    "CURY3": 0.45,   # ROE atual 79% mas média 3 anos estimada em ~45%
    "DIRR3": 0.38,   # ROE atual 44%, média 3 anos ~38%
    "MDNE3": 0.22,   # ROE atual 27%, média 3 anos ~22%
    "CYRE3": 0.13,   # ROE atual 11%, média 3 anos ~13%
}

# Payout sustentável para incorporadoras (ignora distribuições extraordinárias)
# Usa média histórica recorrente, não o payout realizado no trimestre
_PAYOUT_INCORPORADORA = {
    "CURY3": 0.50,
    "DIRR3": 0.62,
    "MDNE3": 0.55,
    "CYRE3": 0.55,
}

# P/L de referência por incorporadora (validado — só muda na revisão trimestral)
# Evita distorção do PoC: resultado contábil pode estar sub/superavaliado
_PL_REF_INCORPORADORA = {
    "CURY3": 10.1,
    "DIRR3": 8.5,
    "MDNE3": 5.79,
    "CYRE3": 6.0,
}

# Teto de crescimento para incorporadoras (evita perpetuidade irreal)
_G_TETO_INCORPORADORA = 0.12   # 12% nominal máximo

# Crescimento validado por ticker para utilities com formula confirmada
# Revisão: a cada trimestre — checar novos leilões, capex e guidance de dividendos
_G_OVERRIDE_UTILITY = {
    # Telecom
    "TIMS3": 0.07,   # cenario medio validado (DY ~10.7% + g 7%)
    # Elétricas — g nominal travado por subsetor (revisado trimestralmente)
    "TAEE11": 0.060,  # Transmissora pura: RAP indexada IPCA/IGPM, crescimento = inflação
    "ISAE4":  0.060,  # Transmissora pura: idem TAEE, portfólio de concessões mais novas
    "ALUP11": 0.120,  # Transmissora + capex: 9 projetos entrando até 2029 + América Latina
    "EGIE3":  0.100,  # Geradora: TAG + Jirau + expansão eólica — capex pesado mas crescimento real
    "AXIA3":  0.120,  # Geradora privatizada: descotização (upside enorme) + maior geradora do país
    "CPFE3":  0.090,  # Distribuidora integrada: concessões renovadas 30 anos + State Grid
    "EQTL3":  0.130,  # Turnaround comprovado: Sabesp + saneamento + expansão Norte/Nordeste
    "CMIG4":  0.050,  # Estatal: payout alto mas crescimento limitado por interferência política
    "CPLE3":  0.090,  # Ex-estatal privatizada 2023: ganhos de eficiência + capex renovação
}


def _tir_utility(dados: dict, ticker: str) -> ResultadoTIR:
    dy = _dec(dados.get("dy")) or 0.0
    r = ResultadoTIR(None, "utility", NOME_METODO["utility"])
    if ticker in _G_OVERRIDE_UTILITY:
        g = _G_OVERRIDE_UTILITY[ticker]
        fonte_g = f"{int(g*100)}% (cenario medio validado)"
    else:
        g = IPCA_BASE
        fonte_g = "inflacao (receita regulada indexada)"
    tir = _tir_nominal(dy, g)
    r.tir = tir
    r.memoria = [
        Passo("Dividend yield (DY)", _p(dy)),
        Passo(f"g = {fonte_g}", _p(g)),
        Passo("TIR nominal = (1+DY) x (1+g) - 1", _p(tir)),
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
    tir = _tir_nominal(dy, g)
    r.tir = tir
    r.memoria = [
        Passo("DY reportado (ja amplificado pelo desconto)", _p(dy)),
        Passo("g da controlada", _p(g)),
        Passo("TIR nominal = (1+DY) x (1+g) - 1", _p(tir)),
        Passo("Desconto de NAV (kicker se fechar)", _p(info["desconto"])),
        Passo("Contingencias / NAV (risco, cauda esquerda)", _p(info["contingencia_nav"])),
    ]
    r.alerta = ALERTAS.get(ticker, "")
    return r


def classificar(ticker: str):
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
        return _tir_banco(dados, ticker)
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


def _dy_normalizado(ativo_data):
    """DY normalizado: media dos ultimos 2-3 anos COMPLETOS (exclui o ano
    corrente, que costuma estar parcial). Suaviza o dividendo de pico das
    ciclicas/incorporadoras sem carregar o passado magro de 5 anos. Retorna
    decimal (ex.: 0.055) ou None se nao houver historico."""
    import datetime
    hist = ativo_data.get('historico_dy', {}) if isinstance(ativo_data, dict) else {}
    if not hist:
        return None
    ano_atual = datetime.datetime.now().year
    anos = sorted(a for a in hist.keys() if isinstance(a, int) and a < ano_atual)
    if not anos:
        anos = sorted(a for a in hist.keys() if isinstance(a, int))
    ult = anos[-3:]                              # ate 3 anos completos mais recentes
    vals = [hist[a] for a in ult if hist.get(a)]
    if not vals:
        return None
    return (sum(vals) / len(vals)) / 100.0       # historico_dy em %, retorna decimal


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
        "dy_norm": _dy_normalizado(ativo_data),
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
