"""
logica_score.py
===============
Score de Confluencia do RADAR.

Ideia central (o diferencial): em vez de um numero so, produz DOIS:
  1) SCORE        -> soma ponderada dos sinais, em [-100, +100] (direcao+forca)
  2) CONCORDANCIA -> quantos sinais independentes apontam no mesmo sentido (robustez)

Um score +60 com 4/4 sinais concordando vale muito mais que um +60 puxado por
um unico sinal extremo. Nenhum concorrente mostra a concordancia.

Sinais que vem REAIS do arquivo da CVM (via cvm_insiders):
  - insider_pessoas  (Diretoria + Conselho de Administracao)   peso alto
  - recompra         (a propria Companhia comprando/vendendo)  peso medio
  - controlador      (estrutural)                              peso PEQUENO

Sinais que entram quando voce plugar o RADAR (opcionais):
  - valuation        (desconto vs preco justo; +=barato)
  - dividend_safety  (0-10 do RADAR)
"""

import pandas as pd

from cvm_insiders import (
    carregar_local, baixar_vlmo, MAPA_TICKER_CNPJ,
    CARGOS_PESSOAS_CHAVE, CARGO_CONTROLADOR, MOV_COMPRA, MOV_VENDA, ATIVOS_ACAO,
)

PESOS = {
    "insider_pessoas": 0.35,
    "recompra":        0.25,
    "valuation":       0.20,
    "dividend_safety": 0.15,
    "controlador":     0.05,   # peso pequeno, conforme decidido
}


def _liq(sub):
    compra = sub["vol"].where
