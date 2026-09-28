"""
Radar multi-tempo (top-down): semanal -> diário -> 60 min -> 15 min.
Direção e regiões nos tempos maiores; momento e gatilhos nos menores.
O disparo final é no Profit, em tempo real: os gatilhos são preços para alarme.
"""
import os
import sys
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if AQUI not in sys.path:
    sys.path.insert(0, AQUI)
import radar_engine as R  # noqa: E402
import radar_mtf as M      # noqa: E402

st.set_page_config(page_title="Radar multi-tempo", page_icon="🧭", layout="wide")

UNIVERSO = ["PETR4", "VALE3", "BPAC11", "BBAS3", "BBSE3", "B3SA3", "KLBN11", "BRAP4",
            "SUZB3", "PSSA3", "ITUB4", "BBDC4", "AXIA3", "PRIO3"]
DEMO = os.environ.get("RADAR_DEMO") == "1"
COR_DIR = {"alta": ("#D5EEDD", "#135C31"), "baixa": ("#F9DCDB", "#8E1B19"), "lateral": ("#E6EAEF", "#2B3642")}
COR = {"alta": "#1E8A4C", "baixa": "#C8322F", "neutro": "#5B6878"}

st.markdown("""
<style>
.block-container{padding-top:1.4rem}
.tb{width:100%;border-collapse:collapse;background:#FFFFFF;color:#16202B;border-radius:10px;overflow:hidden;font-size:.9rem}
.tb th{background:#1D3557;color:#FFFFFF;text-align:left;padding:7px 9px;font-weight:600}
.tb td{padding:6px 9px;border-bottom:1px solid #E3E8EE;color:#16202B;vertical-align:top}
.chip{display:inline-block;border-radius:6px;padding:1px 8px;font-size:.78rem;font-weight:700}
.box{border:1px solid #CBD3DC;border-left:6px solid var(--c,#1D3557);border-radius:10px;padding:10px 14px;background:#FFFFFF;color:#16202B;margin-bottom:10px}
.box h5{margin:0 0 4px;color:#16202B;font-size:.98rem}.box p{margin:0 0 5px;color:#16202B;font-size:.9rem;line-height:1.45}
.aviso{background:#FBE6C2;color:#4A2F00;border:1px solid #E8C27A;border-radius:10px;padding:8px 14px;margin:4px 0 12px;font-size:.9rem}
</style>""", unsafe_allow_html=True)

INTERVALOS = {"S": ("1wk", "5y"), "D": ("1d", "2y"), "60": ("60m", "6mo"), "15": ("15m", "60d")}

