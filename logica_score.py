"""
logica_score.py
===============
Score de Confluencia do RADAR.

Ideia central (o diferencial): em vez de um numero so, produz DOIS:
  1) SCORE        -> soma ponderada dos sinais, em [-100, +100] (direcao+forca)
  2) CONCORDANCIA -> quantos sinais independentes apontam no mesmo sentido (robustez)

Um score +60 com 4/4 sinais concordando vale muito mais que um +60 puxado por
um unico sinal extremo. Nenhum concorrente mostra a concordancia.

Sinais que vem REAIS do arquivo da CVM (via cvm_insiders):
  - insider_pessoas  (Diretoria + Conselho de Administracao)   peso alto
  - recompra         (a propria Companhia comprando/vendendo)  peso medio
  - controlador      (estrutural)                              peso PEQUENO

Sinais que entram quando voce plugar o RADAR (opcionais):
  - valuation        (desconto vs preco justo; +=barato)
  - dividend_safety  (0-10 do RADAR)
"""

import pandas as pd

from cvm_insiders import (
    carregar_local, baixar_vlmo, carregar_mapa_tickers_local, baixar_mapa_tickers,
    CARGOS_PESSOAS_CHAVE, CARGO_CONTROLADOR, MOV_COMPRA, MOV_VENDA, ATIVOS_ACAO,
)

PESOS = {
    "insider_pessoas": 0.35,
    "recompra":        0.25,
    "valuation":       0.20,
    "dividend_safety": 0.15,
    "controlador":     0.05,   # peso pequeno, conforme decidido
}


def _liq(sub):
    compra = sub["vol"].where(sub["Tipo_Movimentacao"] == MOV_COMPRA, 0).sum()
    venda = sub["vol"].where(sub["Tipo_Movimentacao"] == MOV_VENDA, 0).sum()
    return compra - venda


def sinais_cvm(df: pd.DataFrame, mapa_tickers: dict, tickers: list[str], meses: int = 6) -> pd.DataFrame:
    """
    Extrai os 3 sinais (em R$) do arquivo da CVM, por ticker.

    mapa_tickers: dict {TICKER: CNPJ}, normalmente de baixar_mapa_tickers().
    tickers     : lista de tickers a calcular (ex: os do RADAR do Diego --
                  QUALQUER lista funciona, nao ha universo fixo).
    """
    mapa_filtrado = {t: mapa_tickers[t] for t in tickers if t in mapa_tickers}
    inv = {v: k for k, v in mapa_filtrado.items()}
    d = df[df["CNPJ_Companhia"].isin(mapa_filtrado.values())].copy()
    d["ticker"] = d["CNPJ_Companhia"].map(inv)
    d["vol"] = pd.to_numeric(d["Volume"], errors="coerce")
    d["dt"] = pd.to_datetime(d["Data_Movimentacao"], errors="coerce", format="%Y-%m-%d")
    corte = pd.Timestamp.today() - pd.DateOffset(months=meses)
    d = d[(d["dt"] >= corte) & (d["Tipo_Movimentacao"].isin([MOV_COMPRA, MOV_VENDA]))
          & (d["Tipo_Ativo"].isin(ATIVOS_ACAO))]

    linhas = []
    for tk in tickers:
        sub = d[d["ticker"] == tk]
        linhas.append({
            "ticker": tk,
            "insider_pessoas": _liq(sub[sub["Tipo_Cargo"].isin(CARGOS_PESSOAS_CHAVE)]) if tk in mapa_filtrado else 0.0,
            "controlador":     _liq(sub[sub["Tipo_Cargo"] == CARGO_CONTROLADOR]) if tk in mapa_filtrado else 0.0,
            "recompra":        _liq(sub[sub["Tipo_Empresa"] == "Companhia"]) if tk in mapa_filtrado else 0.0,
        })
    return pd.DataFrame(linhas)


