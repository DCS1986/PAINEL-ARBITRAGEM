"""
RADAR TÉCNICO — Streamlit
Varre os gráficos diários dos ativos, identifica tendência, suportes/resistências,
topos/fundos e figuras, cruza com o momento do mercado (IBOV) e com eventos binários,
e traduz tudo em alertas para você validar no gráfico do Profit.

Deploy: Streamlit Cloud apontando para este arquivo. Dependências em requirements_radar.txt.
Dados: Yahoo Finance (diário, com atraso) ou CSV exportado do gráfico do Profit.
"""
import os
import math
import datetime as dt
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import radar_engine as R

st.set_page_config(page_title="Radar técnico", page_icon="📡", layout="wide")

UNIVERSO = ["PETR4", "VALE3", "BPAC11", "BBAS3", "BBSE3", "B3SA3", "KLBN11", "BRAP4",
            "SUZB3", "PSSA3", "ITUB4", "BBDC4", "AXIA3", "PRIO3"]
EVENTOS_ARQ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eventos_radar.csv")
DEMO = os.environ.get("RADAR_DEMO") == "1"
COR = {"alta": "#1E8A4C", "baixa": "#C8322F", "neutro": "#5B6878"}

st.markdown("""
<style>
.block-container{padding-top:1.4rem}
.card,.plano{border:1px solid #CBD3DC;border-left:6px solid var(--c);border-radius:10px;padding:10px 14px;margin:0 0 10px;background:#FFFFFF;color:#16202B}
.card h4,.plano h4{margin:0 0 2px;font-size:1.02rem;color:#16202B}
.card .meta,.plano .meta{font-size:.8rem;color:#4A5664;margin-bottom:4px}
.card p,.plano p{margin:0 0 3px;font-size:.92rem;line-height:1.42;color:#16202B}
.plano b{color:#16202B}
.chip{display:inline-block;border-radius:6px;padding:0 7px;margin-right:6px;font-size:.75rem;font-weight:700;background:#E6EAEF;color:#2B3642}
.chip.ok{background:#D5EEDD;color:#135C31}.chip.no{background:#F9DCDB;color:#8E1B19}.chip.ev{background:#FBE6C2;color:#6B4300}
.nota2{background:#1D3557;color:#FFFFFF}.nota1{background:#E6EAEF;color:#2B3642}
.evt{background:#FBE6C2;color:#4A2F00;border:1px solid #E8C27A;border-radius:10px;padding:8px 14px;margin:6px 0 12px;font-size:.92rem}
.evt b{color:#4A2F00}
.plano p.aviso{color:#8E1B19;font-weight:600}
</style>""", unsafe_allow_html=True)

# ------------------------------------------------------------------ dados
@st.cache_data(ttl=900, show_spinner=False)
def baixar(ticker: str) -> pd.DataFrame | None:
    if DEMO:
        from synth import synth
        return synth(abs(hash(ticker)) % 1000)
    import yfinance as yf
    sym = ticker if ticker.startswith("^") else ticker + ".SA"
    try:
        df = yf.Ticker(sym).history(period="2y", interval="1d", auto_adjust=False)
    except Exception:
        return None
    if df is None or df.empty:
        return None
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    return df[["Open", "High", "Low", "Close", "Volume"]]

def carregar_eventos() -> pd.DataFrame:
    if "eventos" not in st.session_state:
        try:
            ev = pd.read_csv(EVENTOS_ARQ, sep=";", dtype=str)
        except Exception:
            ev = pd.DataFrame(columns=["data", "evento", "ativos"])
        ev["data"] = pd.to_datetime(ev["data"], errors="coerce").dt.date
        st.session_state.eventos = ev
    return st.session_state.eventos

