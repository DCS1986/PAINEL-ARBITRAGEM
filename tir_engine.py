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
    "inflacao_lp":   0.045,   # inflacao de longo prazo (top-up nominal)
    "premio_risco":  0.045,   # equity risk premium (mesmo do Gordon do RADAR)
    "g_nominal_max": 0.12,    # teto de crescimento sustentavel (Gordon)
    "g_nominal_min": 0.00,    # piso de crescimento
}

# Inflacao base pra converter a TIR NOMINAL em TIR REAL (formato "IPCA + X%",
# igual o mercado apresenta uma NTN-B). Conversao composta:
#   TIR real = (1 + TIR nominal) / (1 + IPCA_BASE) - 1
IPCA_BASE = 0.06

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
    # 1) Qualidade previsivel -> Gordon / Owner's earnings
    **{t: "qualidade" for t in [
        "WEGE3", "ITUB4", "BBDC3", "BBAS3", "BPAC11", "ABCB4", "BRSR6",
        "SANB3", "BMGB4", "B3SA3", "BBSE3", "PSSA3", "CXSE3", "IRBR3",
        "GRND3", "LEVE3", "POMO4", "VULC3", "SHUL4", "CGRA4", "LREN3",
    ]},
    # 2) Utility / contratada -> proxy owner-yield + inflacao (ideal: DCF regulado)
    **{t: "utility" for t in [
        "SBSP3", "CSMG3", "SAPR4", "TAEE11", "EGIE3", "CPFE3", "CPLE3",
        "CMIG4", "EQTL3", "TIMS3", "ISAE4", "AXIA3",
    ]},
    # 3) Ciclica de commodity -> lucro normalizado mid-cycle
    **{t: "ciclica" for t in [
        "VALE3", "PETR4", "PRIO3", "CMIN3", "KLBN4", "RANI3", "SLCE3",
        "KEPL3", "FESA4",
    ]},
    # 4) Holding -> look-through + desconto de NAV
    **{t: "holding" for t in ["ITSA4", "BRAP4", "BRBI11"]},
    # 5) Incorporadora / imobiliario -> ROE sobre patrimonio (nao P/L)
    **{t: "incorporadora" for t in [
        "CYRE3", "CURY3", "DIRR3", "JHSF3", "MDNE3", "ALOS3",
    ]},
}

