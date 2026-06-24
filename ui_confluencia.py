"""
ui_confluencia.py
=================
Camada visual (Streamlit) do Score de Confluencia.

Funciona para QUALQUER lista de tickers (nao ha universo fixo de 13 nem de
40 -- a lista vem de fora, normalmente da coluna CODIGO do RADAR do Diego).

Duas formas de uso:
  1) render_confluencia(st, tickers, extras=None)            -> tela cheia
  2) render_confluencia_card(st, ticker, tickers_universo, extras=None) ->
     card compacto pra dentro da pagina de detalhe de UM ativo (aba
     Movimentacao).

`tickers_universo` em render_confluencia_card precisa ser a MESMA lista
completa usada na tela cheia, porque a normalizacao do score e relativa ao
universo (o maior valor em R$ do grupo) -- passar so 1 ticker quebraria essa
normalizacao.

`extras` (opcional, em ambas): DataFrame com colunas ['ticker','recompra',
'valuation','dividend_safety'] vindo do RADAR -- quando passado, o Score de
Confluencia passa a usar 5 sinais (insider/controlador da CVM + recompra do
Fundamentus + valuation/dividend safety do RADAR) em vez de so os 2 da CVM.
"""

import datetime
import pandas as pd

try:
    from logica_score import score_confluencia, sinais_cvm, PESOS, data_atualizacao, explicar
    from cvm_insiders import baixar_vlmo, baixar_mapa_tickers
    _DEPS_OK = True
    _ERRO_IMPORT = ""
except Exception as e:
    _DEPS_OK = False
    _ERRO_IMPORT = str(e)


