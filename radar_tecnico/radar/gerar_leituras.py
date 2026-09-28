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
    linhas = []
    for t in dict.fromkeys(UNIVERSO + EXTRA):
        df = baixar(t)
        an = R.analisar(t, df, ev, hoje) if df is not None else None
        if an is None:
            continue
        p = R.plano(an, mercado or None)
        ev0 = an.eventos[0] if an.eventos else None
        linhas.append({
            "ativo": t,
            "data_leitura": an.df.index[-1].strftime("%Y-%m-%d"),
            "preco": round(an.preco, 2),
            "tendencia": an.tendencia,
            "vies": p["vies"],
            "local": p["local"],
            "vol": p["vol"],
            "hv_pct": None if math.isnan(an.hv_pct) else round(an.hv_pct, 3),
            "suporte": round(an.suporte.high, 2) if an.suporte else None,
            "resistencia": round(an.resistencia.low, 2) if an.resistencia else None,
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


if __name__ == "__main__":
    main()
