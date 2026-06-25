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
  - controlador      (estrutural)                              peso PEQUENO

IMPORTANTE: o arquivo VLMO da CVM (Art. 11) NAO contem recompra de acoes pela
propria empresa -- ele e exclusivamente sobre negociacao de PESSOAS (insiders).
Tentamos extrair recompra dali via "Tipo_Empresa == Companhia" e descobrimos
que esse campo so distingue se o informe e sobre a companhia, uma controladora
ou uma controlada -- nao quem fez a transacao. Confirmado contra o dataset
inteiro: das ~24 mil linhas, todas tem cargo de pessoa (Diretor/Conselho/
Controlador/Conselho Fiscal); as poucas sem cargo sao "Saldo Inicial"/"Posse"
com quantidade zero, nao recompra real.

Por isso, recompra agora vem de FORA (via `extras`), do Fundamentus (que ja
distingue "Companhia - Tesouraria" no formulario individual da CVM, dado que
o CSV aberto nao expoe). Isso faz a Concordancia cruzar duas FONTES DE
VERDADE diferentes (CVM + Fundamentus), nao uma fonte disfarçada de duas.

POR QUE NAO TEM MAIS VALUATION NEM DIVIDEND SAFETY: esse score e sobre
MOVIMENTACAO -- quem esta comprando/vendendo (insiders, controlador, a
propria empresa). Valuation (quanto custa o papel) e dividend safety (quao
seguro e o dividendo) sao dimensoes DIFERENTES, sem relacao causal com quem
esta comprando/vendendo -- misturar tudo numa "concordancia" so confundia a
leitura sem ganho real de sinal (a pedido do Diego, 24/06).

Sinais que entram via `extras` (vindos do RADAR):
  - recompra         (Fundamentus -- liquido de recompra em R$, mesma janela)
