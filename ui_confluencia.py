"""
ui_confluencia.py
=================
Camada visual (Streamlit) do Score de Confluencia.

Funciona para QUALQUER lista de tickers (nao ha universo fixo de 13 nem de
40 -- a lista vem de fora, normalmente da coluna CODIGO do RADAR do Diego).

Duas formas de uso:
  1) render_confluencia(st, tickers, extras=None, programas=None) -> tela cheia
  2) render_confluencia_card(st, ticker, tickers_universo, extras=None) ->
     card compacto pra dentro da pagina de detalhe de UM ativo (aba
     Movimentacao).

`tickers_universo` em render_confluencia_card precisa ser a MESMA lista
completa usada na tela cheia, porque a normalizacao do score e relativa ao
universo (o maior valor em R$ do grupo) -- passar so 1 ticker quebraria essa
normalizacao.

Esse score e sobre MOVIMENTACAO -- quem esta comprando/vendendo (insiders,
controlador, a propria empresa). Valuation e dividend safety SAIRAM daqui
(eram dimensoes sem relacao causal com movimentacao, so confundiam a leitura
-- a pedido do Diego, 24/06).

`extras` (opcional, em ambas): DataFrame com coluna ['ticker','recompra']
vindo do RADAR (Fundamentus) -- quando passado, o Score de Confluencia passa
a usar 3 sinais (insider/controlador da CVM + recompra do Fundamentus) em
vez de so os 2 da CVM.

`programas` (opcional, so na tela cheia): dict {CNPJ: dict-do-programa} de
programa_recompra_ativo() pra cada ticker -- mostra uma coluna extra na
tabela com quem tem Programa de Recompra EM ANDAMENTO (autorizacao, nao
execucao -- ver cvm_insiders.py).
"""

import datetime
import pandas as pd

try:
    from logica_score import score_confluencia, sinais_cvm, PESOS, data_atualizacao, explicar
    from cvm_insiders import baixar_vlmo, baixar_mapa_tickers, programa_recompra_ativo
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


def render_confluencia(st, tickers: list[str], extras: pd.DataFrame | None = None,
                       df_programas: pd.DataFrame | None = None):
    """Tela cheia: ranking de Score de Confluência de todos os `tickers`.

    df_programas: DataFrame de baixar_programa_recompra() (Programa de
    Recompra EM ANDAMENTO -- autorização, não execução). Se passado, mostra
    uma coluna extra na tabela."""
    st.markdown("#### 🎯 Score de Confluência")
    n_sinais = "3 sinais (CVM + Fundamentus)" if extras is not None else "2 sinais (CVM)"
    st.caption(
        f"Sinais de movimentação cruzados num só número — hoje rodando com {n_sinais}: "
        "insiders (diretoria + conselho, via CVM) e controlador (peso pequeno, via CVM)"
        + (", recompra da própria empresa (via Fundamentus)" if extras is not None else "") +
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

    if df_programas is not None:
        def _prog_txt(ticker):
            cnpj = mapa.get(ticker)
            prog = programa_recompra_ativo(df_programas, cnpj) if cnpj else None
            if not prog:
                return "—"
            return f"✅ até {prog['data_final'].strftime('%m/%Y')}"
        res["Programa de Recompra"] = res["ticker"].apply(_prog_txt)
        cols_show = ["ticker", "score", "concordancia", "Programa de Recompra", "Resumo em português"]
        cols_renome = {"ticker": "Ticker", "score": "Score", "concordancia": "Concordância"}
    else:
        cols_show = ["ticker", "score", "concordancia", "Resumo em português"]
        cols_renome = {"ticker": "Ticker", "score": "Score", "concordancia": "Concordância"}

    res_show = res.rename(columns=cols_renome)[[cols_renome.get(c, c) for c in cols_show]]

    st.dataframe(
        res_show.style.map(_cor_score, subset=["Score"]),
        use_container_width=True, hide_index=True,
    )

    with st.expander("Como ler / valores brutos por papel (R$)"):
        st.markdown(
            "- **Score** (−100 a +100): soma ponderada dos sinais de movimentação.\n"
            "- **Concordância** X/N: quantos sinais apontam no mesmo sentido. "
            "X/N iguais = todos concordam (mais confiável); X menor que N = sinais em conflito.\n"
            "- **0/0**: nenhuma movimentação de insider/controlador/recompra no período "
            "(não é erro — é ausência real de dado).\n"
            "- **Insider e controlador** vêm da CVM (Dados Abertos). **Recompra** vem do "
            "Fundamentus — o arquivo aberto da CVM usado aqui só cobre negociação de "
            "pessoas (Art. 11), não recompra de tesouraria.\n"
            "- **Recompra negativa**: significa que a empresa *vendeu* ações de tesouraria de "
            "volta ao mercado — **não** é cancelamento de ações.\n"
            "- **Programa de Recompra**: autorização do conselho em vigor pra recomprar até "
            "uma data — não é execução (quanto já foi comprado de fato). Dataset separado e "
            "dedicado da CVM, atualizado diariamente."
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
    resumo = explicar(row)
    n_sinais_txt = ""

    # SEM número combinado, SEM comparação com outros tickers -- um score
    # normalizado pelo maior movimento do universo (ex: a compra gigante da
    # AXIA3) faz o MESMO movimento da PETR4 valer -15 hoje e -60 no mês que
    # vem, sem a PETR4 ter feito nada diferente -- numero instavel, ilude
    # mais do que ajuda. Em vez disso: um selo por sinal (Insider/
    # Controlador/Recompra), colorido pra compra ou venda -- mostra
    # concordancia ou divergencia sem nenhuma conta, sem comparar com nada.
    _LABELS_SINAL = {"insider": "Insider", "controlador": "Controlador", "recompra": "Recompra"}
    detalhe = str(row.get("detalhe", "") or "")
    selos_html = ""
    for p in [x.strip() for x in detalhe.split(",") if x.strip()]:
        chave, sinal = p[:-1], p[-1]
        label = _LABELS_SINAL.get(chave, chave)
        cor_selo = "#4CAF6D" if sinal == "+" else "#D9534F"
        icone = "▲" if sinal == "+" else "▼"
        selos_html += (
            f"<span style='display:inline-flex;align-items:center;gap:4px;"
            f"background:{cor_selo}22;border:1px solid {cor_selo};color:{cor_selo};"
            f"border-radius:14px;padding:4px 10px;font-size:0.78em;font-weight:700;'>"
            f"{icone} {label}</span>"
        )
    selos_div = f"<div style='display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;'>{selos_html}</div>" if selos_html else ""

    st.markdown(
        "<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.12);"
        "border-radius:10px;padding:14px 16px;'>"
        f"<div style='font-size:0.78em;color:#ccc;font-weight:600;text-transform:uppercase;"
        f"margin-bottom:8px;'>🎯 Sinais de Movimentação{n_sinais_txt}</div>"
        f"{selos_div}"
        f"<div style='font-size:0.78em;color:#ccc;margin-bottom:6px;'>Concordância: {row['concordancia']}</div>"
        f"<div style='font-size:0.85em;color:#ddd;line-height:1.5;'>{resumo}</div>"
        f"<div style='font-size:0.72em;color:#888;margin-top:8px;'>📅 Dados da CVM até {data_str} "
        f"(insiders reportam mensalmente, com atraso de algumas semanas)</div>"
        "</div>", unsafe_allow_html=True
    )
