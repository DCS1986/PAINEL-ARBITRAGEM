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

@st.cache_data(ttl=1800, show_spinner=False)
def candles(ativo, tf):
    if DEMO:
        from synth_mtf import serie_5m, AGG
        d5 = serie_5m({"PETR4": 0, "VALE3": 1, "BBAS3": 2, "PRIO3": 3, "ITUB4": 4}.get(ativo, 0), dias=200)
        return d5.resample("1D" if tf == "D" else "60min").agg(AGG).dropna()
    import yfinance as yf
    iv, per = ("1d", "9mo") if tf == "D" else ("60m", "2mo")
    try:
        d = yf.Ticker(ativo + ".SA").history(period=per, interval=iv, auto_adjust=False)
    except Exception:
        return None
    if d is None or d.empty:
        return None
    d.index = pd.to_datetime(d.index)
    if d.index.tz is not None:
        d.index = d.index.tz_convert("America/Sao_Paulo").tz_localize(None)
    return d[["Open", "High", "Low", "Close"]]

def foto(r):
    """O gráfico da sugestão com tudo marcado: gatilho, stop, alvo, a região que justifica o stop e o que aconteceu depois."""
    tf = r.get("tf_base") if isinstance(r.get("tf_base"), str) else ("D" if r["horizonte"] == "SWING" else "60")
    d = candles(r["ativo"], tf)
    if d is None or d.empty:
        st.caption("Não consegui carregar o gráfico deste ativo agora.")
        return
    criada = pd.Timestamp(r["criada_em"])
    antes = d[d.index <= criada].iloc[-70:]
    depois = d[d.index > criada]
    d = pd.concat([antes, depois])
    if d.empty:
        return
    passo = (d.index[-1] - d.index[-2]) if len(d) > 1 else pd.Timedelta(days=1)
    x_fim = d.index[-1] + passo * max(8, len(d) // 6)
    x_ini_sug = antes.index[-1] if len(antes) else d.index[0]
    gat, stp, alv = float(r["gatilho"]), float(r["stop"]), float(r["alvo"])
    fig = go.Figure(go.Candlestick(x=d.index, open=d["Open"], high=d["High"], low=d["Low"], close=d["Close"], name=r["ativo"],
                                   increasing_line_color="#1E8A4C", decreasing_line_color="#C8322F", showlegend=False))
    # zonas de risco e de ganho a partir da sugestão
    fig.add_shape(type="rect", x0=x_ini_sug, x1=x_fim, y0=min(gat, stp), y1=max(gat, stp), fillcolor="rgba(200,50,47,.14)", line_width=0)
    fig.add_shape(type="rect", x0=x_ini_sug, x1=x_fim, y0=min(gat, alv), y1=max(gat, alv), fillcolor="rgba(30,138,76,.10)", line_width=0)
    fig.add_vline(x=x_ini_sug, line=dict(color="#6B4300", dash="dot", width=1.5))
    fig.add_annotation(x=x_ini_sug, y=1, yref="paper", text="sugestão criada", showarrow=False, xanchor="left", yanchor="top",
                       font=dict(size=11, color="#6B4300"), bgcolor="#FBE6C2")
    compra = r["direcao"] == "alta"
    linhas = [(gat, "#1D3557", "solid", f"① gatilho {R.brl(gat)}: " + ("entra se passar daqui" if compra else "entra se perder daqui")),
              (stp, "#C8322F", "solid", f"② stop {R.brl(stp)}: a tese acaba aqui"),
              (alv, "#1E8A4C", "solid", f"③ alvo {R.brl(alv)}: primeira região no caminho")]
    if pd.notna(r.get("ref_preco")):
        linhas.append((float(r["ref_preco"]), "#5B6878", "dot", "região que justifica o stop"))
    if pd.notna(r.get("mov_esperado")):
        m = float(r["mov_esperado"])
        linhas.append((gat - m if not compra else gat + m, "#8A96A5", "dash", "movimento normal do ativo no prazo"))
    lo = min(d["Low"].min(), stp, alv, gat) * 0.99
    hi = max(d["High"].max(), stp, alv, gat) * 1.01
    altura_px = 430 - 20
    px_por_real = altura_px / (hi - lo)
    ultimo_px = None
    for y, cor, estilo, txt in sorted(linhas, key=lambda x: -x[0]):
        fig.add_shape(type="line", x0=d.index[0], x1=x_fim, y0=y, y1=y, line=dict(color=cor, width=1.6 if estilo == "solid" else 1.2, dash=estilo))
        py = (hi - y) * px_por_real                     # distância do topo, em pixels
        if ultimo_px is not None and py - ultimo_px < 17:
            py = ultimo_px + 17                         # empurra o rótulo para baixo para não sobrepor
        ultimo_px = py
        deslocamento = -(py - (hi - y) * px_por_real)
        fig.add_annotation(x=x_fim, y=y, text=txt, showarrow=False, xanchor="right", yanchor="middle", yshift=deslocamento,
                           font=dict(size=11, color=cor), bgcolor="rgba(255,255,255,.92)", bordercolor=cor, borderwidth=1, borderpad=2)
    # setas: onde o repique/recuo foi rejeitado
    if pd.notna(r.get("ref_preco")) and len(antes) > 5:
        seg = antes.iloc[-15:]
        i = seg["High"].idxmax() if not compra else seg["Low"].idxmin()
        y = seg.loc[i, "High"] if not compra else seg.loc[i, "Low"]
        txt = {"Repique": "repique rejeitado aqui", "Pullback": "recuo segurou aqui", "Trap": "rompimento falso aqui",
               "Fundo duplo": "segundo fundo", "Topo duplo": "segundo topo", "Rompimento": "região rompida"}.get(r["setup"], "referência")
        fig.add_annotation(x=i, y=y, text=txt, showarrow=True, arrowhead=2, ay=-40 if not compra else 40,
                           font=dict(size=11, color="#16202B"), bgcolor="#FFFFFF", bordercolor="#16202B", borderwidth=1)
    if pd.notna(r.get("entrada_em")) and r.get("entrada_em"):
        fig.add_trace(go.Scatter(x=[pd.Timestamp(r["entrada_em"])], y=[r["entrada_preco"]], mode="markers", name="entrada",
                                 marker=dict(symbol="triangle-up" if compra else "triangle-down", size=14, color="#1D3557")))
    if pd.notna(r.get("saida_em")) and r.get("saida_em"):
        fig.add_trace(go.Scatter(x=[pd.Timestamp(r["saida_em"])], y=[r["saida_preco"]], mode="markers", name="saída",
                                 marker=dict(symbol="x", size=14, color="#16202B")))
    rb = [dict(bounds=["sat", "mon"])]
    if tf == "60":
        rb.append(dict(bounds=[18, 10], pattern="hour"))
    fig.update_layout(height=430, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False, template="plotly_white",
                      plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF", font=dict(color="#16202B"),
                      xaxis=dict(range=[d.index[0], x_fim], rangebreaks=rb), yaxis=dict(range=[lo, hi], gridcolor="#EEF1F4"),
                      legend=dict(orientation="h", y=-0.08))
    st.plotly_chart(fig, width="stretch", theme=None, key=f"foto-{r['id']}")
    st.caption(("Gráfico diário" if tf == "D" else "Gráfico de 60 min") + ". Faixa vermelha = o que você arrisca; faixa verde = o que você busca. "
               "Tudo à direita da linha pontilhada aconteceu depois da sugestão.")

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
    instr = r["instrumento"] if isinstance(r.get("instrumento"), str) and r.get("instrumento") else (
        "à vista ou call ATM/ITM" if r["direcao"] == "alta" else "put ATM/ITM ou venda de call")
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
        foto(r)

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
    if not hist.empty:
        opc = [f"{r['criada_em']} · {r['ativo']} · {r['setup']} → {r['status']}" for _, r in hist.iterrows()]
        esc = st.selectbox("Ver a foto de", opc)
        foto(hist.iloc[opc.index(esc)])
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
