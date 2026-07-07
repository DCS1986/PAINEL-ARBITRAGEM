# setores_data.py — fonte única de dados setoriais
# Importado pelo RADAR Fundamentalista (app.py) e pelo Dossiê (estudo.py)
# Edite aqui; os dois apps atualizam automaticamente.

SETORES = {
    "📄 Papel & Celulose": {
        "tickers": ["KLBN4", "SUZB3", "RANI3"],
        "tagline": "Três empresas, três matérias-primas, três lógicas econômicas completamente distintas.",
        "logica": {
            "titulo": "O que move esse setor",
            "texto": (
                "O mercado agrupa Klabin, Suzano e Irani sob o mesmo rótulo — papel e celulose — "
                "mas são negócios com DNA diferente. O ponto de partida é a matéria-prima: "
                "o tipo de madeira determina o produto, o produto determina o cliente, "
                "o cliente determina a volatilidade e a exposição ao câmbio."
            ),
            "drivers": [
                ("Preço da celulose (BHKP)", "Commodity global cotada em dólar. Ciclos de 2–5 anos. "
                 "Afeta diretamente Suzano. Klabin é parcialmente protegida. Irani tem exposição zero."),
                ("Taxa de câmbio (R$/USD)", "Receita de exportação de celulose é em dólar. "
                 "Dólar alto beneficia exportadoras (Suzano e parte da Klabin). Irani é imune — vende em reais."),
                ("Preço das aparas (OCC)", "Papel reciclado é a matéria-prima principal da Irani. "
                 "Variou de R$610 a R$1.300/tonelada. Cada R$100/t impacta diretamente a margem."),
                ("Custo da madeira", "Plantio próprio (Eucalipto ~7 anos, Pinus ~15 anos) é a principal "
                 "vantagem de custo. Quem tem floresta própria tem previsibilidade de custo por décadas."),
                ("Demanda doméstica de embalagens", "Ligada ao consumo interno, e-commerce e agronegócio. "
                 "Cresceu 2–5% ao ano mesmo em recessão. É o driver da Irani e da embalagem da Klabin."),
            ],
        },
        "comparativo": {
            "dimensoes": [
                "Matéria-prima principal",
                "Produto final",
                "Exposição ao dólar",
                "Exposição ao ciclo de celulose",
                "Mercado principal",
                "Barreira de entrada",
                "Risco-chave",
                "Perfil do investidor",
            ],
            "empresas": {
                "SUZB3": {
                    "nome": "Suzano",
                    "cor": "#63B3ED",
                    "Matéria-prima principal": ("Eucalipto", "fibra curta, crescimento de 7 anos"),
                    "Produto final": ("Celulose BHKP", "commodity global, exportado em fardo"),
                    "Exposição ao dólar": ("Alta", "~100% da receita em dólar", "badge-green"),
                    "Exposição ao ciclo de celulose": ("Máxima", "é o produto único", "badge-red"),
                    "Mercado principal": ("Global", "Europa, China, EUA"),
                    "Barreira de entrada": ("Escala e custo", "maior produtora global, custo entre os mais baixos do mundo"),
                    "Risco-chave": ("Ciclo da celulose", "preço pode cair 30–40% num ciclo negativo"),
                    "Perfil do investidor": ("Commodities + câmbio", "quer exposição a dólar e ciclo global"),
                },
                "KLBN4": {
                    "nome": "Klabin",
                    "cor": "#D4AF37",
                    "Matéria-prima principal": ("Pinus + Eucalipto", "fibra longa e curta — única no Brasil"),
                    "Produto final": ("Papel + Embalagem + Celulose", "portfólio diversificado, 23 plantas"),
                    "Exposição ao dólar": ("Parcial", "exporta celulose, vende embalagem no Brasil", "badge-yellow"),
                    "Exposição ao ciclo de celulose": ("Moderada", "embalagem amorte o ciclo", "badge-yellow"),
                    "Mercado principal": ("Brasil + exportação", "líder em papel para embalagem no Brasil"),
                    "Barreira de entrada": ("Integração vertical + Pinus único", "única com floresta de pinus em escala industrial no Brasil"),
                    "Risco-chave": ("Alavancagem + Capex pesado", "projetos intensivos em capital pressionam caixa por anos"),
                    "Perfil do investidor": ("Diversificação no setor", "menos puro que Suzano, mais estável"),
                },
                "RANI3": {
                    "nome": "Irani",
                    "cor": "#86EFAC",
                    "Matéria-prima principal": ("Aparas (OCC) + Pinus próprio", "70% reciclado, 30% fibra virgem própria"),
                    "Produto final": ("Papelão ondulado + Papel kraft", "embalagem doméstica pura"),
                    "Exposição ao dólar": ("Mínima", "só 15% da receita é exportação", "badge-green"),
                    "Exposição ao ciclo de celulose": ("Zero", "não exporta celulose, não depende do preço global", "badge-green"),
                    "Mercado principal": ("Brasil", "frigoríficos, agro, e-commerce, alimentos"),
                    "Barreira de entrada": ("Integração + localização", "floresta própria de pinus em SC/RS + posição logística"),
                    "Risco-chave": ("Preço das aparas (OCC)", "insumo externo que pode subir 100%+ em eventos climáticos/logísticos"),
                    "Perfil do investidor": ("Brasil puro", "quer crescimento doméstico sem exposição a câmbio ou commodities"),
                },
            },
        },
        "perfis": {
            "SUZB3": {
                "nome": "Suzano",
                "fundacao": "1924",
                "sede": "São Paulo, SP",
                "tagline": "A maior produtora mundial de celulose de eucalipto. Puro jogo de escala, custo e câmbio.",
                "modelo": (
                    "A Suzano planta eucalipto, processa em celulose de fibra curta (BHKP) e exporta "
                    "praticamente tudo em dólar. O produto é commodity global — o preço é dado pelo mercado "
                    "internacional, não pela empresa. Sua vantagem é ser a produtora de menor custo do "
                    "mundo, graças à produtividade do eucalipto brasileiro (o mais rápido do planeta — "
                    "7 anos do plantio ao corte) e à escala das operações após a fusão com a Fibria em 2019."
                ),
                "receita": [
                    ("Celulose BHKP", "~85%", "fibra curta de eucalipto, commodity global"),
                    ("Papel", "~10%", "papel para imprimir/escrever e tissue"),
                    ("Outros", "~5%", "energia, madeira, derivados"),
                ],
                "vantagens": [
                    "Menor custo de produção de celulose do mundo — floresta tropical de crescimento ultrarrápido",
                    "Escala de 10,9 milhões de toneladas/ano — nenhum concorrente chega perto no eucalipto",
                    "Hedge natural: receita em dólar vs. custos em real",
                    "Certificação FSC de toda a base florestal — acesso a mercados premium na Europa",
                ],
                "riscos": [
                    "Preço da celulose cai 30–40% num ciclo negativo — resultado despenca junto",
                    "Dívida em dólar: variação cambial pode gerar prejuízo contábil mesmo com caixa saudável",
                    "Projeto Cerrado (nova fábrica em GO) aumentou alavancagem — deleveraging levará anos",
                    "Produto único: sem diversificação que amortize o ciclo",
                ],
                "barreira": "Escala e custo. Construir uma fábrica de celulose de 2 milhões de toneladas custa ~US$ 5 bilhões e leva 5 anos. Nenhum novo entrante consegue competir no custo sem décadas de plantio próprio.",
            },
            "KLBN4": {
                "nome": "Klabin",
                "fundacao": "1899",
                "sede": "São Paulo, SP",
                "tagline": "A única produtora brasileira com pinus em escala. Integração do bosque à caixa.",
                "modelo": (
                    "A Klabin é a empresa mais complexa do trio. Planta pinus (fibra longa) e eucalipto "
                    "(fibra curta), produz celulose, papel e embalagens — e converte parte em produtos "
                    "acabados como sacos industriais, caixas de papelão e cartões. Vende celulose para "
                    "exportação, mas uma fatia relevante da receita é embalagem doméstica, o que amortece "
                    "o ciclo de commodity. É a maior produtora e exportadora de papel para embalagem do Brasil."
                ),
                "receita": [
                    ("Embalagens (papelão ondulado, caixas)", "~45%", "mercado doméstico, relativamente estável"),
                    ("Papel para embalagem (kraft, cartão)", "~25%", "Brasil e exportação"),
                    ("Celulose (fibra longa e fluff)", "~20%", "exportação, commodity"),
                    ("Sacos industriais", "~10%", "cimento, fertilizante, Brasil"),
                ],
                "vantagens": [
                    "Única produtora de pinus em escala industrial no Brasil — fibra longa que ninguém mais tem",
                    "Diversificação de produto: embalagem amorte o ciclo de celulose",
                    "Integração vertical completa: da floresta ao produto acabado",
                    "Celulose fluff (para fraldas e absorventes) — nicho de margem alta e demanda crescente",
                ],
                "riscos": [
                    "Capex intensivo e constante — projetos de expansão pressionam caixa por anos seguidos",
                    "Alavancagem historicamente alta (4–5x EBITDA em fases de investimento)",
                    "Complexidade operacional: 23 plantas, múltiplos produtos, margens diferentes por linha",
                    "Pinus tem ciclo de 15 anos — planejamento florestal é de altíssimo prazo",
                ],
                "barreira": "O pinus. Ninguém mais tem floresta de pinus em escala no Brasil. Plantar hoje para colher em 15 anos é uma barreira de entrada que efetivamente fecha o mercado para novos entrantes na fibra longa.",
            },
            "RANI3": {
                "nome": "Irani (Celulose Irani)",
                "fundacao": "1941",
                "sede": "Campina da Alegria, SC",
                "tagline": "A única empresa de embalagens sustentáveis pura listada na B3. Brasil puro, sem câmbio.",
                "modelo": (
                    "A Irani não é uma produtora de celulose de mercado. É uma fabricante de embalagens "
                    "que produz sua própria celulose — e usa tudo internamente. Pega aparas (papel "
                    "reciclado descartado por supermercados, e-commerce e frigoríficos), transforma em "
                    "papel kraft e papelão ondulado, e vende para o mercado doméstico. Também tem florestas "
                    "próprias de pinus no Sul (SC e RS), de onde extrai fibra virgem para complementar "
                    "a produção e resina de terebintina como subproduto (usada em tintas a óleo)."
                ),
                "receita": [
                    ("Embalagens de papelão ondulado", "~57%", "frigoríficos, agro, e-commerce, alimentos"),
                    ("Papel para embalagens (kraft)", "~37%", "sacolas, sacos, papel multiwall — Brasil e 15% exportação"),
                    ("Resinas e madeira", "~6%", "terebintina e venda de madeira — subproduto do pinus"),
                ],
                "vantagens": [
                    "Zero exposição ao câmbio e ao ciclo global de celulose — negócio 100% doméstico",
                    "Demanda por embalagem de papelão cresceu 2–5%/ano mesmo em recessão — setor defensivo",
                    "Floresta própria de pinus garante parte do custo estável e previsível",
                    "Capacidade de repasse de preço: quem compra caixa de papelão não tem substituto fácil",
                    "Plataforma Gaia (>R$1 bi investido): ganhos de eficiência ainda sendo colhidos",
                ],
                "riscos": [
                    "Preço das aparas (OCC): insumo externo que representa ~30% do custo — variou de R$610 a R$1.300/t",
                    "Eventos climáticos no Sul (enchentes RS/SC) disruptam o fornecimento de aparas",
                    "Small cap — menor liquidez, menor cobertura de analistas, mais suscetível a humor de mercado",
                    "Capex pesado recente (Gaia) ainda sendo digerido; FCF pressiona no curto prazo",
                ],
                "barreira": "Integração + localização + relacionamento com clientes industriais. No mercado de embalagens, o cliente (frigorífico, agro) não troca de fornecedor facilmente — logística, especificação técnica e volume criam um lock-in operacional relevante.",
            },
        },
    },
    # Placeholder — próximos setores aqui
    "🏦 Bancos": {
        "tickers": ["ITUB4", "BBAS3", "BBDC3", "BPAC11", "SANB3"],
        "tickers_sub": ["ABCB4", "BRSR6", "BMGB4"],
        "label_sub": "Bancos regionais e especializados",
        "tagline": "Mesma licença bancária, oito modelos de negócio completamente distintos. Quem entende a diferença lê o balanço em 10 minutos.",
        "logica": {
            "titulo": "O que move o setor bancário",
            "texto": (
                "Todo banco capta dinheiro a um custo e empresta a um preço maior — a diferença é o spread. "
                "Mas a forma como cada banco capta, para quem empresta e com qual risco é onde os modelos "
                "divergem radicalmente. ITUB e Bradesco são bancões de varejo. BBAS domina o agro e o "
                "funcionalismo. BTG é banco de investimento e wealth. ABC serve exclusivamente empresas. "
                "Banrisul é o banco do RS. BMG só faz consignado para aposentados do INSS. Entender o nicho "
                "de cada um é entender por que um vai bem quando o outro vai mal."
            ),
            "drivers": [
                ("Spread (NIM — Margem Financeira Líquida)", "A diferença entre o juro cobrado do cliente e o juro pago na captação. "
                 "Selic alta aumenta o custo de captação, mas nem sempre aumenta o spread — depende do perfil da carteira. "
                 "Consignado tem spread baixo mas risco também baixo. Crédito pessoal tem spread alto e inadimplência alta."),
                ("Inadimplência (NPL)", "O grande vilão do resultado bancário. Varia por segmento: consignado INSS tem inadimplência "
                 "< 3%, crédito pessoal pode chegar a 10-15%. Banco com carteira concentrada em baixa renda sofre mais em recessão."),
                ("Selic e ciclo de juros", "Juro alto comprime a demanda por crédito mas remunera melhor o PL e a tesouraria. "
                 "Cada banco reage diferente: BTG ama juro alto (tesouraria e renda fixa); varejo de baixa renda sofre "
                 "(inadimplência sobe, demanda cai)."),
                ("Eficiência operacional", "Custo de servir o cliente. Banco digital tem custo por transação próximo de zero. "
                 "Bancão com 4.000 agências tem custo fixo pesado. O índice de eficiência (despesas/receitas) é o termômetro — "
                 "abaixo de 40% é excelente; acima de 60% é ineficiente."),
                ("Qualidade e crescimento da carteira de crédito", "Carteira crescendo é bom sinal, mas só se a qualidade "
                 "se mantiver. O BB errou ao crescer no agro sem critérios — a conta chegou no 1T26 com inadimplência "
                 "saltando de 1% para 6%. Crescimento sem qualidade é receita de provisão futura."),
                ("ROE (Retorno sobre Patrimônio)", "A métrica-rei do setor. Acima de 20% é excepcional (BTG, Itaú). "
                 "Entre 15-20% é sólido. Abaixo de 12% o banco não cobre o custo de capital e destrói valor. "
                 "Bradesco ficou abaixo do custo de capital por dois anos — foi a crise de 2023-2024."),
            ],
        },
        "comparativo": {
            "dimensoes": [
                "Modelo de negócio",
                "Cliente principal",
                "Principal produto de crédito",
                "Exposição ao ciclo econômico",
                "Exposição à política/regulação",
                "Sensibilidade à Selic",
                "ROE atual (ref.)",
                "Risco principal",
                "Perfil do investidor",
            ],
            "grupos": [
                {"label": "Grandes bancos", "tickers": ["ITUB4", "BBAS3", "BBDC3", "BPAC11", "SANB3"]},
                {"label": "Bancos regionais e especializados", "tickers": ["ABCB4", "BRSR6", "BMGB4"]},
            ],
            "empresas": {
                "ITUB4": {
                    "nome": "Itaú Unibanco",
                    "cor": "#F97316",
                    "Modelo de negócio": ("Varejo premium + atacado + seguros", "maior banco privado da AL"),
                    "Cliente principal": ("Alta e média renda", "6 de cada 10 brasileiros de alta renda são clientes"),
                    "Principal produto de crédito": ("Cartão + crédito imobiliário + consignado privado", "mix diversificado"),
                    "Exposição ao ciclo econômico": ("Moderada", "foco em alta renda protege da inadimplência", "badge-yellow"),
                    "Exposição à política/regulação": ("Baixa", "banco privado, sem interferência estatal", "badge-green"),
                    "Sensibilidade à Selic": ("Alta positiva", "tesouraria + PL remunera bem; spread se mantém", "badge-green"),
                    "ROE atual (ref.)": ("~24-26%", "o maior entre os incumbentes"),
                    "Risco principal": ("Competição com fintechs e digitalização do varejo massificado", ""),
                    "Perfil do investidor": ("Qualidade e crescimento previsível", "paga prêmio, mas entrega consistência"),
                },
                "BBAS3": {
                    "nome": "Banco do Brasil",
                    "cor": "#EAB308",
                    "Modelo de negócio": ("Banco estatal universal", "líder em agro, funcionalismo e gestão de ativos"),
                    "Cliente principal": ("Agricultor, servidor público, governo", "processa metade das folhas do setor público"),
                    "Principal produto de crédito": ("Crédito rural + consignado público + crédito governo", "53% do crédito rural do Brasil"),
                    "Exposição ao ciclo econômico": ("Alta", "agro é cíclico — inadimplência rural saltou de 1% para 6% em 2026", "badge-red"),
                    "Exposição à política/regulação": ("Muito alta", "estatal — governo pode intervir na política de crédito", "badge-red"),
                    "Sensibilidade à Selic": ("Alta", "PL e tesouraria remuneram bem; agro sensível a custo de captação", "badge-yellow"),
                    "ROE atual (ref.)": ("~7-8% (1T26)", "pressionado pela crise do agro — era 16% em 2025"),
                    "Risco principal": ("Interferência política + concentração no agro", "inadimplência rural 2025-2026"),
                    "Perfil do investidor": ("Dividendos + tese contrarian", "compra desconto e upside de normalização"),
                },
                "BBDC3": {
                    "nome": "Bradesco",
                    "cor": "#EF4444",
                    "Modelo de negócio": ("Varejo universal", "terceiro maior banco privado, em reestruturação"),
                    "Cliente principal": ("Massa + média renda + PME", "historicamente forte no interior do Brasil"),
                    "Principal produto de crédito": ("Crédito pessoal + PME + consignado", "diversificado mas com foco no varejo"),
                    "Exposição ao ciclo econômico": ("Alta", "massa e PME sofrem mais em recessão e juro alto", "badge-red"),
                    "Exposição à política/regulação": ("Baixa", "banco privado", "badge-green"),
                    "Sensibilidade à Selic": ("Negativa parcial", "custo de captação sobe; cliente de menor renda inadimple mais", "badge-red"),
                    "ROE atual (ref.)": ("~14-15%", "recuperando — era abaixo do custo de capital em 2023-2024"),
                    "Risco principal": ("Execução da reestruturação e concorrência de fintechs no varejo massificado", ""),
                    "Perfil do investidor": ("Tese de turnaround", "aposta na recuperação do ROE; maior upside se entregar"),
                },
                "BPAC11": {
                    "nome": "BTG Pactual",
                    "cor": "#3B82F6",
                    "Modelo de negócio": ("Banco de investimento + wealth + crédito corporativo", "único modelo de atacado puro entre os grandes"),
                    "Cliente principal": ("Grandes empresas + ultra-high net worth", "wealth: R$1,28 tri sob gestão"),
                    "Principal produto de crédito": ("Corporate lending + M&A + mercado de capitais", "crescimento de 22% a/a na carteira"),
                    "Exposição ao ciclo econômico": ("Moderada", "mercado de capitais oscila, mas recorrência do wealth protege", "badge-yellow"),
                    "Exposição à política/regulação": ("Baixa", "banco privado, foco em atacado", "badge-green"),
                    "Sensibilidade à Selic": ("Positiva", "juro alto favorece renda fixa, tesouraria e gestão de ativos", "badge-green"),
                    "ROE atual (ref.)": ("~26-27%", "o mais alto do setor — modelo asset-light e alta alavancagem operacional"),
                    "Risco principal": ("Volatilidade de mercado comprime investment banking; já negocia a P/VP elevado", ""),
                    "Perfil do investidor": ("Crescimento + qualidade", "paga prêmio alto; dividend yield baixo mas crescimento forte"),
                },
                "SANB3": {
                    "nome": "Santander Brasil",
                    "cor": "#EF4444",
                    "Modelo de negócio": ("Varejo universal com matriz global", "único banco internacional com escala no Brasil"),
                    "Cliente principal": ("Varejo PF + PME + atacado", "foco crescente em alta renda"),
                    "Principal produto de crédito": ("Crédito imobiliário + cartão + PME", "diversificado"),
                    "Exposição ao ciclo econômico": ("Alta", "PME e varejo sofrem em recessão e juro elevado", "badge-red"),
                    "Exposição à política/regulação": ("Baixa/Moderada", "banco privado, mas depende da matriz espanhola", "badge-yellow"),
                    "Sensibilidade à Selic": ("Negativa parcial", "custo de captação sobe mais rápido que o spread no varejo", "badge-yellow"),
                    "ROE atual (ref.)": ("~13-15%", "abaixo dos pares — ROE mais fraco do grupo dos grandes privados"),
                    "Risco principal": ("ROE estruturalmente mais baixo; dependência de decisões da matriz espanhola", ""),
                    "Perfil do investidor": ("Dividendos + recuperação", "valuation descontado, mas exige provas de melhora"),
                },
                "ABCB4": {
                    "nome": "ABC Brasil",
                    "cor": "#22C55E",
                    "Modelo de negócio": ("Banco de atacado puro", "sem varejo — 100% crédito para médias e grandes empresas"),
                    "Cliente principal": ("Médias e grandes empresas (middle + corporate)", "sem pessoa física"),
                    "Principal produto de crédito": ("Crédito corporativo + trade finance + derivativos", "inadimplência histórica < 1%"),
                    "Exposição ao ciclo econômico": ("Moderada", "atacado é mais resiliente que varejo; cliente corporativo é mais solvente", "badge-yellow"),
                    "Exposição à política/regulação": ("Baixa", "banco privado, controlado pelo Arab Banking Corporation", "badge-green"),
                    "Sensibilidade à Selic": ("Positiva", "juro alto aumenta spread do crédito corporativo; PL remunera bem", "badge-green"),
                    "ROE atual (ref.)": ("~14-16%", "consistente e previsível — modelo de negócio não muda com o ciclo"),
                    "Risco principal": ("Concentração no atacado — grandes perdas pontuais impactam mais que a inadimplência pulverizada do varejo", ""),
                    "Perfil do investidor": ("Qualidade e estabilidade", "dividend yield consistente; cresce sem surpresas"),
                },
                "BRSR6": {
                    "nome": "Banrisul",
                    "cor": "#A78BFA",
                    "Modelo de negócio": ("Banco regional estatal gaúcho", "vive de funcionalismo público do RS"),
                    "Cliente principal": ("Servidor público e varejo do RS", "294 mil servidores estaduais na folha"),
                    "Principal produto de crédito": ("Consignado público + varejo PF + PME regional", "folha do Estado é o coração do negócio"),
                    "Exposição ao ciclo econômico": ("Moderada", "consignado público é defensivo; PME regional é mais sensível", "badge-yellow"),
                    "Exposição à política/regulação": ("Muito alta", "estatal — governo do RS controla e renova (ou não) o contrato da folha", "badge-red"),
                    "Sensibilidade à Selic": ("Positiva moderada", "juro alto aumenta spread; mas custo de captação também sobe", "badge-yellow"),
                    "ROE atual (ref.)": ("~7-9%", "pressionado — ROE mais baixo do grupo; abaixo do custo de capital"),
                    "Risco principal": ("Dependência total do governo gaúcho; contrato de folha renovado a custo crescente (R$1,26 bi por 5 anos)", ""),
                    "Perfil do investidor": ("Dividendos regionais", "dividend yield atrativo mas com risco político e de execução"),
                },
                "BMGB4": {
                    "nome": "Banco BMG",
                    "cor": "#F97316",
                    "Modelo de negócio": ("Banco mono-produto de consignado INSS", "88% da carteira é aposentado/pensionista"),
                    "Cliente principal": ("Aposentados e pensionistas do INSS", "segmento com menor inadimplência do Brasil"),
                    "Principal produto de crédito": ("Consignado INSS + cartão consignado", "desconto direto no benefício"),
                    "Exposição ao ciclo econômico": ("Muito baixa", "benefício do INSS não cai em recessão — renda garantida", "badge-green"),
                    "Exposição à política/regulação": ("Alta", "governo regula a taxa máxima do consignado INSS (hoje 1,85%/mês)", "badge-red"),
                    "Sensibilidade à Selic": ("Negativa", "teto de taxa regulado não sobe com a Selic — spread comprime", "badge-red"),
                    "ROE atual (ref.)": ("~10-12%", "limitado pelo teto regulatório da taxa"),
                    "Risco principal": ("Teto regulatório de juros + CPI do INSS investigando fraudes no consignado (biometria obrigatória)", ""),
                    "Perfil do investidor": ("Dividendos defensivos", "carteira resiliente, mas crescimento limitado pelo regulador"),
                },
            },
        },
        "perfis": {
            "ITUB4": {
                "nome": "Itaú Unibanco",
                "fundacao": "1945 (fusão Itaú+Unibanco em 2008)",
                "sede": "São Paulo, SP",
                "tagline": "O maior banco privado da América Latina. Disciplina de capital, foco em alta renda e o melhor ROE entre os incumbentes.",
                "modelo": (
                    "O Itaú opera em quatro frentes: varejo (conta corrente, cartão, crédito e seguros para pessoas físicas), "
                    "atacado (crédito para grandes empresas, mercado de capitais, tesouraria), gestão de ativos (fundos, previdência) "
                    "e atividades internacionais (América Latina). O diferencial não é o tamanho — é a seletividade. O Itaú "
                    "deliberadamente abandonou segmentos de menor renda e maior inadimplência, concentrando a carteira em alta e "
                    "média renda. 6 de cada 10 brasileiros de alta renda têm relacionamento com o banco. Isso gera spreads "
                    "melhores, inadimplência menor e fee de serviços mais alto (asset management, corretagem, seguros). "
                    "No 1T26 entregou lucro recorrente de R$ 12,3 bi e ROE de 24,8% — o mais alto entre os incumbentes."
                ),
                "receita": [
                    ("Margem financeira (NII)", "~50%", "spread de crédito e resultado de tesouraria"),
                    ("Receitas de serviços e tarifas", "~25%", "cartão, asset management, advisory, corretagem"),
                    ("Seguros", "~12%", "Itaú Seguros — vida, prestamista, imobiliário"),
                    ("Outros", "~13%", "câmbio, derivativos, international"),
                ],
                "vantagens": [
                    "Melhor ROE entre os bancões incumbentes (~24-26%) — sustentado por décadas, não é pico de ciclo",
                    "Foco na alta renda cria um flywheel: menor inadimplência → menor provisão → mais capital disponível para crescer",
                    "Escala de distribuição: rede própria + parcerias + digital permitem cross-sell sem aumentar custo proporcional",
                    "Transformação digital avançada — 75% das transações já são digitais, com meta de 75% dos clientes em modelo digital-first até 2027",
                    "Seguros e asset management são negócios capital-light dentro do banco, com margens muito mais altas que o crédito",
                ],
                "riscos": [
                    "Valuation premium (P/L ~8x, P/VP ~2x) não tolera decepções — qualquer deterioração é punida",
                    "Competição crescente de BTG no wealth management e de fintechs no varejo digital",
                    "Regulação bancária pode aumentar requisitos de capital, pressionando distribuição de dividendos",
                    "Expansão na América Latina (Chile, Argentina, Colômbia) adiciona risco cambial e político",
                ],
                "barreira": (
                    "A combinação de marca, rede de distribuição, base de dados de clientes e capital regulatório "
                    "cria uma barreira de entrada que nenhuma fintech conseguiu transpor em décadas. "
                    "Nubank chegou a 100 milhões de clientes — mas em rentabilidade por cliente ainda está longe do Itaú."
                ),
            },
            "BBAS3": {
                "nome": "Banco do Brasil",
                "fundacao": "1808 (fundado por Dom João VI)",
                "sede": "Brasília, DF",
                "tagline": "O banco do agro e do funcionalismo. Líder incontestável no crédito rural, mas pagando o preço de uma carteira concentrada.",
                "modelo": (
                    "O BB tem três pilares que nenhum banco privado consegue replicar: o crédito rural (53% do crédito "
                    "agro brasileiro passa pelo BB, com funding subsidiado via FCO e PRONAF), o funcionalismo público "
                    "(processa metade das folhas do setor público federal e estadual — base de consignado captiva), e o "
                    "Tesouro Nacional (agente financeiro do governo federal). Fora isso, é um banco universal com "
                    "seguros (BB Seguridade, controlada listada separadamente) e gestão de ativos. O problema de 2025-2026 "
                    "é exatamente essa concentração: o agro sofreu com El Niño, preços baixos de grãos e endividamento "
                    "acumulado. A inadimplência rural saltou de 1% para 6%, o lucro caiu 54% no 1T26 e o ROE colapsou "
                    "para 7,3%. A BB Seguridade, contudo, continua entregando — o banco dentro do banco que o mercado "
                    "frequentemente esquece."
                ),
                "receita": [
                    ("Margem financeira (NII)", "~45%", "crédito rural + consignado + corporate"),
                    ("BB Seguridade (resultado de equivalência patrimonial)", "~20%", "seguros, previdência e capitalização"),
                    ("Receitas de serviços e tarifas", "~20%", "folha de pagamento, asset management, tarifas"),
                    ("Tesouraria e mercado", "~15%", "títulos públicos e operações com o governo"),
                ],
                "vantagens": [
                    "Monopólio prático no crédito agro — nenhum banco privado tem a rede, o funding subsidiado e a expertise",
                    "Folha do setor público: base captiva de consignado com inadimplência próxima de zero",
                    "BB Seguridade: motor de resultado capital-light e recorrente dentro do conglomerado",
                    "Valuation de desconto (P/L ~4x, P/VP ~0,6x) embute a percepção de risco estatal",
                    "Gestão de ativos: 24,9% de market share — o maior gestor de recursos do Brasil",
                ],
                "riscos": [
                    "Interferência política: governo pode forçar crédito subsidiado, reduzir spread e comprometer rentabilidade",
                    "Concentração no agro: ciclos negativos (clima, preço de commodities) impactam desproporcionalmente",
                    "Inadimplência rural 2025-2026: ainda longe do pico — pode demorar 2-3 anos para normalizar",
                    "Menor eficiência operacional que bancos privados — custo de servir é mais alto",
                ],
                "barreira": (
                    "O acesso ao funding subsidiado (FCO, PRONAF, recursos do Tesouro) é uma barreira que nenhum banco "
                    "privado pode replicar. Quem financia agricultura a taxa de 7-8% a.a. quando o custo de mercado é 14%+ "
                    "está usando um subsídio que só o banco estatal acessa. Isso cria uma vantagem competitiva no agro "
                    "que é, literalmente, impossível de replicar sem ser banco público."
                ),
            },
            "BBDC3": {
                "nome": "Bradesco",
                "fundacao": "1943",
                "sede": "Osasco, SP",
                "tagline": "O gigante em reestruturação. Construído no interior do Brasil, foi o maior banco privado por décadas — agora recupera a rentabilidade.",
                "modelo": (
                    "O Bradesco é o único entre os grandes privados que foi construído de dentro para fora do Brasil — "
                    "nasceu em Marília (SP) e cresceu pelo interior antes de chegar às capitais. Essa origem explica "
                    "sua exposição à massa e às PMEs do interior, que são mais vulneráveis a ciclos de juros altos. "
                    "Em 2022-2024, o banco pagou o preço: inadimplência subindo, provisões estourando, ROE colapsando "
                    "para abaixo do custo de capital. A reestruturação de Marcelo Noronha (CEO desde 2023) levou o banco "
                    "a ser mais seletivo no crédito, a fechar agências, digitalizar e focar em alta renda e crédito "
                    "com garantia. O resultado começou a aparecer em 2025: lucro crescendo, ROE recuperando, ação "
                    "subindo 60% no ano. Em 2026, a tese é de quanto esse ROE ainda pode subir — e se chegará ao "
                    "nível de Itaú, ou ficará estacionado nos 15-17%."
                ),
                "receita": [
                    ("Margem financeira (NII)", "~50%", "spread de crédito PF + PME + corporativo"),
                    ("Seguros (Bradesco Seguros)", "~20%", "vida, saúde, automóvel — joint venture com Munich Re"),
                    ("Receitas de serviços e tarifas", "~18%", "cartão, previdência, corretagem"),
                    ("Outros", "~12%", "mercado de capitais, câmbio, gestão de ativos"),
                ],
                "vantagens": [
                    "Bradesco Seguros: uma das maiores seguradoras do Brasil — negócio capital-light com margens altas",
                    "Rede capilar no interior: presença onde grandes bancos e fintechs chegam com mais dificuldade",
                    "Reestruturação em curso: se o ROE normalizar para 18-20%, o valuation atual (P/L ~6x) está barato",
                    "Cielo integrada: adquirência + produtos bancários criam potencial de cross-sell",
                ],
                "riscos": [
                    "Execução: a reestruturação pode demorar mais ou entregar menos que o prometido",
                    "Concorrência de fintechs no varejo massificado — o segmento que o Bradesco depende mais",
                    "Exposição residual à massa de baixa renda, mais sensível a inadimplência em juro alto",
                    "Valuation não é mais óbvio — após alta de 60% em 2025, o desconto já fechou parcialmente",
                ],
                "barreira": (
                    "A rede de distribuição no interior do Brasil é o ativo mais difícil de replicar. "
                    "Cidades de 30.000 habitantes onde o Bradesco é o único banco presente — e onde "
                    "a fintech não chega sem agência ou correspondente. Mais a Bradesco Seguros, que tem "
                    "escala e relacionamento de décadas com corretores."
                ),
            },
            "BPAC11": {
                "nome": "BTG Pactual",
                "fundacao": "1983",
                "sede": "São Paulo, SP",
                "tagline": "O maior banco de investimento da América Latina. Não é um banco de varejo — é uma máquina de alocar capital.",
                "modelo": (
                    "O BTG é estruturalmente diferente dos outros: não tem agência, não quer o cliente de massa, "
                    "não cresce emprestando para pessoa física no cartão. Ele ganha dinheiro sendo o intermediário "
                    "entre quem tem capital (grandes fortunas, fundos) e quem precisa de capital (grandes empresas, governos). "
                    "A receita tem seis pilares: corporate lending (crédito para grandes empresas, ~R$2,3 bi/tri), "
                    "sales & trading (mesa proprietária e corretagem institucional), investment banking (IPOs, M&As, emissões), "
                    "asset management (R$2,5 tri sob gestão/administração), wealth management (R$1,28 tri — clientes private) "
                    "e consumer finance (Banco PAN + Too Seguros, consignado privado). "
                    "No 1T26 entregou lucro de R$4,8 bi (+42% a/a) e ROAE de 26,6%. "
                    "O modelo de partnership (sócios compram ações — alinhamento total) é um diferencial cultural único."
                ),
                "receita": [
                    ("Corporate Lending", "~23%", "crédito corporativo de alta qualidade — crescimento de 22% a/a"),
                    ("Wealth Management", "~15%", "R$ 1,28 tri sob gestão — crescimento recorde"),
                    ("Sales & Trading", "~19%", "mesa proprietária + corretagem institucional — volátil"),
                    ("Asset Management", "~12%", "R$ 2,5 tri total — taxas de gestão e performance"),
                    ("Consumer Finance & Banking", "~11%", "Banco PAN + Too Seguros — consignado privado"),
                    ("Investment Banking", "~10%", "IPOs, M&As, emissões de dívida — cíclico"),
                    ("Outros (juros e outros)", "~10%", ""),
                ],
                "vantagens": [
                    "Modelo de partnership: sócios são donos — incentivos alinhados, execução consistente há 40 anos",
                    "Wealth Management: R$1,28 tri em assets com crescimento de 44,6% a/a — receita recorrente e crescente",
                    "Corporate Lending: inadimplência próxima de zero em crédito para grandes empresas com garantias robustas",
                    "Marca BTG no mercado de capitais: quando uma empresa quer captar R$1 bi+, o BTG está na lista curta",
                    "Único entre os grandes a ter ROE acima de 26% de forma sustentada",
                ],
                "riscos": [
                    "Valuation elevado (P/VP ~9x) não tolera desaceleração — crescimento tem que ser entregue",
                    "Investment banking é cíclico — em mercados fechados (sem IPOs, sem M&A), essa linha murcha",
                    "Dividend yield baixo (~2%) — não é banco de renda; é banco de crescimento e reinvestimento",
                    "Risco-chave concentrado em poucos sócios-chave — risco de sucessão no longo prazo",
                ],
                "barreira": (
                    "A marca e o relacionamento de décadas com os grandes CEOs e CFOs do Brasil. "
                    "Não é possível construir isso da noite para o dia. Quando a Vale vai emitir uma debênture "
                    "ou o governo quer estruturar um projeto de infraestrutura, o BTG está na mesa. "
                    "Isso vem de 40 anos de execução impecável e de uma cultura de partnership que "
                    "atrai os melhores profissionais do mercado financeiro."
                ),
            },
            "SANB3": {
                "nome": "Santander Brasil",
                "fundacao": "1982 (chegou ao Brasil)",
                "sede": "São Paulo, SP",
                "tagline": "O único banco internacional com escala no Brasil. Terceiro maior privado, mas ainda procurando o modelo certo para o mercado local.",
                "modelo": (
                    "O Santander é um banco universal (PF + PME + atacado), mas com uma particularidade: "
                    "é subsidiária de um grupo global espanhol. Isso tem vantagens (acesso a tecnologia, "
                    "melhores práticas globais, plataforma de câmbio internacional) e desvantagens "
                    "(decisões estratégicas feitas em Madri podem não se adaptar à realidade brasileira, "
                    "e parte do lucro 'vaza' para a matriz). Historicamente, o Santander teve dificuldade "
                    "de encontrar seu nicho no Brasil: não tem o foco em alta renda do Itaú, não tem o "
                    "agro do BB, não tem o interior do Bradesco, não tem o atacado do BTG. "
                    "Em 2026, está buscando diferenciação em crédito imobiliário, alta renda e PME. "
                    "O ROE ainda é o mais baixo entre os grandes privados — o mercado cobra prova."
                ),
                "receita": [
                    ("Margem financeira (NII)", "~52%", "crédito PF + PME + corporate"),
                    ("Receitas de serviços e tarifas", "~22%", "cartão, seguros, corretagem"),
                    ("Seguros e previdência", "~12%", ""),
                    ("Mercado de capitais e câmbio", "~14%", ""),
                ],
                "vantagens": [
                    "Plataforma global: câmbio, trade finance e operações internacionais para clientes com negócios no exterior",
                    "Acesso à tecnologia e melhores práticas do grupo global — Openbank (banco digital do grupo) chegando ao Brasil",
                    "Valuation descontado em relação aos pares: se o ROE normalizar, há upside relevante",
                    "Histórico consistente de pagamento de JCP — yield atrativo dado o valuation baixo",
                ],
                "riscos": [
                    "ROE estruturalmente mais baixo que os pares privados — sem nicho definido que justifique prêmio",
                    "Decisões estratégicas dependem da matriz espanhola — nem sempre otimizadas para o Brasil",
                    "Exposição a PME e varejo de menor renda em ciclo de juro alto e inadimplência elevada",
                    "Competição intensa: Itaú na alta renda, BTG no atacado, Nubank/Inter no varejo digital",
                ],
                "barreira": (
                    "A plataforma global é a barreira real. Para uma empresa brasileira que exporta, "
                    "importa ou tem sócios internacionais, ter um banco com presença em 10 países na mesa "
                    "é conveniente. Mas no varejo PF doméstico, essa vantagem não aparece — o que explica "
                    "o ROE mais baixo: a barreira não se traduz em rentabilidade no negócio principal."
                ),
            },
            "ABCB4": {
                "nome": "ABC Brasil",
                "fundacao": "1989",
                "sede": "São Paulo, SP",
                "tagline": "O banco que nunca atendeu pessoa física. 100% atacado, 100% foco em empresa — e a menor inadimplência do setor.",
                "modelo": (
                    "O ABC Brasil é o mais puro exemplo de especialização no setor bancário brasileiro. "
                    "Não tem agência para pessoa física. Não tem conta corrente de varejo. Não tem cartão de crédito PF. "
                    "Atende exclusivamente médias e grandes empresas (segmento middle market, corporate e large corporate) "
                    "com crédito, trade finance (financiamento ao comércio exterior), câmbio, derivativos, "
                    "banco de investimento e seguros corporativos. "
                    "Controlado pelo Arab Banking Corporation (banco árabe do Barein), tem acesso facilitado "
                    "a funding internacional e a uma rede de relacionamentos no Oriente Médio que "
                    "nenhum banco brasileiro replica. "
                    "A inadimplência histórica abaixo de 1% é o resultado de 35 anos atendendo quem "
                    "tem balanço para mostrar — empresas com faturamento mínimo de R$30 mi anuais."
                ),
                "receita": [
                    ("Margem com clientes (crédito corporativo)", "~55%", "spread sobre carteira de R$32+ bi"),
                    ("Margem com mercado e tesouraria", "~20%", "PL remunerado ao CDI + operações de mercado"),
                    ("Receitas de serviços", "~15%", "banco de investimento, tarifas, câmbio"),
                    ("Seguros e outros", "~10%", ""),
                ],
                "vantagens": [
                    "Inadimplência histórica < 1% — resultado de 35 anos emprestando apenas para empresas com balanço",
                    "Sem exposição ao varejo PF: não sofre com inadimplência de cartão, crédito pessoal ou PME de baixa renda",
                    "Funding internacional (via Arab Banking Corp) com custo menor que captação doméstica — vantagem de spread",
                    "Modelo de negócio simples, previsível e escalável — sem a complexidade operacional de um banco universal",
                    "Alta correlação de receitas com o CDI: PL remunerado a CDI + margem com clientes = proteção natural em juro alto",
                ],
                "riscos": [
                    "Concentração: poucas carteiras grandes — uma inadimplência relevante pontual impacta mais que num banco pulverizado",
                    "Crescimento limitado: não tem varejo para escalar rapidamente — cresce no ritmo das empresas que serve",
                    "Controlador estrangeiro: decisões podem ser influenciadas por dinâmicas do Arab Banking Corporation",
                    "Exposição ao ciclo corporativo: recessão severa aumenta inadimplência mesmo no atacado",
                ],
                "barreira": (
                    "35 anos de relacionamento com o middle e large corporate brasileiro. "
                    "Empresa de faturamento R$300 mi não troca de banco por conveniência — "
                    "o relacionamento, o limite de crédito aprovado e as operações estruturadas em curso "
                    "criam um lock-in real. Mais o funding árabe, que nenhum banco brasileiro vai replicar."
                ),
            },
            "BRSR6": {
                "nome": "Banrisul",
                "fundacao": "1928",
                "sede": "Porto Alegre, RS",
                "tagline": "O banco do Rio Grande do Sul. Seu destino é o destino do RS — e do contrato com o governo estadual.",
                "modelo": (
                    "O Banrisul é um banco estatal regional — o que significa que seu modelo de negócio "
                    "é fundamentalmente diferente de todos os outros nesta lista. "
                    "Ele existe porque o governo do RS quer um banco público estadual. "
                    "O coração do negócio é a folha de pagamento dos servidores públicos gaúchos: "
                    "294 mil servidores ativos, inativos e pensionistas cujo salário passa pelo Banrisul, "
                    "gerando uma base captiva de consignado, conta corrente e produtos financeiros. "
                    "Em julho de 2026, renovou esse contrato por R$1,26 bi — pago à vista, reconhecido como "
                    "intangível e amortizado ao longo de 5 anos. O custo dobrou em relação à renovação "
                    "anterior (que era de 10 anos). Fora a folha, atende PMEs gaúchas e o varejo do RS. "
                    "Toda a sua força e seu risco estão concentrados em um único estado."
                ),
                "receita": [
                    ("Crédito consignado público (servidores RS)", "~40%", "base captiva da folha estadual"),
                    ("Varejo PF e PME gaúcha", "~35%", "clientes pessoas físicas e pequenas empresas do RS"),
                    ("Receitas de serviços", "~15%", "tarifas, previdência, seguros"),
                    ("Tesouraria", "~10%", "títulos públicos e operações de mercado"),
                ],
                "vantagens": [
                    "Base captiva de consignado público — 294 mil servidores estaduais com desconto em folha",
                    "Valuation muito barato (P/VP ~0,5x, P/L ~3x) — desconta o risco político e o ROE baixo",
                    "Dividend yield alto (~9-11%) — governo precisa do dividendo do banco para compor receitas estaduais",
                    "Presença capilar no interior do RS onde os grandes bancos privados não chegam",
                ],
                "riscos": [
                    "100% concentrado no RS — enchentes, seca, recessão regional batem direto no resultado",
                    "Dependência do contrato de folha: renovado a custo crescente (dobrou por ano de contrato na última renovação)",
                    "ROE cronicamente baixo (~7-9%) — estruturalmente abaixo do custo de capital",
                    "Risco político: troca de governo estadual pode mudar a relação ou condições do contrato",
                    "Qualidade de crédito pressionada em PF e PME, com inadimplência subindo em 2026",
                ],
                "barreira": (
                    "O contrato com o governo do RS é a barreira — e também o risco. "
                    "Nenhum banco privado vai entrar no estado para fazer o que o Banrisul faz "
                    "sem o benefício do funding barato do servidor e a capilaridade de 500+ agências no interior. "
                    "Mas essa barreira tem preço: R$1,26 bi a cada 5 anos só para manter o que já tem."
                ),
            },
            "BMGB4": {
                "nome": "Banco BMG",
                "fundacao": "1930 (família Pentagna Guimarães)",
                "sede": "Belo Horizonte, MG",
                "tagline": "O especialista em consignado INSS. Enquanto outros bancões atendem todo mundo, o BMG só atende aposentado — e isso é sua maior força.",
                "modelo": (
                    "O BMG é o banco mais nichado desta lista: 88% da carteira de crédito é formada "
                    "por aposentados e pensionistas do INSS. "
                    "O produto central é o empréstimo consignado, onde as parcelas são descontadas "
                    "diretamente do benefício do INSS — a inadimplência é estruturalmente baixa porque "
                    "o pagador não é a pessoa, é o governo federal. "
                    "A distribuição é feita por correspondentes bancários (terceiros que originam o crédito), "
                    "lojas próprias 'help! Loja de Crédito' (na cor laranja, reconhecível pelo público), "
                    "e canais digitais. "
                    "O desafio é que o governo regula a taxa máxima (hoje 1,85%/mês para o empréstimo e "
                    "2,46%/mês para o cartão). Quando a Selic sobe, o custo de captação sobe, "
                    "mas o teto de taxa não — o spread comprime. "
                    "Em 2025-2026, a CPI do INSS investigando fraudes no consignado criou obrigação de "
                    "biometria facial para cada contratação — adiciona fricção e pode frear a originação."
                ),
                "receita": [
                    ("Empréstimo consignado INSS", "~55%", "produto principal — taxa máxima 1,85%/mês"),
                    ("Cartão consignado INSS", "~25%", "desconto direto no benefício — taxa máxima 2,46%/mês"),
                    ("Consignado privado (CLT)", "~10%", "iniciado em 2025 — menor escala, maior risco"),
                    ("Seguros e outros produtos", "~10%", "Bmg Seguradora — vida, acidentes pessoais"),
                ],
                "vantagens": [
                    "Inadimplência estruturalmente baixa: parcelas descontadas direto do INSS — o devedor não pode deixar de pagar",
                    "Base de aposentados é demograficamente crescente — 35 milhões de beneficiários do INSS e crescendo",
                    "Reconhecimento de marca no público INSS: a cor laranja é sinônimo de consignado no interior do Brasil",
                    "Correspondentes bancários capilarizados onde bancos tradicionais não chegam",
                ],
                "riscos": [
                    "Teto regulatório de taxa: Selic sobe, mas o banco não consegue repassar — spread comprime estruturalmente",
                    "CPI do INSS e fraudes no consignado: biometria obrigatória adiciona fricção e pode reduzir origação",
                    "Concentração extrema em um segmento: qualquer mudança regulatória no consignado INSS impacta 88% da carteira",
                    "ROE limitado pelo teto de taxa: difícil escalar margem acima de 12-14% com spread comprimido",
                    "Consignado privado (CLT) em expansão — risco maior que o INSS, e o banco ainda está aprendendo o segmento",
                ],
                "barreira": (
                    "O reconhecimento de marca no público INSS e a rede de correspondentes são difíceis de replicar. "
                    "O aposentado do interior que reconhece a loja laranja e confia no 'consignado BMG' "
                    "não troca facilmente de banco. Além disso, os correspondentes que originam crédito "
                    "têm relacionamentos de anos com o BMG — e comissões que constroem lealdade. "
                    "A barreira não é tecnológica; é de relacionamento e presença física em regiões remotas."
                ),
            },
        },
    },
    "🛡️ Seguradoras": {
        "tickers": ["BBSE3", "CXSE3", "PSSA3", "IRBR3"],
        "tagline": "Quatro empresas com o mesmo rótulo 'seguradora', mas quatro modelos completamente diferentes. O IRB não é sequer uma seguradora — é o seguro das seguradoras.",
        "logica": {
            "titulo": "O que move o setor de seguros",
            "texto": (
                "O mercado frequentemente coloca BBSE3, CXSE3, PSSA3 e IRBR3 no mesmo balde. É um erro. "
                "A BB Seguridade e a Caixa Seguridade são distribuidoras de seguros que não assumem risco — "
                "usam a rede do banco controlador como canal de vendas e repassam o risco às seguradoras parceiras. "
                "A Porto é uma seguradora de verdade: assume risco, paga sinistro, compete por frota segurada. "
                "O IRB é uma resseguradora — o seguro das seguradoras, que nenhum consumidor final contrata diretamente. "
                "São quatro posições diferentes na cadeia do risco, cada uma com drivers, métricas e riscos distintos."
            ),
            "drivers": [
                ("Resultado de subscrição (Combined Ratio)", "A métrica mais importante de uma seguradora real (Porto, IRB). "
                 "Combined Ratio = (sinistros + despesas) / prêmios. Abaixo de 100% = lucro na operação. "
                 "Para distribuidoras (BBSE, CXSE), esse conceito não se aplica — elas não carregam o risco."),
                ("Resultado financeiro (Float)", "Toda seguradora cobra o prêmio antes de pagar o sinistro. "
                 "O dinheiro no meio tempo é investido — é o float, o coração do modelo de Buffett. "
                 "Selic alta turbina esse resultado: BBSE, CXSE e IRBR se beneficiam muito em juro alto. "
                 "Queda da Selic comprime esse motor."),
                ("Taxa Selic e ciclo de juros", "Impacto duplo: o float rende mais em juro alto, e as reservas técnicas (previdência, capitalização) "
                 "se valorizam. BBSE tem ~23% do lucro vindo do resultado financeiro no 1T26 (+59% a/a). "
                 "É o maior risco de médio prazo: quando os juros caírem, esse motor perde força."),
                ("Sinistralidade e eventos climáticos", "Seca, enchentes, granizo — são os inimigos da seguradora que assume risco. "
                 "Porto paga os carros danificados. IRB paga as seguradoras que pagaram. "
                 "BBSE e CXSE não pagam sinistro — o risco fica com a Mapfre (BBSE) e com as parceiras (CXSE)."),
                ("Canal de distribuição", "Quem vende o seguro e a que custo? BBSE usa o BB (70 mi de clientes). "
                 "CXSE usa a Caixa + 4.000 agências + 13.000 lotéricas. Porto usa 46.000 corretores independentes + exclusividade no Itaú. "
                 "Canal cativo (banco) tem custo de aquisição menor e base captiva. Corretores têm mais volatilidade."),
                ("Penetração do seguro no Brasil", "O Brasil tem baixíssima penetração de seguros vs. PIB. "
                 "Seguro saúde, vida e residencial têm espaço enorme para crescer. "
                 "É o driver estrutural de longo prazo para todo o setor."),
            ],
        },
        "comparativo": {
            "dimensoes": [
                "O que é de verdade",
                "Quem assume o risco do sinistro",
                "Canal de distribuição",
                "Produto principal",
                "Sensibilidade à Selic",
                "Sinistralidade como risco",
                "Exposição política/regulatória",
                "Payout e DY (ref.)",
                "Risco principal",
            ],
            "empresas": {
                "BBSE3": {
                    "nome": "BB Seguridade",
                    "cor": "#F59E0B",
                    "O que é de verdade": ("Distribuidora de seguros", "não é seguradora — não assume risco"),
                    "Quem assume o risco do sinistro": ("Mapfre + Principal Financial Group", "parceiros assumem todo o risco", "badge-green"),
                    "Canal de distribuição": ("Banco do Brasil", "70 milhões de clientes, rede exclusiva"),
                    "Produto principal": ("Seguros rural + vida + previdência", "Brasilseg + Brasilprev + Brasilcap"),
                    "Sensibilidade à Selic": ("Muito positiva", "resultado financeiro = 23% do lucro; +59% em juro alto", "badge-green"),
                    "Sinistralidade como risco": ("Indireto", "se Mapfre quebrar, o contrato é afetado — mas improvável", "badge-green"),
                    "Exposição política/regulatória": ("Alta", "controlada pelo BB (estatal); contrato expira em 2033", "badge-red"),
                    "Payout e DY (ref.)": ("~95% de payout", "DY ~11-12%"),
                    "Risco principal": ("Selic caindo + agro pressionando rural + contrato com BB vence em 2033", ""),
                },
                "CXSE3": {
                    "nome": "Caixa Seguridade",
                    "cor": "#F97316",
                    "O que é de verdade": ("Distribuidora de seguros", "mesma lógica da BBSE — canal bancário exclusivo"),
                    "Quem assume o risco do sinistro": ("Seguradoras parceiras", "CXSE distribui e recebe comissão; não carrega risco", "badge-green"),
                    "Canal de distribuição": ("Caixa Econômica Federal", "4.000 agências + 13.000 lotéricas + R$1 tri em crédito imobiliário"),
                    "Produto principal": ("Seguro habitacional (MIP + DFI)", "obrigatório por lei em todo financiamento imobiliário"),
                    "Sensibilidade à Selic": ("Positiva", "float das reservas rende mais; menor exposição que BBSE", "badge-yellow"),
                    "Sinistralidade como risco": ("Mínimo", "distribuidora pura — parceiras assumem o risco", "badge-green"),
                    "Exposição política/regulatória": ("Muito alta", "controlada pela Caixa (estatal); dependência total do crédito imobiliário federal", "badge-red"),
                    "Payout e DY (ref.)": ("~90% de payout", "DY ~7-8%"),
                    "Risco principal": ("Dependência do crédito habitacional da CEF + risco político estatal", ""),
                },
                "PSSA3": {
                    "nome": "Porto",
                    "cor": "#3B82F6",
                    "O que é de verdade": ("Seguradora completa", "assume risco, paga sinistro, compete por frota"),
                    "Quem assume o risco do sinistro": ("A própria Porto", "underwriting próprio — lucra ou perde com o combined ratio", "badge-red"),
                    "Canal de distribuição": ("46.000 corretores independentes + exclusividade no Itaú", "canal pulverizado + parceria estratégica"),
                    "Produto principal": ("Auto (39%) + Saúde + Residencial + Porto Bank", "4 verticais — era 90% auto, agora diversificada"),
                    "Sensibilidade à Selic": ("Moderada positiva", "float rende mais, mas sinistros afetam independente da Selic", "badge-yellow"),
                    "Sinistralidade como risco": ("Alto", "granizo, furacão, acidente, fraude — paga ela mesma", "badge-red"),
                    "Exposição política/regulatória": ("Baixa", "privada; família Garfinkel + Itaú controlam; sem interferência estatal", "badge-green"),
                    "Payout e DY (ref.)": ("~50-60% de payout", "DY ~5-6% — reinveste mais para crescer"),
                    "Risco principal": ("Sinistralidade elevada em auto; competição agressiva de preço no mercado", ""),
                },
                "IRBR3": {
                    "nome": "IRB Brasil Re",
                    "cor": "#22C55E",
                    "O que é de verdade": ("Resseguradora", "seguro DAS seguradoras — nicho único na B3"),
                    "Quem assume o risco do sinistro": ("O próprio IRB", "assume risco das seguradoras (cedentes) em troca de prêmio de resseguro", "badge-red"),
                    "Canal de distribuição": ("Seguradoras (cedentes)", "Porto, Bradesco, Caixa, etc. transferem parte do risco para o IRB"),
                    "Produto principal": ("Resseguro patrimonial + vida + rural + riscos especiais", "invisível para o consumidor final"),
                    "Sensibilidade à Selic": ("Positiva", "float das reservas técnicas rende mais em juro alto", "badge-yellow"),
                    "Sinistralidade como risco": ("Muito alto", "catástrofes, enchentes, acidentes de aviação — o IRB é o último a pagar", "badge-red"),
                    "Exposição política/regulatória": ("Moderada", "regulado pela SUSEP; histórico de fraude contábil em 2020 pesa na reputação", "badge-yellow"),
                    "Payout e DY (ref.)": ("25% de payout (iniciado)", "DY ~3% — turnaround ainda recente"),
                    "Risco principal": ("Catástrofes globais + disciplina de subscrição + expansão para seguro direto ainda não provada", ""),
                },
            },
        },
        "perfis": {
            "BBSE3": {
                "nome": "BB Seguridade",
                "fundacao": "2012 (IPO)",
                "sede": "Brasília, DF",
                "tagline": "O maior pagador de dividendos do setor. Uma distribuidora de seguros disfarçada de seguradora — e isso é exatamente o que a torna tão lucrativa.",
                "modelo": (
                    "A BB Seguridade não assume risco de seguro. Ela distribui seguros, previdência e capitalização "
                    "pela rede do Banco do Brasil — 70 milhões de clientes, mais de 3.500 pontos de atendimento — "
                    "e cobra comissão. O risco de sinistro fica com os parceiros: Mapfre (seguros, JV 74,9% BB + 25,1% Mapfre) "
                    "e Principal Financial Group (previdência, via Brasilprev). "
                    "Estrutura capital-light com payout de ~85% — não precisa reter capital para cobrir sinistros. "
                    "O resultado tem dois motores: operacional (prêmios, corretagem, sinistralidade das parceiras) "
                    "e financeiro (reservas técnicas da Brasilprev e Brasilcap investidas na Selic). "
                    "Em juro alto o segundo motor turbina o lucro: no 1T26 foi +58,5% a/a e representou 23% do total. "
                    "O detalhe que muda tudo: o contrato de distribuição com o BB vai até 2033. "
                    "O mercado desconta esse risco no valuation — e o P/L de 8x vs. 13-14x histórico do mercado "
                    "é basicamente o 'preço' que o investidor paga pela incerteza de renovação."
                ),
                "receita": [
                    ("Corretagem e distribuição (BB Corretora)", "~40%", "comissão sobre todos os produtos vendidos pela rede BB"),
                    ("Previdência (BrasilPrev)", "~25%", "taxa de gestão + resultado financeiro das reservas PGBL/VGBL — turbinado pela Selic"),
                    ("Seguros rurais (Brasilseg)", "~14%", "maior linha individual; sensível ao agro, El Niño e inadimplência rural"),
                    ("Seguros vida e prestamista (Brasilseg)", "~17%", "prestamista ligado ao consignado — sofre com juro alto; vida é base estável"),
                    ("Capitalização (Brasilcap)", "~4%", "títulos de capitalização — beneficiado pela Selic alta"),
                ],
                "vantagens": [
                    "Modelo capital-light: não assume risco de sinistro → payout de 85% → DY de 11-12%",
                    "Canal exclusivo com 70 milhões de clientes do BB — custo de aquisição praticamente zero",
                    "Brasilprev: líder em previdência privada no Brasil; reservas crescendo 10% a/a",
                    "Resultado financeiro expressivo: Selic alta turbina o float das reservas de previdência e capitalização",
                    "P/L de 8x — desconto histórico vs. média do mercado (13-14x)",
                ],
                "riscos": [
                    "Contrato 2033: o acordo de distribuição com o BB vence daqui a ~7 anos — renovação, condições e custo são incertos; é o maior risco estrutural",
                    "Selic caindo: resultado financeiro (23% do lucro em 1T26) cai imediatamente; recuperação operacional leva trimestres",
                    "Seguro rural (~35% dos prêmios): El Niño, seca e inadimplência rural pressionaram a Brasilseg em 2024-2026",
                    "Prestamista em queda: ligado ao crédito consignado — juro alto reduz tomada de crédito e, com ela, o seguro",
                    "Guidance 2026 conservador: própria empresa projeta resultado operacional de -7% a -3% vs. 2025",
                ],
                "barreira": (
                    "O contrato de exclusividade com o BB e o tamanho da base de clientes são inreplicáveis. "
                    "Nenhuma seguradora privada tem acesso a 70 milhões de clientes com custo de aquisição zero. "
                    "Brasilprev é a maior gestora de previdência privada do Brasil — liderança construída em décadas. "
                    "O problema é que toda essa vantagem depende de um contrato com o estado."
                ),
            },
            "CXSE3": {
                "nome": "Caixa Seguridade",
                "fundacao": "2015 (IPO em 2021)",
                "sede": "Brasília, DF",
                "tagline": "A distribuidora do crédito habitacional. Onde tem financiamento da Caixa, tem seguro da CXSE — e por lei.",
                "modelo": (
                    "A lógica da CXSE é idêntica à da BBSE: distribui seguros pela rede da Caixa Econômica Federal "
                    "e recebe comissão sem assumir o risco de sinistro. Mas o produto-âncora é diferente — e mais defensivo. "
                    "Todo financiamento imobiliário no Brasil exige por lei dois seguros obrigatórios: MIP (Morte e Invalidez) "
                    "e DFI (Danos Físicos ao Imóvel). São embutidos na parcela e cobrados por 10 a 35 anos. "
                    "Cada novo financiamento da Caixa (que detém mais de R$1 tri em carteira imobiliária) "
                    "gera automaticamente mais um contrato de seguro que dura décadas — é o efeito empilhamento. "
                    "A base de recorrência cresce enquanto os contratos antigos ainda estão ativos e os novos chegam. "
                    "No 1T26 entregou lucro de ~R$1,14 bi (+ROE de 65,9%) e DY projetado de ~7-8% para 2026."
                ),
                "receita": [
                    ("Seguro habitacional (MIP + DFI)", "~55%", "obrigatório por lei — base recorrente e crescente"),
                    ("Prestamista e vida", "~20%", "seguro do crédito consignado e pessoal da Caixa"),
                    ("Previdência e capitalização", "~15%", "produtos financeiros da rede Caixa"),
                    ("Residencial e outros", "~10%", "seguros patrimoniais para clientes da Caixa"),
                ],
                "vantagens": [
                    "Efeito empilhamento: cada financiamento gera contrato de 10-35 anos — recorrência que cresce automaticamente",
                    "Seguro habitacional é obrigatório por lei — não há opção de 'não comprar' para quem financia",
                    "Mais de 60% de market share em seguro habitacional — posição de dominância que nenhum concorrente replica",
                    "Canal com 4.000 agências + 13.000 lotéricas — capilaridade ímpar para o público de menor renda",
                    "ROE de 65,9% no 1T26 — extraordinário para qualquer empresa, de qualquer setor",
                ],
                "riscos": [
                    "100% dependente da Caixa como canal e controladora — risco político estatal elevado",
                    "Prestamista pressionado: juros altos reduzem crédito consignado e pessoal",
                    "Resultado financeiro ajuda hoje (Selic alta), mas perde força quando os juros caírem",
                    "Valuation mais esticado que BBSE — P/L de 11-13x já precifica boa parte da qualidade",
                    "Qualquer mudança na política habitacional federal (FGTS, Minha Casa) impacta diretamente",
                ],
                "barreira": (
                    "A exclusividade com a Caixa + a lei que obriga o seguro habitacional = monopólio prático. "
                    "Nenhuma seguradora privada consegue entrar nesse mercado sem ser o parceiro oficial da CEF. "
                    "E o efeito empilhamento cria uma receita que cresce por décadas sem esforço de vendas adicional — "
                    "é o modelo mais defensivo e previsível de toda a lista."
                ),
            },
            "PSSA3": {
                "nome": "Porto",
                "fundacao": "1945",
                "sede": "São Paulo, SP",
                "tagline": "A maior seguradora não-vida do Brasil. Saiu do risco de ser 'só auto' e virou um ecossistema de seguros, serviços e finanças.",
                "modelo": (
                    "A Porto é a única seguradora real desta lista — ela assume risco, subscreve apólices, "
                    "paga sinistros. Não é distribuidora de banco. Nasceu em 1945 como seguradora de automóveis "
                    "e por décadas foi sinônimo de 'seguro de carro'. O problema: auto tinha sinistralidade alta "
                    "e margens comprimidas. A virada estratégica foi deliberada: diluir o auto (que era 90% da receita) "
                    "e crescer nas verticais mais rentáveis. Em 2025, auto era apenas 39%. "
                    "Hoje opera em quatro verticais: Porto Seguro (auto, residencial, empresarial), "
                    "Porto Saúde (planos de saúde e odonto, crescendo forte), Porto Bank (cartão de crédito, consórcio) "
                    "e Porto Serviços (assistências). "
                    "A parceria com o Itaú (exclusividade para auto e residencial nos canais do banco) "
                    "é uma alavanca de distribuição que nenhum concorrente tem — o Itaú Seguro de Auto é, "
                    "na prática, operado pela Porto."
                ),
                "receita": [
                    ("Auto (Porto Seguro + Itaú + Azul Seguros)", "~39%", "era 90% em 2010 — deliberadamente diluído; sinistralidade alta e margens comprimidas"),
                    ("Porto Saúde (planos de saúde e odonto)", "~25%", "vertical mais rentável e em crescimento — margens superiores ao auto"),
                    ("Residencial e empresarial", "~15%", "cross-sell com auto e parceria Itaú — sinistralidade mais baixa"),
                    ("Porto Bank (cartão, consórcio, financiamento)", "~12%", "crescendo via base de 18 mi de clientes — sem custo de aquisição"),
                    ("Porto Serviços (assistências)", "~9%", "assistências 24h e serviços domésticos — fidelização e receita recorrente"),
                ],
                "vantagens": [
                    "Diversificação real: auto 39% da receita — se o mercado de carros parar, a Porto não para",
                    "Porto Saúde crescendo com margens superiores ao auto — driver estrutural dos próximos anos",
                    "Exclusividade nos canais do Itaú: acesso a mais de 50 milhões de clientes com custo de aquisição reduzido",
                    "Taxa de renovação 10 pp acima da média do mercado — fidelidade de cliente acima da concorrência",
                    "18 milhões de clientes únicos — base para cross-sell de saúde, banco e serviços",
                ],
                "riscos": [
                    "Sinistralidade alta: ela paga o que a natureza e os acidentes custam — granizo, enchente, fraude",
                    "Competição agressiva em auto: concorrentes praticando preços baixos para ganhar mercado",
                    "Porto Saúde: custo dos planos de saúde cresce sistematicamente acima da inflação",
                    "DY menor (~5-6%) — reinveste mais para crescer; não é banco de renda no curto prazo",
                    "Valuation mais alto (P/L ~10x) após forte valorização — margem de segurança menor",
                ],
                "barreira": (
                    "A exclusividade no Itaú + 80 anos de marca + rede de 46.000 corretores. "
                    "Um novo entrante levaria décadas para construir a confiança que um corretor tem com a Porto. "
                    "O contrato com o Itaú é uma alavanca que qualquer outra seguradora pagaria bilhões para ter. "
                    "E a liderança em auto (com a sinistralidade controlada que têm) cria um banco de dados de risco "
                    "que é vantagem competitiva de subscrição."
                ),
            },
            "IRBR3": {
                "nome": "IRB Brasil Re",
                "fundacao": "1939 (Governo Vargas)",
                "sede": "Rio de Janeiro, RJ",
                "tagline": "O seguro das seguradoras. O único papel da B3 que nenhum consumidor final conhece — e que é fundamental para que todo o mercado de seguros funcione.",
                "modelo": (
                    "O IRB é uma resseguradora — uma categoria completamente diferente das outras três. "
                    "Quando a Porto vende um seguro de carro de R$200.000, ela pode não querer carregar 100% desse risco "
                    "no balanço. Então ela 'cede' parte do risco ao IRB, pagando um prêmio de resseguro. "
                    "Se o carro for roubado, a Porto paga ao cliente e o IRB ressarce parte para a Porto. "
                    "O IRB não tem cliente pessoa física. Seus clientes são as seguradoras (chamadas de 'cedentes'). "
                    "A métrica-rei é o Combined Ratio — se for abaixo de 100%, a operação de subscrição dá lucro. "
                    "O IRB passou por uma crise grave em 2020 (fraude contábil, Combined Ratio de 140%+). "
                    "Desde 2022 está em turnaround: Combined Ratio voltou para ~85-90%, resultado de subscrição "
                    "cresceu 74,5% no 1T26, sinistralidade doméstica caiu para 35%. "
                    "Em 2026 anunciou expansão para seguro direto (criação de duas seguradoras próprias) — "
                    "é uma mudança estrutural do modelo que o mercado ainda está digerindo."
                ),
                "receita": [
                    ("Resultado de subscrição (prêmios - sinistros - despesas)", "~53%", "coração do negócio — R$180 mi no 1T26, +74,5% a/a"),
                    ("Resultado financeiro (float das reservas)", "~47%", "reservas técnicas investidas rendendo a Selic"),
                ],
                "vantagens": [
                    "Único ressegurador de grande porte listado na B3 — sem comparável doméstico",
                    "Turnaround concluído: Combined Ratio de 140%+ em 2020 para ~85-90% em 2026",
                    "Solvência regulatória de 287% — capital de sobra para crescer e distribuir dividendos",
                    "Mercado de resseguro no Brasil cresceu 7,1% no 1T26 — vento a favor estrutural",
                    "A partir de 2027, reforma tributária (CBS/IBS) zera alíquota do resseguro — potencial ganho de rentabilidade",
                    "Base de dados técnicos de 80+ anos de riscos brasileiros — vantagem de subscrição inreplicável",
                ],
                "riscos": [
                    "Catástrofes de grande escala: enchente, furacão, acidente de aviação podem gerar perda pontual enorme",
                    "Histórico de fraude contábil em 2020 — credibilidade ainda em reconstrução com investidores institucionais",
                    "Expansão para seguro direto em 2026 é aposta não provada — pode consumir capital e desviar foco",
                    "Sinistralidade internacional elevada (~93%) — mercado externo é menos lucrativo que o doméstico",
                    "Dividend yield baixo (~3%) — turnaround recente limita distribuição; ainda não é banco de renda",
                ],
                "barreira": (
                    "80 anos de base de dados técnicos de risco no Brasil. "
                    "Uma resseguradora nova levaria décadas para ter a confiança técnica para assumir "
                    "resseguros de aviação, petróleo ou grandes riscos industriais. "
                    "O IRB sabe exatamente quanto custa um incêndio numa plataforma de petróleo no Brasil — "
                    "e essa informação vale mais do que qualquer capital. "
                    "Mais o oligopólio regulatório: a SUSEP controla a abertura de novas resseguradoras."
                ),
            },
        },
    },
    "⚡ Utilities Elétricas": {
        "tickers": ["TAEE11", "ISAE4", "ALUP11", "EGIE3", "AXIA3", "CPFE3", "EQTL3", "CPLE3"],
        "tickers_sub": ["CMIG4"],
        "label_sub": "Estatal integrada",
        "tagline": "Transmissão, distribuição e geração são três negócios com riscos, receitas e métricas completamente diferentes. Colocar todas no mesmo balde é o erro mais comum do investidor de renda.",
        "logica": {
            "titulo": "A lógica do setor elétrico — três negócios dentro de um rótulo",
            "texto": (
                "O setor elétrico brasileiro tem uma particularidade que poucos investidores internalizam: "
                "transmissão, distribuição e geração são modelos de negócio radicalmente diferentes, "
                "com riscos distintos, indexações distintas e métricas distintas. "
                "Transmissoras recebem a RAP (Receita Anual Permitida) e não dependem de quanto "
                "energia passa pela linha. Distribuidoras recebem pela energia que entregam, sofrem com "
                "inadimplência e furto, e têm revisão tarifária periódica. Geradoras dependem de "
                "chuva (hidrelétricas), vento (eólicas), sol (solares) ou preço de gás (térmicas). "
                "Quem entende essas três lógicas lê qualquer resultado do setor em minutos."
            ),
            "drivers": [
                ("RAP — Receita Anual Permitida (transmissão)", "O coração da transmissão. A ANEEL define quanto a transmissora "
                 "recebe por ano pela disponibilidade das linhas, independente de quanto energia passa. "
                 "Reajustada anualmente por IPCA ou IGPM conforme o contrato. Quanto maior o IGPM vs IPCA, "
                 "melhor para quem tem contratos indexados ao IGPM (como a Taesa, ~60% em IGPM). "
                 "Prazo típico: 30 anos. É o ativo mais próximo de 'renda fixa de longo prazo' na B3."),
                ("Revisão tarifária (distribuição)", "A cada 4-5 anos a ANEEL redefine o WACC regulatório e os custos eficientes "
                 "da distribuidora. Revisão favorável aumenta a margem; revisão desfavorável comprime. "
                 "É o risco estrutural das distribuidoras — independe de quanto a empresa gerencie bem."),
                ("Hidrologia e GSF (geração hidrelétrica)", "GSF = fator de geração. Se chove abaixo da média, as hidrelétricas "
                 "geram menos que o contratado e precisam comprar energia no mercado (custo extra). "
                 "O risco hidrológico é o motivo pelo qual geradoras puras são mais voláteis que transmissoras."),
                ("Curtailment (corte de geração)", "O ONS corta a geração de renováveis quando há sobreoferta no sistema. "
                 "A ENGIE projeta curtailment de 26% em 2026 e 32% em 2027 — energia que foi investida "
                 "mas não pode ser vendida. Afeta eólicas e solares, especialmente no Nordeste."),
                ("Taxa de juros (Selic)", "Utilities são duration longa — o valor presente dos fluxos futuros é muito "
                 "sensível à taxa de desconto. Selic alta comprime o valuation de transmissoras e "
                 "geradoras, e aumenta o custo da dívida das distribuidoras. Quando a Selic cai, "
                 "as utilities sobem — é a equação que explica o IEEX (índice do setor)."),
                ("Inadimplência e perdas (distribuição)", "Distribuidoras têm dois inimigos silenciosos: a inadimplência "
                 "(consumidor não paga) e as perdas técnicas/não-técnicas (furto de energia). "
                 "A ANEEL permite repassar parte das perdas para a tarifa, mas o excedente fica com "
                 "a distribuidora. É o risco que a Equatorial sabe gerenciar melhor que os pares."),
                ("Mercado Livre de Energia (ACL)", "Grandes consumidores podem comprar energia diretamente de geradoras, "
                 "fora da distribuidora local. A expansão do Mercado Livre pressiona distribuidoras "
                 "(perdem clientes) e abre oportunidades para geradoras (contratos bilaterais de longo prazo)."),
            ],
        },
        "comparativo": {
            "dimensoes": [
                "Segmento principal",
                "Como ganha dinheiro",
                "Indexação da receita",
                "Risco hidrológico/climático",
                "Risco regulatório",
                "Sensibilidade à Selic",
                "Perfil de dividendo",
                "Risco principal",
            ],
            "grupos": [
                {"label": "Transmissoras", "tickers": ["TAEE11", "ISAE4", "ALUP11"]},
                {"label": "Integradas privadas + geração", "tickers": ["EGIE3", "AXIA3", "CPFE3", "EQTL3", "CPLE3"]},
                {"label": "Estatal integrada", "tickers": ["CMIG4"]},
            ],
            "empresas": {
                "TAEE11": {
                    "nome": "Taesa",
                    "cor": "#F59E0B",
                    "Segmento principal": ("Transmissão pura", "13.000 km de linhas, 109 subestações, 18 estados"),
                    "Como ganha dinheiro": ("RAP — disponibilidade das linhas", "não depende de quanto energia passa"),
                    "Indexação da receita": ("~60% IGPM + ~40% IPCA", "em IGPM alto, receita cresce mais que os custos (IPCA)"),
                    "Risco hidrológico/climático": ("Zero", "transmissão não gera energia — independe de chuva", "badge-green"),
                    "Risco regulatório": ("Moderado", "revisão de RAP na renovação de concessões; concessões antigas têm metodologia diferente", "badge-yellow"),
                    "Sensibilidade à Selic": ("Alta negativa", "duration longa; Selic alta comprime valuation", "badge-red"),
                    "Perfil de dividendo": ("Payout ~100%", "DY 7-10%; mas capex futuro e alavancagem (4,7x) podem comprimir"),
                    "Risco principal": ("Alavancagem alta + concessões antigas com metodologia de RAP diferente + capex de R$2,2 bi pendente", ""),
                },
                "ISAE4": {
                    "nome": "ISA Energia (ex-Transmissão Paulista)",
                    "cor": "#22C55E",
                    "Segmento principal": ("Transmissão pura", "maior malha privada do Sudeste; ISA Colombia é controladora"),
                    "Como ganha dinheiro": ("RAP — disponibilidade das linhas", "concessões novas com metodologia mais previsível"),
                    "Indexação da receita": ("IPCA", "contratos mais novos, metodologia mais transparente e previsível"),
                    "Risco hidrológico/climático": ("Zero", "transmissão pura — sem exposição climática", "badge-green"),
                    "Risco regulatório": ("Baixo", "concessões de categoria II/III, mais transparentes; TIR real de 7,7%", "badge-green"),
                    "Sensibilidade à Selic": ("Alta negativa", "duration longa; valuation comprimido em juro alto", "badge-red"),
                    "Perfil de dividendo": ("Payout alto", "DY 8-9%; menor alavancagem que Taesa"),
                    "Risco principal": ("Controlador colombiano (ISA) — decisões estratégicas vindas de fora", ""),
                },
                "EGIE3": {
                    "nome": "Engie Brasil",
                    "cor": "#3B82F6",
                    "Segmento principal": ("Geração renovável + transmissão nascente", "~12,9 GW; 70% hídrica + eólica + solar; 4.500 km de gás (TAG)"),
                    "Como ganha dinheiro": ("PPAs (contratos de longo prazo) + PLD spot + RAP de transmissão", "maior geradora privada do Brasil"),
                    "Indexação da receita": ("IPCA (PPAs) + PLD mercado livre", "parcela exposta ao preço spot é volátil"),
                    "Risco hidrológico/climático": ("Alto", "70% hídrica; seca afeta geração; curtailment 26% projetado em 2026", "badge-red"),
                    "Risco regulatório": ("Moderado", "revisão periódica de PPAs e regras do mercado livre", "badge-yellow"),
                    "Sensibilidade à Selic": ("Moderada negativa", "alavancagem elevada; mas ativos de longa vida protegem parcialmente", "badge-yellow"),
                    "Perfil de dividendo": ("Payout 55% (mínimo)", "DY ~4-5%; ciclo de capex pesado reduz payout temporariamente"),
                    "Risco principal": ("Curtailment crescente + ciclo de capex pesado (Jirau + transmissão) + Selic alta comprime valuation", ""),
                },
                "AXIA3": {
                    "nome": "Axia Energia (ex-Eletrobras)",
                    "cor": "#A78BFA",
                    "Segmento principal": ("Geração hídrica + transmissão", "a maior do Brasil; privatizada em 2022"),
                    "Como ganha dinheiro": ("Cotas de energia (portfólio cativo) + ACL + RAP", "processo de descotização em andamento"),
                    "Indexação da receita": ("IPCA (maioria) + preço livre", "portfólio mais descontratado vs pares; TIR implícita ~10%"),
                    "Risco hidrológico/climático": ("Alto", "gigante hídrica; GSF e seca afetam diretamente", "badge-red"),
                    "Risco regulatório": ("Muito alto", "acordo com governo (CDE, descotização) ainda sendo digerido; risco político pós-privatização", "badge-red"),
                    "Sensibilidade à Selic": ("Alta negativa", "duration muito longa; empresa de menor custo = mais sensível à taxa de desconto", "badge-red"),
                    "Perfil de dividendo": ("DY ~6-7%", "dividendos expressivos após reestruturação, mas portfólio mais descontratado limita"),
                    "Risco principal": ("Complexidade pós-privatização + risco político (governo ainda questiona acordos) + portfólio mais descontratado", ""),
                },
                "CPFE3": {
                    "nome": "CPFL Energia",
                    "cor": "#EF4444",
                    "Segmento principal": ("Distribuidora integrada + geração", "2ª maior distribuidora (14% de mercado); 10,3 mi de clientes; controlada pela State Grid China"),
                    "Como ganha dinheiro": ("Tarifa de distribuição regulada + receita de geração", "concessões renovadas por 30 anos em 2026"),
                    "Indexação da receita": ("IGPM/IPCA (reajuste tarifário) + ciclo de revisão ANEEL", "distribuição: receita regulada; geração: PPAs e mercado livre"),
                    "Risco hidrológico/climático": ("Moderado", "tem geração própria (4.411 MW), mas distribuição é 70%+ do EBITDA", "badge-yellow"),
                    "Risco regulatório": ("Alto", "revisão tarifária define a rentabilidade da distribuição; WACC regulatório é o driver", "badge-red"),
                    "Sensibilidade à Selic": ("Alta negativa", "alavancagem + valuation de duration longa", "badge-red"),
                    "Perfil de dividendo": ("Payout ~78%", "DY 8-9%; consistente; favorecido pela State Grid que quer retorno"),
                    "Risco principal": ("Controlador chinês (State Grid) — pode priorizar interesse geopolítico vs. rentabilidade; revisão tarifária ANEEL", ""),
                },
                "EQTL3": {
                    "nome": "Equatorial Energia",
                    "cor": "#F97316",
                    "Segmento principal": ("Distribuidora + saneamento + geração", "a melhor alocadora de capital do setor; adquire distribuidoras problemáticas e recupera"),
                    "Como ganha dinheiro": ("Tarifa de distribuição + taxa de saneamento + geração", "modelo de turnaround: compra barato, recupera, vende ou retém"),
                    "Indexação da receita": ("Tarifa regulada + revisão ANEEL", "foco em distribuidoras com maior potencial de recuperação de perdas"),
                    "Risco hidrológico/climático": ("Baixo", "foco em distribuição; geração é minoritária no resultado", "badge-green"),
                    "Risco regulatório": ("Moderado", "WACC regulatório é crítico, mas a gestão operacional compensa a regulação adversa", "badge-yellow"),
                    "Sensibilidade à Selic": ("Alta negativa", "empresa growth com duration longa; Selic alta comprime valuation do crescimento futuro", "badge-red"),
                    "Perfil de dividendo": ("Payout ~25%", "DY 2-4%; reinveste quase tudo para crescer — não é banco de renda"),
                    "Risco principal": ("Alavancagem em fase de expansão (3,5x) + integração de Sabesp (15%) + execução em saneamento ainda não provada", ""),
                },
                "ALUP11": {
                    "nome": "Alupar",
                    "cor": "#34D399",
                    "Segmento principal": ("Transmissão + geração + América Latina", "9.576 km de linhas; Brasil, Peru, Colômbia, Chile"),
                    "Como ganha dinheiro": ("RAP (transmissão ~75%) + geração (eólica, hídrica, PCH) + comercialização", "TIR real implícita ~8,1%"),
                    "Indexação da receita": ("IPCA + IGPM (mix) + USD (17% das receitas pós-expansão Peru)", "diversificação geográfica e cambial é o diferencial"),
                    "Risco hidrológico/climático": ("Moderado", "tem geração hídrica e eólica, mas transmissão é ~75% do EBITDA", "badge-yellow"),
                    "Risco regulatório": ("Baixo/Moderado", "portfólio de concessões novas; América Latina adiciona risco regulatório externo", "badge-yellow"),
                    "Sensibilidade à Selic": ("Alta negativa", "duration longa; valuation comprimido em juro alto", "badge-red"),
                    "Perfil de dividendo": ("Payout crescente", "DY ~3% hoje; ciclo de capex pesado (R$9 bi); dividendo cresce com entradas em operação"),
                    "Risco principal": ("Alavancagem ~4x em pico de capex + risco regulatório em Peru/Colômbia/Chile + curtailment na geração", ""),
                },
                "CMIG4": {
                    "nome": "Cemig",
                    "cor": "#6B7280",
                    "Segmento principal": ("Estatal integrada MG", "maior distribuidora do Brasil + geração + transmissão; controlada por Minas Gerais"),
                    "Como ganha dinheiro": ("Distribuição + geração + transmissão + comercialização", "holding com subsidiárias (Cemig D, Cemig GT)"),
                    "Indexação da receita": ("Tarifa regulada + PPAs + RAP", "portfólio diversificado mas com risco político estatal"),
                    "Risco hidrológico/climático": ("Alto", "significativa geração hídrica própria", "badge-red"),
                    "Risco regulatório": ("Alto", "estatal estadual sujeita a interferência política de Minas Gerais; debate de federalização", "badge-red"),
                    "Sensibilidade à Selic": ("Alta negativa", "empresa alavancada e de duration longa", "badge-red"),
                    "Perfil de dividendo": ("Payout variável", "DY 8-12%; mas sujeito a decisões políticas do Estado de MG"),
                    "Risco principal": ("Risco político (governo MG + debate de federalização) + posição vendida em energia + alavancagem", ""),
                },
                "CPLE3": {
                    "nome": "Copel",
                    "cor": "#6B7280",
                    "Segmento principal": ("Ex-estatal integrada PR", "privatizada em 2023; geração + transmissão + distribuição no Paraná"),
                    "Como ganha dinheiro": ("Distribuição Paraná + geração hídrica + transmissão", "privatização abriu caminho para eficiência operacional"),
                    "Indexação da receita": ("Tarifa regulada + PPAs + RAP", "perfil mais transparente pós-privatização"),
                    "Risco hidrológico/climático": ("Alto", "forte presença hídrica no Paraná (Iguaçu, Jordão)", "badge-red"),
                    "Risco regulatório": ("Moderado", "privatizada reduz risco político; ainda ajustando eficiência operacional", "badge-yellow"),
                    "Sensibilidade à Selic": ("Alta negativa", "alavancagem + duration longa", "badge-red"),
                    "Perfil de dividendo": ("Payout variável pós-privatização", "DY 6-8%; gestão privada focada em eficiência e capital"),
                    "Risco principal": ("Integração pós-privatização ainda em curso; resultado financeiro ainda não normalizou", ""),
                },
            },
        },
        "perfis": {
            "TAEE11": {
                "nome": "Taesa (Transmissora Aliança de Energia Elétrica)",
                "fundacao": "2009 (parceria Cemig + ISA Colombia)",
                "sede": "Belo Horizonte, MG",
                "tagline": "A NTN-B da bolsa. Receita de longo prazo indexada à inflação, payout de 100%, sem risco climático. O preço que se paga é a alavancagem.",
                "modelo": (
                    "A Taesa é a transmissora pura mais conhecida da B3. Opera mais de 13.000 km de linhas de "
                    "transmissão e 109 subestações em 18 estados. O modelo é simples e poderoso: "
                    "vence um leilão da ANEEL, constrói a linha e passa a receber a RAP (Receita Anual Permitida) "
                    "por 30 anos. A RAP não depende de quanto energia flui pela linha — só de a linha estar disponível "
                    "dentro dos parâmetros técnicos (parâmetros de indisponibilidade geram desconto na RAP, "
                    "chamado de Parcela Variável). Com receita indexada à inflação (60% IGPM + 40% IPCA), "
                    "payout de 100% e sem risco climático, a Taesa é comparada a uma NTN-B de longo prazo. "
                    "O que diferencia dos títulos públicos: risco de renovação de concessões antigas "
                    "com metodologia menos favorável, e alavancagem de 4,7x que limita novos investimentos."
                ),
                "receita": [
                    ("RAP de transmissão", "~95%", "receita contratada por 30 anos, reajustada por IGPM/IPCA"),
                    ("Reforços e melhorias autorizados", "~5%", "RAP adicional por obras autorizadas na concessão"),
                ],
                "vantagens": [
                    "Zero risco climático: transmissão não gera energia — chuva, seca, vento não importam",
                    "RAP indexada à inflação: receita do próximo ano é basicamente conhecida hoje",
                    "Payout de ~100% do lucro regulatório: quem compra recebe praticamente todo o lucro",
                    "Portfólio de categoria II/III (mais transparente): menor risco de surpresa regulatória nas concessões novas",
                    "Quando o IGPM supera o IPCA: receita cresce mais que os custos — assimetria positiva",
                ],
                "riscos": [
                    "Alavancagem de 4,7x dívida líquida/EBITDA — a maior entre as transmissoras da B3",
                    "Concessões antigas têm metodologia diferente: revisão pode reduzir 15-20% da RAP dessas linhas",
                    "Capex pendente de R$2,2 bi em projetos — a empresa precisa captar e construir",
                    "IGPM negativo (já aconteceu em 2017) reduz a receita das concessões indexadas a esse índice",
                    "Selic alta eleva o custo da dívida e comprime o valuation (duration muito longa)",
                ],
                "barreira": (
                    "Uma vez vencido o leilão, a concessão é exclusiva por 30 anos. "
                    "Ninguém constrói uma linha de transmissão paralela — o regulador não autoriza. "
                    "O custo de construção da infraestrutura e a exclusividade regulatória criam "
                    "um monopólio natural de altíssima barreira. "
                    "O desafio não é a concorrência — é vencer o próximo leilão a uma RAP que ainda dê retorno."
                ),
            },
            "ISAE4": {
                "nome": "ISA Energia Brasil (ex-Transmissão Paulista)",
                "fundacao": "1999 (Transmissão Paulista) / controladora ISA Colombia fundada 1967",
                "sede": "São Paulo, SP",
                "tagline": "A transmissora com o melhor portfólio de novas concessões. Mais previsível que a Taesa, menor alavancagem, controlador colombiano.",
                "modelo": (
                    "A ISA Energia é a segunda maior transmissora privada do Brasil, com foco no Sudeste. "
                    "Controlada pela ISA Interconexión Eléctrica S.A. (Colombia), uma das maiores empresas "
                    "de transmissão da América Latina. O diferencial da ISA vs Taesa está na qualidade "
                    "do portfólio: as concessões são predominantemente de categoria II e III, "
                    "com metodologia regulatória mais moderna e transparente — menos risco de surpresas "
                    "na revisão de RAP. Menor alavancagem que a Taesa, TIR real implícita de ~7,7%, "
                    "o que a coloca em posição mais defensiva no setor. Também tem participação minoritária "
                    "da Axia Energia (ex-Eletrobras) em algumas concessões, o que cria uma relação "
                    "estratégica com a maior geradora do país."
                ),
                "receita": [
                    ("RAP de transmissão", "~98%", "receita contratada por 30 anos, predominantemente indexada ao IPCA"),
                    ("Outros serviços", "~2%", "operação e manutenção de terceiros"),
                ],
                "vantagens": [
                    "Portfólio de concessões modernas (cat. II/III): menor risco regulatório vs Taesa",
                    "Menor alavancagem: mais espaço para novos leilões sem pressionar o balanço",
                    "TIR real implícita de ~7,7% — bem acima da NTN-B de prazo semelhante",
                    "Controlador com track record: ISA Colombia opera transmissão em 6 países com excelência",
                    "Zero risco climático — mesmo modelo de receita da Taesa",
                ],
                "riscos": [
                    "Controlador colombiano: decisões vêm de fora do Brasil — alinhamento com minoritários nem sempre é total",
                    "Selic alta comprime valuation como em qualquer transmissora de duration longa",
                    "Menor liquidez que Taesa na B3 — spread bid/ask maior para investidores institucionais",
                    "Depende de novos leilões para crescer — mercado de transmissão é competitivo",
                ],
                "barreira": (
                    "Idem à Taesa: exclusividade regulatória de 30 anos e custo proibitivo de infraestrutura. "
                    "Adicionalmente, o relacionamento com a Axia e a presença no Sudeste (onde está a maior "
                    "demanda do país) são vantagens geográficas e de relacionamento difíceis de replicar."
                ),
            },
            "EGIE3": {
                "nome": "Engie Brasil Energia",
                "fundacao": "1994 (como Nacional Energética; marca Engie desde 2016)",
                "sede": "Florianópolis, SC",
                "tagline": "A maior geradora privada do Brasil. 100% renovável, controlada pela Engie francesa. O desafio é o curtailment crescente e o capex pesado.",
                "modelo": (
                    "A Engie Brasil é a maior empresa privada de geração de energia do país, com ~12,9 GW "
                    "de capacidade instalada em 145 usinas. O portfólio é 100% renovável: hidrelétricas (~70%), "
                    "eólicas, solares e biomassa. Além disso, é sócia da TAG — a maior malha de transporte "
                    "de gás natural do Brasil, com 4.500 km em 10 estados. "
                    "O modelo de receita combina PPAs (contratos de longo prazo, indexados ao IPCA) "
                    "com exposição ao mercado livre (PLD spot). "
                    "O desafio atual: curtailment crescente (26% projetado em 2026, 32% em 2027) "
                    "— o ONS corta a geração renovável em momentos de sobreoferta. "
                    "A estratégia de resposta é migrar parte do portfólio para transmissão, "
                    "que gera RAP previsível e não sofre curtailment. Em 2025, venceu lotes "
                    "de transmissão nos leilões da ANEEL — a diversificação está em andamento."
                ),
                "receita": [
                    ("PPAs de longo prazo (geração hídrica + eólica)", "~60%", "contratos indexados ao IPCA com distribuidoras e grandes consumidores"),
                    ("TAG (transporte de gás, participação ~32%)", "~20%", "RAP regulada — receita previsível, sem exposição a preço de gás"),
                    ("Mercado livre de energia (ACL)", "~15%", "preço spot variável — mais volátil"),
                    ("Transmissão nascente + outros", "~5%", "RAP de novos projetos em construção (Asa Branca, Graúna)"),
                ],
                "vantagens": [
                    "Controladora Engie (França): acesso a tecnologia, capital barato e modelo global de energia renovável",
                    "TAG: ativo de transmissão de gás com receita regulada — reduz a volatilidade da geração",
                    "100% renovável: posicionamento ESG premium para contratos com multinacionais exigentes",
                    "Maior geradora privada: escala garante acesso aos melhores PPAs e aos maiores leilões",
                    "Expansão em transmissão: diversifica para ativos de menor volatilidade",
                ],
                "riscos": [
                    "Curtailment: 26-32% projetado para 2026-2027 — energia produzida mas não vendida",
                    "Dependência hídrica (~70%): secas ou GSF negativo afetam diretamente a geração",
                    "Ciclo de capex pesado: Jirau, Asa Branca, Graúna — R$6 bi investidos em 2025 pressionam o FCF",
                    "Payout reduzido para mínimo de 55% no ciclo de capex — DY caiu vs histórico",
                    "Selic alta + alavancagem acima de 2,5x: pressão financeira em ciclo de investimento",
                ],
                "barreira": (
                    "Concessões hidrelétricas são praticamente inreplicáveis — os melhores rios já têm dono. "
                    "Quem tem Itá, Machadinho, Estreito e Jaguara tem ativos que não se licenciam mais hoje. "
                    "A TAG é a única malha de transporte de gás em 10 estados — monopólio natural regulado. "
                    "E a marca Engie com 30 anos no Brasil abre portas que novos entrantes levariam décadas para abrir."
                ),
            },
            "AXIA3": {
                "nome": "Axia Energia (ex-Eletrobras)",
                "fundacao": "1961 (como Eletrobras); privatizada em 2022; renomeada Axia Energia em 2025",
                "sede": "Rio de Janeiro, RJ",
                "tagline": "A maior empresa do setor elétrico brasileiro. Privatizada em 2022, ainda digerindo a transição. TIR implícita de 10% real.",
                "modelo": (
                    "A Axia é a antiga Eletrobras — a maior empresa do setor elétrico brasileiro, "
                    "com cerca de 30 GW de capacidade instalada e participação em dezenas de "
                    "concessões de geração e transmissão. A privatização de 2022 foi o maior evento "
                    "do setor em décadas, mas a transição ainda está sendo digerida. "
                    "O portfólio tem uma peculiaridade: parte significativa das usinas opera em 'regime de cotas' "
                    "— um modelo regulatório onde a energia é dividida entre distribuidoras a preço fixo, "
                    "tirando a geração do mercado livre. O processo de 'descotização' (sair das cotas) "
                    "está em andamento mas é lento, o que significa que o portfólio ainda é menos "
                    "lucrativo do que poderia ser. "
                    "Em 2025 concluiu a migração para o Novo Mercado da B3, simplificou a estrutura "
                    "acionária e iniciou a venda de ativos não-estratégicos — são os primeiros sinais "
                    "de que a gestão privada está gerando valor."
                ),
                "receita": [
                    ("Geração hídrica em cotas", "~50%", "preço regulado; menos lucrativo que o mercado livre"),
                    ("Geração hídrica em ACL (mercado livre)", "~30%", "preço de mercado — potencial de crescimento com descotização"),
                    ("Transmissão (RAP)", "~15%", "concessões de transmissão em diversas regiões"),
                    ("Outros (comercialização, participações)", "~5%", ""),
                ],
                "vantagens": [
                    "Maior empresa do setor — presença em praticamente todos os grandes projetos hídricos do Brasil",
                    "TIR real implícita de ~10%: bem acima de pares de transmissão (~7-8%)",
                    "Descotização: cada usina que sai das cotas entra no mercado livre a preço melhor — upside de longo prazo",
                    "Novo Mercado: governança melhorando, estrutura acionária simplificada",
                    "Custo de geração entre os mais baixos do mundo (hídrica velha = sem depreciação relevante)",
                ],
                "riscos": [
                    "Risco político: governo ainda questiona aspectos do acordo de privatização; risco de revisão de termos",
                    "Portfólio mais descontratado: menos energia comprometida em contratos de longo prazo vs pares",
                    "Descotização é lenta: upside real ainda depende de decisões regulatórias e políticas",
                    "Complexidade: dezenas de subsidiárias, concessões e participações — difícil de analisar",
                    "GSF: maior exposição hídrica do setor = mais vulnerável à seca",
                ],
                "barreira": (
                    "São décadas de concessões hídrica em rios que já foram inventariados — "
                    "Tucuruí, Balbina, Itaipu (participação), Angra (nuclear): ativos que jamais serão "
                    "licenciados de novo. A escala de 30 GW e o papel sistêmico no SIN "
                    "(o ONS não opera sem a Axia) criam uma barreira que é, na prática, o próprio Brasil."
                ),
            },
            "CPFE3": {
                "nome": "CPFL Energia",
                "fundacao": "1912",
                "sede": "Campinas, SP",
                "tagline": "A distribuidora integrada com a maior capilaridade do Sudeste. DY consistente de 8-9% e controlador chinês que quer estabilidade.",
                "modelo": (
                    "A CPFL é uma das maiores empresas do setor elétrico brasileiro, com presença "
                    "em distribuição (14% do mercado nacional, 10,3 mi de clientes em 687 municípios), "
                    "geração (4.411 MW, entre as maiores privadas) e transmissão. "
                    "Controlada desde 2017 pela State Grid Corporation of China — a maior empresa "
                    "de energia do mundo, atendendo 1,1 bilhão de pessoas. "
                    "O controlador quer estabilidade e dividendos, não aventura: o plano de R$29,8 bi "
                    "para 2025-2029 foca em modernizar a distribuição existente (R$24,7 bi em distribuição), "
                    "não em crescer por aquisições agressivas. "
                    "Em maio de 2026, renovou as concessões das três distribuidoras principais "
                    "(CPFL Paulista, Piratininga, RGE) por mais 30 anos — uma redução relevante de "
                    "risco de prazo que o mercado subestimou."
                ),
                "receita": [
                    ("Distribuição de energia (CPFL Paulista, Piratininga, RGE, Santa Cruz)", "~65%", "2ª maior distribuidora do Brasil em volume"),
                    ("Geração (hídrica + eólica + solar + biomassa)", "~25%", "4.411 MW de capacidade instalada"),
                    ("Transmissão (CPFL Transmissão)", "~8%", "RAP de linhas de transmissão"),
                    ("Comercialização e serviços", "~2%", ""),
                ],
                "vantagens": [
                    "Concessões renovadas por 30 anos em 2026: risco de prazo eliminado para as principais distribuidoras",
                    "State Grid como controlador: acesso a capital barato (empréstimo em RMB do NDB), tecnologia chinesa e planejamento de longo prazo",
                    "2ª maior distribuidora em volume: escala que poucos concorrentes têm no Sudeste",
                    "DY consistente de 8-9%: controlador quer dividendo; payout de 78% é sustentável",
                    "Gestão operacional eficiente: CPFL tem histórico de índices de qualidade acima da média do setor",
                ],
                "riscos": [
                    "Controlador chinês: geopolítica pode criar ruído regulatório ou político no futuro",
                    "Revisão tarifária: WACC regulatório da ANEEL define a rentabilidade da distribuição — risco periódico",
                    "Alavancagem moderada e capex de R$29,8 bi: FCF comprometido para crescimento, não para DY extra",
                    "Exposição ao Sudeste: crescimento da GD (painéis solares) pode reduzir consumo faturado das distribuidoras",
                    "Mercado Livre: migração de grandes clientes para ACL reduz base de consumidores cativos",
                ],
                "barreira": (
                    "687 municípios com concessão exclusiva de distribuição no Sudeste e Sul. "
                    "Nenhum concorrente entra nesse território — a concessão é de 30 anos, renovada. "
                    "A combinação de escala, capilaridade e o apoio da maior empresa de energia do "
                    "mundo como controlador cria uma posição que é inatingível por qualquer novo entrante."
                ),
            },
            "EQTL3": {
                "nome": "Equatorial Energia",
                "fundacao": "2004",
                "sede": "São Luís, MA",
                "tagline": "A melhor alocadora de capital do setor elétrico. Compra distribuidoras caóticas, enxuga, recupera e gera retorno acima de qualquer par.",
                "modelo": (
                    "A Equatorial não é uma distribuidora comum — é uma operadora especializada em "
                    "turnaround de distribuidoras. O modelo é simples de explicar e difícil de executar: "
                    "compra distribuidoras com altíssima inadimplência, furto e ineficiência "
                    "(pagando barato por isso), reduz as perdas, melhora a cobrança, normativa "
                    "os índices de qualidade e passa a extrair margem de uma operação que "
                    "estava destruindo valor. Fez isso com a Eletrobras/CEMAR (Maranhão), "
                    "com a CELPA (Pará), com a COELCE (Ceará), com a CELG-D (Goiás), com a CEA (Amapá) "
                    "e com a CEPISA (Piauí). Cada aquisição foi uma aposta que o mercado duvidou "
                    "e a Equatorial executou. Em 2025, entrou no saneamento (15% da Sabesp) "
                    "e já tem posições em saneamento em outros estados. "
                    "DY baixo porque reinveste quase tudo — mas valorização histórica "
                    "é a melhor do setor por décadas."
                ),
                "receita": [
                    ("Distribuição de energia (6 estados)", "~75%", "MA, PA, CE, GO, AP, PI — foco em Norte/Nordeste onde havia mais potencial"),
                    ("Saneamento (Sabesp 15% + outros)", "~15%", "novo vetor de crescimento — mesma lógica de turnaround"),
                    ("Geração, transmissão e telecom", "~10%", "ativos complementares vendidos quando maduros"),
                ],
                "vantagens": [
                    "Track record de turnaround: cada aquisição que o mercado duvidou, a Equatorial executou",
                    "Gestão de perdas superior: reduz inadimplência e furto nos níveis que distribuidoras estatais nunca conseguiram",
                    "Regiões de maior potencial: Norte e Nordeste têm mais espaço para redução de perdas que Sudeste já maduro",
                    "Expansão em saneamento: a mesma lógica de turnaround aplicada a um setor ainda mais ineficiente",
                    "TIR real de 11,1% implícita: premium justificado pelo histórico e pelo pipeline de crescimento",
                ],
                "riscos": [
                    "Alavancagem de 3,5x em fase de expansão — cada nova aquisição pressiona mais o balanço",
                    "Sabesp (15%): primeira entrada no saneamento de grande escala — execução ainda não provada",
                    "Não é banco de renda: DY de 2-4% decepciona investidores que buscam renda mensal",
                    "Regulação adversa: WACC regulatório menor ou opex regulatório mais restritivo comprimir margens",
                    "Integração de múltiplos ativos simultâneos: complexidade operacional cresce com o portfólio",
                ],
                "barreira": (
                    "A capacidade de executar turnaround é a barreira — e ela não se compra, se constrói em décadas. "
                    "A Equatorial tem um playbook testado, uma equipe que já fez isso 6 vezes e "
                    "relacionamentos com reguladores e comunidades locais que constroem confiança. "
                    "Nenhum concorrente combina o histórico de execução com o acesso a capital "
                    "e a disposição de atuar em regiões que outros evitam. "
                    "É o modelo mais difícil de imitar no setor."
                ),
            },
            "ALUP11": {
                "nome": "Alupar Investimento",
                "fundacao": "2000 (holding formalizada em 2007)",
                "sede": "São Paulo, SP",
                "tagline": "A transmissora com ambição latino-americana. Controle 100% nacional, expansão no Peru e Colômbia, e a única com concessão vitalícia no exterior.",
                "modelo": (
                    "A Alupar é uma holding privada de controle nacional que opera transmissão e geração "
                    "no Brasil e na América Latina. No Brasil, detém 9.576 km de linhas de transmissão "
                    "em 42 sistemas — a terceira maior transmissora privada do país em RAP. "
                    "No exterior, opera no Peru (6 projetos de transmissão + 1 PCH), na Colômbia "
                    "(PCH Morro Azul + 2 transmissoras, incluindo concessão VITALÍCIA) e no Chile. "
                    "O modelo é transmissão como core (~75% do EBITDA, RAP previsível) "
                    "complementado por geração (4 UHEs, 4 PCHs, 7 eólicos, 1 solar — 798 MW). "
                    "A geração serve para complementar, não como motor principal. "
                    "O grande diferencial: com 17% das receitas em USD após os projetos do Peru, "
                    "a Alupar reduz a exposição à regulação brasileira. "
                    "Está em ciclo pesado de capex (R$9 bi no ciclo atual), o que comprime o DY "
                    "hoje mas cria o pipeline de crescimento para os próximos 5-7 anos."
                ),
                "receita": [
                    ("RAP de transmissão Brasil", "~65%", "42 sistemas; IPCA e IGPM; projetos entrando até 2029"),
                    ("Geração renovável Brasil", "~20%", "hídrica, eólica, PCH, solar — 798 MW; PPAs de longo prazo"),
                    ("Transmissão e geração América Latina", "~15%", "Peru, Colômbia, Chile — crescente; parte em USD"),
                ],
                "vantagens": [
                    "Controle 100% nacional: fundadores operam e são donos — alinhamento total de interesses",
                    "Concessão vitalícia na Colômbia: ativo único no setor — RAP sem prazo de vencimento",
                    "Expansão em USD (Peru): hedge natural contra depreciação do real",
                    "Pipeline de entrada operacional: projetos entram até 2029 gerando RAP incremental",
                    "TIR real implícita de ~8,1%: superior à Taesa (~4,7%) e próxima da ISA (~7,7%)",
                ],
                "riscos": [
                    "Alavancagem em pico de ~4x: capex de R$9 bi nos próximos anos pressiona o balanço",
                    "Risco regulatório externo: Peru, Colômbia e Chile têm marcos menos previsíveis que o Brasil",
                    "DY atual baixo (~3%): ciclo de capex comprime dividendo; investidor de renda pode se frustrar",
                    "Curtailment na geração eólica: afeta receita do segmento de geração",
                    "Execução simultânea: 12 projetos em andamento, 9 fora do Brasil — gestão complexa",
                ],
                "barreira": (
                    "Concessões de 30 anos — e na Colômbia, vitalícia. "
                    "A capacidade de executar transmissão em países com regulação distinta é expertise "
                    "que poucos têm e que anos de presença no exterior constroem. "
                    "A escala de 9.576 km de linhas abre portas em leilões onde operadores menores "
                    "não conseguem participar. E o controle familiar alinhado "
                    "garante que o retorno ao acionista é o objetivo, não objetivos políticos."
                ),
            },
            "CMIG4": {
                "nome": "Cemig",
                "fundacao": "1952 (por Juscelino Kubitschek)",
                "sede": "Belo Horizonte, MG",
                "tagline": "A estatal integrada de Minas Gerais. Maior distribuidora do Brasil, com risco político que o mercado desconta no preço.",
                "modelo": (
                    "A Cemig é uma holding integrada — opera distribuição (Cemig D), "
                    "geração e transmissão (Cemig GT) e tem participações em outras empresas do setor. "
                    "É a maior distribuidora do Brasil em número de municípios atendidos e a quarta "
                    "em transmissão. Controlada pelo Estado de Minas Gerais (50,97% das ONs), "
                    "sofre com o conflito clássico do estatal: o governo quer dividendos para fechar "
                    "as contas do estado, mas também quer tarifas baixas para os eleitores. "
                    "Em 2025, gerou discussão sobre possível federalização como parte do acordo "
                    "da dívida de MG com o governo federal — um risco que assusta o mercado "
                    "mas ainda não se concretizou."
                ),
                "receita": [
                    ("Distribuição Minas Gerais (Cemig D)", "~55%", "maior distribuidora do Brasil em cobertura geográfica"),
                    ("Geração hídrica e eólica (Cemig GT)", "~30%", "portfólio diversificado, mas com exposição hídrica"),
                    ("Transmissão", "~10%", "4ª maior do Brasil"),
                    ("Participações e comercialização", "~5%", ""),
                ],
                "vantagens": [
                    "Escala: maior distribuidora em municípios atendidos — MG tem 853 municípios",
                    "DY alto (8-12%): governo precisa de dividendo para fechar as contas do estado",
                    "Valuation descontado pelo risco político: quem acredita no desconto pode se beneficiar",
                    "Portfólio diversificado: geração + transmissão + distribuição reduz concentração em um segmento",
                ],
                "riscos": [
                    "Risco político: governo MG intervém em gestão, tarifa e alocação de capital",
                    "Debate de federalização: dívida de MG com a União pode levar à transferência do controle",
                    "Posição vendida em energia: Cemig ficou descoberta em contratos de energia, gerando prejuízo",
                    "Alavancagem ~2,3-2,5x: não é crítico mas limita flexibilidade",
                    "Eficiência abaixo de privados: custo de servir mais alto por natureza estatal",
                ],
                "barreira": (
                    "A concessão de distribuição em Minas Gerais — o estado mais rico em recursos naturais "
                    "e o terceiro maior estado em PIB do Brasil. "
                    "O portfólio de usinas hidrelétricas em rios mineiros é inreplicável. "
                    "O problema: a barreira é do Estado de MG, não da empresa — "
                    "e o controlador pode usá-la para objetivos políticos em vez de econômicos."
                ),
            },
            "CPLE3": {
                "nome": "Copel",
                "fundacao": "1954",
                "sede": "Curitiba, PR",
                "tagline": "A ex-estatal do Paraná. Privatizada em 2023, agora sob gestão privada buscando eficiência que o Estado nunca priorizou.",
                "modelo": (
                    "A Copel é a empresa integrada de energia do Paraná — geração (hídrica no rio Iguaçu "
                    "e afluentes), transmissão e distribuição. Em 2023, foi privatizada pelo governo do Paraná, "
                    "encerrando 70 anos como estatal. A privatização abriu espaço para buscar eficiência "
                    "operacional, reduzir custos e orientar a gestão para retorno ao acionista "
                    "em vez de objetivos políticos. "
                    "Diferente da Cemig (que ainda é estatal), a Copel já não tem o risco "
                    "de interferência política do governo. Mas ainda está no processo de ajuste "
                    "pós-privatização: normalização do resultado financeiro, revisão de contratos "
                    "e alinhamento da cultura organizacional ao modelo privado leva tempo."
                ),
                "receita": [
                    ("Distribuição Paraná (Copel DIS)", "~55%", "distribuição regulada em todo o estado do Paraná"),
                    ("Geração hídrica + eólica (Copel GeT)", "~30%", "Iguaçu, Jordão e complexos eólicos"),
                    ("Transmissão (Copel Transmissão)", "~12%", "RAP de linhas em todo o Brasil"),
                    ("Telecomunicações (Copel Telecom)", "~3%", "fibra óptica no Paraná — diferencial único"),
                ],
                "vantagens": [
                    "Privatização recente: gestão privada ainda capturando eficiência que o estado não priorizou",
                    "Única utility listada com braço de telecom próprio: Copel Telecom é diferencial raro no setor",
                    "Paraná: estado com melhor qualidade de crédito e menor inadimplência do Brasil — base de consumidores sólida",
                    "Geração hídrica no Iguaçu: hidrologia de boa qualidade no Sul (diferente do Sudeste/Nordeste)",
                ],
                "riscos": [
                    "Resultado pós-privatização ainda normalizando: curva de aprendizado da gestão privada",
                    "Alavancagem: ciclo de investimentos pós-privatização pressiona o balanço",
                    "Hidrologia Sul: enchentes no RS/SC em 2024 mostraram que o Sul também tem risco climático",
                    "Copel Telecom: negócio diferente do core elétrico, exige expertise e capex específicos",
                ],
                "barreira": (
                    "Concessão exclusiva de distribuição em todo o Paraná — um estado de 11 mi de habitantes "
                    "e PIB relevante. As usinas do rio Iguaçu são um dos maiores sistemas hídricos do Sul "
                    "e são inreplicáveis. A rede de transmissão de fibra óptica da Copel Telecom "
                    "seria levada décadas para ser construída por qualquer entrante. "
                    "Pós-privatização, o risco de interferência política foi eliminado — "
                    "a barreira ficou mais limpa."
                ),
            },
        },
    },
    "🏗️ Incorporadoras": {
        "tickers": ["CURY3", "DIRR3", "CYRE3", "MDNE3"],
        "tagline": "O setor onde mais importa saber o que a empresa NÃO é. MCMV e alto padrão são negócios tão diferentes que deveriam ter nomes distintos — mas o mercado os mistura no mesmo índice.",
        "logica": {
            "titulo": "O que move o setor — e por que MCMV e alto padrão são mundos diferentes",
            "texto": (
                "A primeira coisa que o investidor de incorporadora precisa internalizar: "
                "MCMV (baixa renda) e alto padrão são dois negócios com ciclos opostos. "
                "Quando a Selic sobe e o crédito encarece, o alto padrão desacelera — "
                "o comprador de R$2 mi sente o juro. O MCMV continua, porque o crédito é subsidiado "
                "pelo FGTS a taxas de 4-10,5% ao ano, independente da Selic. "
                "Em 2025-2026, 75% dos lançamentos em São Paulo foram MCMV — enquanto o alto padrão "
                "perdeu velocidade de vendas. Entender em qual faixa cada empresa opera é mais importante "
                "do que qualquer múltiplo."
            ),
            "drivers": [
                ("FGTS e o subsídio do MCMV — o motor que não para", (
                    "O FGTS financia o MCMV a taxas de 4% a 10,5% ao ano, bem abaixo do mercado (9-11%). "
                    "Em 2026, R$205 bilhões disponíveis para financiamentos — crescimento de 17% sobre 2025. "
                    "O FGTS tem R$214 bi de reservas. Enquanto o FGTS existir, o MCMV não para. "
                    "Isso cria uma proteção estrutural que as incorporadoras de baixa renda não têm no alto padrão."
                )),
                ("Selic e crédito habitacional — o inimigo do médio/alto padrão", (
                    "Crédito fora do MCMV (SBPE) é financiado a 9-11% ao ano. "
                    "Com Selic em 14,5% e inflação pressionando, o comprador de médio/alto padrão "
                    "perde poder de compra ou posterga a decisão. "
                    "Por isso a Cyrela (CYRE3) viu lançamentos de alto padrão caírem 71% no 1T26, "
                    "enquanto a Cury (CURY3) cresceu 33% no mesmo período."
                )),
                ("VGV e VSO — as métricas que substituem o P/L", (
                    "VGV (Valor Geral de Vendas): o volume total a ser lançado. "
                    "VSO (Velocidade de Vendas sobre Oferta): % do estoque vendido no trimestre. "
                    "VSO acima de 25% é saudável — indica demanda forte. Abaixo de 15%, acumula estoque. "
                    "O P/L de incorporadora é distorcido pelo PoC (reconhecimento de receita ao longo da obra) — "
                    "o que foi vendido hoje só entra no resultado em 18-36 meses. Sempre olhe VGV e VSO primeiro."
                )),
                ("Landbank — a matéria-prima mais escassa", (
                    "Landbank é o banco de terrenos disponíveis para lançar. "
                    "Quanto mais anos de visibilidade, mais estável o crescimento. "
                    "Cury: R$24,9 bi (3+ anos). Direcional: R$51,3 bi (8+ anos). "
                    "A forma de adquirir o terreno muda tudo: permuta (o terreno entra como pagamento "
                    "por unidades futuras) não consome caixa. "
                    "Direcional compra 86% via permuta — por isso tem caixa mesmo com landbank gigante."
                )),
                ("INCC e custo de construção — o risco que vem de fora", (
                    "O INCC (custo da construção) subiu acima da inflação em 2025-2026 — "
                    "escassez de mão de obra afeta 82% das empresas. "
                    "Incorporadoras repassam o INCC no preço de venda — mas com defasagem. "
                    "Quem tem contrato de fornecimento de longo prazo ou método construtivo industrializado "
                    "(formas de alumínio da Direcional, alvenaria estrutural da Cury) tem mais controle de custo."
                )),
                ("PoC — por que o lucro não reflete o presente", (
                    "PoC (Percentual de Obra Concluída): a receita é reconhecida conforme a obra avança. "
                    "Uma unidade vendida hoje por R$500 mil só gera receita ao longo dos 24-36 meses de construção. "
                    "Por isso o resultado atual reflete vendas de 1-3 anos atrás, não o presente. "
                    "O 'resultado a apropriar' (backlog) é o dado que mostra o futuro — "
                    "incorporadoras com alto backlog têm receita previsível por anos."
                )),
            ],
        },
        "comparativo": {
            "dimensoes": [
                "Posicionamento de produto",
                "Motor de demanda",
                "Geografia",
                "Método construtivo",
                "Landbank (visibilidade)",
                "ROE (referência)",
                "Sensibilidade à Selic",
                "Dividendo (DY)",
                "Risco principal",
            ],
            "grupos": [
                {"label": "MCMV e baixa renda — protegidos pelo FGTS", "tickers": ["CURY3", "DIRR3"]},
                {"label": "Multi-segmento — exposição ao ciclo de juros", "tickers": ["CYRE3", "MDNE3"]},
            ],
            "empresas": {
                "CURY3": {
                    "nome": "Cury Construtora",
                    "cor": "#F97316",
                    "Posicionamento de produto": ("MCMV puro", "todas as faixas do programa; nenhuma exposição ao médio/alto padrão"),
                    "Motor de demanda": ("FGTS + subsídio", "imune à Selic — crédito a 4-10,5% independe do mercado", "badge-green"),
                    "Geografia": ("SP + RJ metropolitano", "empreendimentos em áreas centrais com transporte — diferencial de localização"),
                    "Método construtivo": ("Alvenaria estrutural", "blocos de concreto — flexibilidade e eficiência; custo controlado"),
                    "Landbank (visibilidade)": ("R$24,9 bi — 3+ anos", "82.119 unidades em 88 empreendimentos"),
                    "ROE (referência)": ("79,5% (1T26)", "maior ROE do setor; caixa líquido positivo", "badge-green"),
                    "Sensibilidade à Selic": ("Muito baixa", "MCMV não depende de crédito de mercado", "badge-green"),
                    "Dividendo (DY)": ("DY ~13%", "payout alto — sem necessidade de reter capital"),
                    "Risco principal": ("Mudança nas regras do MCMV/FGTS + concentração em SP/RJ + escassez de mão de obra", ""),
                },
                "DIRR3": {
                    "nome": "Direcional",
                    "cor": "#3B82F6",
                    "Posicionamento de produto": ("MCMV (faixas 2 e 3) + médio-baixo (Riva)", "duas marcas; Riva para renda até R$13 mil (também enquadrada no MCMV em 2026)"),
                    "Motor de demanda": ("FGTS + SBPE médio-baixo", "MCMV protegido; Riva beneficiada pela nova faixa 4", "badge-green"),
                    "Geografia": ("8 estados + DF", "maior construtora em área do Brasil; diversificação regional reduz risco"),
                    "Método construtivo": ("Formas de alumínio industrializadas", "ciclo de construção mais curto e custo previsível; escala nacional"),
                    "Landbank (visibilidade)": ("R$51,3 bi — 8+ anos", "86% via permuta — não consome caixa; o maior landbank do setor"),
                    "ROE (referência)": ("44% (2025)", "menor que Cury mas elevado para o setor; cresce 25% ao ano", "badge-yellow"),
                    "Sensibilidade à Selic": ("Baixa (MCMV) / Moderada (Riva)", "Riva pode ser afetada se Selic não cair; MCMV é protegido", "badge-yellow"),
                    "Dividendo (DY)": ("DY ~17%", "payout generoso + R$804 mi pagos em 2025; alavancagem baixa"),
                    "Risco principal": ("Concentração no MCMV + desaceleração da Riva em juros altos + INCC pressionando custos", ""),
                },
                "CYRE3": {
                    "nome": "Cyrela",
                    "cor": "#EF4444",
                    "Posicionamento de produto": ("Alto padrão + médio + MCMV", "Cyrela (luxo) + Living (médio) + Vivaz (MCMV) — São Paulo como principal mercado"),
                    "Motor de demanda": ("Renda alta + crédito SBPE", "comprador de luxo não financia — paga à vista; médio padrão sensível à Selic", "badge-red"),
                    "Geografia": ("SP + 16 estados e 66 cidades", "forte no Sudeste; alto padrão concentrado em SP"),
                    "Método construtivo": ("Múltiplos métodos + JVs", "opera via parcerias (Cury, Lavvi, Plano&Plano) — escala sem necessidade de construção própria"),
                    "Landbank (visibilidade)": ("Não divulga consolidado", "portfólio concentrado em projetos de alto VGV unitário"),
                    "ROE (referência)": ("11% (1T26)", "pressionado pela desaceleração do alto padrão; muito abaixo dos pares MCMV", "badge-red"),
                    "Sensibilidade à Selic": ("Alta", "alto padrão sofre quando crédito encarece; lançamentos -48% no 1T26", "badge-red"),
                    "Dividendo (DY)": ("DY ~12%", "payout alto historicamente; mas resultado pressionado reduz base"),
                    "Risco principal": ("Desaceleração do alto padrão em SP + ROE baixo vs pares + concorrência de luxo importado", ""),
                },
                "MDNE3": {
                    "nome": "Moura Dubeux",
                    "cor": "#8B5CF6",
                    "Posicionamento de produto": ("Alto padrão + médio + MCMV (Nordeste)", "Moura Dubeux (luxo) + Mood (médio) + Ún1ca (MCMV) — holding MDNE fundada em 2026"),
                    "Motor de demanda": ("Renda alta nordestina + crescimento regional", "Nordeste tem demanda reprimida maior que SP; menos concorrência no luxo", "badge-green"),
                    "Geografia": ("7 estados do Nordeste", "liderança absoluta no mercado imobiliário do Nordeste — barreiras regionais elevadas"),
                    "Método construtivo": ("Verticalizado + modelo de condomínio", "construtora verticalizada; modelo único de 'condomínio' onde clientes compram terreno coletivamente"),
                    "Landbank (visibilidade)": ("R$5,5 bi VGV guidance 2026", "landbank crescendo com Ún1ca (MCMV) para diversificar risco"),
                    "ROE (referência)": ("ROAE 27% (1T26)", "forte para o padrão do segmento; P/L de 5,79x", "badge-yellow"),
                    "Sensibilidade à Selic": ("Moderada", "alto padrão sensível, mas Nordeste tem menos especulação que SP; nova marca MCMV protege", "badge-yellow"),
                    "Dividendo (DY)": ("DY ~17%", "alta distribuição; pagou R$351 mi em 2025"),
                    "Risco principal": ("Concentração geográfica no Nordeste + integração das 3 marcas ainda recente + Ún1ca (MCMV) em fase inicial", ""),
                },
            },
        },
        "perfis": {
            "CURY3": {
                "nome": "Cury Construtora e Incorporadora",
                "fundacao": "1963 (por Elias Cury em São Paulo)",
                "sede": "São Paulo, SP",
                "tagline": "A incorporadora de MCMV com o maior ROE do Brasil. Em 63 anos, nunca vendeu um imóvel fora do programa habitacional — e é exatamente isso que a torna tão rentável.",
                "modelo": (
                    "A Cury é uma das mais puras histórias de foco do mercado imobiliário brasileiro. "
                    "Em 63 anos de história, atua quase exclusivamente no MCMV — "
                    "em São Paulo e Rio de Janeiro metropolitano, nas faixas mais altas do programa. "
                    "O modelo tem três vantagens estruturais que se reforçam mutuamente. "
                    "Primeiro, o crédito: FGTS a 4-10,5% ao ano não muda com a Selic — "
                    "quando o mercado de médio padrão desacelera, a Cury continua vendendo. "
                    "Segundo, a localização: empreendimentos em áreas centrais próximas a metrô e "
                    "serviços, diferente de concorrentes que vão para a periferia mais barata. "
                    "Terceiro, o método construtivo: alvenaria estrutural (blocos de concreto) "
                    "permite flexibilidade de planta, custo controlado e velocidade de entrega. "
                    "O resultado: ROE de 79,5% no 1T26 — o mais alto do setor — mesmo com caixa líquido "
                    "positivo, o que demonstra que a geração de caixa é real, não alavancada. "
                    "Entre 2020 e 2025, multiplicou receita em 5x, VGV em 5,5x e lucro em 5,7x."
                ),
                "receita": [
                    ("MCMV faixas 2, 3 e 4 — São Paulo", "~65%", "principal mercado; áreas centrais com transporte; ticket médio crescente"),
                    ("MCMV faixas 2, 3 e 4 — Rio de Janeiro", "~35%", "segundo mercado; expansão acelerada nos últimos 3 anos"),
                ],
                "vantagens": [
                    "ROE de 79,5% (1T26) — o mais alto do setor, mesmo sendo caixa líquido positivo",
                    "MCMV imune à Selic: crédito a 4-10,5% via FGTS não muda com a taxa de mercado",
                    "Localização diferenciada: empreendimentos próximos ao metrô em SP/RJ — demanda captiva",
                    "Landbank de R$24,9 bi com 3+ anos de visibilidade — crescimento previsível",
                    "Velocidade de vendas (VSO) de 46% no 1T26 — a mais alta do setor",
                ],
                "riscos": [
                    "Zero diversificação: qualquer mudança nas regras do MCMV ou FGTS impacta 100% da receita",
                    "Concentração em SP e RJ: dois mercados, sem diversificação geográfica",
                    "Escassez de mão de obra: causou atrasos em obras em 2025; produtividade em recuperação em 2026",
                    "Sucessão executiva: modelo de Co-CEO anunciado em 2026 — transição de gestão é risco de curto prazo",
                    "Valuation esticado: P/L de 7-8x para uma empresa de MCMV é acima da média histórica do setor",
                ],
                "barreira": (
                    "63 anos construindo para o mesmo público no mesmo mercado. "
                    "A Cury conhece cada zona de uso de São Paulo e Rio de Janeiro como ninguém. "
                    "Sabe onde tem metro previsto, onde vai ter densificação, onde o terreno ainda está barato. "
                    "Esse banco de dados de décadas de relacionamento com prefeituras, "
                    "vendedores de terreno e a Caixa Econômica Federal é inreplicável. "
                    "Qualquer entrante levaria anos para construir a rede de relacionamentos "
                    "que permite a Cury comprar terreno antes do concorrente saber que está à venda."
                ),
            },
            "DIRR3": {
                "nome": "Direcional Engenharia",
                "fundacao": "1981 (por Ricardo Valadares Gontijo em Belo Horizonte)",
                "sede": "Belo Horizonte, MG",
                "tagline": "A maior construtora do Brasil em área. Dois segmentos, dois clientes, oito estados — e um modelo de permuta que deixa o caixa livre enquanto o landbank cresce.",
                "modelo": (
                    "A Direcional tem um modelo operacional de eficiência industrial. "
                    "Opera em dois segmentos: a marca Direcional (MCMV faixas 2 e 3 — baixa renda) "
                    "e a marca Riva (médio-baixo padrão, apartamentos até R$500 mil — "
                    "que passou a ser enquadrada no MCMV faixa 4 em 2026). "
                    "Presente em 8 estados e no DF, é a maior construtora em área do Brasil. "
                    "O que diferencia a Direcional dos concorrentes é a combinação de três fatores. "
                    "Primeiro, o método construtivo industrializado com formas de alumínio — "
                    "encurta o ciclo de obra, reduz desperdício e viabiliza escala nacional. "
                    "Segundo, o modelo de permuta: 86% do landbank é adquirido via permuta — "
                    "o terreno entra como pagamento de unidades futuras, sem desembolso de caixa. "
                    "Terceiro, o crédito associativo: no MCMV, o risco de inadimplência transfere "
                    "para o banco financiador na assinatura do contrato — a Direcional recebe "
                    "sem risco de o comprador não pagar. "
                    "No 1T26: receita de R$1,2 bi (+30% a/a), lucro de R$200 mi (+27%), "
                    "margem bruta ajustada de 42,9% — a maior do setor."
                ),
                "receita": [
                    ("Direcional (MCMV faixas 2 e 3)", "~55%", "8 estados e DF; método industrializado; alta escala"),
                    ("Riva (médio-baixo, até R$500 mi)", "~45%", "enquadrada no MCMV faixa 4 em 2026; VGV +20% no 1T26"),
                ],
                "vantagens": [
                    "Landbank de R$51,3 bi com 8+ anos de visibilidade — o maior do setor",
                    "86% do landbank via permuta: o maior banco de terrenos sem desembolso de caixa",
                    "Formas de alumínio: método industrializado que reduz prazo de entrega e custo",
                    "Riva na faixa 4 do MCMV: a subsidiária de médio padrão passou a ter acesso ao crédito subsidiado",
                    "Maior construtora em área do Brasil — escala que gera poder de negociação com fornecedores",
                ],
                "riscos": [
                    "Concentração no MCMV: dependência do FGTS e do orçamento público habitacional",
                    "Riva sensível à Selic: crédito SBPE mais caro afeta clientes de médio padrão fora do MCMV",
                    "INCC pressionando: custo de construção acima da inflação desde 2025",
                    "Dois segmentos, dois riscos: gestão de marcas com públicos diferentes exige execução cuidadosa",
                    "Alavancagem subindo: geração de caixa sólida mas pagamento de R$804 mi em dividendos em 2025 elevou endividamento",
                ],
                "barreira": (
                    "40 anos de MCMV e o maior landbank do setor formam a barreira. "
                    "Nenhum novo entrante consegue replicar R$51 bi de terrenos já aprovados e identificados "
                    "em 8 estados sem anos de trabalho. "
                    "As formas de alumínio (método construtivo industrializado) vieram de décadas "
                    "de aprendizado operacional — não se compra só o equipamento, "
                    "compra-se o know-how de como usá-lo com escala. "
                    "E o relacionamento de 40 anos com prefeituras do interior do Brasil "
                    "para aprovação de empreendimentos é impossível de acelerar."
                ),
            },
            "CYRE3": {
                "nome": "Cyrela Brazil Realty",
                "fundacao": "1962 (por Elie Horn em São Paulo)",
                "sede": "São Paulo, SP",
                "tagline": "A maior incorporadora de alto padrão de São Paulo. Três marcas, três segmentos, uma cidade que concentra 60% do mercado de luxo do Brasil.",
                "modelo": (
                    "A Cyrela é a empresa mais complexa do setor listado. "
                    "Opera com três marcas próprias (Cyrela para alto padrão, Living para médio, "
                    "Vivaz para MCMV) e tem participação em cinco JVs listadas na B3 "
                    "(Lavvi, Plano&Plano, Cury, entre outras). "
                    "O core é o alto padrão em São Paulo — onde projetos de R$2+ bi de VGV "
                    "como o Epic by Pininfarina (210 metros, maior residencial de SP) "
                    "definem a marca. A estratégia funciona em ciclos de juros baixos: "
                    "o comprador de luxo financia parte do imóvel, e com crédito barato "
                    "aumenta o poder de compra. Em juros altos, o efeito inverte. "
                    "Em 2026, os lançamentos de alto padrão caíram 71% — o mercado esperou. "
                    "A Vivaz (MCMV) compensa parcialmente, mas com margem e ROE muito menores. "
                    "As JVs listadas (especialmente Cury) criam valor que não aparece no P/L da Cyrela."
                ),
                "receita": [
                    ("Alto padrão — marca Cyrela", "~51%", "São Paulo; projetos icônicos de R$500 mil a R$5 mi por unidade"),
                    ("Médio padrão — marca Living", "~23%", "classe média SP e outras praças; mais sensível à Selic"),
                    ("MCMV — marca Vivaz", "~26%", "parceria com Caixa; crescendo para compensar o alto padrão"),
                ],
                "vantagens": [
                    "Marca premium de 60 anos: 'Cyrela' é sinônimo de qualidade na cabeça do comprador de alto padrão em SP",
                    "Projetos icônicos: Epic by Pininfarina (VGV R$2 bi) — não é construção, é obra de arte vendável",
                    "JVs listadas (Cury, Lavvi): participação em empresas de alto crescimento que criam valor não precificado",
                    "Diversificação de segmento: quando o alto padrão desacelera, Vivaz sustenta a operação",
                    "Geração de caixa sólida: mesmo com ROE baixo, converte bem lucro em caixa",
                ],
                "riscos": [
                    "ROE de 11% no 1T26 — muito abaixo dos pares MCMV (Cury 79%, Direcional 44%)",
                    "Alto padrão sensível à Selic: lançamentos caíram 71% no 1T26 com juros altos",
                    "Concorrência crescente no luxo: JHSF, Lavvi e incorporadoras internacionais disputam o mesmo público",
                    "Vivaz com margem menor: o crescimento que compensa o alto padrão vem com ROE inferior",
                    "Mercado concentrado em SP: 60%+ do resultado vem de uma única praça",
                ],
                "barreira": (
                    "A marca Cyrela é a barreira — e é uma barreira cultural, não financeira. "
                    "Um comprador que paga R$3 mi por um apartamento compra o endereço, "
                    "o nome do arquiteto e o status da construtora. "
                    "60 anos construindo em São Paulo com qualidade consistente "
                    "criam um ativo intangível que nenhum novo entrante replica em menos de duas décadas. "
                    "E a carteira de JVs com incorporadoras de crescimento "
                    "(Cury, Lavvi) cria um portfólio diversificado que o mercado ainda não precifica corretamente."
                ),
            },
            "MDNE3": {
                "nome": "MDNE (Moura Dubeux Engenharia)",
                "fundacao": "1983 (em Recife, PE — por Jorge Moura e Dubeux)",
                "sede": "Recife, PE",
                "tagline": "O maior grupo imobiliário do Nordeste. 42 anos, 260 empreendimentos, três marcas e um modelo de condomínio que não existe em São Paulo.",
                "modelo": (
                    "A Moura Dubeux tem um modelo diferente de todas as outras incorporadoras listadas. "
                    "Além da incorporação tradicional, opera o chamado 'modelo de condomínio': "
                    "os clientes compram cotas do terreno coletivamente, formam um condomínio, "
                    "e a MD constrói por conta do condomínio cobrando taxa de administração mensal. "
                    "Isso gera receita recorrente durante a obra e reduz o risco de crédito "
                    "(o cliente paga mensalmente conforme a obra avança). "
                    "Em 2026, reorganizou-se como holding MDNE com três marcas: "
                    "Moura Dubeux (alto padrão e luxo + segunda residência), "
                    "Mood (médio padrão, lançada em 2023) e "
                    "Ún1ca (MCMV no Nordeste, em parceria com a Direcional — "
                    "joint venture chamada Ún1ca para o segmento econômico nordestino). "
                    "Opera em 7 estados nordestinos, com liderança de mercado absoluta na região — "
                    "260 empreendimentos entregues em 42 anos e VGV lançado de R$5,5 bi projetados para 2026."
                ),
                "receita": [
                    ("Alto padrão e luxo — marca Moura Dubeux", "~55%", "Recife, Fortaleza, Natal, João Pessoa; segunda residência na costa nordestina"),
                    ("Médio padrão — marca Mood", "~30%", "lançada em 2023; crescendo rápido; primeira residência classe média"),
                    ("MCMV — marca Ún1ca (JV com Direcional)", "~15%", "iniciada em 2025; em crescimento acelerado; acesso ao FGTS"),
                ],
                "vantagens": [
                    "Monopólio regional: 42 anos de liderança no Nordeste — nenhum concorrente nacional tem a mesma escala regional",
                    "Modelo de condomínio: receita recorrente durante a obra + risco de crédito menor",
                    "DY de 17%: alta distribuição de lucros; P/L de 5,79x — um dos mais baratos do setor",
                    "Nordeste com demanda reprimida: menos saturado que SP; cliente de alto padrão regional tem menos opções",
                    "Ún1ca (MCMV): diversificação que protege em ciclo de juro alto; JV com Direcional traz expertise",
                ],
                "riscos": [
                    "Concentração no Nordeste: PIB regional mais fraco — recessão nacional impacta mais",
                    "Três marcas recentes: Mood (2023) e Ún1ca (2025) ainda em maturação — execução simultânea é risco",
                    "Alto padrão sensível à Selic: o core do negócio sofre quando crédito encarece",
                    "Small cap: liquidez menor (R$8 mi/dia) — spread bid/ask maior, menos cobertura de analistas",
                    "Dependência familiar: empresa fundada pela família Dubeux — risco de governança em eventual transição",
                ],
                "barreira": (
                    "42 anos de presença dominante no Nordeste. "
                    "O comprador de alto padrão em Recife não compra da Cyrela — compra da Moura Dubeux. "
                    "Essa confiança de marca regional, construída empreendimento a empreendimento "
                    "em uma região onde poucos nacionais apostaram, é inreplicável no curto prazo. "
                    "O modelo de condomínio é outro diferencial que os concorrentes não dominam — "
                    "o cliente nordestino está habituado a esse modelo e o prefere. "
                    "E o banco de terrenos de décadas na costa nordestina, "
                    "em regiões que valorizaram com o turismo interno pós-pandemia, "
                    "é uma posição que nenhum novo entrante vai encontrar disponível."
                ),
            },
        },
    },
    "💧 Saneamento": {
        "tickers": ["SBSP3", "CSMG3", "SAPR4"],
        "tagline": "O setor mais defensivo da bolsa — e o mais transformado em 2024-2026. Sabesp e Copasa privatizadas, Sanepar ainda estatal. O mesmo negócio regulado, três momentos completamente diferentes.",
        "logica": {
            "titulo": "O que move o setor de saneamento",
            "texto": (
                "Saneamento é, conceitualmente, o negócio mais simples da bolsa: "
                "monopólio regional, tarifa regulada, demanda inelástica. "
                "Ninguém deixa de usar água quando a tarifa sobe. Ninguém tem escolha de fornecedor. "
                "Mas o detalhe que o investidor precisa dominar é o modelo regulatório — "
                "porque é ele que determina quanto a empresa pode cobrar, quanto investe e quando é remunerada. "
                "Em 2024-2026, o setor passou pela maior transformação em décadas: "
                "Sabesp privatizada em julho de 2024, Copasa privatizada em junho de 2026, "
                "ambas com a Equatorial como investidora de referência. "
                "O playbook é o mesmo: turnaround operacional + aceleração de capex + universalização. "
                "Quem entende esse modelo entende as três."
            ),
            "drivers": [
                ("BRR — Base de Remuneração Regulatória: o ativo que gera tudo", (
                    "A BRR é o valor dos ativos reconhecidos pelo regulador. "
                    "Sobre ela incide o WACC regulatório (custo de capital definido pela agência), "
                    "gerando a 'receita regulatória' que sustenta a tarifa. "
                    "Quanto maior a BRR (mais investimento reconhecido), maior a receita autorizada. "
                    "Por isso o capex de universalização é o motor de crescimento do setor — "
                    "cada real investido e reconhecido vira receita recorrente por décadas."
                )),
                ("Revisão tarifária periódica — o evento que define tudo", (
                    "A cada 4-5 anos, o regulador revisita o WACC, o OPEX eficiente e a BRR. "
                    "Uma revisão favorável aumenta a receita autorizada; desfavorável comprime. "
                    "É o maior risco e a maior oportunidade do setor. "
                    "Sabesp: revisão anual até 2030 (processo de universalização acelerado). "
                    "Sanepar: revisão 2025-2028 entregou apenas 3,77% — mercado frustrado."
                )),
                ("Marco Legal do Saneamento (2020) e a universalização", (
                    "A Lei 14.026/2020 estabeleceu metas de universalização: "
                    "99% de acesso a água e 90% a esgoto até 2033. "
                    "Isso criou o ambiente para privatizações — "
                    "empresas privadas têm mais capital e incentivo para investir. "
                    "Brasil ainda teria déficit de ~100 mi de pessoas sem acesso pleno a esgoto — "
                    "é o mercado endereçável que justifica o capex de R$70 bi da Sabesp."
                )),
                ("Turnaround operacional — o motor pós-privatização", (
                    "Empresas estatais de saneamento têm ineficiência estrutural: "
                    "excesso de pessoal, opex descontrolado, investimento politicamente motivado. "
                    "A Equatorial provou no setor elétrico que consegue cortar 40-50% do opex em 2-3 anos. "
                    "Sabesp: opex caiu de R$11,8 bi para R$8,8 bi em 2025 — R$3 bi cortados em 1 ano. "
                    "Copasa: expectativa de R$6,1 bi de EBITDA em 2028 vs R$3,5 bi em 2026."
                )),
                ("Capex e universalização — o paradoxo do crescimento", (
                    "Para crescer a BRR (e a receita futura), a empresa precisa investir. "
                    "Para investir, precisa se endividar. Para se endividar, precisa de tarifa adequada. "
                    "É um ciclo virtuoso — quando o regulador reconhece o investimento. "
                    "E vicioso — quando o regulador atrasa o reconhecimento ou "
                    "destina os ganhos para os consumidores em vez do acionista (caso dos precatórios da Sanepar)."
                )),
            ],
        },
        "comparativo": {
            "dimensoes": [
                "Status atual",
                "Controlador",
                "Área de concessão",
                "Tamanho (BRR estimada)",
                "Meta de capex",
                "WACC regulatório (ref.)",
                "Fase operacional",
                "Dividendo (DY)",
                "Risco principal",
            ],
            "grupos": [
                {"label": "Privatizadas — playbook Equatorial em andamento", "tickers": ["SBSP3", "CSMG3"]},
                {"label": "Estatal — aguarda ciclo regulatório", "tickers": ["SAPR4"]},
            ],
            "empresas": {
                "SBSP3": {
                    "nome": "Sabesp",
                    "cor": "#3B82F6",
                    "Status atual": ("Privatizada — jul/2024", "maior oferta de saneamento da história: R$14,8 bi"),
                    "Controlador": ("Equatorial (15%) + mercado", "Estado de SP retém 18%; Equatorial tem lock-up de 5 anos"),
                    "Área de concessão": ("375 municípios — SP", "22% da população brasileira; 31% do PIB nacional — a melhor área do país"),
                    "Tamanho (BRR estimada)": ("R$88 bi (2024) → R$158 bi (2030)", "maior BRR do setor; cresce R$20 bi só em 2026"),
                    "Meta de capex": ("R$70 bi até 2029", "quase 3x o capex histórico anual — universalização acelerada"),
                    "WACC regulatório (ref.)": ("~7,86% real", "menor do setor — SP tem risco menor; mas volume de investimento compensa"),
                    "Fase operacional": ("Turnaround avançado", "opex cortou R$3 bi em 1 ano; metas à frente do cronograma"),
                    "Dividendo (DY)": ("DY crescente (50% em 2026-27 → 100% em 2030)", "payout sobe conforme universalização avança"),
                    "Risco principal": ("Execução do capex de R$70 bi + revisão tarifária política (gov. Tarcísio em 2026)", ""),
                },
                "CSMG3": {
                    "nome": "Copasa",
                    "cor": "#22C55E",
                    "Status atual": ("Privatizada — jun/2026", "operação de R$8-10 bi; modelo similar à Sabesp"),
                    "Controlador": ("Equatorial (até 30%) + mercado", "Estado de MG retém ~5% + golden share; privatização concluída em junho"),
                    "Área de concessão": ("Minas Gerais", "maior estado do Brasil em extensão; 3ª economia; grande déficit de esgoto"),
                    "Tamanho (BRR estimada)": ("R$15,5 bi (2025) → crescendo", "BRR menor que Sabesp, mas WACC regulatório maior — compensação estrutural"),
                    "Meta de capex": ("R$21 bi até 2030", "EBITDA projetado R$6,1 bi em 2028 vs R$3,5 bi em 2026"),
                    "WACC regulatório (ref.)": ("~9,42% real (vs 7,86% da Sabesp)", "maior WACC = maior rentabilidade regulatória; diferencial estrutural da Copasa"),
                    "Fase operacional": ("Turnaround iniciando", "privatização concluída em junho — Equatorial assumindo gestão; ganhos de eficiência a capturar"),
                    "Dividendo (DY)": ("DY baixo no início (~3%)", "ação subiu 126% em 12 meses — expectativa já foi antecipada"),
                    "Risco principal": ("Execução do turnaround + regulação mineira + concessionamento BH em definição", ""),
                },
                "SAPR4": {
                    "nome": "Sanepar",
                    "cor": "#F59E0B",
                    "Status atual": ("Estatal do Paraná", "controle do governo do PR; sem processo de privatização no horizonte"),
                    "Controlador": ("Governo do Paraná", "maioria acionária estatal; sem perspectiva de privatização no curto prazo"),
                    "Área de concessão": ("346 municípios — PR", "Paraná tem alta cobertura histórica de água; déficit maior em esgoto"),
                    "Tamanho (BRR estimada)": ("Menor que pares", "empresa mais madura e eficiente; menor potencial de crescimento da BRR"),
                    "Meta de capex": ("Ciclo conservador", "empresa quase universalizada em água; foco em esgoto e modernização"),
                    "WACC regulatório (ref.)": ("Definido pela AGEPAR", "revisão tarifária 2025-2028: +3,77% — abaixo das expectativas do mercado"),
                    "Fase operacional": ("Operação madura", "alta cobertura histórica; menor potencial de crescimento que os pares em turnaround"),
                    "Dividendo (DY)": ("DY ~5% (histórico)", "precatórios R$4 bi destinados aos usuários — frustrou expectativa de dividendo extraordinário"),
                    "Risco principal": ("Revisão tarifária conservadora + precatórios para consumidores + estatal sem catalisador de privatização", ""),
                },
            },
        },
        "perfis": {
            "SBSP3": {
                "nome": "Sabesp (Companhia de Saneamento Básico do Estado de SP)",
                "fundacao": "1973",
                "sede": "São Paulo, SP",
                "tagline": "A maior empresa de saneamento da América Latina. Privatizada em 2024 pela maior oferta de saneamento da história — e o turnaround mais ambicioso do setor começa agora.",
                "modelo": (
                    "A Sabesp é um monopólio de saneamento no estado de São Paulo — "
                    "atende 375 municípios, incluindo a capital e a Grande São Paulo, "
                    "que sozinhas concentram 22% da população brasileira e 31% do PIB nacional. "
                    "Em julho de 2024, o governo de SP vendeu 32% das ações por R$14,8 bi — "
                    "a maior oferta de saneamento da história do Brasil (demanda de R$187 bi). "
                    "A Equatorial pagou R$6,9 bi por 15% e assumiu como investidora de referência. "
                    "O modelo pós-privatização tem três vetores: (1) turnaround operacional "
                    "(opex cortou R$3 bi em 2025 — de R$11,8 para R$8,8 bi); "
                    "(2) aceleração de capex (R$20 bi em 2026, quase 3x o histórico anual); "
                    "(3) universalização e crescimento da BRR. "
                    "Cada real investido e reconhecido pela ARSESP vira receita regulatória futura — "
                    "o motor de valorização de longo prazo. "
                    "O CEO Carlos Piani (ex-Equatorial Maranhão) declarou: 'Estamos à frente das metas, "
                    "o que nos permite sonhar' — sinalizando possível expansão para outras concessões."
                ),
                "receita": [
                    ("Água — tarifa regulada", "~65%", "distribuição de água tratada para 375 municípios paulistas"),
                    ("Esgoto — tarifa regulada", "~33%", "coleta e tratamento; meta de 90% de cobertura até 2033"),
                    ("Outros serviços", "~2%", "resíduos, construção para terceiros, serviços técnicos"),
                ],
                "vantagens": [
                    "Melhor área de concessão do Brasil: SP concentra 22% da população e 31% do PIB — demanda e renda acima da média",
                    "Turnaround comprovado: R$3 bi de opex cortados em 1 ano — a Equatorial provou que consegue fazer em saneamento o que fez em energia",
                    "BRR crescendo de R$88 bi para R$158 bi até 2030 — cada real de capex vira receita regulatória futura",
                    "Política de dividendos crescente: 50% do lucro em 2026-27, chegando a 100% a partir de 2030",
                    "Revisão tarifária anual até 2030 — ciclo curto reduz o risco de investimento não reconhecido",
                ],
                "riscos": [
                    "Execução do capex de R$70 bi: quase 3x o histórico — escassez de empreiteiros, licenças e pessoal capacitado",
                    "Revisão tarifária politicamente sensível: Tarcísio de Freitas com agenda eleitoral em 2026 pode pressionar tarifas",
                    "Residências irregulares incluídas na universalização: custo e operacionalização incertos",
                    "Valuation já captura parte da transformação: ação subiu muito desde a privatização — margem de segurança menor",
                    "Lock-up da Equatorial até 2029: limitação de liquidez do controlador no curto prazo",
                ],
                "barreira": (
                    "O monopólio regulado é a barreira definitiva. "
                    "Nenhuma empresa entra em São Paulo para concorrer com a Sabesp — "
                    "a concessão vai até 2060 em contrato único com 375 municípios. "
                    "Quem quer saneamento na região metropolitana de SP, paga para a Sabesp. "
                    "E com a aceleração do capex e o reconhecimento tarifário anual, "
                    "cada ano que passa aumenta os ativos da base regulatória — "
                    "criando uma barreira de ativos que vai crescendo com o tempo."
                ),
            },
            "CSMG3": {
                "nome": "Copasa (Companhia de Saneamento de Minas Gerais)",
                "fundacao": "1963 (como COMAG; Copasa desde 1974)",
                "sede": "Belo Horizonte, MG",
                "tagline": "A segunda maior privatização de saneamento do Brasil — concluída em junho de 2026. Mesma Equatorial, mesmo playbook, maior WACC regulatório. O turnaround começa agora.",
                "modelo": (
                    "A Copasa atende Minas Gerais — o maior estado do Brasil em extensão territorial, "
                    "com importantes economias agropecuária, industrial e mineral. "
                    "Em junho de 2026, o governo de MG concluiu a privatização: "
                    "a Equatorial assumiu ~30% como investidora de referência, "
                    "em operação estimada em R$8-10 bi. "
                    "O diferencial estrutural da Copasa vs Sabesp: o WACC regulatório. "
                    "A ARSAE (agência mineira) fixou WACC real de ~9,42% vs ~7,86% da ARSESP. "
                    "Isso significa que MG remunera cada real de ativo regulatório a uma taxa 20% maior "
                    "que São Paulo — mesmo com BRR menor, a rentabilidade por real investido é superior. "
                    "O playbook é idêntico ao da Sabesp: turnaround operacional "
                    "(EBITDA projetado de R$3,5 bi em 2026 para R$6,1 bi em 2028, CAGR de 30%+), "
                    "aceleração de capex (R$3,1 bi em 2026 a R$4,5 bi em 2030) "
                    "e crescimento da BRR de R$15,5 bi para R$36+ bi até 2030."
                ),
                "receita": [
                    ("Água — tarifa regulada (ARSAE/MG)", "~60%", "abastecimento em MG; 3ª revisão tarifária com reajuste de 6,56% em 2026"),
                    ("Esgoto — tarifa regulada", "~38%", "cobertura de esgoto ainda abaixo da média nacional — maior espaço de crescimento"),
                    ("Resíduos e outros", "~2%", "coleta e tratamento de resíduos industriais; serviços complementares"),
                ],
                "vantagens": [
                    "WACC regulatório de 9,42% real: 20% maior que Sabesp — maior retorno por real de ativo reconhecido",
                    "Maior crescimento relativo da BRR: de R$15,5 bi para R$36 bi até 2030 (vs crescimento proporcionalmente menor da Sabesp)",
                    "Mesmo controlador da Sabesp: Equatorial com playbook comprovado — menos incerteza de execução",
                    "Valuation ainda atrativo: ação subiu 126% em 12 meses mas ainda negocia abaixo de pares privatizados equivalentes",
                    "MG tem grande déficit de esgoto: enorme runway de universalização = décadas de crescimento da BRR",
                ],
                "riscos": [
                    "Turnaround ainda no início: privatização concluída em junho — ganhos de eficiência ainda a capturar",
                    "Concessionamento de BH: renovação do contrato com Belo Horizonte foi condição da privatização — qualquer ajuste impacta a base",
                    "Regulação mineira: ARSAE pode ser mais conservadora que ARSESP no reconhecimento de investimentos",
                    "Risco político residual: Estado de MG retém 5% + golden share — ainda pode interferir em decisões estratégicas",
                    "Valuation precificou boa parte: ação já subiu muito com expectativa de privatização; execução precisa corresponder",
                ],
                "barreira": (
                    "Monopólio regulado em Minas Gerais — mesmo modelo da Sabesp. "
                    "Mas a Copasa tem uma vantagem adicional: o WACC mais alto da ARSAE "
                    "cria uma 'vantagem regulatória' estrutural que não depende de gestão, "
                    "mas de metodologia da agência. "
                    "E com a Equatorial como controladora — que já provou em 7 distribuidoras de energia "
                    "que consegue transformar ativos ineficientes em geradores de valor — "
                    "a tese de turnaround tem o executor mais credenciado do setor."
                ),
            },
            "SAPR4": {
                "nome": "Sanepar (Companhia de Saneamento do Paraná)",
                "fundacao": "1963",
                "sede": "Curitiba, PR",
                "tagline": "O saneamento do Paraná — eficiente, estatal e sem catalisador. Operação madura, tarifa conservadora, precatórios que foram para o consumidor em vez do acionista.",
                "modelo": (
                    "A Sanepar é a empresa de saneamento do Paraná — controlada pelo governo estadual. "
                    "Opera 346 concessões municipais, com cobertura de água já alta historicamente "
                    "(Paraná tem índices acima da média nacional). O foco atual é expansão de esgoto "
                    "e modernização das redes. "
                    "Diferente das pares privatizadas, a Sanepar não passou por turnaround — "
                    "já era uma empresa relativamente eficiente. "
                    "O grande evento de 2026 foi a decisão da AGEPAR sobre os R$4 bi de precatórios "
                    "(dinheiro recebido via vitória judicial): a agência regulatória determinou "
                    "que o valor será repassado aos consumidores via redução de tarifa, "
                    "e não distribuído como dividendo extraordinário. "
                    "O mercado frustrado explica a queda de ~8% das ações em 2026. "
                    "Também em 2026, a revisão tarifária entregou apenas 2,49% (IRT) — "
                    "bem abaixo da inflação — comprimindo margens e frustrou as expectativas."
                ),
                "receita": [
                    ("Água — tarifa regulada (AGEPAR/PR)", "~55%", "cobertura histórica alta no PR; crescimento via novos usuários e reajuste tarifário"),
                    ("Esgoto — tarifa regulada", "~43%", "déficit de esgoto no Paraná ainda a ser endereçado — maior runway de crescimento"),
                    ("Outros serviços", "~2%", "resíduos industriais; serviços técnicos para municípios"),
                ],
                "vantagens": [
                    "Operação madura e eficiente: sem o 'mato alto' das estatais que vão para privatização — base operacional sólida",
                    "Cobertura alta de água: menor risco operacional e de qualidade; Paraná tem melhores indicadores do setor",
                    "Dívida controlada: dívida líquida/EBITDA de 0,71x — folga para investimento sem comprometer a estrutura financeira",
                    "P/VP abaixo de 1x: negocia abaixo do valor patrimonial — piso de proteção para o investidor",
                    "Estado do Paraná: melhor qualidade de crédito entre os estados brasileiros — menor risco de interferência política irresponsável",
                ],
                "riscos": [
                    "Precatórios para consumidores: R$4 bi que o mercado esperava como dividendo foram para os usuários — frustrou a tese de dividendo extraordinário",
                    "Revisão tarifária conservadora: IRT 2026 de 2,49% (abaixo da inflação) comprime receita real",
                    "Sem catalisador de privatização: governo do PR não sinaliza privatização; sem repricing de múltiplo no horizonte",
                    "Crescimento limitado: empresa mais madura = menor crescimento de BRR = menor expansão de receita vs pares",
                    "Lucro pressionado: 1T26 com queda de 70,8% (efeito base de comparação alta + itens não recorrentes de 2025)",
                ],
                "barreira": (
                    "346 concessões municipais no Paraná — o mesmo monopólio regulado dos pares. "
                    "A Sanepar tem uma vantagem específica: décadas de relacionamento com os municípios paranaenses "
                    "e um histórico de qualidade de serviço que reduz o risco de revogação de concessões. "
                    "O Paraná tem o melhor perfil de pagadores do Brasil — "
                    "inadimplência menor, consumo per capita maior, renda acima da média. "
                    "A barreira aqui é mais operacional do que de turnaround: "
                    "quem tentasse entrar não teria como competir por concessões já consolidadas."
                ),
            },
        },
    },
    "⛏️ Mineração": {
        "tickers": ["VALE3", "CMIN3"],
        "tickers_sub": ["BRAP4"],
        "label_sub": "Holding com participação na Vale",
        "tagline": "O mesmo minério de ferro, três posições completamente diferentes na cadeia: a maior produtora do mundo, a segunda maior do Brasil com foco puro em ferro, e uma holding que dá exposição à Vale com desconto de NAV.",
        "logica": {
            "titulo": "O que move a mineração — e por que a China manda em tudo",
            "texto": (
                "Mineração de ferro é, antes de mais nada, uma tese sobre a China. "
                "O país consome ~70% do minério de ferro comercializado globalmente — "
                "para fazer aço, que vira construção civil, carros, navios e máquinas. "
                "Quando a China estimula sua economia (infraestrutura, habitação), "
                "a demanda por aço sobe, o preço do minério sobe, as mineradoras lucram mais. "
                "Quando a China desacelera (como fez em 2023-2024 com a crise imobiliária), "
                "o minério cai e leva o resultado das mineradoras junto. "
                "O Brasil é o maior exportador mundial de minério de ferro — "
                "a Vale responde por ~20% das exportações globais."
            ),
            "drivers": [
                ("Preço do minério de ferro (62% Fe, CFR Qingdao)", (
                    "É o driver que manda em tudo. Cotado em dólar por tonelada. "
                    "Em 2021, chegou a US$230/t. Em 2024, caiu para US$90/t com a crise imobiliária chinesa. "
                    "Em 2026, oscila entre US$95-110/t. "
                    "Cada US$10 de variação no preço muda o EBITDA da Vale em ~US$3-4 bi/ano. "
                    "É o risco e o upside mais importante do setor."
                )),
                ("China e o setor imobiliário — o maior comprador do mundo", (
                    "A construção civil chinesa consome ~35% de todo o aço produzido. "
                    "Com a crise das incorporadoras (Evergrande, Country Garden), "
                    "a demanda por aço caiu e arrastou o minério. "
                    "Estímulos do governo chinês (infraestrutura, veículos elétricos, "
                    "energia renovável) são o principal gatilho de alta para o setor. "
                    "Sem entender a China, não se entende mineração."
                )),
                ("Custo C1 — o que separa os eficientes dos vulneráveis", (
                    "C1 é o custo operacional de extrair e entregar o minério no porto. "
                    "Vale: ~US$23-25/t (referência mundial de eficiência). "
                    "CMIN: ~US$23/t (1T26) — competitiva. "
                    "Produtores australianos (Rio Tinto, BHP): US$18-20/t. "
                    "Produtores marginais (alguns africanos, chineses): US$80+/t. "
                    "Quando o minério cai para US$80, os marginais param e a oferta cai — "
                    "sustenta o preço para os produtores de baixo custo."
                )),
                ("Câmbio (R$/USD)", (
                    "Receita em dólar, custo em real. "
                    "Real desvalorizado = margem maior para Vale e CMIN. "
                    "Real apreciado = margem comprimida mesmo com preço do minério estável. "
                    "Em 2025-2026, dólar a R$5,80-6,10 ajudou as margens em reais."
                )),
                ("Qualidade do minério (teor de Fe%)", (
                    "Minério de maior teor de Fe (65%+) vale mais que o benchmark 62%. "
                    "Vale tem o minério de maior qualidade do mundo (Sistema Norte, Carajás: 67% Fe). "
                    "CMIN produz no Quadrilátero Ferrífero (MG): ~62-63% — padrão benchmark. "
                    "A Vale consegue prêmio de preço de US$5-15/t sobre a CMIN por conta da qualidade."
                )),
                ("Metais básicos — o segundo motor da Vale", (
                    "A Vale está diversificando além do ferro: cobre, níquel e outros metais. "
                    "Cobre é o metal da transição energética (veículos elétricos, energia solar, cabos). "
                    "CMIN não tem metais básicos — é ferro puro. "
                    "Quem compra Vale compra uma opção no cobre; quem compra CMIN, não."
                )),
            ],
        },
        "comparativo": {
            "dimensoes": [
                "O que é de verdade",
                "Produto principal",
                "Custo C1 (referência)",
                "Qualidade do minério",
                "Diversificação de produto",
                "Exposição ao câmbio",
                "Governança",
                "Dividendo (DY)",
                "Risco principal",
            ],
            "grupos": [
                {"label": "Mineradoras puras", "tickers": ["VALE3", "CMIN3"]},
                {"label": "Holding com participação na Vale", "tickers": ["BRAP4"]},
            ],
            "empresas": {
                "VALE3": {
                    "nome": "Vale",
                    "cor": "#22C55E",
                    "O que é de verdade": ("Maior mineradora do mundo em ferro", "2ª maior em níquel; presença em 30+ países"),
                    "Produto principal": ("Minério de ferro Carajás (~70% EBITDA)", "o melhor minério do mundo: 67% Fe, sistema Norte no Pará"),
                    "Custo C1 (referência)": ("~US$23-25/t (ferro)", "referência mundial — um dos mais baixos do planeta", "badge-green"),
                    "Qualidade do minério": ("Premium (67% Fe, Carajás)", "prêmio de US$5-15/t sobre benchmark — clientes pagam mais", "badge-green"),
                    "Diversificação de produto": ("Alta", "ferro + níquel + cobre + manganês + carvão — aposta na transição energética", "badge-green"),
                    "Exposição ao câmbio": ("Máxima positiva", "receita em dólar, custo predominante em real", "badge-green"),
                    "Governança": ("Corporação privada", "sem controlador majoritário — gestão profissional; mais vulnerável a ativismo"),
                    "Dividendo (DY)": ("DY variável 6-12%", "política: 30% do EBITDA ajustado; oscila com ciclo"),
                    "Risco principal": ("China + Brumadinho (passivo ambiental em curso) + meta de produção de Carajás", ""),
                },
                "CMIN3": {
                    "nome": "CSN Mineração",
                    "cor": "#F59E0B",
                    "O que é de verdade": ("2ª maior mineradora de ferro do Brasil", "focada em ferro; controlada pela CSN (78%)"),
                    "Produto principal": ("Minério de ferro 62% Fe (QF, MG)", "benchmark de mercado; Quadrilátero Ferrífero em MG"),
                    "Custo C1 (referência)": ("~US$23/t (1T26)", "competitivo; mas sem o prêmio de qualidade da Vale", "badge-yellow"),
                    "Qualidade do minério": ("Padrão benchmark (62% Fe)", "sem prêmio — vende ao preço de referência do mercado", "badge-yellow"),
                    "Diversificação de produto": ("Baixa", "minério de ferro puro; sem metais básicos — exposição máxima ao ciclo do ferro", "badge-red"),
                    "Exposição ao câmbio": ("Máxima positiva", "receita em dólar, custo em real", "badge-green"),
                    "Governança": ("Controlada pela CSN (78%)", "decisões estratégicas podem favorecer a controladora em detrimento dos minoritários", "badge-red"),
                    "Dividendo (DY)": ("DY variável", "R$768 mi distribuídos em abr/2026 (ref. 2025); depende do resultado e da CSN"),
                    "Risco principal": ("Minério de ferro puro — sem diversificação; risco de controladora (CSN) extraindo caixa", ""),
                },
                "BRAP4": {
                    "nome": "Bradespar",
                    "cor": "#8B5CF6",
                    "O que é de verdade": ("Holding com participação na Vale", "~4,5% das ações da Vale; sem operação própria"),
                    "Produto principal": ("Exposição à Vale via participação", "o resultado é o dividendo da Vale multiplicado pela participação"),
                    "Custo C1 (referência)": ("N/A — holding", "não opera mina; resultado vem do dividendo da Vale", "badge-yellow"),
                    "Qualidade do minério": ("N/A — holding", "exposição indireta à qualidade da Vale"),
                    "Diversificação de produto": ("N/A — holding", "exposição 100% à Vale — tudo que move a Vale, move a Bradespar"),
                    "Exposição ao câmbio": ("Via Vale", "indireta — beneficia quando Vale se beneficia"),
                    "Governança": ("Controlada pelo Bradesco", "banco controla a holding; alinhado com distribuição de dividendos"),
                    "Dividendo (DY)": ("DY alto quando Vale paga bem", "desconto de NAV aumenta o yield efetivo vs comprar Vale direto"),
                    "Risco principal": ("Desconto de NAV pode não fechar; holding com custos que corroem o valor ao longo do tempo", ""),
                },
            },
        },
        "perfis": {
            "VALE3": {
                "nome": "Vale S.A.",
                "fundacao": "1942 (como Companhia Vale do Rio Doce, estatal; privatizada em 1997)",
                "sede": "Rio de Janeiro, RJ",
                "tagline": "A maior mineradora de ferro do mundo. Carajás é o maior e melhor depósito de minério de ferro do planeta — e a Vale tem ele há 80 anos.",
                "modelo": (
                    "A Vale é uma das cinco maiores empresas de mineração do mundo e a maior exportadora "
                    "de minério de ferro do planeta. Opera em dois grandes segmentos: "
                    "Metais Ferrosos (~70% do EBITDA) e Metais Básicos (~15%). "
                    "O coração do negócio é o Sistema Norte — a mina de Carajás, no Pará. "
                    "Carajás tem o maior depósito de minério de ferro de alta qualidade do mundo: "
                    "reservas de ~7 bilhões de toneladas com teor médio de 67% Fe "
                    "(benchmark é 62%). A qualidade superior gera prêmio de preço de US$5-15/t. "
                    "A logística é integrada: ferrovia EFC (Estrada de Ferro Carajás, 892 km) "
                    "leva o minério diretamente ao Porto do Itaqui (MA) — "
                    "sem baldeação, sem intermediário, menor custo. "
                    "Em metais básicos, a Vale tem níquel no Canadá (Voisey's Bay) "
                    "e cobre em projetos de desenvolvimento. "
                    "Com a transição energética, cobre e níquel ganham relevância — "
                    "o Sossego e o Salobo (cobre no PA) são apostas de longo prazo."
                ),
                "receita": [
                    ("Minério de ferro e pelotas (Sistema Norte — Carajás)", "~55%", "67% Fe; premium sobre benchmark; EFC + Porto Itaqui"),
                    ("Minério de ferro (Sistema Sudeste — MG)", "~20%", "62-63% Fe; Quadrilátero Ferrífero; sistema mais antigo e caro"),
                    ("Níquel e subprodutos (cobre, cobalto, platina)", "~12%", "Canadá, Brasil, Indonesia; metal da bateria EV"),
                    ("Cobre (Sossego, Salobo — PA)", "~8%", "crescimento acelerado; apoio da transição energética"),
                    ("Outros (manganês, ferroligas, logística)", "~5%", ""),
                ],
                "vantagens": [
                    "Carajás: o melhor minério do mundo em qualidade e reservas — inreplicável em qualquer outra jurisdição",
                    "Custo C1 entre os mais baixos do planeta: ~US$23-25/t vs produtores marginais a US$80+/t",
                    "Logística própria (EFC + Porto Itaqui): controle do custo de ponta a ponta sem dependência de terceiros",
                    "Diversificação em metais da transição: cobre e níquel crescem em relevância com veículos elétricos",
                    "Sem controlador majoritário: gestão profissional com foco em retorno ao acionista",
                ],
                "riscos": [
                    "China: 70% das exportações vão para a China — qualquer desaceleração afeta diretamente",
                    "Brumadinho: passivo ambiental e reputacional em curso desde 2019 — provisões continuam pesando",
                    "Metais básicos: cobre e níquel ainda não são escala suficiente para compensar volatilidade do ferro",
                    "Produção de Carajás com metas ambiciosas: execução de S11D a plena capacidade é desafio logístico",
                    "Câmbio apreciado comprime margens em reais mesmo sem queda do preço do minério",
                ],
                "barreira": (
                    "Carajás é a barreira definitiva. "
                    "O depósito foi descoberto em 1967 por geólogos da Vale e da US Steel — "
                    "e nunca se encontrou outro igual no mundo em qualidade e escala. "
                    "Quem não tem Carajás não tem o mesmo produto. "
                    "Adicione a ferrovia de 892 km e o porto próprio: "
                    "construir essa logística hoje custaria US$15-20 bi e levaria 10-15 anos. "
                    "A Vale tem isso funcionando há décadas."
                ),
            },
            "CMIN3": {
                "nome": "CSN Mineração S.A.",
                "fundacao": "1977 (como área de mineração da CSN; IPO em 2021)",
                "sede": "São Paulo, SP",
                "tagline": "A segunda maior mineradora de ferro do Brasil. Operação concentrada no Quadrilátero Ferrífero — puro jogo de preço do minério, câmbio e custo C1.",
                "modelo": (
                    "A CSN Mineração é a operação de mineração da CSN (Companhia Siderúrgica Nacional), "
                    "separada em empresa independente e aberta em IPO em 2021. "
                    "Opera no Quadrilátero Ferrífero (MG), na mina Casa de Pedra — "
                    "uma das maiores minas a céu aberto do Brasil. "
                    "O modelo é simples e direto: extrai minério de ferro (62% Fe), "
                    "transporta via MRS Logística até o Terminal de Carvão (TECAR) no Porto de Itaguaí (RJ) "
                    "e exporta, principalmente para a China. "
                    "Uma parte significativa do minério abastece a própria CSN "
                    "(que produz aço e precisa de minério) — captivo interno com preço de mercado. "
                    "Produziu recorde de 45,5 milhões de toneladas em 2025 (+4,6% acima do guidance). "
                    "Custo C1 de US$23,1/t no 1T26 — competitivo, mas sem o prêmio de qualidade da Vale."
                ),
                "receita": [
                    ("Exportação de minério de ferro (62% Fe)", "~70%", "China é o principal destino; preço benchmark 62% Fe CFR"),
                    ("Vendas para CSN (mercado interno)", "~20%", "captivo — a controladora usa o minério para produzir aço"),
                    ("Pelotas e outros produtos", "~10%", "valor agregado sobre o minério bruto"),
                ],
                "vantagens": [
                    "Custo C1 competitivo (~US$23/t): eficiência operacional que sustenta margem mesmo com minério deprimido",
                    "Produção recorde em 2025: 45,5 mi t — prova de capacidade operacional crescente",
                    "Logística integrada via MRS até Itaguaí: escoamento eficiente sem gargalo logístico",
                    "Captivo interno (CSN): parte da receita não depende do mercado internacional",
                    "Alavancagem baixa: balanço saudável que permite dividendos mesmo em ciclo fraco",
                ],
                "riscos": [
                    "Ferro puro sem diversificação: 100% do resultado depende do preço do minério 62% Fe",
                    "Sem prêmio de qualidade: vende ao benchmark — não tem o diferencial da Vale em Carajás",
                    "Controladora CSN (78%): conflito de interesse potencial — CSN pode extrair caixa da CMIN em detrimento de minoritários",
                    "Dependência da China: perfil de exportação muito concentrado no mercado asiático",
                    "FCF volátil: capex de crescimento e compras de minério de terceiros criam oscilações no caixa",
                ],
                "barreira": (
                    "Casa de Pedra é uma das maiores reservas de minério de ferro do Quadrilátero Ferrífero. "
                    "Mas a barreira da CMIN é menor que a da Vale — "
                    "o minério 62% Fe é mais padronizado e os produtores australianos "
                    "(Rio Tinto, BHP) têm custo C1 de US$18-20/t, abaixo da CMIN. "
                    "A barreira real é operacional: a logística via MRS + Itaguaí "
                    "e a integração com a CSN criam um sistema que funciona "
                    "há décadas e não é fácil de desmontar."
                ),
            },
            "BRAP4": {
                "nome": "Bradespar S.A.",
                "fundacao": "2000 (spin-off do Bradesco para concentrar participações industriais)",
                "sede": "São Paulo, SP",
                "tagline": "A forma de ter Vale com desconto. Holding que detém ~4,5% da Vale — sem operar uma única mina. O rendimento é o dividendo da Vale amplificado pelo desconto de NAV.",
                "modelo": (
                    "A Bradespar é uma holding de participações controlada pelo banco Bradesco. "
                    "Seu único ativo relevante é uma participação de ~4,5% na Vale. "
                    "Não opera mina, não tem receita operacional, não tem funcionários de mineração. "
                    "O resultado é o dividendo recebido da Vale, menos as despesas da holding. "
                    "A tese de investimento é simples: a Bradespar negocia com desconto de NAV "
                    "(valor de mercado < valor das ações da Vale que ela possui). "
                    "Por que o desconto existe? Custos da holding, liquidez menor que a Vale, "
                    "risco de governança (Bradesco decide o que fazer com a participação) "
                    "e impostos sobre o dividendo ao longo da cadeia. "
                    "Quando o desconto se fecha — por buyback, venda de ações ou elevação do dividendo — "
                    "o acionista da Bradespar captura um retorno extra além da variação da Vale."
                ),
                "receita": [
                    ("Dividendos e JCP da Vale", "~95%", "proporcional à participação de ~4,5% e ao dividendo declarado pela Vale"),
                    ("Resultado financeiro e outros", "~5%", "caixa próprio aplicado em renda fixa"),
                ],
                "vantagens": [
                    "Desconto de NAV: comprar Bradespar = comprar Vale mais barato que o mercado",
                    "DY amplificado pelo desconto: o yield efetivo sobre o NAV é maior que comprar Vale direto",
                    "Exposição indireta ao cobre/níquel via Vale: tese de transição energética embutida",
                    "Simplicidade: não tem risco operacional, ambiental nem de produção — só participação financeira",
                ],
                "riscos": [
                    "Desconto de NAV pode persistir ou ampliar: holding costuma negociar com desconto estrutural",
                    "Custos da holding corroem o NAV: despesas administrativas e impostos reduzem o retorno líquido",
                    "Decisão do Bradesco: controlador pode vender a participação na Vale em momento ruim",
                    "Dupla tributação: dividendo da Vale → Bradespar → acionista tem mais um passo tributário",
                    "Liquidez menor que Vale: spread bid/ask maior; mais difícil de sair em momentos de estresse",
                ],
                "barreira": (
                    "A barreira da Bradespar é o próprio desconto de NAV — "
                    "quem quer comprar Vale com desconto precisa comprar a Bradespar. "
                    "Mas não é uma barreira de negócio: "
                    "qualquer um pode comprar Vale diretamente. "
                    "A tese funciona enquanto o desconto existir e enquanto a Vale pagar dividendos. "
                    "Se o desconto fechar, a vantagem da Bradespar desaparece."
                ),
            },
        },
    },
    "🛢️ Petróleo & Gás": {
        "tickers": ["PETR4", "PRIO3"],
        "tickers_sub": ["BRAV3"],
        "label_sub": "Fora do RADAR — no dossiê",
        "tagline": "A mesma commodity, três estratégias opostas: gigante integrada estatal, independente de crescimento e junior oil em consolidação. O Brent comanda os três.",
        "logica": {
            "titulo": "O que move o petróleo — e o que diferencia cada empresa",
            "texto": (
                "O setor de petróleo tem um driver que domina tudo: o preço do Brent. "
                "Mas a forma como cada empresa é afetada é completamente diferente. "
                "A Petrobras é uma gigante integrada estatal — o governo usa ela para política "
                "de preços de combustíveis. A PRIO é uma independente pura — recebe o Brent "
                "e paga custo de extração; tudo o que sobra é margem. A Brava está em consolidação "
                "pós-fusão — comprando ativos maduros que outros venderam. "
                "O que você precisa entender antes de qualquer número: "
                "custo de extração, nível de dívida, grau de integração e exposição ao risco político."
            ),
            "drivers": [
                ("O Brent — o driver que manda em tudo", (
                    "O petróleo Brent é a referência global. Em torno de US$77/bbl (2026), "
                    "está em nível que deixa a Petrobras confortável (breakeven ~US$30-35) "
                    "mas aperta margens de produtores com custo mais alto. "
                    "Cada US$1 de queda no Brent reduz o EBITDA da Petrobras em ~US$500 mi/ano. "
                    "Para a PRIO, com custo de ~US$9/bbl, há muita gordura. "
                    "Abaixo de US$50, todas sofrem. Acima de US$70, todas lucram bem."
                )),
                ("OPEP+ e geopolítica — quem define a oferta", (
                    "A OPEP+ controla ~40% da oferta global e usa cortes para sustentar o preço. "
                    "Em 2025-2026, o cartel manteve disciplina, mas o crescimento do shale americano "
                    "e a capacidade ociosa pressionam para baixo. "
                    "Tensões no Oriente Médio (Irã, estreito de Ormuz) são risco de alta súbita. "
                    "O Brasil é produtor crescente e não é membro da OPEP — "
                    "pode vender o quanto produzir sem cotas."
                )),
                ("Custo de extração (lifting cost) — o que separa os bons dos ruins", (
                    "É o custo operacional de produzir cada barril. "
                    "Petrobras pré-sal: <US$6/bbl — um dos mais baixos do mundo. "
                    "PRIO pós-Wahoo: ~US$8-9/bbl. Shale americano: US$30-50/bbl. "
                    "Quanto menor o lifting cost, maior a margem em qualquer cenário de Brent "
                    "e maior a sobrevivência em crise. "
                    "O pré-sal brasileiro é vantagem competitiva de escala global."
                )),
                ("Risco político — especialmente na Petrobras", (
                    "A Petrobras é estatal e o governo usa sua política de preços de combustíveis "
                    "como instrumento político. "
                    "Em 2022-2024, pressão para gasolina barata comprimiu margens do refino. "
                    "O governo define o CEO e o conselho — risco permanente de gestão não ótima. "
                    "PRIO e Brava não têm esse risco."
                )),
                ("Curva de declínio e depleção dos campos", (
                    "Todo campo de petróleo declina com o tempo. "
                    "A empresa precisa investir continuamente em novos poços ou aquisições "
                    "para manter ou crescer a produção. "
                    "Petrobras compensa com novos FPSOs no pré-sal (8 até 2030). "
                    "PRIO compra campos maduros que outros abandonaram e revitaliza. "
                    "Brava herdou campos em estágio maduro da fusão 3R+Enauta."
                )),
                ("Dívida e alavancagem — especialmente nas juniors", (
                    "Aquisições de campos são caras. "
                    "A PRIO se alavancou para comprar Peregrino (US$3 bi). "
                    "A Brava herdou dívida da fusão e comprou Tartaruga Verde por US$450 mi. "
                    "Em Brent alto, a dívida é gerenciável. Em Brent baixo, pode ser catastrófica. "
                    "Sempre checar: qual é o Brent de break-even da dívida, não só da extração."
                )),
            ],
        },
        "comparativo": {
            "dimensoes": [
                "Perfil da empresa",
                "Modelo de negócio",
                "Custo de extração (lifting cost)",
                "Exposição ao Brent",
                "Risco político",
                "Dívida/alavancagem",
                "Dividendo",
                "Catalisador principal 2026",
                "Risco principal",
            ],
            "grupos": [
                {"label": "Empresas do setor", "tickers": ["PETR4", "PRIO3", "BRAV3"]},
            ],
            "empresas": {
                "PETR4": {
                    "nome": "Petrobras",
                    "cor": "#22C55E",
                    "Perfil da empresa": ("Gigante integrada estatal", "maior empresa do Brasil; meta 3,4 mi boed em 2028"),
                    "Modelo de negócio": ("E&P + refino + gás + distribuição", "integrada: extrai, refina e vende o produto final"),
                    "Custo de extração (lifting cost)": ("<US$6/barril", "pré-sal entre os mais baratos do mundo", "badge-green"),
                    "Exposição ao Brent": ("Alta — amortecida pelo refino", "refino ganha quando Brent cai; E&P perde — proteção natural", "badge-yellow"),
                    "Risco político": ("Muito alto", "governo define CEO, preços de combustíveis e política de dividendos", "badge-red"),
                    "Dívida/alavancagem": ("Baixa", "empresa superavitária; caixa sólido; dividendo mínimo garantido", "badge-green"),
                    "Dividendo": ("DY 8-12%", "política: 45% do FCF; governo precisa do dividendo para fechar contas"),
                    "Catalisador principal 2026": ("Novos FPSOs pré-sal (P-78, P-79, P-80, P-82, P-83)", "expansão da produção até 3,4 mi boed"),
                    "Risco principal": ("Preço de combustíveis + interferência política no board + Brent abaixo de US$50", ""),
                },
                "PRIO3": {
                    "nome": "PRIO",
                    "cor": "#3B82F6",
                    "Perfil da empresa": ("Maior independente do Brasil", "de 5 kboed em 2015 para +190 kboed em 2026"),
                    "Modelo de negócio": ("E&P puro — sem refino", "compra campos maduros de grandes petroleiras, revitaliza e reduz custo"),
                    "Custo de extração (lifting cost)": ("~US$9/bbl (1T26)", "meta <US$7 com Wahoo pleno; dos mais baixos entre independentes", "badge-green"),
                    "Exposição ao Brent": ("Máxima", "sem refino para amortecer — cada US$1 de Brent vai direto ao EBITDA", "badge-red"),
                    "Risco político": ("Baixo", "empresa privada — sem governo, sem política de preços, sem CEO indicado", "badge-green"),
                    "Dívida/alavancagem": ("Moderada pós-Peregrino", "meta de 1x dívida/EBITDA até 2027 a US$60; recompra ativa", "badge-yellow"),
                    "Dividendo": ("DY crescente a partir de 2026", "política sendo definida; yield prospectivo 10-15% a US$60 Brent"),
                    "Catalisador principal 2026": ("Wahoo a 40 kboed + Peregrino com custo reduzido a US$7/bbl", ""),
                    "Risco principal": ("Brent abaixo de US$50 + alavancagem em descompressão + ramp-up de Wahoo", ""),
                },
                "BRAV3": {
                    "nome": "Brava Energia",
                    "cor": "#F97316",
                    "Perfil da empresa": ("2ª maior independente do Brasil", "fusão 3R Petroleum + Enauta (set/2024); em consolidação"),
                    "Modelo de negócio": ("E&P com mix onshore/offshore", "Atlanta (óleo leve) + Papa-Terra + gás + campos 3R"),
                    "Custo de extração (lifting cost)": ("Variável (~US$15-25)", "mix de campos; Atlanta mais eficiente; Papa-Terra mais caro", "badge-yellow"),
                    "Exposição ao Brent": ("Máxima", "sem refino; desconto adicional em Papa-Terra (óleo pesado)", "badge-red"),
                    "Risco político": ("Baixo/Moderado", "empresa privada; OPA Ecopetrol pode trazer controle por estatal colombiana", "badge-yellow"),
                    "Dívida/alavancagem": ("Alta — em redução", "dívida da fusão + US$450 mi de Tartaruga Verde; FCF neutro em 2026", "badge-red"),
                    "Dividendo": ("Sem dividendo relevante 2026", "foco em desalavancagem e integração; OPA a R$23 é o 'dividendo' do mercado"),
                    "Catalisador principal 2026": ("Papa-Terra em escala + OPA Ecopetrol (prêmio 28% vs mercado)", ""),
                    "Risco principal": ("Alavancagem elevada + integração pós-fusão + OPA Ecopetrol pendente de CADE/ANP", ""),
                },
            },
        },
        "perfis": {
            "PETR4": {
                "nome": "Petrobras",
                "fundacao": "1953 (fundada por Getúlio Vargas)",
                "sede": "Rio de Janeiro, RJ",
                "tagline": "A empresa mais lucrativa do Brasil. O pré-sal é o ativo; a política é o risco permanente.",
                "modelo": (
                    "A Petrobras é uma empresa integrada de petróleo e gás — extrai no pré-sal, "
                    "refina nas suas refinarias e vende combustível e derivados para o mercado "
                    "brasileiro e para exportação. Com meta de 3,4 milhões de boed até 2028 e "
                    "custo de extração abaixo de US$6/barril, é uma das operações de mais baixo custo "
                    "do planeta. O pré-sal brasileiro — especialmente Búzios, com reservas gigantescas "
                    "na Bacia de Santos — é o coração do negócio: óleo leve de alta qualidade, "
                    "em águas profundas, com FPSOs que chegam a produzir 200 mil barris/dia cada. "
                    "O plano 2026-2030 prevê US$109 bi de investimento, 62% no pré-sal, "
                    "com 8 novos sistemas de produção até 2030, sendo 7 já contratados. "
                    "A integração com o refino funciona como amortecedor: quando o Brent cai, "
                    "o refino compra petróleo barato e sustenta margens. "
                    "O custo total médio de produção (incluindo royalties e participações governamentais) "
                    "é de US$30,4/boe no quinquênio — muito abaixo do preço de equilíbrio do mercado."
                ),
                "receita": [
                    ("E&P (exploração e produção)", "~60%", "pré-sal é o motor; <US$6/bbl de lifting cost; 8 novos FPSOs até 2030"),
                    ("Refino, Transporte e Comercialização", "~30%", "1,8 mi bpd de capacidade; expansão para 2,1 mi até 2030"),
                    ("Gás natural e energia", "~7%", "TAG, transporte de gás, termelétricas"),
                    ("Outros (fertilizantes, biocombustíveis)", "~3%", "biorrefino em expansão; US$1,2 bi aprovado em 2026"),
                ],
                "vantagens": [
                    "Pré-sal: custo <US$6/bbl — um dos mais baixos do mundo; óleo leve de alta qualidade",
                    "Búzios: maior reservatório offshore fora do Oriente Médio — reservas imensas, produção crescente por décadas",
                    "Integração E&P + refino: proteção natural quando o Brent cai (refino compra barato)",
                    "Dividendo garantido: política de 45% do FCF; governo precisa do dividendo — alinhamento forçado",
                    "Escala operacional: única operadora de FPSOs em águas ultra-profundas no Brasil; know-how inreplicável",
                ],
                "riscos": [
                    "Risco político: CEO indicado pelo governo; preços de combustíveis como instrumento político",
                    "Refino pressionado: governo quer gasolina barata — comprime margens do segmento",
                    "Margem Equatorial: nova fronteira exploratória com licenciamento ambiental incerto (IBAMA)",
                    "Brent estruturalmente mais baixo: plano assume US$63/bbl em 2026; abaixo disso, capex é revisto",
                    "Transição energética: portfólio de longo prazo concentrado em hidrocarbonetos",
                ],
                "barreira": (
                    "O pré-sal é a barreira mais alta do setor de petróleo no mundo. "
                    "Operar FPSOs em águas de 2.000-3.000 metros, perfurar poços de 6.000-7.000 metros "
                    "passando pela camada de sal, é um desafio de engenharia que só meia dúzia de "
                    "empresas no planeta domina — e a Petrobras é operadora de praticamente todos. "
                    "Ninguém entra no pré-sal sem ela, e ela tem mais de 70 anos de know-how local."
                ),
            },
            "PRIO3": {
                "nome": "PRIO (PetroRio)",
                "fundacao": "2010 (como HRT Petroleum; virou PetroRio em 2014; PRIO em 2021)",
                "sede": "Rio de Janeiro, RJ",
                "tagline": "A maior independente do Brasil. Compra o que a Chevron, Equinor e Petrobras descartaram — e extrai mais petróleo com menos custo.",
                "modelo": (
                    "A PRIO tem um modelo único e comprovado: compra campos de petróleo maduros "
                    "que grandes petroleiras decidiram abandonar, assume a operação, corta custos "
                    "e aumenta a recuperação dos reservatórios. "
                    "Fez isso com Frade (da Chevron), Albacora Leste (da Petrobras), "
                    "cluster Polvo+Tubarão Martelo (da Dommo) e, mais recentemente, "
                    "Peregrino (da Equinor) — o maior campo da empresa, 100% adquirido em 2025. "
                    "O resultado: de 5 mil barris/dia e custo de US$35/bbl em 2015 "
                    "para +190 mil barris/dia e custo de US$9/bbl em 2026. "
                    "Wahoo é o próximo capítulo: primeiro campo desenvolvido do zero pela PRIO, "
                    "conectado ao FPSO Valente via tieback de Frade, com custo marginal de "
                    "apenas US$1/bbl (usa infraestrutura existente) e capacidade de 40 kboed. "
                    "Peregrino, que a Equinor operava a US$500 mi/ano de custo, "
                    "já está sendo operado pela PRIO a US$370 mi e deve chegar a US$250 mi "
                    "quando o gasoduto de gás for reativado em 2026 — US$250 mi de ganho anual."
                ),
                "receita": [
                    ("Peregrino", "~40%", "campo pesado da Equinor; PRIO cortou custo de US$500 mi para meta US$250 mi/ano"),
                    ("Frade + Wahoo", "~30%", "Wahoo a 40 kboed com custo marginal de US$1/bbl — maior catalisador de 2026"),
                    ("Albacora Leste", "~15%", "campo da Petrobras revendido; PRIO aumentou produção e eficiência"),
                    ("Polvo + Tubarão Martelo + outros", "~15%", "cluster offshore menor na Bacia de Campos"),
                ],
                "vantagens": [
                    "Modelo de revitalização comprovado: compra barato, corta custo, aumenta produção — 100% de execução",
                    "Lifting cost ~US$9/bbl (meta US$7): margem expressiva mesmo com Brent a US$50",
                    "Zero risco político: privada, independente, sem governo determinando preços ou CEO",
                    "Wahoo: custo marginal de US$1/bbl por usar infraestrutura do Frade — puro upside",
                    "Peregrino: sinergias de US$250 mi/ano vs Equinor — maior captura de valor de campo único",
                ],
                "riscos": [
                    "Brent é tudo: sem refino para amortecer — cada US$1 de queda vai direto no EBITDA",
                    "Alavancagem pós-Peregrino: US$3 bi de aquisição; meta 1x dívida/EBITDA até 2027 a US$60",
                    "Declínio natural: campos maduros declinam — precisa de perfurações contínuas (Albacora Leste+30 kboed)",
                    "Ramp-up de Wahoo: GOR (razão gás-óleo) alto; cada poço precisa de 10 dias de estabilização",
                    "Concentração na Bacia de Campos: todos os ativos offshore no RJ — risco operacional concentrado",
                ],
                "barreira": (
                    "O know-how de revitalização de campos maduros é a barreira. "
                    "A PRIO desenvolveu metodologias próprias para extrair mais petróleo "
                    "de reservatórios dados como esgotados. "
                    "Isso se combina com uma cultura de custo obsessiva — "
                    "cortou o OpEx de Peregrino pela metade em menos de um ano. "
                    "E a reputação junto às grandes petroleiras que querem desinvestir "
                    "é a maior vantagem competitiva: quando a Chevron, Equinor ou Petrobras "
                    "quer vender um campo, a PRIO está na lista curta dos compradores."
                ),
            },
            "BRAV3": {
                "nome": "Brava Energia",
                "fundacao": "2024 (fusão 3R Petroleum + Enauta)",
                "sede": "Rio de Janeiro, RJ",
                "tagline": "A junior oil em consolidação. Nasceu da fusão de dois modelos distintos — ainda provando que o todo vale mais que as partes. OPA da Ecopetrol coloca o horizonte em suspenso.",
                "modelo": (
                    "A Brava Energia nasceu em setembro de 2024 da fusão entre a 3R Petroleum "
                    "(campos maduros onshore e offshore) e a Enauta (campo de Atlanta). "
                    "Atlanta é o ativo premium da empresa: óleo leve de altíssima qualidade, "
                    "offshore no Espírito Santo, com menor desconto no Brent. "
                    "Os campos de Papa-Terra (óleo pesado, Bacia de Campos) e de gás "
                    "(Peroá e Manati, offshore) completam o portfólio. "
                    "Em janeiro de 2026, comprou 50% de Tartaruga Verde e Espadarte por US$450 mi "
                    "— campos operados pela Petrobras com 14 poços produtores e produção "
                    "de ~55 kboed a 100%. "
                    "Em maio de 2026, a Ecopetrol (estatal colombiana) lançou OPA "
                    "para assumir 51% da empresa a R$23/ação (prêmio de até 28%). "
                    "A operação aguarda aprovação do CADE e da ANP — e muda completamente "
                    "o perfil de risco da empresa se concluída."
                ),
                "receita": [
                    ("Atlanta (óleo leve offshore)", "~35%", "óleo premium; menor desconto vs Brent; principal ativo da Enauta"),
                    ("Papa-Terra (óleo pesado offshore)", "~25%", "FPSO P-63; óleo viscoso com maior desconto no Brent"),
                    ("Tartaruga Verde + Espadarte (novo)", "~15%", "50% adquiridos em 2026; operado pela Petrobras; 14 poços"),
                    ("Gás natural (Peroá, Manati)", "~15%", "offshore ES/BA; escoamento via gasodutos"),
                    ("Campos onshore 3R", "~10%", "herdados da 3R; menor prioridade estratégica"),
                ],
                "vantagens": [
                    "Atlanta: óleo leve de alta qualidade — menor desconto vs Brent, maior preço realizado",
                    "2ª maior independente em reservas: escala que abre portas em desinvestimentos de grandes petroleiras",
                    "OPA Ecopetrol a R$23: piso de preço no curto prazo com prêmio de 28%",
                    "Tartaruga Verde: 14 poços produtores, operado pela Petrobras — produção previsível e já funcionando",
                    "Diversificação de portfólio: onshore + offshore + gás + óleo leve + óleo pesado",
                ],
                "riscos": [
                    "Integração pós-fusão não provada: 3R e Enauta tinham culturas e sistemas operacionais distintos",
                    "Alavancagem alta: dívida da fusão + US$450 mi de Tartaruga Verde = balanço apertado",
                    "OPA Ecopetrol incerta: aprovação de CADE e ANP pode demorar ou não acontecer",
                    "Papa-Terra: óleo pesado = maior desconto no Brent e campo operacionalmente mais complexo",
                    "FCF neutro em 2026: alta produção, mas capex pesado e dívida consomem o caixa",
                ],
                "barreira": (
                    "Atlanta é o principal ativo de barreira — campo de óleo leve offshore "
                    "que a Enauta levou anos para desenvolver e que poucos independentes "
                    "conseguiriam financiar. "
                    "O know-how da Enauta em desenvolvimento greenfield offshore "
                    "é raro no Brasil fora da Petrobras. "
                    "Mas a Brava ainda está construindo sua identidade pós-fusão — "
                    "a barreira real ainda está sendo testada na execução."
                ),
            },
        },
    },
    "🌾 Agronegócio": {
        "tickers": ["SLCE3", "KEPL3"],
        "tagline": "Dois negócios dentro do agro: uma produtora de grãos pura e uma fabricante de equipamentos para armazenar esses grãos. O mesmo ciclo, posições diferentes na cadeia.",
        "logica": {
            "titulo": "O que move o agronegócio",
            "texto": (
                "A SLC Agrícola produz soja, milho e algodão — resultado ligado diretamente "
                "ao preço da commodity em dólar. "
                "A Kepler Weber fabrica silos para armazenar o que o produtor colheu — "
                "ciclo menos volátil, sustentado pelo déficit estrutural de 145 mi t "
                "de armazenagem no Brasil."
            ),
            "drivers": [
                ("Preço das commodities", "Soja e milho cotados em dólar no CBOT. Queda de 20% no preço reduz receita da SLC proporcionalmente."),
                ("Câmbio", "Toda receita do agro é em dólar; custos em real. Dólar alto beneficia a SLC e aumenta poder de compra do produtor para investir em silo."),
                ("Déficit de armazenagem", "Brasil produz 320 mi t/safra, capacidade estática é 175 mi t. Déficit de 145 mi t cria demanda secular para a Kepler independente do preço."),
                ("Arrendamento", "SLC arrenda ~70% das terras em sacos de soja/ha. Quando preço cai, custo cai junto — hedge natural de margem."),
                ("Insumos", "Fertilizantes e defensivos têm componente de câmbio. Normalização 2023-2026 beneficiou margens da SLC."),
            ],
        },
        "comparativo": {
            "dimensoes": [
                "O que faz de verdade",
                "Posição na cadeia",
                "Exposição à commodity",
                "Exposição ao câmbio",
                "Ciclicidade",
                "Dividendo (DY)",
                "Risco principal",
            ],
            "grupos": [
                {"label": "Agronegócio", "tickers": ["SLCE3", "KEPL3"]},
            ],
            "empresas": {
                "SLCE3": {
                    "nome": "SLC Agrícola",
                    "cor": "#22C55E",
                    "O que faz de verdade": ("Produtora de grãos e algodão", "soja, milho e algodão — maior produtora agrícola listada do Brasil"),
                    "Posição na cadeia": ("Produtora pura", "planta, colhe e vende a commodity diretamente"),
                    "Exposição à commodity": ("Máxima", "receita = volume × preço em dólar", "badge-red"),
                    "Exposição ao câmbio": ("Máxima positiva", "receita em dólar, custo em real — dólar alto amplifica resultado", "badge-green"),
                    "Ciclicidade": ("Alta", "preço de commodity oscila 30-50% em ciclos de 2-4 anos", "badge-red"),
                    "Dividendo (DY)": ("DY variável 5-12%", "payout 50%; oscila com o ciclo de preços"),
                    "Risco principal": ("Preço de soja + câmbio apreciado + clima adverso = resultado negativo", ""),
                },
                "KEPL3": {
                    "nome": "Kepler Weber",
                    "cor": "#F59E0B",
                    "O que faz de verdade": ("Silos e equipamentos de armazenagem de grãos", "~80% de market share em silos metálicos no Brasil"),
                    "Posição na cadeia": ("Fornecedor de infraestrutura", "vende ao produtor, não produz — menos exposição ao preço"),
                    "Exposição à commodity": ("Indireta", "produtor com resultado bom investe mais; déficit garante demanda base", "badge-yellow"),
                    "Exposição ao câmbio": ("Positiva por proxy", "produtor em dólar tem mais caixa para investir em armazenagem", "badge-green"),
                    "Ciclicidade": ("Moderada", "déficit de 145 mi t sustenta demanda base mesmo em ciclos fracos", "badge-yellow"),
                    "Dividendo (DY)": ("DY 6-10%", "pagadora consistente; carteira de pedidos de 12+ meses"),
                    "Risco principal": ("Safra ruim + queda de commodity = produtor adia investimento em silo", ""),
                },
            },
        },
        "perfis": {
            "SLCE3": {
                "nome": "SLC Agrícola S.A.",
                "fundacao": "1977",
                "sede": "Porto Alegre, RS",
                "tagline": "A maior produtora agrícola listada do Brasil. 700 mil hectares, soja + milho + algodão, tudo vendido em dólar.",
                "modelo": (
                    "Produtora pura de commodities — não beneficia nem exporta diretamente. "
                    "Opera ~18 fazendas em 7 estados do Cerrado. "
                    "~70% das áreas são arrendadas em sacos de soja/hectare: "
                    "quando o preço cai, o custo cai junto — proteção automática de margem. "
                    "Em 2025-2026, queda de ~20% no preço da soja e câmbio mais forte "
                    "pressionaram margens vs o pico de 2022-2023."
                ),
                "receita": [
                    ("Soja", "~55%", "principal cultura; exportada via tradings"),
                    ("Algodão", "~30%", "maior margem unitária; demanda global crescente"),
                    ("Milho (safrinha)", "~15%", "segunda safra no mesmo solo — custo marginal menor"),
                ],
                "vantagens": [
                    "Maior produtora listada: escala de 700 mil ha gera poder de negociação com fornecedores",
                    "Arrendamento como hedge: custo em sacos de soja cai quando preço cai automaticamente",
                    "Cerrado: produtividade acima da média nacional; logística para exportação otimizada",
                    "Diversificação: soja + milho + algodão suaviza dependência de uma única commodity",
                ],
                "riscos": [
                    "Preço de soja: queda de 20% no preço reduz receita proporcionalmente",
                    "Câmbio apreciado: real forte comprime margens da receita em dólar",
                    "Clima: seca ou excesso de chuva impacta produção nas 18 fazendas",
                    "Arrendamento renovável: risco de não renovação ou aumento de custo pelo dono da terra",
                ],
                "barreira": (
                    "40 anos de relacionamento com donos de terra para arrendamento de longo prazo. "
                    "Gestão de 18 fazendas em 7 estados com agricultura de precisão é operação "
                    "que levou décadas para construir. "
                    "Novo entrante precisaria de capital, terra disponível e reputação ao mesmo tempo."
                ),
            },
            "KEPL3": {
                "nome": "Kepler Weber S.A.",
                "fundacao": "1925 (Panambi, RS)",
                "sede": "Panambi, RS",
                "tagline": "O líder absoluto em armazenagem de grãos no Brasil. 80% de market share e déficit de 145 mi t de capacidade ainda a preencher.",
                "modelo": (
                    "Fabrica silos metálicos, secadores de grãos, elevadores de canecas e "
                    "sistemas de transporte para armazenagem. "
                    "Líder com ~80% de market share em silos metálicos. "
                    "Motor secular: Brasil produz 320 mi t e tem capacidade de 175 mi t — "
                    "déficit de 145 mi t cria demanda estrutural que não depende do preço da soja. "
                    "Expansão do agro para MATOPIBA gera novas fazendas sem infraestrutura — "
                    "demanda crescente por silos e secadores do zero."
                ),
                "receita": [
                    ("Silos metálicos", "~55%", "produto principal; ~80% de market share"),
                    ("Secadores de grãos", "~20%", "equipamento crítico pós-colheita; exigido para qualidade de exportação"),
                    ("Sistemas de transporte", "~15%", "elevadores e correias — cross-sell natural com o silo"),
                    ("Exportação e serviços", "~10%", "América do Sul, África; instalação e manutenção"),
                ],
                "vantagens": [
                    "80% de market share: liderança de 100 anos — nenhum concorrente chega perto",
                    "Déficit de 145 mi t: demanda estrutural secular independente do ciclo econômico",
                    "Câmbio positivo por proxy: produtor em dólar tem mais poder de compra para investir",
                    "Carteira de 12+ meses de pedidos: visibilidade excepcional no setor industrial",
                ],
                "riscos": [
                    "Ciclicidade do agro: safra ruim + queda de commodity = produtor adia investimento",
                    "Aço: preço internacional afeta custo dos silos",
                    "Enchentes RS: sede em Panambi — desastres no Sul impactam operações",
                    "Importados chineses: silos via dumping em câmbio apreciado",
                ],
                "barreira": (
                    "100 anos de know-how e rede de revendedores em todo o Brasil agrícola. "
                    "O produtor que compra um silo quer quem estará lá em 10 anos. "
                    "A Kepler tem esse canal — um entrante precisaria de décadas para construir."
                ),
            },
        },
    },
    "🔩 Autopeças & Industrial": {
        "tickers": ["LEVE3", "POMO4", "VULC3", "SHUL4"],
        "tagline": "Cinco empresas de 'autopeças e industrial' — mas com modelos, clientes e ciclos completamente diferentes. A LEVE vende para mecânica no interior do Brasil. A KEPL vende para fazendas. A POMO vende ônibus para o governo.",
        "logica": {
            "titulo": "O que move o setor — e por que cada empresa tem seu próprio ciclo",
            "texto": (
                "Autopeças e industrial é o setor mais heterogêneo da bolsa. "
                "LEVE3, POMO4, VULC3, SHUL4 e KEPL3 estão no mesmo índice setorial — "
                "mas têm clientes, ciclos e riscos completamente diferentes. "
                "A Mahle (LEVE3) vende velas e filtros para o aftermarket de carros. "
                "A Marcopolo (POMO4) fabrica carrocerias de ônibus para o governo e para exportação. "
                "A Vulcabras (VULC3) faz tênis Under Armour e Olympikus no Brasil. "
                "A Schuler (SHUL4) fabrica peças de aço estampado para montadoras. "
                "A Kepler Weber (KEPL3) fabrica silos e equipamentos para armazenagem de grãos. "
                "Entender o cliente final de cada uma é mais importante do que qualquer múltiplo."
            ),
            "drivers": [
                ("Frota circulante e idade média do veículo — o motor do aftermarket", (
                    "Quanto mais velha a frota, maior a demanda por peças de reposição. "
                    "O Brasil tem frota média de 11+ anos — uma das mais velhas do mundo desenvolvido. "
                    "Isso cria demanda estrutural para o aftermarket independente do ciclo econômico. "
                    "A Mahle (LEVE3) é o maior beneficiário: quanto mais velhos os carros, "
                    "mais filtros, velas e kits de motor são trocados nas mecânicas."
                )),
                ("Câmbio — o duplo efeito para exportadores", (
                    "Empresas que exportam (Mahle, Marcopolo, Kepler) faturam em dólar "
                    "mas têm custos em real. Dólar alto = margens melhores. "
                    "Mas câmbio também afeta custo de matéria-prima: aço e borracha têm "
                    "componente de preço internacional. Importadoras de componentes sofrem com dólar alto."
                )),
                ("Investimento em infraestrutura e frotas — o ciclo da Marcopolo", (
                    "Ônibus são comprados por prefeituras (frota municipal), "
                    "empresas de turismo e operadores de fretamento. "
                    "Prefeituras compram quando têm orçamento (BNDES, verbas federais). "
                    "Exportação para Américas, África e Ásia adiciona diversificação geográfica. "
                    "Em 2026, BRT (Bus Rapid Transit) em capitais brasileiras é catalisador."
                )),
                ("Agronegócio e safra — o ciclo da Kepler Weber", (
                    "A Kepler fabrica silos, secadores e transportadores de grãos. "
                    "Quando o agronegócio vai bem (preço de commodity alto, câmbio favorável), "
                    "produtores e cooperativas investem em armazenagem. "
                    "Com a safra recorde brasileira e déficit de armazenagem, "
                    "a Kepler opera com carteira de pedidos de 12+ meses."
                )),
                ("OEM vs aftermarket — dois mercados com lógicas opostas", (
                    "OEM (Original Equipment Manufacturer): vende para montadoras (Ford, GM, Toyota) "
                    "que colocam as peças nos carros novos. Segue o ciclo de produção de veículos. "
                    "Aftermarket: vende para o mercado de reposição (mecânicas, distribuidores). "
                    "Segue a frota circulante — anticíclico. "
                    "Schuler (SHUL4) é OEM puro. Mahle tem os dois, com predominância do aftermarket."
                )),
            ],
        },
        "comparativo": {
            "dimensoes": [
                "O que faz de verdade",
                "Cliente principal",
                "Modelo OEM vs aftermarket",
                "Exposição ao câmbio",
                "Ciclicidade do negócio",
                "Margem bruta (ref.)",
                "Dividendo (DY)",
                "Risco principal",
            ],
            "grupos": [
                {"label": "Autopeças e componentes", "tickers": ["LEVE3", "SHUL4"]},
                {"label": "Equipamentos e industrial", "tickers": ["POMO4", "VULC3"]},
            ],
            "empresas": {
                "LEVE3": {
                    "nome": "Mahle Metal Leve",
                    "cor": "#3B82F6",
                    "O que faz de verdade": ("Peças de motor — pistões, filtros, velas", "componentes de motor para carros leves e pesados"),
                    "Cliente principal": ("Aftermarket (mecânicas e distribuidores)", "~70% das receitas; OEM (montadoras) ~30%"),
                    "Modelo OEM vs aftermarket": ("Aftermarket dominante", "anticíclico — frota velha gera demanda constante", "badge-green"),
                    "Exposição ao câmbio": ("Alta positiva", "exporta para Europa e EUA; dólar alto aumenta margens", "badge-green"),
                    "Ciclicidade do negócio": ("Baixa", "aftermarket não para em recessão — carro velho precisa de peça", "badge-green"),
                    "Margem bruta (ref.)": ("~38-40%", "uma das mais altas do setor industrial brasileiro"),
                    "Dividendo (DY)": ("DY 8-12%", "payout elevado; controladora Mahle alemã quer dividendo"),
                    "Risco principal": ("Eletrificação da frota: carro elétrico tem menos peças de motor — ameaça estrutural de longo prazo", ""),
                },
                "SHUL4": {
                    "nome": "Schuler (Schuler S.A.)",
                    "cor": "#6B7280",
                    "O que faz de verdade": ("Peças estampadas de aço para carrocerias", "componentes estruturais para montadoras — portas, chassi, reforços"),
                    "Cliente principal": ("Montadoras (OEM puro)", "Ford, GM, Toyota, Stellantis — 100% B2B com grandes clientes"),
                    "Modelo OEM vs aftermarket": ("OEM 100%", "segue ciclo de produção de veículos das montadoras", "badge-red"),
                    "Exposição ao câmbio": ("Moderada", "matéria-prima (aço) tem componente dólar; cliente paga em real", "badge-yellow"),
                    "Ciclicidade do negócio": ("Alta", "produção de veículos cai em recessão; montadoras reduzem pedidos", "badge-red"),
                    "Margem bruta (ref.)": ("~18-22%", "menor que aftermarket por ser commodity industrial"),
                    "Dividendo (DY)": ("DY variável ~5%", "payout dependente de resultado — mais variável que pares"),
                    "Risco principal": ("OEM concentrado em poucos clientes + risco de eletrificação (precisa adaptar estamparia) + ciclo automotivo", ""),
                },
                "POMO4": {
                    "nome": "Marcopolo",
                    "cor": "#22C55E",
                    "O que faz de verdade": ("Carrocerias de ônibus", "líder mundial em ônibus; exporta para 100+ países"),
                    "Cliente principal": ("Prefeituras + operadoras de ônibus + exportação", "Brasil ~50%; exterior ~50%"),
                    "Modelo OEM vs aftermarket": ("OEM (não é autopeças)", "faz o produto final — não a peça; cada ônibus é um projeto", "badge-yellow"),
                    "Exposição ao câmbio": ("Alta positiva", "~50% das receitas em moeda estrangeira (dólar, euro, peso)", "badge-green"),
                    "Ciclicidade do negócio": ("Moderada", "exportação suaviza o ciclo doméstico; renovação de frotas tem demanda estrutural", "badge-yellow"),
                    "Margem bruta (ref.)": ("~20-24%", "margens crescendo com mix favorável de exportação e BRT"),
                    "Dividendo (DY)": ("DY 5-8%", "payout consistente; histórico de JCP trimestral"),
                    "Risco principal": ("Eletrificação de ônibus: BYD e Volvo elétricos competem por frotas novas; Marcopolo precisa adaptar", ""),
                },
                "KEPL3": {
                    "nome": "Kepler Weber",
                    "cor": "#F59E0B",
                    "O que faz de verdade": ("Silos e equipamentos para armazenagem de grãos", "líder no Brasil em armazenagem; 80% de market share em silos"),
                    "Cliente principal": ("Produtores rurais + cooperativas + tradings", "agronegócio brasileiro; exportação para Américas e África"),
                    "Modelo OEM vs aftermarket": ("Capital goods (bens de capital)", "não é autopeça — é equipamento de fazenda; ciclo de investimento rural", "badge-yellow"),
                    "Exposição ao câmbio": ("Alta positiva", "cliente rural vende soja em dólar — quando dólar sobe, produtor tem mais poder de compra", "badge-green"),
                    "Ciclicidade do negócio": ("Alta (mas ciclo diferente)", "segue o agro, não o automobilístico; safra recorde = demanda por armazenagem", "badge-yellow"),
                    "Margem bruta (ref.)": ("~28-32%", "liderança de mercado permite precificação — margem acima de pares industriais"),
                    "Dividendo (DY)": ("DY 6-10%", "pagadora consistente; carteira de pedidos de 12+ meses dá visibilidade"),
                    "Risco principal": ("Ciclicidade do agro: safra ruim + queda de commodity reduz investimento do produtor rural", ""),
                },
                "VULC3": {
                    "nome": "Vulcabras Azaleia",
                    "cor": "#EF4444",
                    "O que faz de verdade": ("Calçados esportivos e casual", "Under Armour + Olympikus no Brasil; 50+ mi de pares/ano"),
                    "Cliente principal": ("Consumidor final via varejo", "Renner, Riachuelo, lojas próprias, e-commerce — B2C"),
                    "Modelo OEM vs aftermarket": ("Não é autopeça", "fabricante de calçados — confusão de classificação setorial", "badge-yellow"),
                    "Exposição ao câmbio": ("Moderada negativa", "licença Under Armour paga royalty em dólar; matéria-prima com componente importado", "badge-yellow"),
                    "Ciclicidade do negócio": ("Moderada", "consumo de calçados é menos cíclico que bens duráveis, mas sensível à renda", "badge-yellow"),
                    "Margem bruta (ref.)": ("~42-45%", "a mais alta do grupo — brand premium da Under Armour e escala de produção"),
                    "Dividendo (DY)": ("DY 3-5%", "crescimento reinvestido; capex em automação de produção"),
                    "Risco principal": ("Renovação do contrato Under Armour + concorrência de importados asiáticos + sensibilidade ao consumo de baixa renda", ""),
                },
            },
        },
        "perfis": {
            "LEVE3": {
                "nome": "Mahle Metal Leve S.A.",
                "fundacao": "1950 (como Metal Leve; controlada pela Mahle alemã desde 1996)",
                "sede": "São Paulo, SP",
                "tagline": "O negócio que prospera quando o carro envelhece. Aftermarket anticíclico, controladora alemã que financia o P&D, e a única empresa do grupo que a Mahle listou fora da Alemanha.",
                "modelo": (
                    "A Mahle Metal Leve é a subsidiária brasileira do grupo Mahle — "
                    "um dos maiores fabricantes de componentes automotivos do mundo, "
                    "com sede em Stuttgart, Alemanha. "
                    "No Brasil, fabrica pistões, anéis de segmento, buchas, "
                    "filtros (óleo, ar, combustível) e velas de ignição. "
                    "O modelo tem duas frentes: OEM (~30%), onde vende diretamente para "
                    "GM, Ford, Stellantis e Volkswagen que montam os carros novos; "
                    "e aftermarket (~70%), onde vende para distribuidores e mecânicas "
                    "que trocam peças em carros usados. "
                    "O aftermarket é o diferencial: com frota média de 11+ anos no Brasil, "
                    "cada motor exige troca de pistão, filtro ou vela em média a cada 2-3 anos. "
                    "Quanto mais velha a frota, mais demanda — é anticíclico por natureza. "
                    "A controladora alemã custeia o P&D global (€1 bi/ano em inovação) "
                    "e o Brasil se beneficia do know-how sem pagar por isso diretamente. "
                    "Exporta componentes para Europa e América do Norte, capturando o câmbio favorável."
                ),
                "receita": [
                    ("Aftermarket Brasil", "~55%", "mecânicas, distribuidores, varejo de autopeças — anticíclico e recorrente"),
                    ("OEM Brasil (montadoras)", "~25%", "GM, Ford, Stellantis, VW — segue produção de veículos novos"),
                    ("Exportação (OEM global)", "~20%", "componentes para Europa e EUA; dólar alto melhora margens"),
                ],
                "vantagens": [
                    "Aftermarket anticíclico: frota velha gera demanda constante independente do PIB",
                    "P&D financiado pela matriz: Mahle alemã investe €1 bi/ano em inovação — LEVE3 acessa sem pagar",
                    "Margem bruta de 38-40%: entre as mais altas do setor industrial — brand reconhecido pelo mecânico",
                    "Exportação em dólar: ~20% das receitas em moeda forte protege em desvalorizações do real",
                    "Único papel do grupo Mahle listado fora da Alemanha: acesso a gestão global com liquidez local",
                ],
                "riscos": [
                    "Eletrificação da frota: carro elétrico não tem pistão, filtro de óleo nem vela — ameaça estrutural de 10-20 anos",
                    "Concentração no motor a combustão: 90%+ das receitas dependem de tecnologia em transição",
                    "OEM sujeito ao ciclo automotivo: montadoras param produção em crise e afeta 25% da receita",
                    "Controladora estrangeira: dividendo certo, mas decisões estratégicas vêm de Stuttgart — potencial de conflito com minoritários",
                ],
                "barreira": (
                    "Marca reconhecida pelo mecânico. No aftermarket, quem decide a peça é o mecânico — "
                    "não o dono do carro. E o mecânico de Franca, Uberlândia ou Manaus "
                    "conhece e confia na Mahle há décadas. "
                    "Construir essa confiança com 50.000 mecânicos no Brasil inteiro "
                    "é um ativo invisível que nenhum concorrente recompra. "
                    "Mais o know-how técnico da matriz alemã: "
                    "qualidade de produto que importados asiáticos ainda não replicam no motor."
                ),
            },
            "POMO4": {
                "nome": "Marcopolo S.A.",
                "fundacao": "1949 (em Caxias do Sul, RS — por Reinaldo Pasa)",
                "sede": "Caxias do Sul, RS",
                "tagline": "O maior fabricante de carrocerias de ônibus do mundo. Exporta para 100+ países, e cada ônibus é um projeto de engenharia — não uma linha de produção em série.",
                "modelo": (
                    "A Marcopolo não fabrica o chassi do ônibus — fabrica a carroceria. "
                    "O chassi vem da Volvo, Mercedes ou Scania; a Marcopolo coloca em cima "
                    "a estrutura de passageiros (o que o passageiro vê e sente). "
                    "É a maior fabricante de carrocerias de ônibus do mundo em volume. "
                    "Opera em dois mercados distintos: Brasil (~50% da receita), "
                    "onde os clientes são prefeituras (ônibus urbano), empresas de turismo "
                    "e fretamento; e exterior (~50%), onde exporta para América Latina, "
                    "África, Índia, Austrália e Europa, com fabricação local em alguns países. "
                    "O produto é customizado — cada pedido tem especificações diferentes. "
                    "Isso cria barreiras de engenharia e relacionamento com o cliente "
                    "que produtos padronizados não têm. "
                    "Em 2025-2026, o BRT (Bus Rapid Transit) nas capitais brasileiras "
                    "e o programa de eletrificação de frotas municipais são os maiores catalisadores. "
                    "A Marcopolo já fabrica carrocerias para ônibus elétricos — "
                    "é uma das poucas do setor que mitigou o risco de eletrificação."
                ),
                "receita": [
                    ("Ônibus urbano — Brasil", "~30%", "prefeituras e operadoras; BRT e eletrificação são catalisadores 2025-2026"),
                    ("Ônibus rodoviário e turismo — Brasil", "~20%", "empresas de fretamento e turismo; ciclo ligado à economia"),
                    ("Exportação (América Latina + África + outros)", "~35%", "dólar/euro nas receitas; margens melhores que o mercado doméstico"),
                    ("Fabricação local no exterior (JVs)", "~15%", "Índia, Austrália, Colômbia — receita em moeda local"),
                ],
                "vantagens": [
                    "Líder mundial em carrocerias de ônibus: escala que nenhum concorrente brasileiro alcança",
                    "50% de exportação: diversificação geográfica que suaviza o ciclo doméstico",
                    "Produto customizado: cada ônibus é um projeto — barreiras de engenharia e relacionamento",
                    "Já fabrica para elétricos: adaptação estratégica que evita a armadilha da eletrificação",
                    "Caxias do Sul: cluster industrial gaúcho com fornecedores especializados e mão de obra qualificada",
                ],
                "riscos": [
                    "Dependência de orçamento público: prefeituras compram quando têm verba — ciclo político afeta demanda doméstica",
                    "Eletrificação em andamento: BYD e Volvo Elétrico competem pela carroceria de ônibus elétrico",
                    "Câmbio de dois gumes: exportação beneficia margem, mas matéria-prima importada sobe junto",
                    "Enchentes RS (2024): sede em Caxias do Sul sofreu impacto operacional — risco geográfico concentrado",
                ],
                "barreira": (
                    "75 anos de know-how em engenharia de carrocerias de ônibus. "
                    "O ônibus urbano de São Paulo, de Lagos, de Melbourne e de Montevidéu "
                    "pode ser da Marcopolo — e cada cidade tem normas técnicas, "
                    "dimensões e especificações diferentes. "
                    "Dominar isso em 100+ países é uma barreira de conhecimento técnico e "
                    "relacionamento institucional que nenhum entrante replica em menos de décadas."
                ),
            },
            "VULC3": {
                "nome": "Vulcabras Azaleia S.A.",
                "fundacao": "1952 (como Calçados Azaleia; Vulcabras desde 2011)",
                "sede": "Jundiaí, SP",
                "tagline": "O maior fabricante de calçados esportivos do Brasil. Faz Under Armour para o Brasil e Olympikus — 50 milhões de pares por ano, saindo de Horizonte (CE).",
                "modelo": (
                    "A Vulcabras é a maior fabricante de calçados esportivos do Brasil — "
                    "em volume de produção, não em receita de marca. "
                    "Opera com duas marcas: Olympikus (própria, focada em performance popular) "
                    "e Under Armour (licença exclusiva para o Brasil — fabrica, distribui e vende). "
                    "A fábrica principal fica em Horizonte (CE) — maior complexo industrial "
                    "de calçados do hemisfério sul, com mais de 13.000 funcionários. "
                    "O Nordeste tem dois benefícios estruturais: custo de mão de obra menor "
                    "e incentivos fiscais do estado do Ceará. "
                    "O modelo de licença da Under Armour é o diferencial: "
                    "a Vulcabras paga royalty (em dólar, um custo), "
                    "mas recebe o brand premium de uma marca global de alta performance "
                    "que ela não precisaria construir do zero. "
                    "Vende via varejo (Renner, Riachuelo), e-commerce e lojas multimarcas."
                ),
                "receita": [
                    ("Under Armour Brasil (licença)", "~48%", "marca premium — maior ticket médio; paga royalty em dólar; contrato vigente"),
                    ("Olympikus", "~40%", "marca própria — boa penetração no interior e classes B/C; maior margem líquida"),
                    ("Outros (exportação, private label)", "~12%", "exportação para América Latina; produção para terceiros"),
                ],
                "vantagens": [
                    "Maior complexo industrial de calçados do hemisfério sul: escala de 50 mi de pares/ano gera custo unitário imbatível",
                    "Under Armour: brand premium sem o risco de construir uma marca global do zero",
                    "Nordeste: custo de mão de obra menor + incentivos fiscais do Ceará = estrutura de custo competitiva",
                    "Margem bruta 42-45%: a mais alta do grupo — mix de marca premium com produção eficiente",
                    "Olympikus como proteção: marca própria cresce sem depender de contrato de licença",
                ],
                "riscos": [
                    "Renovação do contrato Under Armour: se perder a licença, perde ~48% da receita do dia para a noite",
                    "Royalty em dólar: custo da licença sobe com o dólar — margem comprimida em desvalorizações do real",
                    "Importados asiáticos: concorrência de calçados chineses e vietnamitas comprime preços no varejo",
                    "Exposição à renda da classe C: Olympikus e Under Armour entry-level sensíveis a crises de renda",
                ],
                "barreira": (
                    "Escala industrial e a licença Under Armour. "
                    "Construir um complexo de 13.000 funcionários especializados em calçados esportivos "
                    "leva décadas — e criar o conhecimento técnico de solado, "
                    "espuma de amortecimento e cabedal esportivo é barreira de processo. "
                    "A Under Armour escolheu a Vulcabras porque ela é a única no Brasil "
                    "com capacidade de produzir em escala e qualidade para uma marca premium global."
                ),
            },
            "SHUL4": {
                "nome": "Schuler S.A.",
                "fundacao": "1937 (em São Bento do Sul, SC)",
                "sede": "São Bento do Sul, SC",
                "tagline": "A maior estamparia de aço do Brasil. Fabrica as partes metálicas que ninguém vê — mas que todo carro tem. Puro OEM, puro ciclo automotivo.",
                "modelo": (
                    "A Schuler é uma OEM pura — fabrica exclusivamente para montadoras. "
                    "O produto são peças estampadas de aço: portas, capôs, para-lamas, "
                    "reforços estruturais de chassi, componentes de suspensão. "
                    "É o que o cliente nunca vê, mas que está em todo veículo. "
                    "A demanda segue diretamente a produção de veículos no Brasil — "
                    "quando as montadoras produzem mais, a Schuler fatura mais; "
                    "quando param (crise de semicondutores, recessão), a Schuler para junto. "
                    "A matéria-prima principal é o aço plano — cujo preço é cotado internacionalmente "
                    "e tem componente de câmbio, criando risco de margem quando o real desvaloriza "
                    "sem que o cliente (montadora) aceite reajuste imediato. "
                    "Opera em Santa Catarina, com uma estrutura industrial robusta "
                    "e relacionamento de décadas com as principais montadoras do Brasil."
                ),
                "receita": [
                    ("Peças estampadas para carros de passeio", "~60%", "GM, Ford, Stellantis, VW, Toyota — clientes concentrados"),
                    ("Peças para veículos comerciais e pesados", "~30%", "caminhões e ônibus — ciclo diferente do passeio"),
                    ("Ferramental e outros serviços", "~10%", "matrizes e ferramentas para clientes industriais"),
                ],
                "vantagens": [
                    "Relacionamento de décadas com montadoras: trocam de fornecedor raramente — custo de mudança é enorme",
                    "Santa Catarina: polo industrial consolidado com fornecedores especializados e logística para portos",
                    "Especialização técnica: estampagem de alta precisão é barreira de processo que startups não replicam",
                    "Veículos comerciais: diversificação com caminhões e ônibus que têm ciclo diferente do passeio",
                ],
                "riscos": [
                    "OEM 100%: qualquer queda na produção de veículos impacta diretamente a receita",
                    "Concentração de clientes: poucos clientes grandes — perder um é perder fatia relevante",
                    "Aço como risco: commodity internacional com componente cambial; repricing com montadora é lento",
                    "Eletrificação: carros elétricos têm menos peças estampadas de aço (estrutura diferente) — risco de médio prazo",
                ],
                "barreira": (
                    "O processo de qualificação de um novo fornecedor numa montadora leva 2-3 anos "
                    "de testes, auditorias e certificações. "
                    "A Schuler já passou por esse processo com todos os clientes — "
                    "a barreira de entrada não é o equipamento (pode-se comprar uma prensa), "
                    "mas o histórico de qualidade que dá confiança à montadora para homologar. "
                    "E São Bento do Sul concentra um cluster de indústrias de metal-mecânica "
                    "que cria um ambiente de fornecedores especializados difícil de replicar."
                ),
            },
            "KEPL3": {
                "nome": "Kepler Weber S.A.",
                "fundacao": "1925 (em Panambi, RS)",
                "sede": "Panambi, RS",
                "tagline": "O líder absoluto em armazenagem de grãos no Brasil. 80% de market share em silos — e a safra recorde do agro brasileiro ainda está criando demanda por mais capacidade.",
                "modelo": (
                    "A Kepler Weber não é autopeça — é uma empresa de bens de capital para o agronegócio. "
                    "Fabrica silos (metálicos e de concreto), secadores de grãos, "
                    "transportadores (elevadores de canecas, correias) e sistemas de controle "
                    "para armazenagem de soja, milho, trigo e outros grãos. "
                    "É líder absoluta no Brasil com ~80% de market share em silos metálicos — "
                    "o produto mais vendido do portfólio. "
                    "O mercado-alvo são produtores rurais individuais, cooperativas e tradings "
                    "(Bunge, ADM, Cargill, LDC). "
                    "O diferencial do modelo: o Brasil tem grave déficit de armazenagem. "
                    "A capacidade estática nacional é de ~175 milhões de toneladas, "
                    "enquanto a produção de grãos superou 320 milhões em 2025. "
                    "Cada tonelada de grão produzida sem armazém adequado é prejuízo para o produtor. "
                    "Isso cria demanda estrutural que não depende do ciclo econômico convencional — "
                    "depende do ciclo do agronegócio."
                ),
                "receita": [
                    ("Silos metálicos e acessórios", "~55%", "produto principal; liderança de 80% de mercado; vende a produtores e cooperativas"),
                    ("Secadores de grãos", "~20%", "equipamento crítico pós-colheita; crescimento com qualidade exigida para exportação"),
                    ("Sistemas de transporte (elevadores, correias)", "~15%", "logística interna do silo — cross-sell natural com a venda do silo"),
                    ("Exportação e serviços", "~10%", "América do Sul, África e outros; instalação e manutenção"),
                ],
                "vantagens": [
                    "80% de market share em silos: nenhum concorrente chega perto — liderança consolidada em décadas",
                    "Déficit estrutural de armazenagem: Brasil produz 320 mi t de grãos com capacidade de 175 mi t — runway de crescimento secular",
                    "Câmbio positivo por proxy: cliente rural vende soja em dólar — dólar alto dá mais poder de compra para investir em armazenagem",
                    "Carteira de pedidos de 12+ meses: visibilidade de receita acima da média industrial",
                    "Panambi como polo: 100 anos de know-how em equipamentos agroindustriais no RS — cluster com fornecedores especializados",
                ],
                "riscos": [
                    "Ciclicidade do agro: safra ruim + queda de commodity = produtor adia investimento em armazenagem",
                    "Aço como matéria-prima: preço internacional afeta custo dos silos; repasse ao cliente tem defasagem",
                    "Concentração geográfica: RS como base industrial — enchentes de 2024 impactaram operações",
                    "Concorrência de importados: silos chineses entram via dumping em períodos de câmbio apreciado",
                ],
                "barreira": (
                    "100 anos de know-how e 80% de mercado criam uma barreira quase intransponível. "
                    "O produtor rural que vai comprar um silo de R$500 mil "
                    "não arrisca com um fornecedor desconhecido — "
                    "ele quer quem estará lá para dar assistência em 10 anos. "
                    "A Kepler tem rede de revendedores e assistência técnica em todo o Brasil agrícola — "
                    "um entrante precisaria de décadas para construir esse canal. "
                    "E a posição de liderança cria um efeito de rede: "
                    "cooperativa que já tem silos Kepler compra mais Kepler "
                    "porque os sistemas são integrados."
                ),
            },
        },
    },
    "🏪 Shoppings": {
        "tickers": ["ALOS3"],
        "tickers_sub": ["MULT3"],
        "label_sub": "Fora do RADAR — no dossiê",
        "tagline": "Mesma licença de shopping, dois modelos opostos: Allos aposta em escala (44 shoppings, diversificação geográfica); Multiplan aposta em qualidade (20 shoppings, os melhores do Brasil). A métrica que os diferencia é a conversão de vendas em aluguel.",
        "logica": {
            "titulo": "O que move o setor de shoppings",
            "texto": (
                "Shopping center é, conceitualmente, um negócio de imóvel comercial com receita variável. "
                "O dono do shopping não vende o produto — o lojista vende. "
                "O shopping cobra aluguel, que tem duas partes: uma fixa (mínimo garantido) "
                "e uma variável (percentual sobre as vendas do lojista). "
                "Quanto mais o lojista vende, mais o shopping recebe. "
                "Por isso, o crescimento de vendas dos lojistas (SSS — Same Store Sales) "
                "é o termômetro principal do setor. "
                "A grande virada pós-pandemia: shoppings deixaram de ser só lugares de compra "
                "e viraram destinos de experiência — gastronomia, lazer, academia, clínica. "
                "Isso aumenta o tempo de permanência e o ticket do consumidor."
            ),
            "drivers": [
                ("SSS — Vendas nas Mesmas Lojas: o termômetro do setor", (
                    "SSS mede o crescimento de vendas das lojas que estavam abertas no mesmo período do ano anterior. "
                    "É o indicador mais importante — afasta distorções de abertura de lojas novas. "
                    "Em 2025-2026, Allos, Multiplan cresceram 6-9% de SSS, acima da inflação. "
                    "Quando SSS cresce, o aluguel variável cresce junto — e há espaço para reajustar o fixo."
                )),
                ("IGP-M e IPCA — a indexação dos contratos", (
                    "A maioria dos contratos de aluguel de shopping é reajustada pelo IGP-M ou IPCA anualmente. "
                    "IGP-M alto = bom para o shopping (receita sobe mais); IGP-M baixo = receita cresce menos. "
                    "Em 2024, IGP-M negativo comprimiu receitas. Em 2025-2026, normalização foi positiva. "
                    "É o driver que explica por que a receita de aluguel pode crescer ou cair sem mudar o fluxo de clientes."
                )),
                ("Taxa de ocupação e custo de ocupação", (
                    "Vacância alta = aluguel médio menor + pressão para reduzir o fixo. "
                    "Allos e Multiplan operam com vacância abaixo de 5% — sinal de demanda forte por espaço. "
                    "Custo de ocupação = aluguel ÷ vendas do lojista. Abaixo de 12% é confortável. "
                    "Quando o SSS cresce, o custo de ocupação cai automaticamente — "
                    "abrindo espaço para o shopping subir o aluguel no próximo contrato."
                )),
                ("Selic e NTN-B — o risco de duration", (
                    "Shopping é um ativo de longa duração (os fluxos de caixa vêm por décadas). "
                    "Selic alta aumenta a taxa de desconto e comprime o valor presente dos fluxos — "
                    "por isso a ação de shopping cai quando os juros sobem, mesmo com resultado operacional bom. "
                    "É o mesmo efeito de uma NTN-B: quando os juros de mercado sobem, o preço cai."
                )),
                ("Mix de lojas — a transformação estrutural pós-pandemia", (
                    "O mix de lojas mudou radicalmente: vestuário caiu de 40%+ para ~32% da ABL; "
                    "alimentação subiu para 15%; serviços (academia, clínica, coworking) chegam a 24%. "
                    "Esse reposicionamento é importante porque lojas de serviço e gastronomia "
                    "têm menor risco de serem substituídas pelo e-commerce — "
                    "você não compra um corte de cabelo ou uma consulta médica online."
                )),
                ("NOI e FFO — as métricas certas para avaliar shoppings", (
                    "P/L não funciona para shoppings (depreciação distorce). "
                    "NOI (Net Operating Income) = receita de aluguel - despesas operacionais do imóvel. "
                    "FFO (Funds From Operations) = lucro + depreciação + amortização — proxy do caixa recorrente. "
                    "P/FFO é o múltiplo correto: Allos negocia ~10x, Multiplan ~12x FFO 2026."
                )),
            ],
        },
        "comparativo": {
            "dimensoes": [
                "Estratégia",
                "Portfólio",
                "Qualidade dos ativos",
                "Conversão vendas → aluguel",
                "Receita por m²",
                "Diversificação geográfica",
                "Múltiplo (P/FFO 2026)",
                "Dividendo (DY)",
                "Risco principal",
            ],
            "grupos": [
                {"label": "Shoppings listados", "tickers": ["ALOS3", "MULT3"]},
            ],
            "empresas": {
                "ALOS3": {
                    "nome": "Allos",
                    "cor": "#3B82F6",
                    "Estratégia": ("Escala e diversificação", "44 shoppings — o maior portfólio do Brasil em número de ativos"),
                    "Portfólio": ("44 shoppings (11.000+ lojas)", "maior presença nacional; mix de médio e grande porte"),
                    "Qualidade dos ativos": ("Médio-alta", "58% da receita vem de shoppings com vendas < R$1 bi/ano", "badge-yellow"),
                    "Conversão vendas → aluguel": ("9,6%", "menor que Multiplan — mais espaço para crescer ou maior dificuldade de repassar?", "badge-yellow"),
                    "Receita por m²": ("Próxima aos pares", "ABL de ~1,25 mi m²; receita de aluguel ~R$463 mi/tri"),
                    "Diversificação geográfica": ("Alta", "presente em todas as regiões — risco concentrado menor", "badge-green"),
                    "Múltiplo (P/FFO 2026)": ("~10x", "desconto vs Multiplan — reflete qualidade média do portfólio"),
                    "Dividendo (DY)": ("DY ~9% (2026E)", "recompras + dividendos; alta distribuição de FCL"),
                    "Risco principal": ("Portfólio com mais ativos de médio porte e incêndio no Tijuca (6% da receita) em 2026", ""),
                },
                "MULT3": {
                    "nome": "Multiplan",
                    "cor": "#EF4444",
                    "Estratégia": ("Qualidade e concentração", "20 shoppings — poucos, mas entre os melhores do Brasil"),
                    "Portfólio": ("20 shoppings (5.000+ lojas)", "portfólio menor, mais seletivo; dominante em cidades-chave"),
                    "Qualidade dos ativos": ("Premium", "73% do portfólio com vendas > R$1 bi/ano — o melhor índice do setor", "badge-green"),
                    "Conversão vendas → aluguel": ("10,5%", "maior do setor — poder de precificação superior justifica o prêmio de múltiplo", "badge-green"),
                    "Receita por m²": ("A mais alta do setor", "vendas/m² cresceram 10,9% em 2025 — Multiplan lidera o ranking"),
                    "Diversificação geográfica": ("Moderada", "concentrada em SP, RJ e Sul — risco geográfico maior que Allos", "badge-yellow"),
                    "Múltiplo (P/FFO 2026)": ("~12x", "prêmio justificado pela qualidade — portfólio premium com menor risco"),
                    "Dividendo (DY)": ("DY ~5-6%", "reinveste mais em expansão; dividendo menor que Allos"),
                    "Risco principal": ("Valuation esticado em cenário de Selic alta; concentração geográfica em SP/RJ", ""),
                },
            },
        },
        "perfis": {
            "ALOS3": {
                "nome": "Allos S.A.",
                "fundacao": "2019 (fusão Aliansce + Sonae Sierra Brasil; renomeada Allos em 2022)",
                "sede": "Rio de Janeiro, RJ",
                "tagline": "A maior plataforma de shoppings do Brasil em número de ativos. 44 shoppings, diversificação nacional e a Helloo como motor de receita de mídia.",
                "modelo": (
                    "A Allos nasceu da fusão entre a Aliansce Shopping Centers e a Sonae Sierra Brasil em 2019, "
                    "e foi renomeada em 2022 para refletir o reposicionamento estratégico. "
                    "Com 44 shoppings e mais de 11.000 lojas, é o maior portfólio do Brasil em número de ativos. "
                    "A estratégia é de escala e diversificação geográfica: presente em todas as regiões, "
                    "com shoppings de médio e grande porte que atendem diferentes perfis de consumidor. "
                    "Além do aluguel tradicional, a Allos tem dois vetores de crescimento adicionais: "
                    "a Helloo (plataforma de mídia em shoppings — painéis, aeroportos, mídia digital), "
                    "que cresce rápido e tem margens melhores que o aluguel; "
                    "e um pipeline de expansão via ABL incremental nos shoppings existentes. "
                    "Em 2026, o incêndio no Shopping Tijuca (janeiro) impactou ~6% da receita de aluguel "
                    "temporariamente — o ativo operou com capacidade reduzida no 1T26."
                ),
                "receita": [
                    ("Aluguel mínimo garantido", "~55%", "base fixa dos contratos de locação, reajustada por IGP-M/IPCA"),
                    ("Aluguel variável (% das vendas)", "~20%", "percentual sobre vendas dos lojistas — cresce com SSS"),
                    ("Estacionamento e serviços", "~12%", "receita de rotatividade e serviços aos lojistas"),
                    ("Helloo (mídia em shoppings e aeroportos)", "~8%", "crescimento acelerado; margens superiores ao aluguel"),
                    ("Cessão de direito e outros", "~5%", "key money e receitas imobiliárias não recorrentes"),
                ],
                "vantagens": [
                    "44 shoppings: maior diversificação geográfica do setor — nenhum ativo representa mais de 10% da receita",
                    "Helloo: plataforma de mídia em crescimento com margens superiores ao aluguel e receitas crescentes",
                    "DY de ~9% em 2026: alta distribuição de FCL atrativa para investidores de renda",
                    "Valuation com desconto (10x FFO) vs Multiplan — potencial de re-rating se qualidade do portfólio melhorar",
                    "Recompras de ações ativas: programa de buyback aumenta o FFO por ação sem crescimento operacional",
                ],
                "riscos": [
                    "Portfólio de qualidade média: 58% da receita vem de shoppings com vendas < R$1 bi/ano",
                    "Incêndio no Tijuca (jan/2026): impacto temporário mas real de ~6% da receita",
                    "Selic alta comprime o valuation: shopping é ativo de duration longa — taxa de desconto importa",
                    "Conversão de 9,6%: menor poder de precificação vs Multiplan — lojistas pagam menos por real de venda",
                    "Integração ainda em andamento: fusão de 2019 ainda sendo otimizada em sistemas e processos",
                ],
                "barreira": (
                    "44 concessões em pontos estratégicos das cidades. "
                    "Um shopping bem localizado é inreplicável — não se constrói outro no mesmo quarteirão. "
                    "O custo de construção de um shopping novo (R$500 mi a R$2 bi) e o tempo de maturação "
                    "(5-7 anos para atingir ocupação plena) criam uma barreira de entrada altíssima. "
                    "A Helloo adiciona uma barreira de rede: 44 shoppings + aeroportos criam escala de mídia "
                    "que anunciantes pagam prêmio para acessar."
                ),
            },
            "MULT3": {
                "nome": "Multiplan Empreendimentos Imobiliários",
                "fundacao": "1974 (por José Isaac Peres)",
                "sede": "Rio de Janeiro, RJ",
                "tagline": "A shopping premium do Brasil. 20 shoppings, 73% com vendas acima de R$1 bilhão — e a maior conversão de vendas em aluguel do setor. Qualidade justifica o prêmio de múltiplo.",
                "modelo": (
                    "A Multiplan foi fundada por José Isaac Peres em 1974 e construiu ao longo de 50 anos "
                    "um portfólio de 20 shoppings concentrados em localidades premium: "
                    "BarraShopping (RJ), MorumbiShopping (SP), ParkShopping (BSB), BH Shopping (MG), "
                    "entre outros. A estratégia é o oposto da Allos: poucos ativos, mas os melhores. "
                    "73% do portfólio tem vendas anuais superiores a R$1 bilhão — o melhor índice do setor. "
                    "Isso se traduz na maior conversão de vendas em aluguel: 10,5% vs 9,6% da Allos. "
                    "Em termos práticos: para cada R$100 que o lojista vende, "
                    "a Multiplan captura R$10,50 em aluguel. Esse poder de precificação vem da qualidade "
                    "— lojista que está no MorumbiShopping não tem alternativa de mesma qualidade próxima. "
                    "A Multiplan também tem um componente imobiliário relevante: "
                    "desenvolve apartamentos e escritórios no entorno dos shoppings — "
                    "o projeto de cidade completa ao redor do shopping (multimix)."
                ),
                "receita": [
                    ("Aluguel mínimo garantido", "~52%", "base fixa reajustada por IGP-DI/IPCA; portfólio premium permite mínimos maiores"),
                    ("Aluguel variável (% das vendas)", "~22%", "maior percentual variável que os pares — reflexo da qualidade do lojista"),
                    ("Estacionamento", "~13%", "alto fluxo de veículos em shoppings premium — receita relevante"),
                    ("Desenvolvimento imobiliário (multimix)", "~8%", "apartamentos e escritórios no entorno dos shoppings — ciclo mais longo"),
                    ("Cessão de direito e outros", "~5%", "key money e receitas não recorrentes"),
                ],
                "vantagens": [
                    "73% do portfólio com vendas > R$1 bi/ano: qualidade de ativo incomum — lojistas pagam prêmio para estar lá",
                    "10,5% de conversão: maior poder de precificação do setor — cada real de venda gera mais aluguel",
                    "Vendas/m² cresceram 10,9% em 2025: maior taxa de crescimento entre os pares",
                    "50 anos de track record: Multiplan construiu shoppings que viraram referência de consumo nas suas cidades",
                    "Multimix: desenvolvimento imobiliário ao redor cria ecossistema de valor que valoriza o próprio shopping",
                ],
                "riscos": [
                    "Valuation de prêmio (12x FFO): não tolera decepção — qualquer desaceleração é punida no preço",
                    "Concentração geográfica: forte em SP, RJ e Sul — recessão regional impacta mais que portfólio nacional",
                    "Selic alta é o maior inimigo: duration longa do ativo = valuation comprimido em cenário de juro alto",
                    "DY mais baixo (~5-6%): reinveste mais; para investidores de renda pura, a Allos é mais atrativa",
                    "Expansão limitada: portfólio premium tem menos oportunidades de crescimento via novos shoppings",
                ],
                "barreira": (
                    "50 anos de curadoria de localização e de mix de lojistas. "
                    "O MorumbiShopping em São Paulo ou o BarraShopping no Rio "
                    "têm listas de espera de lojistas que querem entrar. "
                    "Quando o Zara, a Apple ou a Nike quer estar em São Paulo, "
                    "o MorumbiShopping está na lista curta — e a Multiplan sabe "
                    "negociar esse poder de escassez em aluguel. "
                    "Isso é uma vantagem competitiva de marca que levou meio século para construir "
                    "e que nenhum shopping novo replica mesmo com capital infinito."
                ),
            },
        },
    },
}