def _baixar(tickers, tf):
    if DEMO:
        from synth import synth
        from synth_intraday import synth5
        out = {}
        for t in tickers:
            seed = sum(map(ord, t)) % 97
            if tf in ("S", "D"):
                d = synth(seed, n=600)
                out[t] = R.semanal(d) if tf == "S" else d
            else:
                i5 = synth5(seed, dias=60)
                i5.index = i5.index.tz_localize(None)
                agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
                out[t] = i5.resample("60min" if tf == "60" else "15min").agg(agg).dropna()
        return out
    import yfinance as yf
    iv, per = INTERVALOS[tf]
    syms = [t + ".SA" for t in tickers]
    raw = yf.download(syms, period=per, interval=iv, group_by="ticker", auto_adjust=False, progress=False, threads=True)
    out = {}
    for t, s in zip(tickers, syms):
        try:
            d = raw[s] if len(syms) > 1 else raw
            d = d[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"])
            if d.index.tz is not None:
                d.index = d.index.tz_convert("America/Sao_Paulo").tz_localize(None)
            if len(d):
                out[t] = d
        except Exception:
            pass
    return out

@st.cache_data(ttl=3600, show_spinner=False)
def dados_lentos(tickers, tf):
    return _baixar(list(tickers), tf)

@st.cache_data(ttl=300, show_spinner=False)
def dados_rapidos(tickers, tf):
    return _baixar(list(tickers), tf)

with st.sidebar:
    st.header("Radar multi-tempo")
    ativos = st.multiselect("Ativos", UNIVERSO, default=UNIVERSO)
    if st.button("Atualizar agora", width="stretch"):
        dados_rapidos.clear()
        dados_lentos.clear()
    st.caption("Semanal e diário: sem efeito do atraso. 60 e 15 min: até 15 min de atraso (Yahoo). "
               "O disparo é no Profit: coloque os gatilhos como alarme de preço.")

st.title("Radar multi-tempo")
st.markdown("<div class='aviso'>Leitura <b>de cima para baixo</b>: o semanal e o diário dizem <b>para onde</b> e <b>onde estão as regiões</b>; "
            "o 60 e o 15 dizem <b>quando</b>. A decisão final acontece no Profit, em tempo real, quando o preço tocar um dos <b>gatilhos</b>.</div>",
            unsafe_allow_html=True)

if not ativos:
    st.stop()

with st.spinner("Lendo semanal, diário, 60 e 15 minutos..."):
    series = {tf: (dados_lentos if tf in ("S", "D") else dados_rapidos)(tuple(ativos), tf) for tf, _ in M.TFS}
    cascatas = {}
    for a in ativos:
        L = {}
        for tf, nome in M.TFS:
            df = series[tf].get(a)
            if df is not None and len(df) >= 60:
                lt = M.ler_tf(a, tf, nome, df)
                if lt:
                    L[tf] = lt
        if "D" in L:
            cascatas[a] = M.cascata(a, L)

if not cascatas:
    st.error("Não consegui ler os gráficos agora. Tente novamente em alguns minutos.")
    st.stop()

ordem = sorted(cascatas.values(), key=lambda c: -M.pontuacao(c))

def hoje(ativo):
    """Variação do dia e horário do último dado, a partir do 15 min."""
    q = series["15"].get(ativo)
    if q is None or len(q) < 2:
        return None, None
    dias = q.index.normalize()
    ult = dias[-1]
    ant = q[dias < ult]
    if not len(ant):
        return None, q.index[-1]
    return q["Close"].iloc[-1] / ant["Close"].iloc[-1] - 1, q.index[-1]

def chip(direcao, texto):
    bg, fg = COR_DIR.get(direcao, COR_DIR["lateral"])
    return f"<span class='chip' style='background:{bg};color:{fg}'>{texto}</span>"

tab_mapa, tab_ativo, tab_guia = st.tabs(["Mapa", "Análise do ativo", "Como ler"])

with tab_mapa:
    linhas = []
    for c in ordem:
        cels = ""
        var, _hora = hoje(c.ativo)
        if var is None:
            cels += "<td>–</td>"
        else:
            cels += f"<td>{chip('alta' if var > 0 else 'baixa' if var < 0 else 'lateral', R.pct(var, 2))}</td>"
        for tf, _ in M.TFS:
            L = c.leituras.get(tf)
            cels += f"<td>{chip(L.direcao, L.rotulo) if L else '–'}</td>"
        dest = "; ".join(f"{s.nome} ({tf})" for tf, s in c.destaques[:3]) or "–"
        linhas.append(f"<tr><td><b>{c.ativo}</b></td>{cels}<td>{c.alinhamento}</td><td>{dest}</td></tr>")
    st.markdown("<table class='tb'><tr><th>Ativo</th><th>Hoje</th><th>Semanal</th><th>Diário</th><th>60 min</th><th>15 min</th><th>Alinhamento</th><th>Destaques</th></tr>"
                + "".join(linhas) + "</table>", unsafe_allow_html=True)
    hs = [hoje(c.ativo)[1] for c in ordem]
    hs = [h for h in hs if h is not None]
    st.caption("Cada célula mostra a **tendência** (médias e topos/fundos daquele tempo gráfico) e a **fase** (o que os últimos candles estão fazendo). "
               "Ex.: 'Baixa · repicando' = tendência de baixa, mas subindo agora. "
               + (f"Dados de 15 min até {max(hs):%d/%m %H:%M} (Yahoo, com atraso). " if hs else "")
               + "Ordenado pelos cenários mais completos.")

def grafico(L: M.LeituraTF, n_barras=160):
    d = L.an.df.iloc[-n_barras:]
    off = len(L.an.df) - len(d)
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, row_heights=[0.55, 0.15, 0.15, 0.15], vertical_spacing=0.02)
    fig.add_trace(go.Candlestick(x=d.index, open=d["Open"], high=d["High"], low=d["Low"], close=d["Close"], name=L.an.ativo,
                                 increasing_line_color="#1E8A4C", decreasing_line_color="#C8322F"), 1, 1)
    for col, cor, nome in (("EMA9", "#2F6FB3", "MME9"), ("EMA21", "#C77A12", "MME21"), ("SMA50", "#6B4FA0", "MM50"), ("SMA200", "#16202B", "MM200")):
        fig.add_trace(go.Scatter(x=d.index, y=d[col], line=dict(color=cor, width=1.2), name=nome), 1, 1)
    lo, hi = d["Low"].min(), d["High"].max()
    for z in L.an.zonas:
        if z.toques < 2 and z is not L.an.suporte and z is not L.an.resistencia:
            continue
        if z.high < lo - L.an.atr or z.low > hi + L.an.atr:
            continue
        cor = "rgba(30,138,76,.15)" if z.tipo == "suporte" else "rgba(200,50,47,.13)"
        h = max(z.high - z.low, L.an.atr * 0.12)
        fig.add_hrect(y0=z.mid - h / 2, y1=z.mid + h / 2, fillcolor=cor, line_width=0, row=1, col=1)
    th = [(L.an.df.index[i], p) for i, p in L.an.highs if i >= off]
    tl = [(L.an.df.index[i], p) for i, p in L.an.lows if i >= off]
    if th:
        fig.add_trace(go.Scatter(x=[x for x, _ in th], y=[p for _, p in th], mode="markers", marker=dict(symbol="triangle-down", size=8, color="#C8322F"), name="topos"), 1, 1)
    if tl:
        fig.add_trace(go.Scatter(x=[x for x, _ in tl], y=[p for _, p in tl], mode="markers", marker=dict(symbol="triangle-up", size=8, color="#1E8A4C"), name="fundos"), 1, 1)
    for s in L.an.sinais + L.traps:
        if s.idx is not None and s.idx >= off:
            fig.add_annotation(x=L.an.df.index[s.idx], y=L.an.df["High"].iloc[s.idx], text=s.nome, showarrow=True, arrowhead=2, ay=-35,
                               font=dict(size=10, color=COR.get(s.direcao, "#16202B")), row=1, col=1)
    fig.add_trace(go.Scatter(x=d.index, y=d["RSI"], line=dict(color="#6B4FA0", width=1.2), name="IFR"), 2, 1)
    for y in (30, 70):
        fig.add_hline(y=y, line=dict(color="#8A96A5", dash="dot", width=1), row=2, col=1)
    fig.add_trace(go.Scatter(x=d.index, y=d["DIDI_R"], line=dict(color="#2F6FB3", width=1.2), name="Didi rápida (3/8)"), 3, 1)
    fig.add_trace(go.Scatter(x=d.index, y=d["DIDI_L"], line=dict(color="#C8322F", width=1.2), name="Didi lenta (20/8)"), 3, 1)
    fig.add_hline(y=1, line=dict(color="#16202B", width=1), row=3, col=1)
    fig.add_trace(go.Scatter(x=d.index, y=d["OBV"], line=dict(color="#1E8A4C", width=1.2), name="OBV"), 4, 1)
    fig.add_trace(go.Scatter(x=d.index, y=d["OBVM"], line=dict(color="#8A96A5", width=1, dash="dot"), name="média OBV"), 4, 1)
    rb = [dict(bounds=["sat", "mon"])]
    if L.tf in ("60", "15"):
        rb.append(dict(bounds=[18, 10], pattern="hour"))
    fig.update_xaxes(rangebreaks=rb)
    fig.update_layout(height=760, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False, template="plotly_white",
                      plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF", font=dict(color="#16202B"), legend=dict(orientation="h", y=-0.04, x=0, yanchor="top"))
    fig.update_yaxes(gridcolor="#EEF1F4")
    fig.update_yaxes(title_text="IFR", row=2, col=1)
    fig.update_yaxes(title_text="Didi", row=3, col=1)
    fig.update_yaxes(title_text="OBV", row=4, col=1)
    return fig

with tab_ativo:
    at = st.selectbox("Ativo", [c.ativo for c in ordem])
    c = cascatas[at]
    cor = COR.get(c.vies, "#5B6878")
    st.markdown(f"<div class='box' style='--c:{cor}'><h5>{at} · viés {c.vies} · {c.forca} de {len(c.leituras)} tempos a favor</h5>"
                f"<p>{c.alinhamento}.</p>"
                f"<p><b>Para carregar (dias ou semanas):</b> {c.plano_carrego}</p>"
                f"<p><b>Para entrar agora ou fazer day trade:</b> {c.plano_curto}</p></div>", unsafe_allow_html=True)
    if c.gatilhos:
        gt = pd.DataFrame([dict(Gatilho=g[0], Preço=round(float(g[1]), 2), Direção=g[2]) for g in c.gatilhos])
        st.markdown("**Gatilhos para colocar como alarme de preço no Profit**")
        st.dataframe(gt, hide_index=True, width="stretch", column_config={"Preço": st.column_config.NumberColumn(format="R$ %.2f")})
    abas = st.tabs([n for tf, n in M.TFS if tf in c.leituras])
    for aba, (tf, nome) in zip(abas, [x for x in M.TFS if x[0] in c.leituras]):
        L = c.leituras[tf]
        with aba:
            g1, g2 = st.columns([2.3, 1])
            g1.plotly_chart(grafico(L), width="stretch", theme=None)
            with g2:
                a = L.an
                sup = R.brl(a.suporte.high) if a.suporte else "–"
                res = R.brl(a.resistencia.low) if a.resistencia else "–"
                itens = [f"<b>Tendência:</b> {a.tendencia} (ADX {a.adx:.0f}; {a.estrutura})",
                         f"<b>Agora:</b> {L.rotulo.split(' · ')[-1]} (preço {'acima' if a.preco > a.df['EMA9'].iloc[-1] else 'abaixo'} da MME9) · último dado {a.df.index[-1]:%d/%m %H:%M}",
                         f"<b>Médias:</b> preço {'acima' if a.preco > a.df['EMA21'].iloc[-1] else 'abaixo'} da MME21"
                         + ("" if np.isnan(a.df['SMA200'].iloc[-1]) else f" e {'acima' if a.preco > a.df['SMA200'].iloc[-1] else 'abaixo'} da MM200"),
                         f"<b>Regiões:</b> suporte {sup} · resistência {res}",
                         f"<b>{L.ifr_txt}</b>", f"<b>{L.obv_txt}</b>", f"<b>{L.didi_txt}</b>"]
                st.markdown(f"<div class='box'><h5>{nome}</h5>" + "".join(f"<p>{x}</p>" for x in itens) + "</div>", unsafe_allow_html=True)
                sinais = a.sinais + L.traps
                if sinais:
                    for s in sinais:
                        st.markdown(f"<div class='box' style='--c:{COR.get(s.direcao, '#5B6878')}'><h5>{s.nome}</h5><p>{s.texto}</p></div>", unsafe_allow_html=True)
                else:
                    st.caption("Nenhuma figura ou armadilha ativa neste tempo gráfico.")

with tab_guia:
    st.markdown("""
### Como ler de cima para baixo

**1. Semanal: a maré.** Define se você nada a favor ou contra. Semanal em alta com o diário corrigindo é o cenário clássico de compra.
Semanal em baixa: compras só como trade curto, com stop curto.

**2. Diário: as regiões.** Suportes, resistências, médias e figuras do diário definem **onde** faz sentido agir e onde fica o stop de um carrego.
Muitas vezes a análise pode parar aqui: se o diário dá um pullback na média ou um trap num suporte relevante, dá para montar carrego à vista ou com opção.

**3. 60 minutos: o momento.** Mostra se a correção do diário está terminando (IFR saindo do sobrevendido, Didi com agulhada, OBV voltando a subir).

**4. 15 minutos: o gatilho.** Define o preço exato de entrada e de invalidação. Esses preços são os **gatilhos**: coloque como alarme no Profit.

**5. No Profit, em tempo real (5 min):** quando o alarme tocar, abra o 5 minutos e confirme o candle. Trap de compra ou de venda no 5 min
num nível que o diário também marca é a entrada de day trade com melhor relação risco/retorno.

### Os indicadores
- **Médias (9, 21, 50, 200):** direção e suporte dinâmico. Preço acima da 21 e 21 acima da 50 = tendência de alta saudável.
- **IFR:** força. Acima de 70 esticado para cima, abaixo de 30 esticado para baixo. Divergências (preço renova, IFR não) avisam perda de força.
- **OBV:** o volume confirma o preço? OBV subindo com preço caindo = alguém acumulando.
- **Didi Index:** médias de 3 e 20 normalizadas pela de 8. **Agulhada** (as duas cruzam a linha em sentidos opostos quase juntas) marca início de movimento.
- **Traps:** rompimento de topo ou fundo relevante que volta em poucos candles. Quem entrou no rompimento fica preso e alimenta o movimento contrário.
""")