def _cor_score(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return ""
    if v > 5:
        return "background-color: #1b5e20; color: #F1EFE8; font-weight: 700"
    if v < -5:
        return "background-color: #7f1d1d; color: #F1EFE8; font-weight: 700"
    return "background-color: #3a3a3a; color: #dddddd"


def _carregar_cache(st, ano: int):
    """Baixa (com cache de 12h) tanto o arquivo de movimentações (VLMO)
    quanto o mapa ticker->CNPJ (FCA). Os dois são independentes; se um
    falhar, o outro ainda pode funcionar -- por isso ficam em caches
    separados em vez de uma função só."""
    @st.cache_data(ttl=60 * 60 * 12, show_spinner="Baixando dados da CVM (movimentações)...")
    def _vlmo(ano_ref):
        return baixar_vlmo(int(ano_ref))

    @st.cache_data(ttl=60 * 60 * 24, show_spinner="Baixando cadastro de tickers da CVM...")
    def _mapa(ano_ref):
        return baixar_mapa_tickers(int(ano_ref))

    return _vlmo(ano), _mapa(ano)


def _aviso_defasagem(st, df):
    dt_max = data_atualizacao(df)
    if dt_max is None:
        st.warning("Não foi possível determinar a data de atualização dos dados.")
        return
    dias = (pd.Timestamp.today().normalize() - dt_max.normalize()).days
    st.info(
        f"📅 **Dados da CVM atualizados até {dt_max.strftime('%d/%m/%Y')}** "
        f"({dias} dias atrás). As empresas reportam mensalmente e com atraso — "
        f"isso é normal, não é falha do app."
    )


def render_confluencia(st, tickers: list[str], extras: pd.DataFrame | None = None):
    """Tela cheia: ranking de Score de Confluência de todos os `tickers`."""
    st.markdown("#### 🎯 Score de Confluência")
    n_sinais = "5 sinais (CVM + Fundamentus + RADAR)" if extras is not None else "2 sinais (CVM)"
    st.caption(
        f"Sinais cruzados num só número — hoje rodando com {n_sinais}: insiders "
        "(diretoria + conselho, via CVM) e controlador (peso pequeno, via CVM)"
        + (", recompra da própria empresa (via Fundamentus), valuation e dividend "
           "safety (do RADAR)" if extras is not None else "") +
        " — com grau de concordância entre fontes independentes. "
        "Fonte: CVM — Dados Abertos."
    )

    if not _DEPS_OK:
        st.error("Não consegui carregar os módulos do Score (cvm_insiders.py / logica_score.py).")
        st.caption(f"🔧 Detalhe técnico: {_ERRO_IMPORT}")
        return

    ano_atual = datetime.date.today().year
    c1, c2 = st.columns([1, 1])
    with c1:
        ano = st.number_input("Ano de referência", min_value=2021,
                              max_value=ano_atual + 1, value=ano_atual, step=1)
    with c2:
        meses = st.select_slider("Janela (meses)", options=[3, 6, 12], value=6)

    try:
        df, mapa = _carregar_cache(st, int(ano))
    except Exception as e:
        st.error(f"Não consegui baixar os dados da CVM para {int(ano)}: {e}")
        return

    _aviso_defasagem(st, df)

    nao_cobertos = [t for t in tickers if t not in mapa]
    if nao_cobertos:
        st.caption(
            f"⚠️ {len(nao_cobertos)} ticker(s) não encontrados no cadastro atual da "
            f"CVM (podem ter mudado de código ou não negociar mais separadamente): "
            f"{', '.join(nao_cobertos)}"
        )

    try:
        res = score_confluencia(df, mapa, tickers, meses=int(meses), extras=extras)
    except Exception as e:
        st.error(f"Erro ao calcular o score: {e}")
        return

    if res.empty:
        st.info("Sem dados para o período selecionado.")
        return

    res = res.copy()
    res["Resumo em português"] = res.apply(explicar, axis=1)
    res_show = res.rename(columns={
        "ticker": "Ticker", "score": "Score", "concordancia": "Concordância",
    })[["Ticker", "Score", "Concordância", "Resumo em português"]]

    st.dataframe(
        res_show.style.map(_cor_score, subset=["Score"]),
        use_container_width=True, hide_index=True,
    )

    with st.expander("Como ler / valores brutos por papel (R$)"):
        st.markdown(
            "- **Score** (−100 a +100): soma ponderada dos sinais.\n"
            "- **Concordância** X/N: quantos sinais apontam no mesmo sentido. "
            "X/N iguais = todos concordam (mais confiável); X menor que N = sinais em conflito.\n"
            "- **0/0**: nenhuma movimentação de insider/controlador/recompra no período "
            "(não é erro — é ausência real de dado).\n"
            "- **Insider e controlador** vêm da CVM (Dados Abertos). **Recompra** vem do "
            "Fundamentus — o arquivo aberto da CVM usado aqui só cobre negociação de "
            "pessoas (Art. 11), não recompra de tesouraria.\n"
            "- **Recompra negativa**: significa que a empresa *vendeu* ações de tesouraria de "
            "volta ao mercado — **não** é cancelamento de ações. Cancelamento é um evento "
            "corporativo diferente, reportado em outro lugar (Fato Relevante/Assembleia)."
        )
        st.write("Pesos:", PESOS)
        st.dataframe(sinais_cvm(df, mapa, tickers, meses=int(meses)),
                    use_container_width=True, hide_index=True)


def obter_score_resumido(st, ticker: str, tickers_universo: list[str], meses: int = 6,
                          ano: int | None = None, extras: pd.DataFrame | None = None):
    """
    Versão "sem desenho" do Score de Confluência -- devolve só os números,
    pra usar em resumos/cards compactos (ex: aba Visão Geral) sem duplicar
    o card cheio. Retorna dict {'score', 'concordancia', 'resumo'} ou None
    se não houver dados/erro.
    """
    if not _DEPS_OK:
        return None
    ano = ano or datetime.date.today().year
    try:
        df, mapa = _carregar_cache(st, int(ano))
        if ticker.upper() not in mapa:
            return None
        res = score_confluencia(df, mapa, tickers_universo, meses=int(meses), extras=extras)
    except Exception:
        return None
    linha = res[res["ticker"] == ticker.upper()]
    if linha.empty:
        return None
    row = linha.iloc[0]
    return {"score": row["score"], "concordancia": row["concordancia"], "resumo": explicar(row)}


def render_confluencia_card(
    st, ticker: str, tickers_universo: list[str],
    meses: int = 6, ano: int | None = None,
    extras: pd.DataFrame | None = None,
):
    """
    Card compacto pra dentro da pagina de detalhe de UM ativo.

    tickers_universo: a lista COMPLETA de tickers do RADAR (ex: df['CÓDIGO']),
    necessaria pra normalizar o score corretamente -- nao passar so [ticker].
    """
    if not _DEPS_OK:
        st.caption(f"🔧 Score de Confluência indisponível: {_ERRO_IMPORT}")
        return

    ano = ano or datetime.date.today().year
    try:
        df, mapa = _carregar_cache(st, int(ano))
        res = score_confluencia(df, mapa, tickers_universo, meses=int(meses), extras=extras)
    except Exception as e:
        st.caption(f"🔧 Não consegui calcular o Score de Confluência: {e}")
        return

    linha = res[res["ticker"] == ticker.upper()]
    dt_max = data_atualizacao(df)
    data_str = dt_max.strftime("%d/%m/%Y") if dt_max is not None else "—"

    if ticker.upper() not in mapa:
        st.markdown(
            "<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.12);"
            "border-radius:10px;padding:14px 16px;'>"
            "<div style='font-size:0.78em;color:#ccc;font-weight:600;text-transform:uppercase;"
            "margin-bottom:6px;'>🎯 Score de Confluência</div>"
            f"<div style='font-size:0.85em;color:#888;'>Ticker '{ticker}' não encontrado no "
            "cadastro atual da CVM (pode ter mudado de código).</div>"
            "</div>", unsafe_allow_html=True
        )
        return

    if linha.empty:
        st.markdown(
            "<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.12);"
            "border-radius:10px;padding:14px 16px;'>"
            "<div style='font-size:0.78em;color:#ccc;font-weight:600;text-transform:uppercase;"
            "margin-bottom:6px;'>🎯 Score de Confluência</div>"
            "<div style='font-size:0.85em;color:#888;'>Sem dados para este ativo no período.</div>"
            "</div>", unsafe_allow_html=True
        )
        return

    row = linha.iloc[0]
    score = row["score"]
    cor = "#4CAF6D" if score > 5 else ("#D9534F" if score < -5 else "#aaaaaa")
    resumo = explicar(row)
    n_sinais_txt = " (com recompra, valuation e dividend safety)" if extras is not None else ""

    # ---- Contexto de posição: "32,4" sozinho nao diz nada pra ninguem,
    # nem pra quem usa o app todo dia. Mostra onde esse score fica relativo
    # aos outros ativos do RADAR HOJE (a escala -100/+100 e relativa ao
    # universo, nao um teto fixo -- por isso a posicao importa mais que o
    # numero absoluto).
    total_ativos = len(res)
    posicao = int((res["score"] > score).sum()) + 1
    if score > 0:
        pos_txt = f"{posicao}º maior score de {total_ativos} ativos do RADAR hoje"
    elif score < 0:
        posicao_neg = int((res["score"] < score).sum()) + 1
        pos_txt = f"{posicao_neg}º menor score de {total_ativos} ativos do RADAR hoje"
    else:
        pos_txt = f"score neutro entre {total_ativos} ativos do RADAR hoje"

    # Barra visual: posição RELATIVA aos ativos de hoje (0% = pior score do
    # dia, 100% = melhor) -- não uma escala fixa -100/+100, que na prática
    # quase nunca é alcançada nos dois extremos ao mesmo tempo (precisaria
    # de um ativo no máximo absoluto em TODOS os sinais simultaneamente).
    # Assim os dois extremos da barra são sempre alcançáveis, porque são
    # definidos pelos próprios dados de hoje, não por um teto teórico.
    if total_ativos > 1:
        pct_pos = (total_ativos - posicao) / (total_ativos - 1) * 100
    else:
        pct_pos = 50
    pct_pos = max(2, min(98, pct_pos))   # nunca cola na borda visualmente
    barra_html = (
        "<div style='position:relative;height:8px;background:linear-gradient(to right,"
        "#3a3a3a 0%,#5B8DB8 50%,#D4AF37 100%);border-radius:4px;margin:8px 0 4px 0;'>"
        f"<div style='position:absolute;left:{pct_pos}%;top:-3px;width:3px;height:14px;"
        f"background:#F1EFE8;border-radius:1px;transform:translateX(-50%);'></div>"
        "</div>"
        "<div style='display:flex;justify-content:space-between;font-size:0.65em;color:#888;'>"
        f"<span>Pior do dia</span><span>Melhor do dia</span></div>"
    )

    st.markdown(
        "<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.12);"
        "border-radius:10px;padding:14px 16px;'>"
        f"<div style='font-size:0.78em;color:#ccc;font-weight:600;text-transform:uppercase;"
        f"margin-bottom:8px;'>🎯 Score de Confluência{n_sinais_txt}</div>"
        f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:6px;'>"
        f"<span style='font-size:1.5em;font-weight:900;color:{cor};'>{score:.1f}</span>"
        f"<span style='font-size:0.85em;color:#ccc;'>Concordância: {row['concordancia']}</span>"
        "</div>"
        f"{barra_html}"
        f"<div style='font-size:0.78em;color:{cor};font-weight:700;margin:6px 0 8px 0;'>{pos_txt}</div>"
        f"<div style='font-size:0.85em;color:#ddd;line-height:1.5;'>{resumo}</div>"
        f"<div style='font-size:0.72em;color:#888;margin-top:8px;'>📅 Dados da CVM até {data_str} "
        f"(insiders reportam mensalmente, com atraso de algumas semanas)</div>"
        "</div>", unsafe_allow_html=True
    )