# ------------------------------------------------------------------ barra lateral
with st.sidebar:
    st.header("Radar técnico")
    ativos = st.multiselect("Ativos", UNIVERSO + ["BOVA11", "WEGE3", "RENT3", "ELET3", "ABEV3", "GGBR4", "CSAN3"], default=UNIVERSO)
    extra = st.text_input("Outros tickers (separados por vírgula)", "")
    ativos += [x.strip().upper() for x in extra.split(",") if x.strip()]
    tf = st.radio("Tempo gráfico", ["Diário", "Semanal"], horizontal=True)
    dias_ev = st.slider("Avisar eventos com antecedência de (dias)", 3, 30, 10)
    st.divider()
    arq = st.file_uploader("Dados exportados do Profit (opcional)", type=["csv", "txt"],
                           help="Exporte o gráfico diário no Profit (botão direito → Exportar dados). Os ativos do arquivo substituem os do Yahoo.")
    if st.button("Atualizar dados agora", width="stretch"):
        baixar.clear()
    st.caption("Fonte padrão: Yahoo Finance (diário, pode ter atraso). Leituras objetivas para validar no gráfico, não recomendações.")

hoje = pd.Timestamp(dt.date.today())
eventos = carregar_eventos()
ev_df = eventos.dropna(subset=["data"]).copy()

profit = {}
if arq is not None:
    try:
        profit = R.ler_csv_profit(arq)
        st.sidebar.success(f"Arquivo do Profit: {', '.join(profit)}")
    except Exception as e:
        st.sidebar.error(f"Não consegui ler o arquivo: {e}")

def serie(t):
    df = profit.get(t)
    if df is None:
        df = baixar(t)
    if df is not None and tf == "Semanal":
        df = R.semanal(df)
    return df

# ------------------------------------------------------------------ análise
with st.spinner("Lendo os gráficos..."):
    ibov_df = serie("^BVSP")
    ibov = R.analisar("IBOV", ibov_df, ev_df, hoje, dias_ev) if ibov_df is not None else None
    mercado = ibov.tendencia if ibov else None
    analises, falhas = {}, []
    for t in dict.fromkeys(ativos):
        df = serie(t)
        an = R.analisar(t, df, ev_df, hoje, dias_ev) if df is not None else None
        if an is None:
            falhas.append(t)
        else:
            analises[t] = an

# ------------------------------------------------------------------ cabeçalho: momento do mercado
st.title("Radar técnico")
st.caption(f"{hoje:%d/%m/%Y} · tempo gráfico {tf.lower()} · {len(analises)} ativos lidos"
           + (f" · sem dados: {', '.join(falhas)}" if falhas else ""))

c1, c2, c3, c4, c5 = st.columns(5)
if ibov:
    c1.metric("Ibovespa", f"{ibov.preco:,.0f}".replace(",", "."), R.pct(ibov.var_dia))
    c2.metric("Tendência do índice", ibov.tendencia, f"ADX {ibov.adx:.0f}", delta_color="off")
    c3.metric("Vol realizada do índice", f"{ibov.hv20*100:.0f}%", f"percentil {ibov.hv_pct*100:.0f} no ano", delta_color="off")
else:
    c1.metric("Ibovespa", "sem dados")
if analises:
    acima50 = np.mean([a.preco > a.df["SMA50"].iloc[-1] for a in analises.values() if not math.isnan(a.df["SMA50"].iloc[-1])])
    acima200 = np.mean([a.preco > a.df["SMA200"].iloc[-1] for a in analises.values() if not math.isnan(a.df["SMA200"].iloc[-1])] or [np.nan])
    c4.metric("Ativos acima da MM50", f"{acima50*100:.0f}%")
    c5.metric("Ativos acima da MM200", "–" if math.isnan(acima200) else f"{acima200*100:.0f}%")

