"""
cvm_insiders.py  (v2 - validado contra arquivo real de 2026)
============================================================
Ingestor de negociacoes de administradores e controladores ("insiders oficiais")
para o RADAR Fundamentalista.

Fonte  : CVM - Portal Dados Abertos. Conjunto "Cias Abertas: Documentos:
         Valores Mobiliarios Negociados e Detidos" (Art. 11 da Resolucao CVM 44).
Licenca: Open Data Commons ODbL. Redistribuicao permitida em produto desde que
         com atribuicao -> exibir "Fonte: CVM - Dados Abertos" no app.

URL (so trocar o ano):
    https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/DADOS/vlmo_cia_aberta_2026.zip

O ZIP contem 2 CSVs:
  - vlmo_cia_aberta_AAAA.csv      -> metadados dos documentos (header)
  - vlmo_cia_aberta_con_AAAA.csv  -> CONSOLIDADO com as movimentacoes (usamos este)

Formato dos CSVs: separador ';', encoding latin-1.
ATENCAO: os campos numericos (Quantidade, Preco_Unitario, Volume) vem em formato
AMERICANO (ponto decimal, sem separador de milhar) -> conversao direta por float.
As datas vem em ISO (AAAA-MM-DD).

Granularidade: informe MENSAL por companhia, com algumas semanas de defasagem.
E um sinal de CONVICCAO de medio prazo, nao gatilho de curto prazo.
"""

import io
import zipfile
import unicodedata
from datetime import date

import pandas as pd
import requests

URL_BASE = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/DADOS/vlmo_cia_aberta_{ano}.zip"

# CNPJs travados e confirmados contra o arquivo de 2026 (a empresa LISTADA de
# cada ticker; subsidiarias e holdings homonimas foram descartadas).
MAPA_TICKER_CNPJ = {
    "PETR4":  "33.000.167/0001-01",  # Petroleo Brasileiro - Petrobras
    "VALE3":  "33.592.510/0001-54",  # Vale
    "BPAC11": "30.306.294/0001-45",  # Banco BTG Pactual
    "BBAS3":  "00.000.000/0001-91",  # Banco do Brasil
    "BBSE3":  "17.344.597/0001-94",  # BB Seguridade
    "B3SA3":  "09.346.601/0001-25",  # B3
    "KLBN11": "89.637.490/0001-45",  # Klabin
    "BRAP4":  "03.847.461/0001-92",  # Bradespar
    "SUZB3":  "16.404.287/0001-55",  # Suzano
    "PSSA3":  "02.149.205/0001-69",  # Porto Seguro
    "ITUB4":  "60.872.504/0001-23",  # Itau Unibanco Holding
    "BBDC4":  "60.746.948/0001-12",  # Banco Bradesco
    "AXIA3":  "00.001.180/0001-26",  # Axia Energia (ex-Eletrobras)
}

# Quem e "pessoa-chave" (convicao de quem opera a empresa) vs estrutural.
CARGOS_PESSOAS_CHAVE = [
    "Diretor ou Vinculado",
    "Conselho de Administração ou Vinculado",
]
CARGO_CONTROLADOR = "Controlador ou Vinculado"

# Movimentacoes que representam decisao de mercado (convicao). O resto
# (Saldo Inicial, Posse, Desligamento, emprestimo, bonificacao, plano de
# remuneracao, desdobramento...) e ruido tecnico e fica de fora.
MOV_COMPRA = "Compra à vista"
MOV_VENDA = "Venda à vista"

# Ativos de interesse para o sinal de acao (Units cobrem KLBN11, BPAC11).
ATIVOS_ACAO = ["Ações", "Units"]


def _sem_acento(texto) -> str:
    if texto is None:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def baixar_vlmo(ano: int | None = None, timeout: int = 60) -> pd.DataFrame:
    """Baixa o ZIP do ano e devolve o DataFrame consolidado (_con_)."""
    ano = ano or date.today().year
    url = URL_BASE.format(ano=ano)
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": "RADAR/1.0"})
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        nome_con = next(n for n in zf.namelist() if "_con_" in n.lower())
        with zf.open(nome_con) as f:
            return pd.read_csv(f, sep=";", encoding="latin-1", dtype=str, low_memory=False)