def _norm_simetrica(serie: pd.Series) -> pd.Series:
    """Normaliza para [-1,+1] dividindo pelo maior valor absoluto do universo."""
    m = serie.abs().max()
    return serie / m if m and m > 0 else serie * 0.0


def data_atualizacao(df_cvm: pd.DataFrame) -> pd.Timestamp | None:
    """
    Data mais recente de movimentação efetivamente presente no arquivo da CVM.
    Mostrar isso na tela é essencial: o arquivo e atualizado semanalmente, mas
    os INFORMES sao mensais e chegam com algumas semanas de atraso -> a data
    mais recente quase nunca e "hoje".
    """
    dt = pd.to_datetime(df_cvm["Data_Movimentacao"], errors="coerce", format="%Y-%m-%d")
    return dt.max() if dt.notna().any() else None


def explicar(row: pd.Series) -> str:
    """
    Traduz uma linha do resultado de score_confluencia() para uma frase em
    portugues simples, sem siglas nem numeros tecnicos. E a "tradução" que
    precisa aparecer DENTRO da tela, nao so explicada em conversa.
    """
    detalhe = str(row.get("detalhe", "") or "")
    if not detalhe:
        return "Nenhuma movimentação de insider, controlador ou recompra registrada no período."

    partes = [p.strip() for p in detalhe.split(",")]
    frases = []
    for p in partes:
        if p.startswith("insider+"):
            frases.append("a diretoria/conselho está comprando")
        elif p.startswith("insider-"):
            frases.append("a diretoria/conselho está vendendo")
        elif p.startswith("recompra+"):
            frases.append("a empresa está recomprando suas próprias ações")
        elif p.startswith("recompra-"):
            frases.append("a empresa está reduzindo ações em tesouraria")
        elif p.startswith("controlador+"):
            frases.append("o controlador está comprando (peso pequeno no score)")
        elif p.startswith("controlador-"):
            frases.append("o controlador está vendendo (peso pequeno no score)")
        elif p.startswith("valuation+"):
            frases.append("está com desconto no valuation")
        elif p.startswith("valuation-"):
            frases.append("está caro no valuation")
        elif p.startswith("dividend+"):
            frases.append("tem dividendo seguro")

    if len(frases) == 1:
        corpo = frases[0]
    else:
        corpo = ", ".join(frases[:-1]) + " e " + frases[-1]

    conc = str(row.get("concordancia", "0/0"))
    try:
        usados, total = (int(x) for x in conc.split("/"))
    except ValueError:
        usados, total = 0, 0

    if total == 0:
        forca = ""
    elif usados == total and total >= 2:
        forca = " — sinal de confiança forte, todos os sinais concordam."
    elif usados == total:
        forca = " — sinal consistente."
    else:
        forca = f" — leitura ambígua, os sinais não concordam entre si ({conc})."

    return f"Resumo: {corpo}{forca}"