prox = ev_df[(pd.to_datetime(ev_df["data"]) >= hoje) & (pd.to_datetime(ev_df["data"]) <= hoje + pd.Timedelta(days=dias_ev))].sort_values("data")
if len(prox):
    itens = " · ".join(f"<b>{r.evento}</b> em {(pd.Timestamp(r.data) - hoje).days} dia(s) ({pd.Timestamp(r.data):%d/%m})" for r in prox.itertuples())
    st.markdown(f"<div class='evt'>Eventos binários à frente: {itens}. IV costuma inflar antes e desabar depois; gaps ficam mais prováveis.</div>", unsafe_allow_html=True)

if mercado:
    amp = f"{acima50*100:.0f}% dos ativos acima da MM50" if analises else ""
    humor = ("comprador" if mercado.startswith("Alta") else "vendedor" if mercado.startswith("Baixa") else "sem direção")
    st.markdown(f"**Leitura do momento:** índice em {mercado.lower()} (mercado {humor}), {amp}. "
                "Sinais a favor do índice ganham peso no ranking; contra o índice, perdem.")

tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(["Plano do dia", "Alertas", "Mapa dos ativos", "Gráfico e leitura", "Eventos", "Como usar"])


# ------------------------------------------------------------------ plano do dia
with tab0:
    st.markdown("Uma linha por ativo juntando **tendência + onde o preço está + vol + eventos**. "
                "Primeiro os cenários claros, depois os que pedem observação. É o ponto de partida para abrir o gráfico no Profit.")
    planos = sorted(((R.plano(a, mercado), a) for a in analises.values()), key=lambda x: (-x[0]["nota"], x[1].ativo))
    claros = [x for x in planos if x[0]["nota"] == 2]
    obs = [x for x in planos if x[0]["nota"] == 1]
    fora = [x for x in planos if x[0]["nota"] == 0]
    def card_plano(p, a):
        cor = COR.get(p["vies"], COR["neutro"])
        badge = "<span class='chip nota2'>cenário claro</span>" if p["nota"] == 2 else "<span class='chip nota1'>observar</span>"
        av = "".join(f"<p class='aviso'>{x}</p>" for x in p["avisos"])
        return (f"<div class='plano' style='--c:{cor}'><h4>{a.ativo} · {R.brl(a.preco)} {badge}</h4>"
                f"<div class='meta'>tendência {a.tendencia.lower()} · {p['local']} · vol {p['vol']}"
                + (f" · evento em {a.eventos[0][2]}d" if a.eventos else "") + "</div>"
                f"<p><b>À vista:</b> {p['vista']}</p><p><b>Opções:</b> {p['opcoes']}</p>{av}</div>")
    if claros:
        st.subheader(f"Cenários claros ({len(claros)})")
        cA, cB = st.columns(2)
        for k, (p, a) in enumerate(claros):
            (cA if k % 2 == 0 else cB).markdown(card_plano(p, a), unsafe_allow_html=True)
    if obs:
        st.subheader(f"Observar ({len(obs)})")
        cA, cB = st.columns(2)
        for k, (p, a) in enumerate(obs):
            (cA if k % 2 == 0 else cB).markdown(card_plano(p, a), unsafe_allow_html=True)
    if fora:
        st.caption("Sem vantagem clara hoje: " + ", ".join(a.ativo for _, a in fora) + ".")

# ------------------------------------------------------------------ alertas
def forca_txt(f):
    return "●" * f + "○" * (3 - f)

