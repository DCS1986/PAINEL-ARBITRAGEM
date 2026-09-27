"""
Radar Técnico — motor de análise.
Lê candles diários (OHLCV) e devolve: tendência, estrutura de topos/fundos,
zonas de suporte/resistência, sinais (rompimentos, pullbacks, topo/fundo duplo,
compressão, divergências...) e uma "lente de opções" (vol realizada, movimento
esperado até o vencimento, eventos binários, strikes de referência).

Nada aqui é recomendação: são leituras objetivas para você validar no gráfico.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

# ------------------------------------------------------------------ indicadores
def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()

def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n, min_periods=n).mean()

def true_range(df: pd.DataFrame) -> pd.Series:
    pc = df["Close"].shift(1)
    return pd.concat([df["High"] - df["Low"], (df["High"] - pc).abs(), (df["Low"] - pc).abs()], axis=1).max(axis=1)

def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    return true_range(df).ewm(alpha=1 / n, adjust=False).mean()

def rsi(c: pd.Series, n: int = 14) -> pd.Series:
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50)

def adx(df: pd.DataFrame, n: int = 14) -> pd.Series:
    up = df["High"].diff()
    dn = -df["Low"].diff()
    pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=df.index)
    ndm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=df.index)
    tr = true_range(df).ewm(alpha=1 / n, adjust=False).mean()
    pdi = 100 * pdm.ewm(alpha=1 / n, adjust=False).mean() / tr
    ndi = 100 * ndm.ewm(alpha=1 / n, adjust=False).mean() / tr
    dx = 100 * (pdi - ndi).abs() / (pdi + ndi).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False).mean().fillna(0)

def hist_vol(c: pd.Series, n: int = 20) -> pd.Series:
    r = np.log(c / c.shift(1))
    return r.rolling(n).std() * math.sqrt(252)

def pct_rank(s: pd.Series, window: int = 252) -> float:
    w = s.dropna().iloc[-window:]
    if len(w) < 30:
        return float("nan")
    return float((w < w.iloc[-1]).mean())

# ------------------------------------------------------------------ estrutura
def pivots(df: pd.DataFrame, k: int = 5):
    """Topos/fundos confirmados (k candles de cada lado)."""
    h, l = df["High"].values, df["Low"].values
    highs, lows = [], []
    for i in range(k, len(df) - k):
        if h[i] == h[i - k:i + k + 1].max() and (h[i] > h[i - k:i]).all():
            highs.append((i, h[i]))
        if l[i] == l[i - k:i + k + 1].min() and (l[i] < l[i - k:i]).all():
            lows.append((i, l[i]))
    return highs, lows

def structure(highs, lows) -> str:
    if len(highs) < 2 or len(lows) < 2:
        return "indefinida"
    hh = highs[-1][1] > highs[-2][1]
    hl = lows[-1][1] > lows[-2][1]
    if hh and hl:
        return "topos e fundos ascendentes"
    if not hh and not hl:
        return "topos e fundos descendentes"
    return "mista (sem direção clara)"

@dataclass
class Zona:
    low: float
    high: float
    toques: int
    ultimo: int      # índice do último toque
    tipo: str = ""   # suporte / resistência (em relação ao preço atual)

    @property
    def mid(self):
        return (self.low + self.high) / 2

def zones(df: pd.DataFrame, highs, lows, atr_now: float, lookback: int = 260) -> list[Zona]:
    start = max(0, len(df) - lookback)
    pts = sorted([(p, i) for i, p in highs + lows if i >= start])
    if not pts:
        return []
    tol = max(atr_now * 0.6, pts[-1][0] * 0.004)
    groups, cur = [], [pts[0]]
    for p in pts[1:]:
        if p[0] - cur[-1][0] <= tol:
            cur.append(p)
        else:
            groups.append(cur)
            cur = [p]
    groups.append(cur)
    out = []
    for g in groups:
        prices = [x[0] for x in g]
        out.append(Zona(min(prices), max(prices), len(g), max(x[1] for x in g)))
    # extremos de 52 semanas sempre contam como referência
    w = df.iloc[start:]
    for price, idx in ((w["High"].max(), int(np.argmax(w["High"].values)) + start),
                       (w["Low"].min(), int(np.argmin(w["Low"].values)) + start)):
        if not any(z.low - tol <= price <= z.high + tol for z in out):
            out.append(Zona(price, price, 1, idx))
    last = df["Close"].iloc[-1]
    for z in out:
        z.tipo = "suporte" if z.mid < last else "resistência"
    return sorted(out, key=lambda z: z.mid)

# ------------------------------------------------------------------ resultado
@dataclass
class Sinal:
    nome: str
    direcao: str          # alta / baixa / neutro
    forca: int            # 1..3
    texto: str
    stop: float | None = None
    alvo: float | None = None
    idx: int | None = None

@dataclass
class Analise:
    ativo: str
    df: pd.DataFrame
    preco: float
    var_dia: float
    tendencia: str
    tend_score: int
    estrutura: str
    adx: float
    rsi: float
    atr: float
    hv20: float
    hv_pct: float
    zonas: list
    suporte: Zona | None
    resistencia: Zona | None
    highs: list
    lows: list
    sinais: list = field(default_factory=list)
    opcoes: list = field(default_factory=list)
    eventos: list = field(default_factory=list)
    mov_esperado: float | None = None
    dias_venc: int | None = None
    venc: pd.Timestamp | None = None

def brl(x):
    return "R$ " + f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def pct(x, casas=1):
    return f"{x*100:+.{casas}f}%".replace(".", ",")

# ------------------------------------------------------------------ vencimentos B3
def terceira_sexta(ano, mes):
    d = pd.Timestamp(ano, mes, 1)
    return d + pd.Timedelta(days=(4 - d.weekday()) % 7 + 14)

def proximo_vencimento(hoje: pd.Timestamp, min_dias: int = 5):
    for k in range(0, 4):
        m = (hoje.month - 1 + k) % 12 + 1
        a = hoje.year + (hoje.month - 1 + k) // 12
        v = terceira_sexta(a, m)
        if (v - hoje).days >= min_dias:
            return v
    return terceira_sexta(hoje.year + 1, 1)

# ------------------------------------------------------------------ análise principal
def analisar(ativo: str, df: pd.DataFrame, eventos: pd.DataFrame | None = None,
             hoje: pd.Timestamp | None = None, dias_evento: int = 10) -> Analise | None:
    df = df.dropna(subset=["Open", "High", "Low", "Close"]).copy()
    if len(df) < 60:
        return None
    if "Volume" not in df:
        df["Volume"] = np.nan
    c = df["Close"]
    df["EMA9"], df["EMA21"] = ema(c, 9), ema(c, 21)
    df["SMA50"], df["SMA200"] = sma(c, 50), sma(c, 200)
    df["ATR"], df["RSI"], df["ADX"] = atr(df), rsi(c), adx(df)
    df["HV20"] = hist_vol(c)
    mid = sma(c, 20)
    sd = c.rolling(20).std()
    df["BBW"] = (4 * sd) / mid
    df["VOLM"] = df["Volume"].rolling(20).mean()

    last = df.iloc[-1]
    preco, a_now = float(last["Close"]), float(last["ATR"])
    var_dia = float(c.iloc[-1] / c.iloc[-2] - 1)
    highs, lows = pivots(df)
    est = structure(highs, lows)
    zs = zones(df, highs, lows, a_now)
    sup = max([z for z in zs if z.tipo == "suporte"], key=lambda z: z.mid, default=None)
    res = min([z for z in zs if z.tipo == "resistência"], key=lambda z: z.mid, default=None)

    # ---- tendência (pontuação -5..+5)
    sc = 0
    sc += 1 if preco > last["EMA21"] else -1
    if not math.isnan(last["SMA50"]):
        sc += 1 if last["EMA21"] > last["SMA50"] else -1
        slope = df["SMA50"].iloc[-1] - df["SMA50"].iloc[-11]
        sc += 1 if slope > 0 else -1
    if not math.isnan(last["SMA200"]):
        sc += 1 if preco > last["SMA200"] else -1
    sc += 1 if est.startswith("topos e fundos asc") else (-1 if est.startswith("topos e fundos desc") else 0)
    forte = last["ADX"] >= 25
    if sc >= 3:
        tend = "Alta forte" if forte else "Alta"
    elif sc <= -3:
        tend = "Baixa forte" if forte else "Baixa"
    elif sc >= 1 and last["ADX"] >= 20:
        tend = "Alta"
    elif sc <= -1 and last["ADX"] >= 20:
        tend = "Baixa"
    else:
        tend = "Lateral"

    an = Analise(ativo, df, preco, var_dia, tend, sc, est, float(last["ADX"]), float(last["RSI"]), a_now,
                 float(last["HV20"]), pct_rank(df["HV20"]), zs, sup, res, highs, lows)
    n = len(df)
    H, L, C, O, V, VM = (df[k].values for k in ("High", "Low", "Close", "Open", "Volume", "VOLM"))

    def add(nome, direcao, forca, texto, stop=None, alvo=None, idx=None):
        an.sinais.append(Sinal(nome, direcao, forca, texto, stop, alvo, idx))

    def volx(i):
        return (V[i] / VM[i]) if VM[i] and not np.isnan(VM[i]) and VM[i] > 0 and not np.isnan(V[i]) else float("nan")

    def volmsg(vx):
        if math.isnan(vx):
            return "."
        s = f"{vx:.1f}".replace(".", ",")
        return f", com volume {s}× a média." if vx >= 1 else f", mas com volume abaixo da média ({s}×): rompimento menos confiável."

    # ---- 1/2 rompimento de resistência / perda de suporte (últimos 3 pregões)
    for z in zs:
        for i in range(1, 4):
            j = n - i
            if j < 1:
                break
            if C[j] > z.high and C[j - 1] <= z.high and C[-1] > z.high and z.toques >= 2:
                vx = volx(j)
                acima = [w for w in zs if w.low > C[-1]]
                add("Rompimento de resistência", "alta", 3 if vx >= 1.3 else (1 if vx < 1 else 2),
                    f"Rompeu a região de {brl(z.high)} ({z.toques} toques) há {i} pregão(s)"
                    + (volmsg(vx))
                    + " O que era resistência tende a virar suporte: um reteste que segure é o ponto de confirmação.",
                    stop=z.low - 0.5 * a_now, alvo=acima[0].low if acima else None, idx=j)
                break
            if C[j] < z.low and C[j - 1] >= z.low and C[-1] < z.low and z.toques >= 2:
                vx = volx(j)
                abaixo = [w for w in zs if w.high < C[-1]]
                add("Perda de suporte", "baixa", 3 if vx >= 1.3 else (1 if vx < 1 else 2),
                    f"Perdeu a região de {brl(z.low)} ({z.toques} toques) há {i} pregão(s)"
                    + (volmsg(vx))
                    + " Suporte perdido tende a virar resistência.",
                    stop=z.high + 0.5 * a_now, alvo=abaixo[-1].high if abaixo else None, idx=j)
                break

    # ---- 3/4 pullback a favor da tendência
    e21 = float(last["EMA21"])
    if tend.startswith("Alta"):
        ref = max(e21, sup.high if sup else e21)
        if L[-3:].min() <= ref + 0.3 * a_now and C[-1] > e21 and C[-1] >= O[-1]:
            add("Pullback na tendência de alta", "alta", 2 if tend == "Alta" else 3,
                f"Em tendência de alta, recuou até {'a MME21' if ref == e21 else 'o suporte'} ({brl(ref)}) e fechou acima com candle comprador."
                " É o ponto clássico de reentrada a favor da tendência.",
                stop=min(L[-5:].min(), sup.low if sup else L[-5:].min()) - 0.3 * a_now,
                alvo=highs[-1][1] if highs and highs[-1][1] > C[-1] else (res.low if res else None), idx=n - 1)
    if tend.startswith("Baixa"):
        ref = min(e21, res.low if res else e21)
        if H[-3:].max() >= ref - 0.3 * a_now and C[-1] < e21 and C[-1] <= O[-1]:
            add("Repique na tendência de baixa", "baixa", 2 if tend == "Baixa" else 3,
                f"Em tendência de baixa, subiu até {'a MME21' if ref == e21 else 'a resistência'} ({brl(ref)}) e fechou abaixo com candle vendedor.",
                stop=max(H[-5:].max(), res.high if res else H[-5:].max()) + 0.3 * a_now,
                alvo=lows[-1][1] if lows and lows[-1][1] < C[-1] else (sup.high if sup else None), idx=n - 1)

    # ---- 5/6 topo duplo / fundo duplo
    if len(highs) >= 2:
        (i1, h1), (i2, h2) = highs[-2], highs[-1]
        if abs(h1 - h2) <= 0.6 * a_now and i2 - i1 >= 8 and n - i2 <= 30:
            neck = L[i1:i2 + 1].min()
            if max(h1, h2) - neck >= 1.5 * a_now and C[-1] < max(h1, h2):
                conf = C[-1] < neck
                add("Topo duplo" + (" confirmado" if conf else " em formação"), "baixa", 3 if conf else 1,
                    f"Dois topos em {brl(h1)} e {brl(h2)} com linha de pescoço em {brl(neck)}. "
                    + ("O preço já perdeu o pescoço: a figura está ativa." if conf else "Só vira sinal se perder o pescoço; até lá é alerta de exaustão."),
                    stop=max(h1, h2) + 0.3 * a_now, alvo=neck - (max(h1, h2) - neck), idx=i2)
    if len(lows) >= 2:
        (i1, l1), (i2, l2) = lows[-2], lows[-1]
        if abs(l1 - l2) <= 0.6 * a_now and i2 - i1 >= 8 and n - i2 <= 30:
            neck = H[i1:i2 + 1].max()
            if neck - min(l1, l2) >= 1.5 * a_now and C[-1] > min(l1, l2):
                conf = C[-1] > neck
                add("Fundo duplo" + (" confirmado" if conf else " em formação"), "alta", 3 if conf else 1,
                    f"Dois fundos em {brl(l1)} e {brl(l2)} com linha de pescoço em {brl(neck)}. "
                    + ("O preço já rompeu o pescoço: a figura está ativa." if conf else "Só vira sinal se romper o pescoço."),
                    stop=min(l1, l2) - 0.3 * a_now, alvo=neck + (neck - min(l1, l2)), idx=i2)

    # ---- 7 mudança de estrutura (primeiro sinal de reversão)
    if tend.startswith("Baixa") and highs and C[-1] > highs[-1][1] and C[-2] <= highs[-1][1]:
        add("Mudança de estrutura para alta", "alta", 2,
            f"Mesmo em tendência de baixa, fechou acima do último topo ({brl(highs[-1][1])}). Primeiro sinal de reversão; precisa de um fundo mais alto para confirmar.",
            stop=lows[-1][1] if lows else None, idx=n - 1)
    if tend.startswith("Alta") and lows and C[-1] < lows[-1][1] and C[-2] >= lows[-1][1]:
        add("Mudança de estrutura para baixa", "baixa", 2,
            f"Mesmo em tendência de alta, fechou abaixo do último fundo ({brl(lows[-1][1])}). Primeiro sinal de enfraquecimento.",
            stop=highs[-1][1] if highs else None, idx=n - 1)

    # ---- 8 compressão de volatilidade
    bbw_pct = pct_rank(df["BBW"])
    if not math.isnan(bbw_pct) and bbw_pct <= 0.12:
        add("Volatilidade comprimida", "neutro", 2,
            f"A largura das Bandas de Bollinger está entre as {bbw_pct*100:.0f}% menores do último ano. "
            "Compressão costuma anteceder movimento forte, sem dizer a direção: vale definir o gatilho (rompimento de "
            + (f"{brl(res.low)}" if res else "máxima recente") + " ou perda de " + (f"{brl(sup.high)}" if sup else "mínima recente") + ").",
            idx=n - 1)

    # ---- 9 divergências de IFR
    R = df["RSI"].values
    if len(highs) >= 2:
        (i1, h1), (i2, h2) = highs[-2], highs[-1]
        if h2 > h1 and R[i2] < R[i1] - 3 and n - i2 <= 15:
            add("Divergência baixista no IFR", "baixa", 1,
                f"Topo mais alto no preço ({brl(h2)}) com IFR mais baixo ({R[i2]:.0f} vs {R[i1]:.0f}): a alta perdeu força.", idx=i2)
    if len(lows) >= 2:
        (i1, l1), (i2, l2) = lows[-2], lows[-1]
        if l2 < l1 and R[i2] > R[i1] + 3 and n - i2 <= 15:
            add("Divergência altista no IFR", "alta", 1,
                f"Fundo mais baixo no preço ({brl(l2)}) com IFR mais alto ({R[i2]:.0f} vs {R[i1]:.0f}): a queda perdeu força.", idx=i2)

    # ---- 10 cruzamento 50/200
    s50, s200 = df["SMA50"].values, df["SMA200"].values
    for i in range(1, 11):
        j = n - i
        if j < 1 or np.isnan(s200[j - 1]):
            break
        if s50[j] > s200[j] and s50[j - 1] <= s200[j - 1]:
            add("Cruzamento de alta 50/200", "alta", 1, f"A MM50 cruzou acima da MM200 há {i} pregão(s): mudança de tendência de longo prazo.", idx=j)
            break
        if s50[j] < s200[j] and s50[j - 1] >= s200[j - 1]:
            add("Cruzamento de baixa 50/200", "baixa", 1, f"A MM50 cruzou abaixo da MM200 há {i} pregão(s): mudança de tendência de longo prazo.", idx=j)
            break

    # ---- 11 esticado em região
    if res and an.rsi >= 72 and res.low - preco <= a_now:
        add("Esticado na resistência", "baixa", 1, f"IFR {an.rsi:.0f} a menos de 1 ATR da resistência {brl(res.low)}: pouco espaço para cima no curto prazo.", idx=n - 1)
    if sup and an.rsi <= 28 and preco - sup.high <= a_now:
        add("Esticado no suporte", "alta", 1, f"IFR {an.rsi:.0f} a menos de 1 ATR do suporte {brl(sup.high)}: queda esticada chegando em região de defesa.", idx=n - 1)

    # ---- eventos e lente de opções
    hoje = hoje or pd.Timestamp.today().normalize()
    venc = proximo_vencimento(hoje)
    dias = int((venc - hoje).days)
    an.venc, an.dias_venc = venc, dias
    if not math.isnan(an.hv20):
        an.mov_esperado = preco * an.hv20 * math.sqrt(max(dias, 1) / 365)
    if eventos is not None and len(eventos):
        for _, e in eventos.iterrows():
            try:
                d = pd.Timestamp(e["data"])
            except Exception:
                continue
            alvo_at = str(e.get("ativos", "*")).upper().replace(" ", "")
            if alvo_at not in ("*", "", "NAN") and ativo.upper() not in alvo_at.split(","):
                continue
            dd = (d - hoje).days
            if 0 <= dd <= max(dias_evento, dias):
                an.eventos.append((d, str(e["evento"]), dd))
    an.eventos.sort()
    an.opcoes = lente_opcoes(an)
    return an

def lente_opcoes(an: Analise) -> list[str]:
    out = []
    if not math.isnan(an.hv_pct):
        if an.hv_pct >= 0.7:
            out.append(f"Vol realizada alta para o ativo (HV20 {an.hv20*100:.0f}%, maior que em {an.hv_pct*100:.0f}% dos pregões do último ano): prêmios tendem a estar caros, o ambiente favorece venda. Confirme a IV no Profit.")
        elif an.hv_pct <= 0.3:
            out.append(f"Vol realizada baixa para o ativo (HV20 {an.hv20*100:.0f}%, menor que em {100-an.hv_pct*100:.0f}% dos pregões do último ano): prêmios tendem a estar baratos, favorece compra ATM ou levemente ITM; vender prêmio barato rende pouco para o risco.")
        else:
            out.append(f"Vol realizada em nível médio (HV20 {an.hv20*100:.0f}%, percentil {an.hv_pct*100:.0f}).")
    if an.mov_esperado:
        up, dn = an.preco + an.mov_esperado, an.preco - an.mov_esperado
        mov_pct = str(round(an.mov_esperado / an.preco * 100, 1)).replace(".", ",")
        t = f"Movimento esperado (1 desvio) até o vencimento de {an.venc:%d/%m} ({an.dias_venc} dias): ±{brl(an.mov_esperado)} ({mov_pct}%), de {brl(dn)} a {brl(up)}."
        if an.suporte:
            t += f" Suporte {brl(an.suporte.high)} " + ("fica fora" if an.suporte.high < dn else "fica dentro") + " dessa faixa;"
        if an.resistencia:
            t += f" resistência {brl(an.resistencia.low)} " + ("fica fora." if an.resistencia.low > up else "fica dentro.")
        out.append(t)
    for d, nome, dd in an.eventos:
        out.append(f"Evento em {dd} dia(s): {nome} ({d:%d/%m}). A IV costuma subir até o evento e cair logo depois; venda que atravessa o evento carrega risco de gap, compra feita antes paga IV inflada.")
    if an.tendencia.startswith("Alta") and an.suporte:
        out.append(f"A favor da tendência de alta: venda de put com strike abaixo do suporte {brl(an.suporte.low)} deixa a região de defesa entre o preço e o seu strike.")
    elif an.tendencia.startswith("Baixa") and an.resistencia:
        out.append(f"A favor da tendência de baixa: venda de call com strike acima da resistência {brl(an.resistencia.high)} deixa a região de oferta entre o preço e o seu strike.")
    elif an.tendencia == "Lateral" and an.suporte and an.resistencia:
        out.append(f"Lateral entre {brl(an.suporte.high)} e {brl(an.resistencia.low)}: as bordas do canal são as referências naturais de strike para as duas pontas.")
    return out

def pontuar(an: Analise, s: Sinal, mercado: str | None = None) -> float:
    p = s.forca
    if (s.direcao == "alta" and an.tendencia.startswith("Alta")) or (s.direcao == "baixa" and an.tendencia.startswith("Baixa")):
        p += 1
    if mercado and s.direcao != "neutro":
        if (s.direcao == "alta" and mercado.startswith("Alta")) or (s.direcao == "baixa" and mercado.startswith("Baixa")):
            p += 0.5
        elif (s.direcao == "alta" and mercado.startswith("Baixa")) or (s.direcao == "baixa" and mercado.startswith("Alta")):
            p -= 0.5
    return p

# ------------------------------------------------------------------ dados do Profit (CSV exportado)
def ler_csv_profit(arquivo) -> dict[str, pd.DataFrame]:
    """Aceita o CSV/TXT exportado do gráfico do Profit (separador ; e vírgula decimal)."""
    raw = pd.read_csv(arquivo, sep=None, engine="python", dtype=str)
    cols = {c: c.strip().lower() for c in raw.columns}
    def acha(*chaves):
        for c, lc in cols.items():
            if any(k in lc for k in chaves):
                return c
        return None
    m = {"Date": acha("data", "date"), "Open": acha("abert", "open"), "High": acha("máx", "max", "high"),
         "Low": acha("mín", "min", "low"), "Close": acha("fech", "close", "últ", "ult"), "Volume": acha("volume", "vol")}
    if not all(m[k] for k in ("Date", "Open", "High", "Low", "Close")):
        raise ValueError("Não encontrei as colunas Data/Abertura/Máxima/Mínima/Fechamento no arquivo.")
    tick = acha("ativo", "papel", "ticker", "símbolo", "simbolo")
    df = pd.DataFrame()
    for k, c in m.items():
        if c is None:
            continue
        if k == "Date":
            df[k] = pd.to_datetime(raw[c].str.strip(), dayfirst=True, errors="coerce")
        else:
            s = raw[c].astype(str).str.strip()
            if s.str.contains(",", regex=False).any():
                s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
            df[k] = pd.to_numeric(s, errors="coerce")
    df["Ativo"] = raw[tick].str.strip().str.upper() if tick else "ARQUIVO"
    df = df.dropna(subset=["Date", "Close"])
    out = {}
    for a, g in df.groupby("Ativo"):
        g = g.groupby(g["Date"].dt.normalize()).agg(Open=("Open", "first"), High=("High", "max"), Low=("Low", "min"),
                                                     Close=("Close", "last"), **({"Volume": ("Volume", "sum")} if "Volume" in g else {}))
        out[a] = g.sort_index()
    return out

def semanal(df: pd.DataFrame) -> pd.DataFrame:
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
    if "Volume" in df:
        agg["Volume"] = "sum"
    return df.resample("W-FRI").agg(agg).dropna(subset=["Close"])
