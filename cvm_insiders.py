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
import re
import zipfile
import unicodedata
from datetime import date

import pandas as pd
import requests

URL_BASE = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/DADOS/vlmo_cia_aberta_{ano}.zip"

URL_FCA = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_{ano}.zip"

# Pequenas correções manuais pra inconsistências CONHECIDAS de cadastro na
# propria CVM, onde a coluna Codigo_Negociacao vem com lixo (ex: "000000" ou
# um codigo numerico interno) em vez do ticker real. Confirmado por
# CNPJ/Nome_Empresarial no arquivo fca_cia_aberta_valor_mobiliario.
_CORRECOES_CADASTRO_CVM = {
    "BPAC11": "30.306.294/0001-45",  # Banco BTG Pactual (Codigo_Negociacao vem "000000")
    "CMIN3":  "08.902.291/0001-15",  # CSN Mineração (Codigo_Negociacao vem codigo interno)
}

# Aliases de classe de ação: o ticker da planilha do Diego nao e o mesmo
# registrado na CVM, mas e a MESMA empresa (mesmo CNPJ) -- so uma classe de
# acao diferente (ex: preferencial vs unit). Insider, recompra e fatos
# relevantes sao da empresa como um todo, entao vale usar o CNPJ da classe
# que de fato consta no cadastro. Confirmado a pedido do Diego: KLBN4 nao
# negocia mais separadamente, so existe KLBN11 (units) hoje -- mesmo CNPJ.
_ALIASES_CLASSE_ACAO = {
    "KLBN4": "89.637.490/0001-45",  # Klabin -- so negocia via KLBN11 hoje, mesma empresa
}

_PADRAO_TICKER = re.compile(r"^(?=.*[A-Z])[A-Z0-9]{4}\d{1,2}$")


def baixar_mapa_tickers(ano: int | None = None, timeout: int = 60) -> dict:
    """
    Baixa o Formulario Cadastral (FCA) da CVM e devolve {TICKER: CNPJ} pra
    TODAS as empresas listadas na B3 (458+ tickers) -- nao so um universo
    fixo. Fonte: fca_cia_aberta_valor_mobiliario_AAAA.csv (Codigo_Negociacao
    x CNPJ_Companhia). Mesma licenca ODbL do restante dos dados da CVM.
    """
    ano = ano or date.today().year
    url = URL_FCA.format(ano=ano)
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": "RADAR/1.0"})
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        nome = next(n for n in zf.namelist() if "valor_mobiliario" in n.lower())
        with zf.open(nome) as f:
            df = pd.read_csv(f, sep=";", encoding="latin-1", dtype=str, low_memory=False)
    return _construir_mapa_tickers(df)


def carregar_mapa_tickers_local(caminho_zip: str) -> dict:
    """Mesma coisa que baixar_mapa_tickers(), mas a partir de um ZIP local
    (uso offline/teste, sem precisar de rede)."""
    with zipfile.ZipFile(caminho_zip) as zf:
        nome = next(n for n in zf.namelist() if "valor_mobiliario" in n.lower())
        with zf.open(nome) as f:
            df = pd.read_csv(f, sep=";", encoding="latin-1", dtype=str, low_memory=False)
    return _construir_mapa_tickers(df)


def _construir_mapa_tickers(df: pd.DataFrame) -> dict:
    validos = df[df["Codigo_Negociacao"].str.match(_PADRAO_TICKER, na=False)]
    mapa = dict(zip(validos["Codigo_Negociacao"], validos["CNPJ_Companhia"]))
    mapa.update(_CORRECOES_CADASTRO_CVM)
    mapa.update(_ALIASES_CLASSE_ACAO)
    return mapa




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


# ---- Recompra REAL (verificacao por documento individual) -----------------
# O CSV "_con_" (insiders) e o dataset "Programa de Recompra" (autorizacao)
# NAO contem a execucao real de recompra -- confirmado exaustivamente em
# sessao de depuracao com o Diego. A execucao real (data/quantidade/preco/
# intermediario) so existe no FORMULARIO INDIVIDUAL de cada empresa/mes,
# que e um documento (provavelmente PDF) -- nao um CSV estruturado. O outro
# CSV dentro do MESMO zip do VLMO (sem o "_con_") e um INDICE desses
# documentos, com a coluna Link_Download apontando pro documento real.
#
# IMPORTANTE: a verificacao de "tem recompra real" por PDF abaixo foi
# escrita mas NUNCA TESTADA contra o documento de verdade (as ferramentas
# usadas para construir isso nao tem acesso a internet) -- precisa ser
# validada rodando no Streamlit Cloud antes de confiar no resultado.

def baixar_indice_documentos(ano: int | None = None, timeout: int = 60) -> pd.DataFrame:
    """Baixa o indice de documentos individuais (formularios) do mesmo ZIP do
    VLMO -- o CSV sem '_con_', que tem a coluna Link_Download apontando pro
    formulario individual de cada empresa/mes (onde mora a recompra real)."""
    ano = ano or date.today().year
    url = URL_BASE.format(ano=ano)
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": "RADAR/1.0"})
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        nome_idx = next(n for n in zf.namelist() if "_con_" not in n.lower())
        with zf.open(nome_idx) as f:
            return pd.read_csv(f, sep=";", encoding="latin-1", dtype=str, low_memory=False)


def carregar_indice_documentos_local(caminho_zip: str) -> pd.DataFrame:
    """Mesma coisa que baixar_indice_documentos(), a partir de um ZIP local."""
    with zipfile.ZipFile(caminho_zip) as zf:
        nome_idx = next(n for n in zf.namelist() if "_con_" not in n.lower())
        with zf.open(nome_idx) as f:
            return pd.read_csv(f, sep=";", encoding="latin-1", dtype=str, low_memory=False)


