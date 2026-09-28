"""
Radar multi-tempo (top-down): semanal -> diário -> 60 min -> 15 min.

Cada tempo gráfico recebe a mesma análise do Radar (tendência por médias + estrutura + ADX,
suportes/resistências, figuras, rompimentos) e mais: IFR, OBV, Didi Index e armadilhas
(traps) de topo/fundo relevante. Depois a cascata junta tudo num plano:
  - o semanal e o diário dizem a DIREÇÃO e as REGIÕES (vale para carrego);
  - o 60 e o 15 dizem o MOMENTO e os GATILHOS (vale para entrar ou para day trade).
Os gatilhos são preços: o disparo acontece no Profit, em tempo real (alarme de preço ou planilha).
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
import radar_engine as R

TFS = [("S", "Semanal"), ("D", "Diário"), ("60", "60 min"), ("15", "15 min")]

# ------------------------------------------------------------------ indicadores extras
def obv(df: pd.DataFrame) -> pd.Series:
    v = df["Volume"].fillna(0)
    sinal = np.sign(df["Close"].diff()).fillna(0)
    return (sinal * v).cumsum()

def didi(df: pd.DataFrame):
    """Didi Index (Odir Aguiar): médias de 3 e 20 normalizadas pela de 8 (linha de referência = 1)."""
    m3, m8, m20 = R.sma(df["Close"], 3), R.sma(df["Close"], 8), R.sma(df["Close"], 20)
    return m3 / m8, m20 / m8

def agulhada(rapida: pd.Series, lenta: pd.Series, janela: int = 3):
    """Agulhada: a curva rápida cruza a referência para um lado e a lenta para o outro, quase juntas."""
    r, l = rapida.values, lenta.values
    n = len(r)
    for i in range(n - 1, max(n - 1 - janela, 1), -1):
        if np.isnan(r[i]) or np.isnan(l[i]):
            continue
        cr_up = r[i] > 1 and r[i - 1] <= 1
        cr_dn = r[i] < 1 and r[i - 1] >= 1
        lw = range(max(i - 1, 1), min(i + 2, n))
        l_dn = any(l[j] < 1 and l[j - 1] >= 1 for j in lw)
        l_up = any(l[j] > 1 and l[j - 1] <= 1 for j in lw)
        if cr_up and l_dn:
            return "alta", n - 1 - i
        if cr_dn and l_up:
            return "baixa", n - 1 - i
    return None, None

# ------------------------------------------------------------------ análise de um tempo gráfico
@dataclass
class LeituraTF:
    tf: str
    nome: str
    an: R.Analise
    direcao: str                 # tendência estrutural: alta / baixa / lateral (médias + topos e fundos)
    ifr_txt: str
    obv_txt: str
    obv_dir: str
    didi_txt: str
    didi_dir: str | None
    traps: list = field(default_factory=list)   # R.Sinal
    ultimo_topo: float | None = None
    ultimo_fundo: float | None = None
    fase: str = ""               # subindo / caindo / reagindo / recuando (últimos candles)
    rotulo: str = ""             # o que aparece no mapa: "Baixa · repicando"
    momento: str = "lateral"     # direção dos últimos candles: alta / baixa / lateral

def traps(an: R.Analise) -> list:
    """Rompimento de topo/fundo relevante (zona com 2+ toques ou último topo/fundo) que volta em até 3 candles."""
    df, zs, a = an.df, an.zonas, an.atr
    H, L, C = df["High"].values, df["Low"].values, df["Close"].values
    n = len(df)
    niveis_top = [(z.high, f"resistência {R.brl(z.high)} ({z.toques} toques)") for z in zs if z.toques >= 2]
    niveis_bot = [(z.low, f"suporte {R.brl(z.low)} ({z.toques} toques)") for z in zs if z.toques >= 2]
    if an.highs:
        niveis_top.append((an.highs[-1][1], f"último topo {R.brl(an.highs[-1][1])}"))
    if an.lows:
        niveis_bot.append((an.lows[-1][1], f"último fundo {R.brl(an.lows[-1][1])}"))
    out = []
    for nv, nome in niveis_top:
        for j in range(n - 4, n - 1):
            if j < 1:
                continue
            if H[j] > nv + 0.1 * a and C[j - 1] <= nv and C[-1] < nv and max(C[j:n - 1]) >= nv - 0.05 * a:
                topo = H[j:].max()
                out.append(R.Sinal("Trap de compra", "baixa", 3 if C[j] > nv else 2,
                                   f"Rompeu {nome} e voltou para baixo em {n - 1 - j} candle(s): quem comprou o rompimento ficou preso.",
                                   stop=topo + 0.1 * a, alvo=None, idx=j))
                break
    for nv, nome in niveis_bot:
        for j in range(n - 4, n - 1):
            if j < 1:
                continue
            if L[j] < nv - 0.1 * a and C[j - 1] >= nv and C[-1] > nv and min(C[j:n - 1]) <= nv + 0.05 * a:
                fundo = L[j:].min()
                out.append(R.Sinal("Trap de venda", "alta", 3 if C[j] < nv else 2,
                                   f"Perdeu {nome} e voltou para cima em {n - 1 - j} candle(s): quem vendeu a perda ficou preso.",
                                   stop=fundo - 0.1 * a, alvo=None, idx=j))
                break
    return out

def ler_tf(ativo: str, tf: str, nome: str, df: pd.DataFrame, hoje=None, eventos=None) -> LeituraTF | None:
    an = R.analisar(ativo, df, eventos if tf == "D" else None, hoje)
    if an is None:
        return None
    d = an.df
    d["OBV"] = obv(d)
    d["OBVM"] = d["OBV"].rolling(20).mean()
    rap, len_ = didi(d)
    d["DIDI_R"], d["DIDI_L"] = rap, len_
    direcao = "alta" if an.tendencia.startswith("Alta") else "baixa" if an.tendencia.startswith("Baixa") else "lateral"
    # IFR
    ifr = an.rsi
    if ifr >= 70:
        ifr_txt = f"IFR {ifr:.0f}: sobrecomprado (esticado para cima)"
    elif ifr <= 30:
        ifr_txt = f"IFR {ifr:.0f}: sobrevendido (esticado para baixo)"
    elif ifr >= 50:
        ifr_txt = f"IFR {ifr:.0f}: força compradora"
    else:
        ifr_txt = f"IFR {ifr:.0f}: força vendedora"
    # OBV
    if d["Volume"].fillna(0).sum() == 0 or math.isnan(d["OBVM"].iloc[-1]):
        obv_txt, obv_dir = "OBV sem volume disponível", "neutro"
    else:
        sobe = d["OBV"].iloc[-1] > d["OBVM"].iloc[-1]
        obv_dir = "alta" if sobe else "baixa"
        preco_sobe = d["Close"].iloc[-1] > d["Close"].iloc[-21] if len(d) > 21 else sobe
        if sobe == preco_sobe:
            obv_txt = "OBV " + ("subindo: o volume confirma a alta" if sobe else "caindo: o volume confirma a queda")
        else:
            obv_txt = "OBV " + ("subindo com preço caindo: acumulação (volume não confirma a queda)" if sobe
                                else "caindo com preço subindo: distribuição (volume não confirma a alta)")
    # Didi
    dd, ha = agulhada(d["DIDI_R"], d["DIDI_L"])
    if dd:
        didi_txt = f"Didi: agulhada de {'compra' if dd == 'alta' else 'venda'} há {ha} candle(s)"
    else:
        r_, l_ = d["DIDI_R"].iloc[-1], d["DIDI_L"].iloc[-1]
        if np.isnan(r_) or np.isnan(l_):
            didi_txt = "Didi: sem dados"
        elif r_ > 1 > l_:
            didi_txt = "Didi: médias abertas para cima (tendência de alta em curso)"
        elif r_ < 1 < l_:
            didi_txt = "Didi: médias abertas para baixo (tendência de baixa em curso)"
        else:
            didi_txt = "Didi: médias embaralhadas (sem direção)"
    tr = traps(an)
    # fase: o que os últimos candles estão fazendo em relação à MME9
    e9 = d["EMA9"].values
    p = an.preco
    inc = e9[-1] - e9[-4]
    if p > e9[-1] and inc > 0:
        fase, momento = "subindo", "alta"
    elif p < e9[-1] and inc < 0:
        fase, momento = "caindo", "baixa"
    elif p > e9[-1]:
        fase, momento = "reagindo", "alta"
    else:
        fase, momento = "recuando", "baixa"
    if direcao == "alta":
        rot = {"subindo": "subindo", "reagindo": "retomando", "recuando": "corrigindo", "caindo": "corrigindo"}[fase]
    elif direcao == "baixa":
        rot = {"caindo": "caindo", "recuando": "retomando a queda", "reagindo": "repicando", "subindo": "repicando"}[fase]
    else:
        rot = {"subindo": "subindo", "reagindo": "subindo", "caindo": "caindo", "recuando": "caindo"}[fase]
    rotulo = f"{an.tendencia} · {rot}"
    return LeituraTF(tf, nome, an, direcao, ifr_txt, obv_txt, obv_dir, didi_txt, dd, tr,
                     an.highs[-1][1] if an.highs else None, an.lows[-1][1] if an.lows else None,
                     fase, rotulo, momento)

# ------------------------------------------------------------------ cascata
@dataclass
class Cascata:
    ativo: str
    leituras: dict
    vies: str
    alinhamento: str
    forca: int                   # 0..4 tempos a favor do viés
    destaques: list
    plano_carrego: str
    plano_curto: str
    gatilhos: list               # (descrição, preço, direção)

def cascata(ativo: str, leituras: dict) -> Cascata:
    ordem = [tf for tf, _ in TFS if tf in leituras]
    dirs = {tf: leituras[tf].direcao for tf in ordem}
    maior = dirs.get("S") or dirs.get("D") or "lateral"
    diario = dirs.get("D", "lateral")
    vies = diario if diario != "lateral" else maior
    forca = sum(1 for tf in ordem if (dirs[tf] if tf in ("S", "D") else leituras[tf].momento) == vies) if vies != "lateral" else 0
    nomes = {tf: n for tf, n in TFS}
    a_favor = [nomes[tf] for tf in ordem if dirs[tf] == vies]
    contra = [nomes[tf] for tf in ordem if vies != "lateral" and dirs[tf] not in (vies, "lateral")]
    s_dir = dirs.get("S", "lateral")
    mom = {tf: leituras[tf].momento for tf in ordem}
    curto_contra = [nomes[tf] for tf in ("60", "15") if tf in mom and vies != "lateral" and mom[tf] != vies]
    if vies == "lateral":
        alinhamento = "Sem direção definida no semanal e no diário"
    elif forca == len(ordem):
        estr_contra = [nomes[tf] for tf in ("60", "15") if tf in dirs and dirs[tf] not in (vies, "lateral")]
        if estr_contra:
            alinhamento = (f"Viés de {vies} e o curto prazo {'subindo' if vies == 'alta' else 'caindo'} agora "
                           f"({', '.join(estr_contra)} ainda de {'baixa' if vies == 'alta' else 'alta'} na estrutura: virada em andamento)")
        else:
            alinhamento = f"Tudo alinhado para {vies}"
    elif s_dir not in (vies, "lateral"):
        alinhamento = f"Conflito: semanal de {s_dir} e diário de {vies} (o diário pode estar só corrigindo o semanal)"
    elif curto_contra:
        base = f"Semanal e diário de {vies}" if s_dir == vies else f"Diário de {vies} (semanal {s_dir})"
        mov = "correção" if vies == "alta" else "repique"
        alinhamento = (f"{base}; {', '.join(curto_contra)} {'corrigindo' if vies == 'alta' else 'repicando'}: "
                       f"{mov} no curto prazo. A entrada a favor do diário vem quando o curto prazo virar de novo")
    else:
        alinhamento = f"Viés de {vies} ({', '.join(a_favor)} a favor)"

    destaques, vistos = [], set()
    for tf in ordem:
        L = leituras[tf]
        for s in L.an.sinais + L.traps:
            if (s.forca >= 2 or s.nome.startswith("Trap")) and (tf, s.nome) not in vistos:
                vistos.add((tf, s.nome))
                destaques.append((tf, s))
        if L.didi_dir:
            destaques.append((tf, R.Sinal("Agulhada do Didi", L.didi_dir, 2, L.didi_txt)))

    # ---- planos
    d = leituras.get("D")
    q = leituras.get("15") or leituras.get("60")
    plano_carrego, plano_curto, gatilhos = "", "", []
    if d:
        sup, res = d.an.suporte, d.an.resistencia
        if vies == "alta" and "S" in dirs and dirs["S"] != "baixa":
            plano_carrego = ("Carrego a favor: compra à vista ou call/venda de put com stop abaixo de "
                             + (R.brl(sup.low) if sup else "o último fundo diário")
                             + (f"; alvo inicial na resistência {R.brl(res.low)}." if res else "."))
        elif vies == "baixa" and "S" in dirs and dirs["S"] != "alta":
            plano_carrego = ("Carrego a favor: proteção, put ou venda de call acima de "
                             + (R.brl(res.high) if res else "o último topo diário") + ".")
        else:
            plano_carrego = "Semanal e diário não concordam: carrego só com tamanho menor, ou esperar o diário definir."
    if q:
        topo, fundo = q.ultimo_topo, q.ultimo_fundo
        trap_q = [s for s in q.traps]
        if trap_q:
            s = trap_q[0]
            plano_curto = (f"{s.nome} no {q.nome}: {s.texto} Operação curta "
                           + ("de compra" if s.direcao == "alta" else "de venda") + (f", invalida em {R.brl(s.stop)}." if s.stop else "."))
            if s.direcao == "alta" and topo:
                gatilhos.append((f"Compra: rompimento do último topo do {q.nome}", topo, "alta"))
            if s.direcao == "baixa" and fundo:
                gatilhos.append((f"Venda: perda do último fundo do {q.nome}", fundo, "baixa"))
        elif vies == "alta":
            p = q.an.preco
            if topo and topo > p:
                plano_curto = f"No {q.nome}, a entrada de compra vem no rompimento do último topo ({R.brl(topo)})"
                gatilhos.append((f"Entrada de compra: rompe o último topo do {q.nome}", topo, "alta"))
            else:
                ref = q.an.df["EMA21"].iloc[-1]
                plano_curto = f"No {q.nome}, o preço já está acima do último topo: melhor esperar um recuo até a MME21 ({R.brl(ref)}) que segure"
                gatilhos.append((f"Zona de recompra: recuo até a MME21 do {q.nome}", ref, "alta"))
            if fundo and fundo < p:
                plano_curto += f", com stop abaixo do último fundo ({R.brl(fundo)})."
                gatilhos.append((f"Invalida a compra: perde o último fundo do {q.nome}", fundo, "baixa"))
            else:
                plano_curto += "."
        elif vies == "baixa":
            p = q.an.preco
            if fundo and fundo < p:
                plano_curto = f"No {q.nome}, a entrada de venda vem na perda do último fundo ({R.brl(fundo)})"
                gatilhos.append((f"Entrada de venda: perde o último fundo do {q.nome}", fundo, "baixa"))
            else:
                ref = q.an.df["EMA21"].iloc[-1]
                plano_curto = f"No {q.nome}, o preço já está abaixo do último fundo: melhor esperar um repique até a MME21 ({R.brl(ref)}) que não passe"
                gatilhos.append((f"Zona de revenda: repique até a MME21 do {q.nome}", ref, "baixa"))
            if topo and topo > p:
                plano_curto += f", com stop acima do último topo ({R.brl(topo)})."
                gatilhos.append((f"Invalida a venda: rompe o último topo do {q.nome}", topo, "alta"))
            else:
                plano_curto += "."
        else:
            plano_curto = "Sem direção nos tempos maiores: só operações curtas nas bordas, a partir de traps."
    if d and d.an.resistencia:
        gatilhos.append(("Diário: rompimento da resistência", float(d.an.resistencia.high), "alta"))
    if d and d.an.suporte:
        gatilhos.append(("Diário: perda do suporte", float(d.an.suporte.low), "baixa"))
    return Cascata(ativo, leituras, vies, alinhamento, forca, destaques, plano_carrego, plano_curto, gatilhos)

def pontuacao(c: Cascata) -> float:
    base = c.forca * 2 if c.vies != "lateral" else 0
    base += sum(3 if s.nome.startswith("Trap") else s.forca for _, s in c.destaques[:6]) * 0.5
    return base