def score_confluencia(
    df_cvm: pd.DataFrame,
    mapa_tickers: dict,
    tickers: list[str],
    meses: int = 6,
    extras: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Calcula Score de Confluencia + Concordancia por ticker.

    mapa_tickers: dict {TICKER: CNPJ}, de baixar_mapa_tickers(). Cobre
                  qualquer ticker da B3 -- nao ha lista fixa.
    tickers     : lista de tickers a calcular (ex: os ~40 do RADAR do Diego,
                  vindos direto da planilha dele -- sempre em sincronia).
    extras: DataFrame opcional do RADAR com colunas ['ticker','valuation',
            'dividend_safety']. valuation ja em [-1,+1] (+=desconto);
            dividend_safety em 0-10. Sinais ausentes sao ignorados e os pesos
            renormalizados entre os presentes.
    """
    base = sinais_cvm(df_cvm, mapa_tickers, tickers, meses=meses)

    # normaliza os 3 sinais monetarios para [-1,+1]
    comp = pd.DataFrame({"ticker": base["ticker"]})
    comp["insider_pessoas"] = _norm_simetrica(base["insider_pessoas"])
    comp["controlador"] = _norm_simetrica(base["controlador"])
    comp["recompra"] = _norm_simetrica(base["recompra"])

    # sinais do RADAR (se vierem)
    if extras is not None:
        comp = comp.merge(extras, on="ticker", how="left")
        if "dividend_safety" in comp:
            comp["dividend_safety"] = comp["dividend_safety"] / 10 * 2 - 1  # 0-10 -> [-1,1]
        if "valuation" in comp:
            comp["valuation"] = comp["valuation"].clip(-1, 1)

    sinais_presentes = [s for s in PESOS if s in comp.columns]

    def _linha(row):
        usados = {s: row[s] for s in sinais_presentes if pd.notna(row[s]) and row[s] != 0}
        if not usados:
            return pd.Series({"score": 0.0, "concordancia": "0/0", "detalhe": ""})
        peso_total = sum(PESOS[s] for s in usados)
        score = sum(PESOS[s] * row[s] for s in usados) / peso_total  # [-1,+1]
        direcao = 1 if score > 0 else -1
        concordam = sum(1 for s, v in usados.items() if (v > 0) == (direcao > 0))
        det = ", ".join(
            f"{s.split('_')[0]}{'+' if row[s] > 0 else '-'}" for s in usados
        )
        return pd.Series({
            "score": round(score * 100, 1),
            "concordancia": f"{concordam}/{len(usados)}",
            "detalhe": det,
        })

    res = comp.join(comp.apply(_linha, axis=1))
    return res[["ticker", "score", "concordancia", "detalhe"]].sort_values(
        "score", ascending=False
    ).reset_index(drop=True)


if __name__ == "__main__":
    TICKERS_RADAR = [
        'BBSE3','ITUB4','BBAS3','BBDC3','ABCB4','BRSR6','SANB3','BMGB4','BPAC11','IRBR3',
        'PSSA3','CXSE3','ITSA4','PETR4','VALE3','BRAP4','CMIN3','GGBR3','KLBN4','UNIP6',
        'LEVE3','SHUL4','VULC3','TIMS3','ALOS3','KEPL3','SLCE3','RANI3','CMIG4','CPLE3',
        'EGIE3','TAEE11','ISAE4','CPFE3','SBSP3','SAPR4','CSMG3','AXIA3','B3SA3','BRBI11',
    ]
    mapa = carregar_mapa_tickers_local("/mnt/user-data/uploads/fca_cia_aberta_2026.zip")
    df = carregar_local("/mnt/user-data/uploads/vlmo_cia_aberta_2026.zip")

    print("=== SCORE DE CONFLUENCIA — 40 ATIVOS DO RADAR (so sinais da CVM, 6 meses) ===\n")
    res = score_confluencia(df, mapa, TICKERS_RADAR, meses=6)
    print(res.to_string(index=False))
    print(f"\nData de atualização do dado: {data_atualizacao(df)}")

    print("\n\n=== COM EXPLICAÇÃO EM PORTUGUÊS (5 primeiras linhas) ===\n")
    for _, row in res.head(5).iterrows():
        print(f"{row['ticker']:8} | score={row['score']:>6} | {row['concordancia']:>4} | {explicar(row)}")

    # exemplo de como ficaria PLUGANDO 2 sinais do RADAR (valuation + DY):
    extras = pd.DataFrame({
        "ticker": ["PETR4", "VALE3", "BBAS3", "ITUB4", "BBDC3"],
        "valuation": [0.30, 0.10, 0.45, -0.20, 0.05],     # +=desconto vs preco justo
        "dividend_safety": [7, 6, 9, 8, 7],                # 0-10 do RADAR
    })
    print("\n\n=== COM 2 SINAIS DO RADAR PLUGADOS (exemplo p/ 5 papeis) ===\n")
    print(score_confluencia(df, mapa, TICKERS_RADAR, meses=6, extras=extras).head(10).to_string(index=False))