def link_documento_mais_recente(indice: pd.DataFrame, cnpj: str, meses: int = 6) -> list[str]:
    """Retorna os links de download dos formularios individuais de um CNPJ
    nos ultimos `meses` meses (mais recente primeiro)."""
    sub = indice[indice["CNPJ_Companhia"] == cnpj].copy()
    sub["dt"] = pd.to_datetime(sub["Data_Referencia"], errors="coerce")
    corte = pd.Timestamp.today() - pd.DateOffset(months=meses)
    sub = sub[sub["dt"] >= corte].sort_values("dt", ascending=False)
    return sub["Link_Download"].dropna().tolist()


_MARCADORES_MOVIMENTACAO_REAL = ["compra à vista", "venda à vista", "compra a vista", "venda a vista"]


def verificar_movimentacao_real(url: str, timeout: int = 20) -> bool | None:
    """
    Baixa o formulario individual (PDF) e verifica se a tabela "Movimentacoes
    no Mes" tem pelo menos UMA linha real de compra/venda -- nao so o cabecalho
    da tabela vazio (que e o que aconteceu com a AXIA3 em fev/2026, mostrado
    pelo Diego). Procura pelos textos literais "Compra à vista"/"Venda à
    vista", que SO aparecem como valor de uma linha de operacao real, nunca
    como cabecalho de coluna -- diferente de "Intermediário", que aparece
    como cabecalho mesmo em tabela vazia.

    Retorna True (tem movimentacao real), False (tabela vazia/sem operacao),
    ou None se nao foi possivel baixar/ler o documento.
    """
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "RADAR/1.0"})
        resp.raise_for_status()
        from pypdf import PdfReader
        leitor = PdfReader(io.BytesIO(resp.content))
        texto = " ".join(pagina.extract_text() or "" for pagina in leitor.pages)
        texto_norm = _sem_acento(texto).lower()
        return any(marcador in texto_norm for marcador in _MARCADORES_MOVIMENTACAO_REAL)
    except Exception:
        return None


def insider_liquido(
    df: pd.DataFrame,
    mapa_tickers: dict,
    tickers: list[str] | None = None,
    meses: int = 6,
    cargos: list[str] | None = None,
    incluir_controlador: bool = False,
) -> pd.DataFrame:
    """
    Fluxo liquido de insiders (compras - vendas, em R$) por ticker nos ultimos
    N meses, considerando apenas Compra/Venda a vista de Acoes/Units.

    mapa_tickers         : dict {TICKER: CNPJ}, normalmente vindo de
                          baixar_mapa_tickers()/carregar_mapa_tickers_local().
                          Cobre QUALQUER ticker listado na B3, nao um universo
                          fixo -- passe os tickers do seu screener (ex: os 40
                          do RADAR) via o parametro `tickers`.
    tickers              : lista de tickers a calcular (default: todos os
                          presentes em mapa_tickers).
    cargos               : lista de Tipo_Cargo a considerar (default: pessoas-chave
                          = Diretoria + Conselho de Administracao).
    incluir_controlador  : se True, adiciona uma coluna separada com o liquido do
                          controlador (que costuma ser estrutural, nao convicao).

    Retorna: ticker, compras_rs, vendas_rs, liquido_rs, n_ops, sinal
             (+ controlador_rs se incluir_controlador=True).
    """
    cargos = cargos or CARGOS_PESSOAS_CHAVE
    tickers = tickers or list(mapa_tickers.keys())
    mapa_filtrado = {t: mapa_tickers[t] for t in tickers if t in mapa_tickers}
    inv = {v: k for k, v in mapa_filtrado.items()}
    alvo = list(mapa_filtrado.values())

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
    for tk in tickers:
        if tk not in mapa_filtrado:
            linhas.append({
                "ticker": tk, "compras_rs": 0.0, "vendas_rs": 0.0,
                "liquido_rs": 0.0, "n_ops": 0,
                **({"controlador_rs": 0.0} if incluir_controlador else {}),
            })
            continue
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
    TICKERS_RADAR = [
        'BBSE3','ITUB4','BBAS3','BBDC3','ABCB4','BRSR6','SANB3','BMGB4','BPAC11','IRBR3',
        'PSSA3','CXSE3','ITSA4','PETR4','VALE3','BRAP4','CMIN3','GGBR3','KLBN4','UNIP6',
        'LEVE3','SHUL4','VULC3','TIMS3','ALOS3','KEPL3','SLCE3','RANI3','CMIG4','CPLE3',
        'EGIE3','TAEE11','ISAE4','CPFE3','SBSP3','SAPR4','CSMG3','AXIA3','B3SA3','BRBI11',
    ]
    mapa = carregar_mapa_tickers_local("/mnt/user-data/uploads/fca_cia_aberta_2026.zip")
    print(f"Mapa ticker->CNPJ: {len(mapa)} tickers cobertos no total")
    faltando = [t for t in TICKERS_RADAR if t not in mapa]
    print(f"Dos 40 do RADAR, faltando: {faltando}")

    df = carregar_local("/mnt/user-data/uploads/vlmo_cia_aberta_2026.zip")
    res = insider_liquido(df, mapa_tickers=mapa, tickers=TICKERS_RADAR, meses=6, incluir_controlador=True)
    pd.options.display.float_format = lambda x: f"{x:,.0f}"
    print(res.to_string(index=False))