"""

import pandas as pd

from cvm_insiders import (
    carregar_local, baixar_vlmo, carregar_mapa_tickers_local, baixar_mapa_tickers,
    CARGOS_PESSOAS_CHAVE, CARGO_CONTROLADOR, MOV_COMPRA, MOV_VENDA, ATIVOS_ACAO,
)

PESOS = {
    "insider_pessoas": 0.55,
    "recompra":        0.35,
    "controlador":     0.10,   # peso pequeno, conforme decidido
}


def _liq(sub):
    compra = sub["vol"].where(sub["Tipo_Movimentacao"] == MOV_COMPRA, 0).sum()
    venda = sub["vol"].where(sub["Tipo_Movimentacao"] == MOV_VENDA, 0).sum()
    return compra - venda


def sinais_cvm(df: pd.DataFrame, mapa_tickers: dict, tickers: list[str], meses: int = 6) -> pd.DataFrame:
    """
    Extrai os 2 sinais REAIS de pessoas (insider_pessoas, controlador) do
    arquivo da CVM, por ticker. Recompra NAO vem daqui (ver nota no topo do
    arquivo) -- entra via `extras` em score_confluencia().

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

    Quando os sinais NAO concordam, agrupa explicitamente quem aponta pra
    cada lado -- listar so os fatos em sequencia (sem dizer qual e otimista
    e qual e pessimista) obriga quem le a decifrar a direcao de cada um por
    conta propria, o que gerou confusao real.
    """
    detalhe = str(row.get("detalhe", "") or "")
    if not detalhe:
        return "Nenhuma movimentação de insider, controlador ou recompra registrada no período."

    _FRASES = {
        "insider+": "diretoria/conselho comprando",
        "insider-": "diretoria/conselho vendendo",
        "recompra+": "empresa recomprando ações",
        "recompra-": "empresa vendeu ações de tesouraria de volta ao mercado (não é cancelamento)",
        "controlador+": "controlador comprando (peso pequeno)",
        "controlador-": "controlador vendendo (peso pequeno)",
    }

    partes = [p.strip() for p in detalhe.split(",")]
    alta, baixa = [], []
    for p in partes:
        texto = _FRASES.get(p)
        if texto is None:
            continue
        (baixa if p.endswith("-") else alta).append(texto)

    conc = str(row.get("concordancia", "0/0"))
    try:
        usados, total = (int(x) for x in conc.split("/"))
    except ValueError:
        usados, total = 0, 0

    # Todos os sinais concordam -> frase unica, sem precisar separar grupos
    if total >= 1 and usados == total:
        todos = alta + baixa
        # Direcao vem da lista REAL (alta tem item = compra), nao do sinal
        # do score arredondado -- um score pequeno como -0.04 arredonda pra
        # exibicao como "-0.0", e em Python "-0.0 < 0" e False, o que
        # invertia a leitura (dizia "compra" quando o sinal real era venda).
        direcao_txt = "compra" if alta else "venda"
        corpo = todos[0] if len(todos) == 1 else ", ".join(todos[:-1]) + " e " + todos[-1]
        # Sem "forte"/"fraco" aqui -- essa intensidade vinha do score
        # normalizado pelo maior movimento do universo, que e instavel (o
        # mesmo movimento de um ticker pode "parecer" forte ou fraco so
        # porque outro ticker teve um pico no mes, sem nada ter mudado no
        # primeiro). So o fato: direcao + quantos sinais concordam.
        if total >= 2:
            return f"Resumo: {corpo} — os {total} sinais disponíveis apontam para {direcao_txt}."
        return f"Resumo: {corpo}."

    # Sinais em conflito -> agrupa explicitamente quem aponta pra cada lado
    if alta and baixa:
        txt_alta = alta[0] if len(alta) == 1 else ", ".join(alta[:-1]) + " e " + alta[-1]
        txt_baixa = baixa[0] if len(baixa) == 1 else ", ".join(baixa[:-1]) + " e " + baixa[-1]
        return (
            f"Sinais de alta ({len(alta)}): {txt_alta}. "
            f"Sinais de baixa ({len(baixa)}): {txt_baixa}. "
            f"Como não concordam entre si ({conc}), a leitura é ambígua."
        )

    return "Nenhuma movimentação de insider, controlador ou recompra registrada no período."



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
    extras: DataFrame opcional com coluna ['ticker','recompra'] -- recompra
            em R$ (líquido compra-venda, via Fundamentus, normalizada aqui
            igual aos sinais da CVM). Sem extras, o score usa só os 2 sinais
            da CVM (insider_pessoas + controlador).
    """
    base = sinais_cvm(df_cvm, mapa_tickers, tickers, meses=meses)

    # normaliza os 2 sinais monetarios da CVM para [-1,+1]
    comp = pd.DataFrame({"ticker": base["ticker"]})
    comp["insider_pessoas"] = _norm_simetrica(base["insider_pessoas"])
    comp["controlador"] = _norm_simetrica(base["controlador"])

    # recompra (Fundamentus, em R$) entra via extras e e normalizada do
    # mesmo jeito que os sinais da CVM (simetrica, por maior valor absoluto
    # do universo).
    if extras is not None:
        comp = comp.merge(extras, on="ticker", how="left")
        if "recompra" in comp:
            comp["recompra"] = _norm_simetrica(comp["recompra"])

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

    # exemplo de como ficaria PLUGANDO a recompra do Fundamentus:
    extras = pd.DataFrame({
        "ticker": ["PETR4", "VALE3", "BBAS3", "ITUB4", "BBDC3"],
        "recompra": [0, 1_000_000, 0, -500_000, 0],        # liquido R$ via Fundamentus
    })
    print("\n\n=== COM RECOMPRA DO FUNDAMENTUS PLUGADA (exemplo p/ 5 papeis) ===\n")
    print(score_confluencia(df, mapa, TICKERS_RADAR, meses=6, extras=extras).head(10).to_string(index=False))
