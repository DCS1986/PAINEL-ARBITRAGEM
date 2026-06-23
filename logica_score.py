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
    carregar_local, baixar_vlmo, MAPA_TICKER_CNPJ,
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


def sinais_cvm(df: pd.DataFrame, meses: int = 6) -> pd.DataFrame:
    """Extrai os 3 sinais (em R$) do arquivo da CVM, por ticker."""
    inv = {v: k for k, v in MAPA_TICKER_CNPJ.items()}
    d = df[df["CNPJ_Companhia"].isin(MAPA_TICKER_CNPJ.values())].copy()
    d["ticker"] = d["CNPJ_Companhia"].map(inv)
    d["vol"] = pd.to_numeric(d["Volume"], errors="coerce")
    d["dt"] = pd.to_datetime(d["Data_Movimentacao"], errors="coerce", format="%Y-%m-%d")
    corte = pd.Timestamp.today() - pd.DateOffset(months=meses)
    d = d[(d["dt"] >= corte) & (d["Tipo_Movimentacao"].isin([MOV_COMPRA, MOV_VENDA]))
          & (d["Tipo_Ativo"].isin(ATIVOS_ACAO))]

    linhas = []
    for tk in MAPA_TICKER_CNPJ:
        sub = d[d["ticker"] == tk]
        linhas.append({
            "ticker": tk,
            "insider_pessoas": _liq(sub[sub["Tipo_Cargo"].isin(CARGOS_PESSOAS_CHAVE)]),
            "controlador":     _liq(sub[sub["Tipo_Cargo"] == CARGO_CONTROLADOR]),
            "recompra":        _liq(sub[sub["Tipo_Empresa"] == "Companhia"]),
        })
    return pd.DataFrame(linhas)


def _norm_simetrica(serie: pd.Series) -> pd.Series:
    """Normaliza para [-1,+1] dividindo pelo maior valor absoluto do universo."""
    m = serie.abs().max()
    return serie / m if m and m > 0 else serie * 0.0


def score_confluencia(
    df_cvm: pd.DataFrame,
    meses: int = 6,
    extras: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Calcula Score de Confluencia + Concordancia por ticker.

    extras: DataFrame opcional do RADAR com colunas ['ticker','valuation',
            'dividend_safety']. valuation ja em [-1,+1] (+=desconto);
            dividend_safety em 0-10. Sinais ausentes sao ignorados e os pesos
            renormalizados entre os presentes.
    """
    base = sinais_cvm(df_cvm, meses=meses)

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
    df = carregar_local("/mnt/user-data/uploads/vlmo_cia_aberta_2026.zip")
    print("=== SCORE DE CONFLUENCIA (so sinais reais da CVM, 6 meses) ===\n")
    print(score_confluencia(df, meses=6).to_string(index=False))

    # exemplo de como ficaria PLUGANDO 2 sinais do RADAR (valuation + DY):
    extras = pd.DataFrame({
        "ticker": ["PETR4", "VALE3", "BBAS3", "ITUB4", "BBDC4"],
        "valuation": [0.30, 0.10, 0.45, -0.20, 0.05],     # +=desconto vs preco justo
        "dividend_safety": [7, 6, 9, 8, 7],                # 0-10 do RADAR
    })
    print("\n\n=== COM 2 SINAIS DO RADAR PLUGADOS (exemplo p/ 5 papeis) ===\n")
    print(score_confluencia(df, meses=6, extras=extras).to_string(index=False))
