"""
ui_confluencia.py
=================
Camada visual (Streamlit) do Score de Confluencia.

Funciona para QUALQUER lista de tickers (nao ha universo fixo de 13 nem de
40 -- a lista vem de fora, normalmente da coluna CODIGO do RADAR do Diego).

Duas formas de uso:
  1) render_confluencia(st, tickers, extras=None, df_programas=None) -> tela cheia
  2) render_confluencia_card(st, ticker, tickers_universo, extras=None) ->
     card compacto pra dentro da pagina de detalhe de UM ativo (aba
     Movimentacao).

`tickers_universo` em render_confluencia_card precisa ser a MESMA lista
completa usada na tela cheia, porque a normalizacao do score e relativa ao
universo (o maior valor em R$ do grupo) -- passar so 1 ticker quebraria essa
normalizacao.

Esse score e sobre MOVIMENTACAO -- quem esta comprando/vendendo (insiders,
controlador, a propria empresa). Valuation e dividend safety SAIRAM daqui
(eram dimensoes sem relacao causal com movimentacao, so confundiam a leitura
-- a pedido do Diego, 24/06).

`extras` (opcional, em ambas): DataFrame com coluna ['ticker','recompra']
vindo do RADAR (Fundamentus) -- quando passado, o Score de Confluencia passa
a usar 3 sinais (insider/controlador da CVM + recompra do Fundamentus) em
vez de so os 2 da CVM.

`df_programas` (opcional, so na tela cheia): DataFrame de
baixar_programa_recompra() -- mostra uma coluna extra na tabela com quem tem
Programa de Recompra EM ANDAMENTO (autorizacao, nao execucao -- ver
cvm_insiders.py).
"""

import datetime
import pandas as pd

try:
    from logica_score import score_confluencia,