def carregar_local(caminho_zip: str) -> pd.DataFrame:
    """Le o consolidado a partir de um ZIP ja baixado (uso offline/teste)."""
    with zipfile.ZipFile(caminho_zip) as zf:
        nome_con = next(n for n in zf.namelist() if "_con_" in n.lower())
        with zf.open(nome_con) as f:
            return pd.read_csv(f, sep=";", encoding="latin-1", dtype=str, low_memory=False)


def insider_liquido(
    df: pd.DataFrame,
    tickers: list[str] | None = None,
    meses: int = 6,
    cargos: list[str] | None = None,
    incluir_controlador: bool = False,
) -> pd.DataFrame:
    """
    Fluxo liquido de insiders (compras - vendas, em R$) por ticker nos ultimos
    N meses, considerando apenas Compra/Venda a vista de Acoes/Units.

    cargos              : lista de Tipo_Cargo a considerar (default: pessoas-chave
                          = Diretoria + Conselho de Administracao).
    incluir_controlador : se True, adiciona uma coluna separada com o liquido do
                          controlador (que costuma ser estrutural, nao convicao).

    Retorna: ticker, compras_rs, vendas_rs, liquido_rs, n_ops, sinal
             (+ controlador_rs se incluir_controlador=True).
    """
    cargos = cargos or CARGOS_PESSOAS_CHAVE
    inv = {v: k for k, v in MAPA_TICKER_CNPJ.items()}
    alvo = (
        [MAPA_TICKER_CNPJ[t] for t in tickers]
        if tickers else list(MAPA_TICKER_CNPJ.values())
    )

    d = df[df["CNPJ_Companhia"].isin(alvo)].copy()
    d["ticker"] = d["CNPJ_Companhia"].map(inv)
    d["vol"] = pd.to_numeric(d["Volume"], errors="coerce")  # formato US
    d["dt"] = pd.to_datetime(d["Data_Movimentacao"], errors="coerce", format="%Y-%m-%d")

    corte = pd.Timestamp.today() - pd.DateOffset(months=meses)
    base = d[
        (d["dt"] >= corte)
        & (d["Tipo_Movimentacao"].isin([MOV_COMPRA, MOV_VENDA]))
        & (d["Tipo_Ativo"].isin(ATIVOS_ACAO))
    ].copy()

    def _liq(sub):
        compra = sub["vol"].where(sub["Tipo_Movimentacao"] == MOV_COMPRA, 0).sum()
        venda = sub["vol"].where(sub["Tipo_Movimentacao"] == MOV_VENDA, 0).sum()
        return compra, venda

    linhas = []
    for tk in (tickers or MAPA_TICKER_CNPJ.keys()):
        sub = base[base["ticker"] == tk]
        pessoas = sub[sub["Tipo_Cargo"].isin(cargos)]
        compra, venda = _liq(pessoas)
        reg = {
            "ticker": tk,
            "compras_rs": compra,
            "vendas_rs": venda,
            "liquido_rs": compra - venda,
            "n_ops": len(pessoas),
        }
        if incluir_controlador:
            ctrl = sub[sub["Tipo_Cargo"] == CARGO_CONTROLADOR]
            c_c, c_v = _liq(ctrl)
            reg["controlador_rs"] = c_c - c_v
        linhas.append(reg)

    out = pd.DataFrame(linhas)
    out["sinal"] = out["liquido_rs"].apply(lambda v: 1 if v > 0 else (-1 if v < 0 else 0))
    return out.sort_values("liquido_rs", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    # Producao (Streamlit Cloud): df = baixar_vlmo(2026)
    # Aqui, teste contra o arquivo local:
    df = carregar_local("/mnt/user-data/uploads/vlmo_cia_aberta_2026.zip")
    res = insider_liquido(df, meses=6, incluir_controlador=True)
    pd.options.display.float_format = lambda x: f"{x:,.0f}"
    print(res.to_string(index=False))