with tab1:
    linhas = []
    for a in analises.values():
        for s in a.sinais:
            linhas.append((R.pontuar(a, s, mercado), a, s))
    f1, f2, f3 = st.columns([2, 1, 1])
    dirs = f1.multiselect("Direção", ["alta", "baixa", "neutro"], default=["alta", "baixa", "neutro"])
    fmin = f2.select_slider("Força mínima", options=[1, 2, 3], value=1)
    so_tend = f3.toggle("Só a favor da tendência", value=False)
    linhas = [x for x in linhas if x[2].direcao in dirs and x[2].forca >= fmin]
    if so_tend:
        linhas = [x for x in linhas if (x[2].direcao == "alta" and x[1].tendencia.startswith("Alta")) or (x[2].direcao == "baixa" and x[1].tendencia.startswith("Baixa")) or x[2].direcao == "neutro"]
    linhas.sort(key=lambda x: -x[0])
    if not linhas:
        st.info("Nenhum sinal com esses filtros. Ausência de sinal também é informação: nada pede ação hoje.")
    colA, colB = st.columns(2)
    for k, (p, a, s) in enumerate(linhas):
        fav = (s.direcao == "alta" and a.tendencia.startswith("Alta")) or (s.direcao == "baixa" and a.tendencia.startswith("Baixa"))
        contra = (s.direcao == "alta" and a.tendencia.startswith("Baixa")) or (s.direcao == "baixa" and a.tendencia.startswith("Alta"))
        chips = f"<span class='chip'>força {forca_txt(s.forca)}</span>"
        if fav:
            chips += "<span class='chip ok'>a favor da tendência</span>"
        if contra:
            chips += "<span class='chip no'>contra a tendência</span>"
        if mercado and s.direcao != "neutro":
            if (s.direcao == "alta") == mercado.startswith("Alta") and not mercado.startswith("Lateral"):
                chips += "<span class='chip ok'>a favor do índice</span>"
            elif not mercado.startswith("Lateral"):
                chips += "<span class='chip no'>contra o índice</span>"
        if a.eventos:
            chips += f"<span class='chip ev'>evento em {a.eventos[0][2]}d</span>"
        refs = []
        if s.stop:
            refs.append(f"invalida abaixo de {R.brl(s.stop)}" if s.direcao == "alta" else f"invalida acima de {R.brl(s.stop)}")
        if s.alvo:
            refs.append(f"próxima região {R.brl(s.alvo)}")
        html = (f"<div class='card' style='--c:{COR[s.direcao]}'><h4>{a.ativo} · {s.nome}</h4>"
                f"<div class='meta'>{R.brl(a.preco)} ({R.pct(a.var_dia)}) · tendência {a.tendencia.lower()} · {chips}</div>"
                f"<p>{s.texto}</p>" + (f"<p class='meta' style='margin-top:4px'>{' · '.join(refs)}</p>" if refs else "") + "</div>")
        (colA if k % 2 == 0 else colB).markdown(html, unsafe_allow_html=True)

# ------------------------------------------------------------------ mapa
with tab2:
    rows = []
    for a in analises.values():
        rows.append({
            "Ativo": a.ativo, "Preço": a.preco, "Dia": a.var_dia, "Tendência": a.tendencia, "Estrutura": a.estrutura,
            "ADX": round(a.adx), "IFR": round(a.rsi),
            "Suporte": a.suporte.high if a.suporte else None,
            "Dist. suporte (ATR)": max(0.0, (a.preco - a.suporte.high) / a.atr) if a.suporte else None,
            "Resistência": a.resistencia.low if a.resistencia else None,
            "Dist. resist. (ATR)": max(0.0, (a.resistencia.low - a.preco) / a.atr) if a.resistencia else None,
            "HV20": a.hv20, "Percentil HV": a.hv_pct,
            "Mov. esperado venc.": (a.mov_esperado / a.preco) if a.mov_esperado else None,
            "Sinais": ", ".join(s.nome for s in a.sinais) or "–",
            "Evento": a.eventos[0][1] + f" ({a.eventos[0][2]}d)" if a.eventos else "",
        })
    mapa = pd.DataFrame(rows)
    if len(mapa):
        ordem = {"Alta forte": 0, "Alta": 1, "Lateral": 2, "Baixa": 3, "Baixa forte": 4}
        mapa = mapa.sort_values("Tendência", key=lambda s: s.map(ordem))
        st.dataframe(mapa, hide_index=True, width="stretch", height=min(620, 42 + 35 * len(mapa)),
                     column_config={
                         "Preço": st.column_config.NumberColumn(format="R$ %.2f"),
                         "Dia": st.column_config.NumberColumn(format="percent"),
                         "Suporte": st.column_config.NumberColumn(format="R$ %.2f"),
                         "Resistência": st.column_config.NumberColumn(format="R$ %.2f"),
                         "Dist. suporte (ATR)": st.column_config.NumberColumn(format="%.1f"),
                         "Dist. resist. (ATR)": st.column_config.NumberColumn(format="%.1f"),
                         "HV20": st.column_config.NumberColumn(format="percent"),
                         "Percentil HV": st.column_config.ProgressColumn(min_value=0, max_value=1, format="percent"),
                         "Mov. esperado venc.": st.column_config.NumberColumn(format="percent"),
                     })
        st.caption("Distâncias em ATR: menos de 1 ATR significa que o preço está praticamente na região. Percentil HV alto = vol realizada cara para o próprio ativo.")

