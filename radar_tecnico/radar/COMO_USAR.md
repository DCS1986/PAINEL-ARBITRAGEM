## Para que serve o Radar

O Radar faz a primeira triagem do dia: diz **onde olhar** e **o que perguntar ao gráfico**. Ele não substitui a sua leitura no Profit. Se um alerta não fizer sentido quando você abrir o gráfico, descarte-o: foi para isso que você abriu.

---

## A rotina (15 minutos, depois do fechamento)

**1. Leia o topo antes de qualquer ativo.** O topo define o **tamanho**, não o que você vai operar.
- Índice em alta com mais de 60% dos ativos acima da MM50: ambiente a favor de compras. Tamanho normal.
- Índice em baixa, ou menos de 40% acima da MM50: compras só nos cenários mais claros, com tamanho menor.
- Faixa amarela de evento (eleição, Copom, Fed): qualquer operação que **atravesse** o evento leva tamanho menor, porque gap e queda de IV são prováveis.

**2. Vá ao Plano do dia.** Anote no máximo **3 candidatos** entre os "cenários claros". Mais que isso vira dispersão. Os de "observar" entram numa lista de espera: são os que podem virar cenário claro nos próximos pregões.

**3. Abra cada candidato em Gráfico e leitura.** Confira três coisas:
- A região (suporte ou resistência) aparece com pelo menos 2 toques.
- A linha de invalidação está perto o suficiente para o risco que você aceita.
- A lente de opções diz se o suporte ou a resistência fica **fora** do movimento esperado até o vencimento. Fora é melhor para quem vende.

**4. Valide no Profit.** Três perguntas, e só entra se as três forem "sim":
1. Eu enxergaria essa região sem o Radar ter me mostrado?
2. O último candle confirma (fechou do lado certo, com volume)?
3. Se der errado, sei exatamente onde saio e quanto perco?

**5. Monte a operação.** Use a coluna **Opções** do Plano como ponto de partida e os seus princípios para o ajuste fino:
- Vol alta: vender prêmio. Para quem vende, o risco é **Δ atual + dias restantes**.
- Vol baixa: comprar. Nunca compre opção de Δ baixo com vol alta.
- Strike de venda: do outro lado da região (put abaixo do suporte, call acima da resistência).
- Compra: Δ 60 ou mais, com stop no mesmo ponto de invalidação do gráfico.

**6. Registre o SETUP na planilha.** Ao abrir a operação, escolha na coluna SETUP o nome que corresponde ao alerta (veja a tabela abaixo). É isso que fecha o ciclo.

---

## Como ler cada peça

| Peça | O que significa | O que fazer com ela |
|---|---|---|
| **Tendência** | Direção das médias + estrutura de topos e fundos + força (ADX) | Operar a favor dela é o padrão; contra ela, só com sinal forte e tamanho menor |
| **Local** | Onde o preço está em relação às regiões (em ATR) | "No suporte" ou "na resistência" = stop curto. "No meio do caminho" = esperar |
| **Vol** | Vol realizada comparada com o último ano do próprio ativo | Alta: vender prêmio. Baixa: comprar. Confirme a IV no Profit |
| **Força ●●●** | Quantas confirmações o sinal tem (volume, figura completa) | ●○○ é aviso; ●●● é sinal |
| **A favor / contra** | Alinhamento com a tendência do ativo e do índice | Dois "a favor" = cenário mais limpo |
| **Invalidação** | Onde a leitura deixa de valer | É o seu stop técnico |

---

## Do alerta para o SETUP da planilha

| Alerta do Radar | SETUP na planilha |
|---|---|
| Pullback na tendência de alta / Repique na tendência de baixa | Pullback |
| Rompimento de resistência / Perda de suporte | Rompimento |
| Fundo ou topo duplo, mudança de estrutura, divergência | Reversão |
| Lateral nas bordas | Lateral / canal |
| Venda por vol alta, sem gatilho gráfico | Vol alta (venda) |
| Compra por vol comprimida | Vol baixa (compra) |
| Operação montada por causa de um evento | Evento |

Depois de 30 a 50 operações encerradas, a aba Dashboard da planilha mostra **qual SETUP dá dinheiro para você**. O que funcionar ganha tamanho; o que não funcionar sai da rotina. Nessa etapa o Radar deixa de ser uma ferramenta genérica e passa a refletir o seu jeito de operar.

---

## O que evitar

- Operar um alerta sem abrir o gráfico.
- Entrar contra a tendência **e** contra o índice ao mesmo tempo.
- Comprar opção barata (Δ baixo) com vol alta: você paga caro por pouca chance.
- Vender prêmio que atravessa um evento sem receber o suficiente pelo risco de gap.
- Tratar "sem sinal" como problema. Dias sem cenário claro são dias de não operar.

## Limites

- Dados diários do Yahoo, com atraso. O Radar serve para planejar antes e depois do pregão, não para operar intraday.
- A vol mostrada é a **realizada** (HV). A IV das opções você confere no Profit. Quando a IV está muito acima da HV, o prêmio está caro.
- Figuras muito subjetivas (OCO, triângulos, bandeiras) ficaram de fora de propósito, porque detectores automáticos erram muito nelas.
