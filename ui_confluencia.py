"""
ui_confluencia.py
=================
Camada visual (Streamlit) do Score de Confluencia, isolada do app.py do RADAR.
Toda a logica de dados vive em logica_score.py / cvm_insiders.py.

Integracao no app.py (3 insercoes no nivel raiz, sem indentacao aninhada):

  1) No topo, junto dos outros imports:
        from ui_confluencia import render_confluencia

  2) Na linha dos botoes de modo, trocar:
        tcol1, tcol2, tcol3, tcol4 = st.columns([1, 1, 1, 7])
     por:
        tcol1, tcol2, tcol3, tcol4, tcol5 = st.columns([1, 1, 1, 1.4, 6])
     e logo apos o bloco "with tcol3:" (Comparar), adicionar:
        with tcol4:
            if st.button("🎯 Confluência", use_container_width=True,
                         type="primary" if st.session_state.modo_exibicao == 'Confluência' else "secondary"):
                st.session_state.modo_exibicao = 'Confluência'
                st.rerun()

  3) Logo APOS o bloco dos botoes (antes de "# --- LISTAGEM DE ATIVOS ---"):
        if st.session_state.modo_exibicao == 'Confluência':
            render_confluencia(st)
            st.stop()
"""

import datetime
import pandas as pd

try:
    from logica_score import score_confluencia, sinais_cvm, PESOS
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


def render_confluencia(st):
    """Desenha o modo Score de Confluencia. Recebe o modulo streamlit (st)."""
    st.markdown("#### 🎯 Score de Confluência")
    st.caption(
        "Sinais oficiais cruzados num só número: insiders (diretoria + conselho), "
        "controlador (peso pequeno) e recompra da própria empresa — com grau de "
        "concordância. Quanto mais sinais apontam no mesmo sentido, mais robusto. "
        "Fonte: CVM — Dados Abertos."
    )

    if not _DEPS_OK:
        st.error(
            "Não consegui carregar os módulos do Score "
            "(cvm_insiders.py / logica_score.py). Confirme que estão no repositório."
        )
        st.caption(f"🔧 Detalhe técnico: {_ERRO_IMPORT}")
        return

    ano_atual = datetime.date.today().year
    c1, c2 = st.columns([1, 1])
    with c1:
        ano = st.number_input("Ano de referência", min_value=2021,
                              max_value=ano_atual + 1, value=ano_atual, step=1)
    with c2:
        meses = st.select_slider("Janela (meses)", options=[3, 6, 12], value=6)

    @st.cache_data(ttl=60 * 60 * 12, show_spinner="Baixando dados da CVM...")
    def _carregar(ano_ref):
        return baixar_vlmo(int(ano_ref))

    try:
        df = _carregar(int(ano))
    except Exception as e:
        st.error(f"Não consegui baixar o arquivo da CVM para {int(ano)}: {e}")
        return

    try:
        res = score_confluencia(df, meses=int(meses))
    except Exception as e:
        st.error(f"Erro ao calcular o score: {e}")
        return

    if res.empty:
        st.info("Sem dados para o período selecionado.")
        return

    res_show = res.rename(columns={
        "ticker": "Ticker", "score": "Score",
        "concordancia": "Concordância", "detalhe": "Sinais",
    })

    st.dataframe(
        res_show.style.map(_cor_score, subset=["Score"]),
        use_container_width=True, hide_index=True,
    )

    with st.expander("Como ler / valores brutos por papel (R$)"):
        st.markdown(
            "- **Score** (−100 a +100): soma ponderada dos sinais.\n"
            "- **Concordância** X/N: quantos sinais apontam no mesmo sentido do score. "
            "4/4 = convicção robusta; 3/5 = sinais em conflito (leitura ambígua).\n"
            "- **Sinais**: quais entraram e em que direção (`insider+`, `recompra-`, etc)."
        )
        st.write("Pesos:", PESOS)
        st.dataframe(sinais_cvm(df, meses=int(meses)),
                    use_container_width=True, hide_index=True)

    st.caption(
        "Valuation e dividend safety entram quando plugados via parâmetro `extras` "
        "de score_confluencia. Fonte: CVM — Dados Abertos (ODbL)."
    )
