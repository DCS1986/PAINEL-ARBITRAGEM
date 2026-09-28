"""
Gera leituras.csv: a leitura técnica do Radar para cada ativo, num formato
que a planilha de opções baixa e usa no SINAL.

Roda sozinho no GitHub (Actions) depois do fechamento; também pode ser
executado à mão:  python radar_tecnico/radar/gerar_leituras.py
"""
import os
import sys
import math
import datetime as dt
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import radar_engine as R  # noqa: E402
import radar_mtf as M  # noqa: E402
import radar_sugestoes as SG  # noqa: E402

UNIVERSO = ["PETR4", "VALE3", "BPAC11", "BBAS3", "BBSE3", "B3SA3", "KLBN11", "BRAP4",
            "SUZB3", "PSSA3", "ITUB4", "BBDC4", "AXIA3", "PRIO3"]
EXTRA = [t.strip().upper() for t in os.environ.get("RADAR_EXTRA", "").split(",") if t.strip()]
DEMO = os.environ.get("RADAR_DEMO") == "1"


def baixar(ticker):
    if DEMO:
        from synth import synth
        return synth(sum(map(ord, ticker)) % 1000)
    import yfinance as yf
    sym = ticker if ticker.startswith("^") else ticker + ".SA"
    try:
        df = yf.Ticker(sym).history(period="2y", interval="1d", auto_adjust=False)
    except Exception as e:
        print(f"[aviso] {ticker}: {e}")
        return None
    if df is None or df.empty:
        print(f"[aviso] {ticker}: sem dados")
        return None
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    return df[["Open", "High", "Low", "Close", "Volume"]]


def baixar_lote(tickers, intervalo, periodo):
    """60 e 15 min de todos os ativos numa chamada só (horário de Brasília, sem fuso)."""
    if DEMO:
        return {}
    import yfinance as yf
    syms = [t + ".SA" for t in tickers]
    try:
        raw = yf.download(syms, period=periodo, interval=intervalo, group_by="ticker", auto_adjust=False, progress=False, threads=True)
    except Exception as e:
        print(f"[aviso] lote {intervalo}: {e}")
        return {}
    out = {}
    for t, s in zip(tickers, syms):
        try:
            d = raw[s][["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"])
            if d.index.tz is not None:
                d.index = d.index.tz_convert("America/Sao_Paulo").tz_localize(None)
            if len(d):
                out[t] = d
        except Exception:
            pass
    return out


def main():
    hoje = pd.Timestamp(dt.date.today())
    try:
        ev = pd.read_csv(os.path.join(AQUI, "eventos_radar.csv"), sep=";", dtype=str)
        ev["data"] = pd.to_datetime(ev["data"], errors="coerce")
        ev = ev.dropna(subset=["data"])
    except Exception:
        ev = None
    ibov_df = baixar("^BVSP")
    ibov = R.analisar("IBOV", ibov_df, ev, hoje) if ibov_df is not None else None
    mercado = ibov.tendencia if ibov else ""
    agora = (pd.Timestamp.now("UTC").tz_localize(None) - pd.Timedelta(hours=3)).strftime("%Y-%m-%d %H:%M")
    linhas = []
    diarios = {}
    for t in dict.fromkeys(UNIVERSO + EXTRA):
        df = baixar(t)
        if df is not None:
            diarios[t] = df
        an = R.analisar(t, df, ev, hoje) if df is not None else None
        if an is None:
            continue
        p = R.plano(an, mercado or None)
        ev0 = an.eventos[0] if an.eventos else None
        linhas.append({
            "ativo": t,
            "data_leitura": an.df.index[-1].strftime("%Y-%m-%d"),
            "gerado_em": agora,
            "preco": round(an.preco, 2),
            "tendencia": an.tendencia,
            "vies": p["vies"],
            "local": p["local"],
            "vol": p["vol"],
            "hv_pct": None if math.isnan(an.hv_pct) else round(an.hv_pct, 3),
            "atr": round(an.atr, 3),
            "mme21": round(float(an.df["EMA21"].iloc[-1]), 2),
            "sup_low": round(an.suporte.low, 2) if an.suporte else None,
            "sup_high": round(an.suporte.high, 2) if an.suporte else None,
            "res_low": round(an.resistencia.low, 2) if an.resistencia else None,
            "res_high": round(an.resistencia.high, 2) if an.resistencia else None,
            "evento": ev0[1] if ev0 else "",
            "evento_dias": ev0[2] if ev0 else None,
            "mercado": mercado,
            "sinais": " | ".join(s.nome for s in an.sinais),
            "plano_opcoes": p["opcoes"],
        })
    out = pd.DataFrame(linhas)
    destino = os.path.join(AQUI, "leituras.csv")
    out.to_csv(destino, sep=";", index=False, encoding="utf-8")
    print(f"{len(out)} ativos gravados em {destino}")

    # ---------------- sugestões de operação + acompanhamento do desfecho
    try:
        sugerir_e_acompanhar(diarios, ev)
    except Exception as e:
        print(f"[aviso] sugestões: {e}")


def sugerir_e_acompanhar(diarios, ev):
    agora = pd.Timestamp.now("UTC").tz_localize(None) - pd.Timedelta(hours=3)
    tickers = list(diarios)
    h60 = baixar_lote(tickers, "60m", "6mo")
    m15 = baixar_lote(tickers, "15m", "60d")
    arq = os.path.join(AQUI, "sugestoes.csv")
    livro = pd.read_csv(arq, sep=";", dtype=str) if os.path.exists(arq) else pd.DataFrame(columns=SG.COLUNAS)
    for c in ("gatilho", "stop", "alvo", "rr", "risco_pct", "prazo_pregoes", "entrada_preco", "saida_preco", "resultado_r", "resultado_pct", "mfe_r", "mae_r"):
        if c in livro:
            livro[c] = pd.to_numeric(livro[c], errors="coerce")
    # 1) atualiza o desfecho das abertas
    livro = SG.atualizar_todos(livro, m15, agora)
    # 2) novas sugestões (só em dia útil, entre 10h30 e 18h30)
    novas = []
    hora = agora.hour + agora.minute / 60
    # SWING só com o candle diário FECHADO (rodada depois das 18h); CURTO durante o pregão, só com candles de 60 min fechados
    horizontes = tuple(h for h, ok in (("SWING", hora >= 18), ("CURTO", 10.5 <= hora <= 17)) if ok)
    if agora.weekday() < 5 and horizontes:
        for t, d in diarios.items():
            d_ok = d if hora >= 18 else d[d.index.normalize() < agora.normalize()]
            h = h60.get(t)
            if h is not None and len(h):
                h = h[h.index + pd.Timedelta(minutes=60) <= agora - pd.Timedelta(minutes=15)]
            series = {"S": R.semanal(d_ok), "D": d_ok, "60": h, "15": m15.get(t)}
            L = {}
            for tf, nome in M.TFS:
                df = series.get(tf)
                if df is not None and len(df) >= 60:
                    lt = M.ler_tf(t, tf, nome, df, eventos=ev)
                    if lt:
                        L[tf] = lt
            if "D" in L:
                novas += SG.gerar(M.cascata(t, L), agora, horizontes=horizontes)
    livro = SG.juntar(livro, novas, agora)
    livro.to_csv(arq, sep=";", index=False, encoding="utf-8")
    abertas = livro["status"].isin(SG.ABERTOS).sum()
    print(f"sugestões: {len(novas)} candidatas, {abertas} abertas, {len(livro)} no histórico")


if __name__ == "__main__":
    main()