# ------------------------------------------------------------------ gráfico e leitura
def grafico(a: R.Analise, s_sel: R.Sinal | None):
    df = a.df.iloc[-180:]
    off = len(a.df) - len(df)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2], vertical_spacing=0.02)
    fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
                                 name=a.ativo, increasing_line_color="#1E8A4C", decreasing_line_color="#C8322F"), 1, 1)
    for col, cor, nome in (("EMA21", "#2F6FB3", "MME21"), ("SMA50", "#C77A12", "MM50"), ("SMA200", "#6B4FA0", "MM200")):
        fig.add_trace(go.Scatter(x=df.index, y=df[col], line=dict(color=cor, width=1.4), name=nome), 1, 1)
    lo, hi = df["Low"].min(), df["High"].max()
    for z in a.zonas:
        if z.high < lo - a.atr * 2 or z.low > hi + a.atr * 2:
            continue
        if z.toques < 2 and z is not a.suporte and z is not a.resistencia:
            continue
        cor = "rgba(30,138,76,.16)" if z.tipo == "suporte" else "rgba(200,50,47,.14)"
        h = max(z.high - z.low, a.atr * 0.15)
        fig.add_hrect(y0=z.mid - h / 2, y1=z.mid + h / 2, fillcolor=cor, line_width=0, row=1, col=1)
        fig.add_annotation(x=df.index[-1], y=z.mid, text=f"{z.tipo} {R.brl(z.mid)} · {z.toques}x", showarrow=False,
                           xanchor="left", xshift=6, font=dict(size=10, color="#34414F"), row=1, col=1)
    ph = [(a.df.index[i], p) for i, p in a.highs if i >= off]
    pl = [(a.df.index[i], p) for i, p in a.lows if i >= off]
    if ph:
        fig.add_trace(go.Scatter(x=[x for x, _ in ph], y=[p * 1.006 for _, p in ph], mode="markers", marker=dict(symbol="triangle-down", size=8, color="#C8322F"), name="topos"), 1, 1)
    if pl:
        fig.add_trace(go.Scatter(x=[x for x, _ in pl], y=[p * 0.994 for _, p in pl], mode="markers", marker=dict(symbol="triangle-up", size=8, color="#1E8A4C"), name="fundos"), 1, 1)
    if s_sel:
        if s_sel.stop:
            fig.add_hline(y=s_sel.stop, line=dict(color="#C8322F", dash="dash", width=1), annotation_text="invalidação", row=1, col=1)
        if s_sel.alvo:
            fig.add_hline(y=s_sel.alvo, line=dict(color="#1E8A4C", dash="dash", width=1), annotation_text="próxima região", row=1, col=1)
        if s_sel.idx is not None and s_sel.idx >= off:
            x = a.df.index[s_sel.idx]
            fig.add_annotation(x=x, y=a.df["High"].iloc[s_sel.idx], text=s_sel.nome, showarrow=True, arrowhead=2, ay=-40, row=1, col=1)
    vcol = ["#1E8A4C" if c >= o else "#C8322F" for o, c in zip(df["Open"], df["Close"])]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=vcol, name="volume", opacity=.6), 2, 1)
    fig.update_layout(height=620, margin=dict(l=10, r=110, t=10, b=10), xaxis_rangeslider_visible=False, template="plotly_white",
                      legend=dict(orientation="h", y=1.02, x=0), plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF", font=dict(color="#16202B"),
                      xaxis=dict(rangebreaks=[dict(bounds=["sat", "mon"])]), xaxis2=dict(rangebreaks=[dict(bounds=["sat", "mon"])]))
    fig.update_yaxes(gridcolor="#EEF1F4")
    return fig

