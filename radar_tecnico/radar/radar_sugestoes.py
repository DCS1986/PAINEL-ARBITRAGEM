"""
Sugestões de operação com entrada, stop, alvo e assimetria explicados,
e o acompanhamento do desfecho de cada sugestão ("e se eu tivesse seguido?").

Regras (iguais para todas as sugestões, para o placar ser honesto):
  - a entrada é uma ORDEM STOP no gatilho: só vale se o preço passar do gatilho depois da sugestão;
  - se o gatilho não for atingido dentro da validade, a sugestão expira sem operação;
  - stop e alvo são os da sugestão; se os dois caem no mesmo candle, conta como stop;
  - no fim do prazo máximo, a operação é encerrada no último preço.
Horizontes:
  SWING  (dias a semanas): leitura no diário, contexto semanal e 60 min. Gatilho vale 3 pregões; prazo máximo 20 pregões.
  CURTO  (horas a 2 dias): leitura no 60 min, contexto diário. Gatilho vale até o fim do pregão seguinte; prazo máximo 2 pregões.
Só vira sugestão o que for EXPLÍCITO: assimetria de pelo menos 2:1 até uma região real, stop curto em ATR,
e os tempos maiores sem estar contra.
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
import radar_engine as R

RR_MIN = 2.0
COLUNAS = ["id", "criada_em", "ativo", "horizonte", "direcao", "setup", "gatilho", "stop", "alvo", "rr", "risco_pct",
           "validade_ate", "prazo_pregoes", "contexto", "por_que_entrada", "por_que_stop", "por_que_alvo", "assimetria",
           "status", "entrada_em", "entrada_preco", "saida_em", "saida_preco", "resultado_r", "resultado_pct",
           "mfe_r", "mae_r", "atualizado_em"]
ABERTOS = ("aguardando gatilho", "em andamento")

def _brl(x):
    return R.brl(float(x))

def _pct(x):
    return f"{x*100:.1f}%".replace(".", ",")

def _alvo(direcao, entrada, stop, zonas, extra=None, dist_max=None):
    """Primeira região real (zona com 2+ toques ou extremo) que dá pelo menos RR_MIN, dentro do alcance do horizonte."""
    risco = abs(entrada - stop)
    cands = []
    for z in zonas:
        if direcao == "alta" and z.low > entrada:
            cands.append((z.low, f"resistência em {_brl(z.low)} ({z.toques} toque{'s' if z.toques > 1 else ''})"))
        if direcao == "baixa" and z.high < entrada:
            cands.append((z.high, f"suporte em {_brl(z.high)} ({z.toques} toque{'s' if z.toques > 1 else ''})"))
    if extra:
        cands.append(extra)
    cands.sort(key=lambda x: x[0], reverse=(direcao == "baixa"))
    for preco, nome in cands:
        rr = abs(preco - entrada) / risco if risco > 0 else 0
        if dist_max is not None and abs(preco - entrada) > dist_max:
            return None, None, 0     # a primeira região boa está longe demais para o prazo
        if rr >= RR_MIN:
            return preco, nome, rr
    return None, None, 0

def _explicacoes(direcao, setup, gatilho, stop, alvo, alvo_nome, ref_txt, atr, tf_nome, horizonte):
    compra = direcao == "alta"
    risco = abs(gatilho - stop)
    ganho = abs(alvo - gatilho)
    rr = ganho / risco
    empate = 1 / (1 + rr)
    folga = abs(stop - ref_txt[1]) if ref_txt[1] is not None else None
    lado = "passar de" if compra else "perder"
    por_que_entrada = (f"{'Compra' if compra else 'Venda'} só se o preço {lado} {_brl(gatilho)} "
                       f"({'máxima' if compra else 'mínima'} do último candle do {tf_nome.lower()}). Esperar o rompimento confirma que "
                       f"{'os compradores' if compra else 'os vendedores'} retomaram o controle; se não acontecer, a operação nem começa e você não perde nada.")
    base = {
        "Pullback": f"fica abaixo de {ref_txt[0]}, a região que segurou a correção. Se o preço perder essa região, deixa de ser um recuo dentro da alta e a tese acaba."
                    if compra else f"fica acima de {ref_txt[0]}, a região que segurou o repique. Se o preço passar dela, deixa de ser um repique dentro da baixa.",
        "Trap": f"fica além do extremo da armadilha ({ref_txt[0]}). A tese é que quem entrou no rompimento falso ficou preso; se o preço voltar lá, a armadilha não funcionou.",
        "Fundo duplo": f"fica abaixo dos dois fundos ({ref_txt[0]}). Se o preço renovar a mínima, a figura deixa de existir.",
        "Topo duplo": f"fica acima dos dois topos ({ref_txt[0]}). Se o preço renovar a máxima, a figura deixa de existir.",
        "Rompimento": f"fica dentro da região rompida ({ref_txt[0]}). Resistência rompida deve virar suporte; se o preço voltar para dentro dela, o rompimento foi falso."
                      if compra else f"fica dentro da região perdida ({ref_txt[0]}). Suporte perdido deve virar resistência; se o preço voltar para dentro dela, a perda foi falsa.",
    }[setup]
    por_que_stop = (f"Fica em {_brl(stop)}: {base}"
                    + (f" A folga de {_brl(folga)} além do nível é uma fração do ATR do {tf_nome.lower()} ({_brl(atr)}), para não ser tirado por um pavio comum." if folga else ""))
    por_que_alvo = f"Fica em {_brl(alvo)}: {alvo_nome}, onde {'os vendedores' if compra else 'os compradores'} apareceram antes. É o primeiro obstáculo real no caminho."
    assimetria = (f"Arrisca {_brl(risco)} por ação ({_pct(risco / gatilho)}) para buscar {_brl(ganho)} ({_pct(ganho / gatilho)}): "
                  f"assimetria de {str(round(rr, 1)).replace('.', ',')} para 1. Com isso, acertar {empate*100:.0f}% das vezes já empata; o resto é lucro.")
    return por_que_entrada, por_que_stop, por_que_alvo, assimetria, rr

def gerar(cascata, agora: pd.Timestamp, eventos=None, horizontes=("SWING", "CURTO")) -> list[dict]:
    """Transforma a leitura multi-tempo de um ativo em sugestões explícitas (pode devolver nenhuma)."""
    L = cascata.leituras
    out = []
    S, D, H = L.get("S"), L.get("D"), L.get("60")
    ativo = cascata.ativo

    def ctx_txt(extra=""):
        partes = []
        for tf, nome in (("S", "semanal"), ("D", "diário"), ("60", "60 min"), ("15", "15 min")):
            if tf in L:
                partes.append(f"{nome}: {L[tf].rotulo.lower()}")
        return "; ".join(partes) + (f". {extra}" if extra else ".")

    def montar(horizonte, tfL, direcao, setup, stop, ref, extra_alvo=None, nota=""):
        an = tfL.an
        d = an.df
        gat = float(d["High"].iloc[-1] + 0.01) if direcao == "alta" else float(d["Low"].iloc[-1] - 0.01)
        if stop is None or (direcao == "alta" and stop >= gat) or (direcao == "baixa" and stop <= gat):
            return
        risco = abs(gat - stop)
        lim_atr = 1.6 if horizonte == "SWING" else 2.0
        if risco > lim_atr * an.atr or risco / gat > (0.06 if horizonte == "SWING" else 0.03):
            return   # stop caro demais: não é explícito
        zonas = [z for z in (D.an.zonas if D else []) + an.zonas if z.toques >= 2]
        atr_d = D.an.atr if D else an.atr
        alvo, alvo_nome, rr = _alvo(direcao, gat, stop, zonas, extra_alvo, dist_max=(6 if horizonte == "SWING" else 1.5) * atr_d)
        if alvo is None:
            return   # sem assimetria real até uma região
        pe, ps, pa, asm, rr = _explicacoes(direcao, setup, gat, stop, alvo, alvo_nome, ref, an.atr, tfL.nome, horizonte)
        ev = [e for e in (D.an.eventos if D else [])] if horizonte == "SWING" else []
        aviso = f"Atenção: {ev[0][1]} em {ev[0][2]} dias, dentro do prazo." if ev else ""
        dias_val = 3 if horizonte == "SWING" else 1
        validade = (agora.normalize() + pd.tseries.offsets.BDay(dias_val) + pd.Timedelta(hours=18))
        out.append(dict(
            id=f"{agora:%Y%m%d%H%M}-{ativo}-{horizonte}-{direcao}",
            criada_em=agora.strftime("%Y-%m-%d %H:%M"), ativo=ativo, horizonte=horizonte, direcao=direcao, setup=setup,
            gatilho=round(gat, 2), stop=round(float(stop), 2), alvo=round(float(alvo), 2), rr=round(rr, 2),
            risco_pct=round(risco / gat, 4), validade_ate=validade.strftime("%Y-%m-%d %H:%M"),
            prazo_pregoes=20 if horizonte == "SWING" else 2, contexto=ctx_txt(" ".join(x for x in (nota, aviso) if x)),
            por_que_entrada=pe, por_que_stop=ps, por_que_alvo=pa, assimetria=asm,
            status="aguardando gatilho", atualizado_em=agora.strftime("%Y-%m-%d %H:%M")))

    def candidatos(tfL):
        """Setups do tempo gráfico com stop técnico e texto da referência."""
        an = tfL.an
        a = an.atr
        res = []
        for s in an.sinais + tfL.traps:
            if s.nome.startswith("Pullback"):
                ref = an.suporte.low if an.suporte and an.suporte.high >= an.df["Low"].iloc[-3:].min() - 0.5 * a else an.df["Low"].iloc[-3:].min()
                res.append(("alta", "Pullback", ref - 0.2 * a, (f"{_brl(ref)} (suporte/mínima do recuo)", ref)))
            elif s.nome.startswith("Repique"):
                ref = an.resistencia.high if an.resistencia and an.resistencia.low <= an.df["High"].iloc[-3:].max() + 0.5 * a else an.df["High"].iloc[-3:].max()
                res.append(("baixa", "Pullback", ref + 0.2 * a, (f"{_brl(ref)} (resistência/máxima do repique)", ref)))
            elif s.nome == "Trap de venda" and s.stop:
                res.append(("alta", "Trap", s.stop, (f"{_brl(s.stop + 0.1 * a)}, a mínima do rompimento falso", s.stop + 0.1 * a)))
            elif s.nome == "Trap de compra" and s.stop:
                res.append(("baixa", "Trap", s.stop, (f"{_brl(s.stop - 0.1 * a)}, a máxima do rompimento falso", s.stop - 0.1 * a)))
            elif s.nome == "Fundo duplo confirmado" and s.stop:
                res.append(("alta", "Fundo duplo", s.stop, (f"{_brl(s.stop + 0.3 * a)}", s.stop + 0.3 * a)))
            elif s.nome == "Topo duplo confirmado" and s.stop:
                res.append(("baixa", "Topo duplo", s.stop, (f"{_brl(s.stop - 0.3 * a)}", s.stop - 0.3 * a)))
            elif s.nome == "Rompimento de resistência" and s.forca >= 3 and s.stop:
                res.append(("alta", "Rompimento", s.stop, (f"{_brl(s.stop + 0.5 * a)}", s.stop + 0.5 * a)))
            elif s.nome == "Perda de suporte" and s.forca >= 3 and s.stop:
                res.append(("baixa", "Rompimento", s.stop, (f"{_brl(s.stop - 0.5 * a)}", s.stop - 0.5 * a)))
        return res

    # ---- SWING: setup no diário, semanal não contra, diário a favor (estrutura ou armadilha)
    if D and "SWING" in horizontes:
        for direcao, setup, stop, ref in candidatos(D):
            if S and S.direcao not in (direcao, "lateral"):
                continue
            if D.direcao != direcao and not (setup == "Trap" and D.direcao == "lateral"):
                continue
            nota = "60 min já virando a favor." if H and H.momento == direcao else "60 min ainda não virou: espere o gatilho."
            montar("SWING", D, direcao, setup, stop, ref, nota=nota)
    # ---- CURTO: setup no 60 min a favor do diário
    if H and D and "CURTO" in horizontes:
        for direcao, setup, stop, ref in candidatos(H):
            if D.direcao not in (direcao, "lateral") and setup != "Trap":
                continue
            montar("CURTO", H, direcao, setup, stop, ref)
    # só a melhor por horizonte e direção
    melhor = {}
    for s in out:
        k = (s["horizonte"], s["direcao"])
        if k not in melhor or s["rr"] > melhor[k]["rr"]:
            melhor[k] = s
    return list(melhor.values())

def atualizar(s: dict, df: pd.DataFrame, agora: pd.Timestamp) -> dict:
    """Recalcula o desfecho de uma sugestão com candles (15 ou 60 min) posteriores à criação."""
    s = dict(s)
    if s.get("status") not in ABERTOS:
        return s
    criada = pd.Timestamp(s["criada_em"])
    validade = pd.Timestamp(s["validade_ate"])
    alta = s["direcao"] == "alta"
    gat, stop, alvo = float(s["gatilho"]), float(s["stop"]), float(s["alvo"])
    risco = abs(gat - stop)
    d = df[df.index > criada]
    if not len(d):
        s["atualizado_em"] = agora.strftime("%Y-%m-%d %H:%M")
        return s
    H, L, C, O = d["High"].values, d["Low"].values, d["Close"].values, d["Open"].values
    idx = d.index
    # 1) gatilho
    ent_i = None
    if pd.isna(s.get("entrada_em")) or not s.get("entrada_em"):
        for i in range(len(d)):
            if idx[i] > validade:
                break
            if (alta and H[i] >= gat) or (not alta and L[i] <= gat):
                ent_i = i
                ent = max(gat, O[i]) if alta else min(gat, O[i])
                s["entrada_em"], s["entrada_preco"] = idx[i].strftime("%Y-%m-%d %H:%M"), round(float(ent), 2)
                break
        if ent_i is None:
            if agora > validade or (len(d) and idx[-1] > validade):
                s["status"] = "não acionada"
            s["atualizado_em"] = agora.strftime("%Y-%m-%d %H:%M")
            return s
    else:
        ent_i = int(np.searchsorted(idx.values, np.datetime64(pd.Timestamp(s["entrada_em"]))))
    ent = float(s["entrada_preco"])
    sessoes = pd.Series(idx.normalize()).drop_duplicates().tolist()
    ses_ent = idx[ent_i].normalize()
    limite = [x for x in sessoes if x >= ses_ent][: int(s["prazo_pregoes"])]
    fim = (limite[-1] + pd.Timedelta(hours=23)) if limite else None
    mfe = mae = 0.0
    for i in range(ent_i, len(d)):
        if fim is not None and len(limite) >= int(s["prazo_pregoes"]) and idx[i] > fim:
            ult = C[i - 1]
            r = ((ult - ent) if alta else (ent - ult)) / risco
            s.update(status="encerrada no prazo", saida_em=idx[i - 1].strftime("%Y-%m-%d %H:%M"), saida_preco=round(float(ult), 2),
                     resultado_r=round(r, 2))
            break
        fav = (H[i] - ent) if alta else (ent - L[i])
        adv = (ent - L[i]) if alta else (H[i] - ent)
        mfe, mae = max(mfe, fav / risco), max(mae, adv / risco)
        if (alta and L[i] <= stop) or (not alta and H[i] >= stop):
            px = min(stop, O[i]) if alta else max(stop, O[i])
            s.update(status="stop", saida_em=idx[i].strftime("%Y-%m-%d %H:%M"), saida_preco=round(float(px), 2),
                     resultado_r=round(((px - ent) if alta else (ent - px)) / risco, 2))
            break
        if (alta and H[i] >= alvo) or (not alta and L[i] <= alvo):
            s.update(status="alvo", saida_em=idx[i].strftime("%Y-%m-%d %H:%M"), saida_preco=round(alvo, 2),
                     resultado_r=round(abs(alvo - ent) / risco, 2))
            break
    else:
        ult = C[-1]
        s.update(status="em andamento", resultado_r=round(((ult - ent) if alta else (ent - ult)) / risco, 2))
    if s.get("saida_preco") not in (None, "") and not pd.isna(s.get("saida_preco")):
        px = float(s["saida_preco"])
        s["resultado_pct"] = round(((px - ent) if alta else (ent - px)) / ent, 4)
    elif s["status"] == "em andamento":
        s["resultado_pct"] = round(((C[-1] - ent) if alta else (ent - C[-1])) / ent, 4)
    s["mfe_r"], s["mae_r"] = round(mfe, 2), round(mae, 2)
    s["atualizado_em"] = agora.strftime("%Y-%m-%d %H:%M")
    return s

def juntar(existentes: pd.DataFrame, novas: list[dict], agora: pd.Timestamp) -> pd.DataFrame:
    """Evita repetir: não cria nova sugestão se já houver uma aberta (ou criada nos últimos 3 pregões) para o mesmo ativo/horizonte/direção."""
    ex = existentes.copy() if existentes is not None and len(existentes) else pd.DataFrame(columns=COLUNAS)
    add = []
    for n in novas:
        mesma = ex[(ex["ativo"] == n["ativo"]) & (ex["horizonte"] == n["horizonte"]) & (ex["direcao"] == n["direcao"])]
        if len(mesma):
            if mesma["status"].isin(ABERTOS).any():
                continue
            ult = pd.to_datetime(mesma["criada_em"]).max()
            if (agora - ult) < pd.Timedelta(days=4):
                continue
        add.append(n)
    if add:
        ex = pd.concat([ex, pd.DataFrame(add)], ignore_index=True)
    for c in COLUNAS:
        if c not in ex:
            ex[c] = None
    return ex[COLUNAS]

def atualizar_todos(livro: pd.DataFrame, dados_por_ativo: dict, agora: pd.Timestamp) -> pd.DataFrame:
    if livro is None or not len(livro):
        return pd.DataFrame(columns=COLUNAS)
    linhas = []
    for r in livro.to_dict("records"):
        df = dados_por_ativo.get(r["ativo"])
        linhas.append(atualizar(r, df, agora) if df is not None else r)
    out = pd.DataFrame(linhas)
    for c in COLUNAS:
        if c not in out:
            out[c] = None
    return out[COLUNAS]