NOME_METODO = {
    "qualidade":     "Gordon (DY + g), g calibrado por ROE",
    "utility":       "Owner-yield + inflacao (proxy do DCF regulado)",
    "ciclica":       "Earnings yield sobre lucro normalizado mid-cycle",
    "holding":       "Look-through + desconto de NAV",
    "incorporadora": "ROE sobre patrimonio ajustado pelo P/VP",
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
def _tir_qualidade(dados: dict) -> ResultadoTIR:
    pl = dados.get("pl")
    dy = _dec(dados.get("dy"))
    roe = _dec(dados.get("roe"))
    r = ResultadoTIR(None, "qualidade", NOME_METODO["qualidade"])

    if not pl or pl <= 0 or dy is None or roe is None:
        r.alerta = "Faltam dados (P/L>0, DY, ROE) ou lucro negativo - Gordon nao se aplica."
        return r

    ey = 1 / pl
    payout_real = dados.get("payout")           # payout real da planilha (ja decimal)
    if payout_real is not None and payout_real > 0:
        payout = _clamp(payout_real, 0, 2.0)
        fonte_payout = "planilha"
    else:
        payout = _clamp(dy * pl, 0, 1)          # fallback: DPA/LPA = DY x P/L
        fonte_payout = "estimado (DY x PL)"
    retencao = max(0.0, 1 - payout)
    g_sust = roe * retencao
    g = _clamp(g_sust, PREMISSAS["g_nominal_min"], PREMISSAS["g_nominal_max"])
    tir = dy + g

    r.tir = tir
    r.memoria = [
        Passo("Earnings yield (1/PL)", _p(ey)),
        Passo("Dividend yield (DY)", _p(dy)),
        Passo(f"Payout ({fonte_payout})", _p(payout)),
        Passo("Retencao (1 - payout)", _p(retencao)),
        Passo("g sustentavel (ROE x retencao)", _p(g_sust)),
        Passo(f"g aplicado (teto {_p(PREMISSAS['g_nominal_max'])})", _p(g)),
        Passo("TIR nominal = DY + g", _p(tir)),
    ]
    return r


def _tir_utility(dados: dict, ticker: str) -> ResultadoTIR:
    pl = dados.get("pl")
    dy = _dec(dados.get("dy"))
    infl = PREMISSAS["inflacao_lp"]
    r = ResultadoTIR(None, "utility", NOME_METODO["utility"])

    if dy is None or dy <= 0:
        r.alerta = "Sem DY confiavel - proxy de utility depende do dividendo."
        return r

    # Receita regulada/contratada e indexada a inflacao: crescimento real ~ 0.
    g = infl
    tir = dy + g
    r.tir = tir
    r.memoria = [
        Passo("Dividend yield (DY)", _p(dy)),
        Passo("Earnings yield (1/PL)", _p(1 / pl) if pl and pl > 0 else "n/d"),
        Passo("g = inflacao (receita indexada, real ~0)", _p(g)),
        Passo("TIR nominal = DY + inflacao", _p(tir)),
        Passo("Obs.", "Proxy. Ideal: DCF do fluxo regulado (WACC vs TIR indexada)."),
    ]
    r.alerta = ALERTAS.get(ticker, "")
    return r


def _tir_ciclica(dados: dict, ticker: str) -> ResultadoTIR:
    pl = dados.get("pl")
    preco = dados.get("preco")
    override = dados.get("lucro_normalizado_pa")
    fator = NORMALIZACAO_CICLICA.get(ticker, 1.0)
    r = ResultadoTIR(None, "ciclica", NOME_METODO["ciclica"])

    if override:                                   # lucro normalizado informado direto
        if not preco or preco <= 0:
            r.alerta = "Sem preco para o lucro normalizado informado."
            return r
        ey_norm = override / preco
        base = f"lucro normalizado informado (R$ {override:.2f}/acao)"
    elif pl and pl > 0:
        ey_norm = fator / pl                       # (LPA x fator) / preco = fator / PL
        base = f"trailing x fator {fator:g}"
    else:
        r.alerta = "Lucro atual negativo - informe 'lucro_normalizado_pa' para ciclica."
        return r

    tir = ey_norm   # ja nominal; nao soma inflacao (preco de commodity ja e nominal)
    r.tir = tir
    r.memoria = [
        Passo("Metodo", "Earnings yield sobre lucro MID-CYCLE, nao trailing"),
        Passo("Base do lucro normalizado", base),
        Passo("Earnings yield normalizado", _p(ey_norm)),
        Passo("TIR nominal (economica)", _p(tir)),
        Passo("Cuidado", "Trailing engana no vale/pico do ciclo. Calibre o fator."),
    ]
    r.alerta = ALERTAS.get(ticker, "")
    return r


def _tir_holding(dados: dict, ticker: str) -> ResultadoTIR:
    dy = _dec(dados.get("dy"))
    info = HOLDINGS.get(ticker, {"desconto": 0.0, "contingencia_nav": 0.0,
                                 "g_subjacente": PREMISSAS["inflacao_lp"]})
    r = ResultadoTIR(None, "holding", NOME_METODO["holding"])

    if dy is None or dy <= 0:
        r.alerta = "Sem DY - holding depende do dividendo look-through."
        return r

    # O DY reportado ja embute o desconto (dividendo / preco de mercado).
    # TIR de renda = DY reportado + crescimento da controlada.
    g = info["g_subjacente"]
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


def _tir_incorporadora(dados: dict, ticker: str) -> ResultadoTIR:
    roe = _dec(dados.get("roe"))
    pvp = dados.get("pvp")
    r = ResultadoTIR(None, "incorporadora", NOME_METODO["incorporadora"])

    if roe is None or not pvp or pvp <= 0:
        r.alerta = "Faltam ROE e P/VP - metodo de incorporadora depende deles."
        return r

    # P/L engana pelo timing de reconhecimento (PoC). ROE sobre patrimonio e
    # mais estavel. Retorno do dono = ROE / (P/VP) = earnings yield suavizado.
    tir = roe / pvp
    r.tir = tir
    r.memoria = [
        Passo("Metodo", "ROE sobre patrimonio (evita distorcao de PoC no lucro)"),
        Passo("ROE", _p(roe)),
        Passo("P/VP", f"{pvp:.2f}"),
        Passo("TIR nominal = ROE / (P/VP)", _p(tir)),
        Passo("Cuidado", "ROE de pico + landbank/VGV a vender mudam a leitura."),
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
    # banco, seguro, varejo, industrial, telecom, etc. -> qualidade (Gordon)
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


def render_tir(st, col_box, col_botao, ticker, row, ativo_data,
               pl_atual_val, dy_num, card_style, limpar_valor):
    """Tudo em um: monta os dados a partir do row/ativo_data, calcula a TIR
    pelo arquetipo e desenha a caixa 'TIR REAL' + o botao da memoria.
    Basta uma unica linha de chamada no app.py."""
    roe_raw = ativo_data.get('roe_num_raw', 0) if isinstance(ativo_data, dict) else 0
    pvp_raw = ativo_data.get('pvp_num_raw', 0) if isinstance(ativo_data, dict) else 0
    payout_raw = row.get('PAYOUT', '-')
    payout_num = limpar_valor(payout_raw) if payout_raw not in (None, '-', '') else None
    # P/L da planilha (PROJETADO) e a fonte confiavel do Diego; pl_atual_val
    # (Fundamentus) fica so como fallback quando o projetado nao existir.
    pl_proj = limpar_valor(row.get('P/L PROJETADO', 0))
    pl_para_tir = pl_proj if (pl_proj and pl_proj > 0) else pl_atual_val
    dados = {
        "preco": limpar_valor(str(row.get('Cotação atual', 0)).replace('R$', '')) or None,
        "pl": pl_para_tir,
        "dy": (dy_num / 100) if dy_num else None,
        "roe": (roe_raw / 100) if roe_raw else None,
        "pvp": pvp_raw or None,
        "payout": (payout_num / 100) if payout_num else None,
        "setor": row.get('SETOR', ''),
    }
    res = calcular_tir(ticker, dados)
    render_tir_real(st, col_box, col_botao, res, card_style)
    return res
