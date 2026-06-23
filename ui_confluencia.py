"""
ui_confluencia.py
=================
Camada visual (Streamlit) do Score de Confluencia.

Duas formas de uso:
  1) render_confluencia(st)        -> tela cheia (ranking de todos os ativos)
  2) render_confluencia_card(st, ticker, meses=6) -> card compacto pra dentro
     da pagina de detalhe de UM ativo (aba Movimentacao, junto com Insiders
     e Recompras que ja existem la).
"""

import datetime
import pandas as pd

try:
    from logica_score import score_confluencia, sinais_cvm, PESOS, data_atualizacao, explicar
    from cvm_insiders import baixar_vlmo
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
        return "background-color: #1b5e20; color: #ffffff; font-weight: 700"
    if v < -5:
        return "background-color: #7f1d1d; color: #ffffff; font-weight: 700"
    return "background-color: #3a3a3a; color: #dddddd"


def _carregar_cvm_cache(st, ano: int):
    @st.cache_data(ttl=60 * 60 * 12, show_spinner="Baixando dados da CVM...")
    def _inner(ano_ref):
        return baixar_vlmo(int(ano_ref))
    return _inner(ano)


def _aviso_defasagem(st, df):
    """Mostra, em destaque, a data real do dado mais recente da CVM."""
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


def render_confluencia(st):
    """Tela cheia: ranking de Score de Confluência de todos os ativos."""
    st.markdown("#### 🎯 Score de Confluência")
    st.caption(
        "Sinais oficiais cruzados num só número: insiders (diretoria + conselho), "
        "controlador (peso pequeno) e recompra da própria empresa — com grau de "
        "concordância. Fonte: CVM — Dados Abertos."
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
        df = _carregar_cvm_cache(st, int(ano))
    except Exception as e:
        st.error(f"Não consegui baixar o arquivo da CVM para {int(ano)}: {e}")
        return

    _aviso_defasagem(st, df)

    try:
        res = score_confluencia(df, meses=int(meses))
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
        )
        st.write("Pesos:", PESOS)
        st.dataframe(sinais_cvm(df, meses=int(meses)),
                    use_container_width=True, hide_index=True)


def render_confluencia_card(st, ticker: str, meses: int = 6, ano: int | None = None):
    """
    Card compacto pra dentro da pagina de detalhe de UM ativo — pensado pra
    entrar na aba Movimentacao, ao lado dos cards de Insiders e Recompras
    que ja existem la (mesmo lugar, mesma logica visual).
    """
    if not _DEPS_OK:
        st.caption(f"🔧 Score de Confluência indisponível: {_ERRO_IMPORT}")
        return

    ano = ano or datetime.date.today().year
    try:
        df = _carregar_cvm_cache(st, int(ano))
        res = score_confluencia(df, meses=int(meses))
    except Exception as e:
        st.caption(f"🔧 Não consegui calcular o Score de Confluência: {e}")
        return

    linha = res[res["ticker"] == ticker.upper()]
    dt_max = data_atualizacao(df)
    data_str = dt_max.strftime("%d/%m/%Y") if dt_max is not None else "—"

    if linha.empty:
        st.markdown(
            "<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.12);"
            "border-radius:10px;padding:14px 16px;'>"
            "<div style='font-size:0.78em;color:#ccc;font-weight:600;text-transform:uppercase;"
            "margin-bottom:6px;'>🎯 Score de Confluência (CVM)</div>"
            "<div style='font-size:0.85em;color:#888;'>Sem dados para este ativo no período.</div>"
            "</div>", unsafe_allow_html=True
        )
        return

    row = linha.iloc[0]
    score = row["score"]
    cor = "#39FF14" if score > 5 else ("#FF4444" if score < -5 else "#aaaaaa")
    resumo = explicar(row)

    st.markdown(
        "<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.12);"
        "border-radius:10px;padding:14px 16px;'>"
        "<div style='font-size:0.78em;color:#ccc;font-weight:600;text-transform:uppercase;"
        "margin-bottom:8px;'>🎯 Score de Confluência (CVM)</div>"
        f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:6px;'>"
        f"<span style='font-size:1.5em;font-weight:900;color:{cor};'>{score:.1f}</span>"
        f"<span style='font-size:0.85em;color:#ccc;'>Concordância: {row['concordancia']}</span>"
        "</div>"
        f"<div style='font-size:0.85em;color:#ddd;line-height:1.5;'>{resumo}</div>"
        f"<div style='font-size:0.72em;color:#888;margin-top:8px;'>📅 Dados da CVM até {data_str} "
        f"(insiders reportam mensalmente, com atraso de algumas semanas)</div>"
        "</div>", unsafe_allow_html=True
    )