with tab3:
    if analises:
        ordem_at = sorted(analises, key=lambda t: -max([R.pontuar(analises[t], s, mercado) for s in analises[t].sinais] or [0]))
        g1, g2 = st.columns([1, 2])
        at = g1.selectbox("Ativo", ordem_at)
        a = analises[at]
        opts = ["(nenhum)"] + [s.nome for s in a.sinais]
        ss = g2.selectbox("Destacar sinal no gráfico", opts, index=1 if a.sinais else 0)
        s_sel = next((s for s in a.sinais if s.nome == ss), None)
        left, right = st.columns([2.2, 1])
        left.plotly_chart(grafico(a, s_sel), width="stretch", theme=None)
        with right:
            st.subheader(f"{a.ativo} · {R.brl(a.preco)}")
            dist_s = f"{(a.preco - a.suporte.high)/a.atr:.1f}".replace(".", ",") if a.suporte else None
            dist_r = f"{(a.resistencia.low - a.preco)/a.atr:.1f}".replace(".", ",") if a.resistencia else None
            txt = f"Tendência **{a.tendencia.lower()}** (ADX {a.adx:.0f}, {a.estrutura}; IFR {a.rsi:.0f}). "
            if a.suporte:
                txt += f"Suporte mais próximo {R.brl(a.suporte.high)} a {dist_s} ATR"
            if a.resistencia:
                txt += f"; resistência {R.brl(a.resistencia.low)} a {dist_r} ATR"
            st.markdown((txt + ".").replace("$", "\\$"))
            st.markdown("**Sinais**")
            if a.sinais:
                for s in a.sinais:
                    st.markdown(f"<div class='card' style='--c:{COR[s.direcao]}'><h4>{s.nome} <span class='chip'>força {forca_txt(s.forca)}</span></h4><p>{s.texto}</p></div>", unsafe_allow_html=True)
            else:
                st.caption("Nenhum sinal ativo. O gráfico não pede ação agora.")
            st.markdown("**Lente de opções**")
            for o in a.opcoes:
                st.markdown(f"<div class='leit'><p>{o}</p></div>", unsafe_allow_html=True)

# ------------------------------------------------------------------ eventos
with tab4:
    st.markdown("Datas que mexem com a volatilidade. Em **ativos**, use `*` para o mercado todo ou liste tickers (ex.: `PETR4,PRIO3`).")
    ed = st.data_editor(eventos, num_rows="dynamic", width="stretch", hide_index=True,
                        column_config={"data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                                       "evento": st.column_config.TextColumn("Evento"), "ativos": st.column_config.TextColumn("Ativos")})
    b1, b2 = st.columns(2)
    if b1.button("Aplicar alterações"):
        st.session_state.eventos = ed
        st.rerun()
    csv = ed.assign(data=pd.to_datetime(ed["data"]).dt.strftime("%Y-%m-%d")).to_csv(sep=";", index=False)
    b2.download_button("Baixar eventos_radar.csv", csv, "eventos_radar.csv", "text/csv",
                       help="Para manter as alterações: suba este arquivo no GitHub no lugar do atual.")

# ------------------------------------------------------------------ como usar
with tab5:
    st.markdown(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "COMO_USAR.md"), encoding="utf-8").read().replace("$", "\\$"))
