"""
Sugestões de operação e o acompanhamento de cada uma: e se eu tivesse seguido?
As sugestões são criadas e acompanhadas automaticamente pelo GitHub (sugestoes.csv).
"""
import os
import sys
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if AQUI not in sys.path:
    sys.path.insert(0, AQUI)
import radar_engine as R  # noqa: E402

st.set_page_config(page_title="Sugestões", page_icon="🎯", layout="wide")
URL = "https://raw.githubusercontent.com/DCS1986/painel-arbitragem/main/radar_tecnico/radar/sugestoes.csv"
DEMO = os.environ.get("RADAR_DEMO") == "1"
COR = {"alta": "#1E8A4C", "baixa": "#C8322F"}
ST = {"aguardando gatilho": ("#FBE6C2", "#6B4300"), "em andamento": ("#DCE8F7", "#1D3557"), "alvo": ("#D5EEDD", "#135C31"),
      "stop": ("#F9DCDB", "#8E1B19"), "encerrada no prazo": ("#E6EAEF", "#2B3642"), "não acionada": ("#E6EAEF", "#5B6878")}

st.markdown("""
<style>
.block-container{padding-top:1.4rem}
.card{border:1px solid #CBD3DC;border-left:6px solid var(--c);border-radius:10px;padding:12px 16px;margin:0 0 12px;background:#FFFFFF;color:#16202B}
.card h4{margin:0 0 4px;font-size:1.05rem;color:#16202B}
.card .meta{font-size:.82rem;color:#4A5664;margin-bottom:6px}
.card p{margin:0 0 7px;font-size:.92rem;line-height:1.45;color:#16202B}
.card b{color:#16202B}
.nums{display:flex;gap:22px;flex-wrap:wrap;margin:6px 0 10px}
.nums div{font-size:.8rem;color:#4A5664}.nums b{display:block;font-size:1.05rem;color:#16202B}
.chip{display:inline-block;border-radius:6px;padding:1px 8px;margin-right:6px;font-size:.76rem;font-weight:700;background:#E6EAEF;color:#2B3642}
.aviso{background:#FBE6C2;color:#4A2F00;border:1px solid #E8C27A;border-radius:10px;padding:8px 14px;margin:4px 0 12px;font-size:.9rem}
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=120, show_spinner=False)
def carregar():
    fontes = [os.path.join(AQUI, "sugestoes.csv")] if DEMO else [URL + f"?t={pd.Timestamp.now():%Y%m%d%H%M}", os.path.join(AQUI, "sugestoes.csv")]
    for f in fontes:
        try:
            d = pd.read_csv(f, sep=";")
            for c in ("gatilho", "stop", "alvo", "rr", "risco_pct", "entrada_preco", "saida_preco", "resultado_r", "resultado_pct", "mfe_r", "mae_r"):
                d[c] = pd.to_numeric(d[c], errors="coerce")
            return d
        except Exception:
            continue
    return pd.DataFrame()

with st.sidebar:
    st.header("Sugestões")
    risco = st.number_input("Quanto você aceitaria perder por operação (R$)", min_value=50, max_value=100000, value=300, step=50,
                            help="Define o tamanho da posição: quantidade = esse valor ÷ distância entre entrada e stop. É assim que o placar vira reais.")
    hz = st.multiselect("Horizonte", ["SWING", "CURTO"], default=["SWING", "CURTO"],
                        format_func=lambda x: "Swing (dias a semanas)" if x == "SWING" else "Curto (horas a 2 dias)")
    if st.button("Recarregar", width="stretch"):
        carregar.clear()

st.title("Sugestões de operação")
st.markdown("<div class='aviso'>O Radar só sugere o que está <b>explícito</b>: assimetria de pelo menos 2 para 1 até uma região real, "
            "stop curto e tempos maiores sem estar contra. Cada sugestão é registrada no momento em que aparece e acompanhada até o fim, "
            "para responder: <b>se eu tivesse seguido, teria ganho ou perdido quanto?</b> Leituras para estudo e decisão sua, não recomendação.</div>",
            unsafe_allow_html=True)

df = carregar()
if df.empty:
    st.info("Ainda não há sugestões registradas. Elas aparecem depois que o GitHub rodar o Radar: as de swing depois do fechamento (18h30) "
            "e as de curto prazo durante o pregão. Volte aqui amanhã.")
    st.stop()
df = df[df["horizonte"].isin(hz)].copy()
df["criada"] = pd.to_datetime(df["criada_em"])
df["qtd"] = np.floor(risco / (df["gatilho"] - df["stop"]).abs() / 1).astype("Int64")
df["qtd100"] = (df["qtd"] // 100 * 100).astype("Int64")
df["resultado_rs"] = df["resultado_r"] * risco

fech = df[df["status"].isin(["alvo", "stop", "encerrada no prazo"])]
abertas = df[df["status"].isin(["aguardando gatilho", "em andamento"])].sort_values("criada", ascending=False)

tab_ab, tab_pl, tab_hist, tab_guia = st.tabs([f"Abertas ({len(abertas)})", "Placar", f"Histórico ({len(df) - len(abertas)})", "Como ler"])

def card(r, completo=True):
    bg, fg = ST.get(r["status"], ("#E6EAEF", "#2B3642"))
    hzt = "Swing · dias a semanas" if r["horizonte"] == "SWING" else "Curto · horas a 2 dias"
    lado = "COMPRA" if r["direcao"] == "alta" else "VENDA"
    instr = ("à vista ou call ATM/ITM" if r["direcao"] == "alta" else "put ATM/ITM ou venda de call")
    res = ""
    if pd.notna(r.get("resultado_r")):
        res = f" · {r['resultado_r']:+.2f}R ({R.brl(r['resultado_r'] * risco)})"
    nums = (f"<div class='nums'><div>gatilho<b>{R.brl(r['gatilho'])}</b></div><div>stop<b>{R.brl(r['stop'])}</b></div>"
            f"<div>alvo<b>{R.brl(r['alvo'])}</b></div><div>assimetria<b>{str(round(r['rr'], 1)).replace('.', ',')} : 1</b></div>"
            f"<div>risco<b>{str(round(r['risco_pct']*100, 1)).replace('.', ',')}%</b></div>"
            f"<div>quantidade p/ {R.brl(risco)} de risco<b>{int(r['qtd']) if pd.notna(r['qtd']) else '–'} ações</b></div></div>")
    corpo = (f"<p><b>Contexto:</b> {r['contexto']}</p><p><b>Entrada.</b> {r['por_que_entrada']}</p>"
             f"<p><b>Stop.</b> {r['por_que_stop']}</p><p><b>Alvo.</b> {r['por_que_alvo']}</p><p><b>Assimetria.</b> {r['assimetria']}</p>") if completo else ""
    desf = ""
    if pd.notna(r.get("entrada_em")) and r.get("entrada_em"):
        desf = f"<p class='meta'>Entrou em {r['entrada_em']} a {R.brl(r['entrada_preco'])}"
        if pd.notna(r.get("saida_em")) and r.get("saida_em"):
            desf += f" · saiu em {r['saida_em']} a {R.brl(r['saida_preco'])}"
        if pd.notna(r.get("mfe_r")):
            desf += f" · andou até {r['mfe_r']:.1f}R a favor e {r['mae_r']:.1f}R contra"
        desf += "</p>"
    return (f"<div class='card' style='--c:{COR[r['direcao']]}'><h4>{r['ativo']} · {lado} · {r['setup']}</h4>"
            f"<div class='meta'><span class='chip' style='background:{bg};color:{fg}'>{r['status']}{res}</span>"
            f"<span class='chip'>{hzt}</span><span class='chip'>{instr}</span> criada em {r['criada_em']} · gatilho vale até {r['validade_ate']}</div>"
            f"{nums}{corpo}{desf}</div>")

with tab_ab:
    if abertas.empty:
        st.caption("Nenhuma sugestão aberta agora. Dias sem sugestão são dias em que nada estava explícito o suficiente.")
    for _, r in abertas.iterrows():
        st.markdown(card(r), unsafe_allow_html=True)

with tab_pl:
    if fech.empty:
        st.caption("Ainda não há sugestões encerradas para o placar.")
    else:
        ganhos = (fech["resultado_r"] > 0).mean()
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Operações encerradas", len(fech))
        c2.metric("Acertos", f"{ganhos*100:.0f}%")
        c3.metric("Resultado médio", f"{fech['resultado_r'].mean():+.2f}R")
        c4.metric("Total em R", f"{fech['resultado_r'].sum():+.1f}R")
        c5.metric(f"Em reais (risco {R.brl(risco)})", R.brl(fech["resultado_r"].sum() * risco))
        nao = (df["status"] == "não acionada").sum()
        st.caption(f"{nao} sugestões expiraram sem o gatilho ser atingido: não entram no placar, porque você não teria entrado.")
        curva = fech.assign(saida=pd.to_datetime(fech["saida_em"])).sort_values("saida")
        curva["acumulado"] = (curva["resultado_r"] * risco).cumsum()
        fig = go.Figure(go.Scatter(x=curva["saida"], y=curva["acumulado"], mode="lines+markers", line=dict(color="#1D3557", width=2)))
        fig.add_hline(y=0, line=dict(color="#8A96A5", dash="dot"))
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10), title="Resultado acumulado se tivesse seguido todas (R$)",
                          template="plotly_white", plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF", font=dict(color="#16202B"))
        st.plotly_chart(fig, width="stretch", theme=None)
        por = fech.groupby(["horizonte", "setup"]).agg(operacoes=("resultado_r", "size"), acertos=("resultado_r", lambda x: (x > 0).mean()),
                                                        media_r=("resultado_r", "mean"), total_r=("resultado_r", "sum")).reset_index()
        por["total_rs"] = por["total_r"] * risco
        st.markdown("**Por horizonte e setup**")
        st.dataframe(por, hide_index=True, width="stretch",
                     column_config={"acertos": st.column_config.NumberColumn("Acertos", format="percent"),
                                    "media_r": st.column_config.NumberColumn("Média (R)", format="%.2f"),
                                    "total_r": st.column_config.NumberColumn("Total (R)", format="%.1f"),
                                    "total_rs": st.column_config.NumberColumn("Total (R$)", format="R$ %.0f")})
        st.caption("R = unidade de risco. +2R significa ganhar duas vezes o que se aceitou perder. Com assimetria de 2:1 ou mais, "
                   "dá para errar mais da metade das vezes e ainda ganhar. Menos de 30 operações ainda é amostra pequena.")

with tab_hist:
    hist = df[~df["status"].isin(["aguardando gatilho", "em andamento"])].sort_values("criada", ascending=False)
    if hist.empty:
        st.caption("Ainda sem histórico.")
    for _, r in hist.head(60).iterrows():
        with st.expander(f"{r['criada_em']} · {r['ativo']} · {'compra' if r['direcao'] == 'alta' else 'venda'} · {r['setup']} → {r['status']}"
                         + (f" ({r['resultado_r']:+.2f}R · {R.brl(r['resultado_r'] * risco)})" if pd.notna(r['resultado_r']) else "")):
            st.markdown(card(r), unsafe_allow_html=True)

with tab_guia:
    st.markdown("""
### Como ler uma sugestão

**Gatilho.** A entrada só acontece se o preço passar do gatilho (compra) ou perder o gatilho (venda) **depois** da sugestão.
Esperar o rompimento é o que confirma a leitura. Se não acontecer, a sugestão expira e você não perdeu nada.

**Stop.** Nunca é um número arbitrário. É o ponto em que **a razão da entrada deixa de existir**: abaixo do suporte que segurou o recuo,
além do extremo da armadilha, abaixo dos dois fundos. Mais uma pequena folga (fração do ATR) para um pavio normal não te tirar.
Cada sugestão explica o porquê do seu stop. Leia sempre: é isso que vai te permitir fazer sozinho.

**Alvo.** A primeira região real no caminho: resistência ou suporte com dois ou mais toques. Se essa região não dá pelo menos 2 para 1, não há sugestão.

**Assimetria.** Quanto você busca para cada real arriscado. Com 3:1, basta acertar 1 em cada 4 para empatar.
**Stop barato** = assimetria alta com stop curto em relação à volatilidade do ativo (ATR).

**Tamanho da posição.** Defina na barra lateral quanto aceita perder por operação. A quantidade é esse valor dividido pela distância entre entrada e stop.
É a mesma perda em reais em qualquer ativo, o que torna o placar comparável.

### O placar
Registra **todas** as sugestões, inclusive as que deram errado. "Não acionada" não conta, porque você não teria entrado.
Com o tempo, o placar por setup mostra em quais leituras vale confiar mais.

### Swing e curto
- **Swing (dias a semanas):** criada depois do fechamento, com o candle diário fechado. O gatilho vale por 3 pregões; a operação dura no máximo 20.
- **Curto (horas a 2 dias):** criada durante o pregão, com candles de 60 min fechados. O gatilho vale até o fim do pregão seguinte; a operação dura no máximo 2 pregões.
  Como os dados chegam com atraso, confirme no Profit antes de agir.
""")
