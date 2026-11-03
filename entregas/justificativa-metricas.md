# Justificativa das métricas — Dashboard 2

**Público-alvo do painel:** quem compra ou vende carro usado (pessoa física ou pequena revenda) e quer entender o mercado sem ler histogramas.

As métricas usam **mediana** em vez de média: na EDA (seção 3), `Price`, `Power_bhp` e `Kilometers_Driven` mostraram forte assimetria à direita e outliers que foram mantidos. A média seria puxada pelos poucos carros de luxo e pelas quilometragens extremas.

Todas as métricas respondem aos filtros da sidebar, aos filtros do topo do Dashboard 2 (cidade, combustível e histórico de donos) e ao clique no gráfico de marcas. Cada KPI mostra também a diferença (*delta*) em relação ao mercado inteiro (todos os 6.019 anúncios), para o público saber se o recorte está acima ou abaixo do padrão.

## Métrica 1: Preço mediano
- **Variável:** `Price` (preço do anúncio, em lakh de rúpias; 1 lakh = 100.000 ₹)
- **O que mede:** o preço "do meio" dos carros do recorte: metade custa menos, metade custa mais. Ao clicar em uma marca, mostra a diferença em relação ao recorte sem o clique.
- **Por que foi escolhida:** o preço é a variável central da EDA, e a mediana resume o valor típico sem ser distorcida pelos carros de luxo (máximo de 160 lakh contra mediana de 5,6).
- **Público-alvo:** compradores e vendedores.
- **Qual decisão pode ser apoiada por essa métrica?** Definir um preço de referência para anunciar ou negociar um carro de determinada marca, cidade ou combustível.
- **O que comunica ao público-alvo:** "um carro típico deste grupo custa cerca de X lakh", e quanto uma marca está acima ou abaixo disso.

## Métrica 2: Carros automáticos (%)
- **Variável:** `Transmission` (Manual / Automatic)
- **O que mede:** a proporção de anúncios com câmbio automático no recorte.
- **Por que foi escolhida:** na EDA (seção 6), `Transmission` é desbalanceada (predomínio do manual) e o boxplot de preço por transmissão mostrou automáticos bem mais caros. A proporção ajuda a explicar por que o preço mediano de um recorte é alto ou baixo.
- **Público-alvo:** compradores que procuram automático e revendas que montam estoque.
- **Qual decisão pode ser apoiada por essa métrica?** Avaliar se há oferta suficiente de automáticos em uma cidade ou marca antes de procurar ou investir em estoque.
- **O que comunica ao público-alvo:** "de cada 10 carros deste grupo, N são automáticos".

## Métrica 3: Idade mediana
- **Variável:** `Vehicle_Age` (idade do carro em anos, com 2019 como referência, criada na EDA)
- **O que mede:** a idade típica dos carros anunciados no recorte.
- **Por que foi escolhida:** na EDA, a idade tem correlação negativa moderada com o preço (Spearman ≈ −0,49): carros mais velhos valem menos. A idade mediana dá contexto ao preço.
- **Público-alvo:** compradores.
- **Qual decisão pode ser apoiada por essa métrica?** Comparar recortes com preços parecidos e escolher o que oferece carros mais novos.
- **O que comunica ao público-alvo:** "os carros deste grupo têm, tipicamente, N anos de uso".

## Métrica 4: Quilometragem mediana
- **Variável:** `Kilometers_Driven` (km rodados)
- **O que mede:** a quilometragem típica dos carros do recorte.
- **Por que foi escolhida:** é o indicador de desgaste mais direto para o comprador. A EDA mostrou valores extremos mantidos (até 6,5 milhões de km), por isso a mediana é usada e não a média.
- **Público-alvo:** compradores.
- **Qual decisão pode ser apoiada por essa métrica?** Saber se a quilometragem de um carro específico está acima ou abaixo do normal para o seu grupo.
- **O que comunica ao público-alvo:** "um carro típico deste grupo rodou cerca de X km".

## Visuais de apoio
- **Preço mediano por marca** (15 marcas com mais anúncios, barras verticais): ranking de preço; o clique numa barra filtra as métricas e o gráfico ao lado.
- **Anúncios por faixa de quilometragem e câmbio** (barras agrupadas): a quilometragem é discretizada em faixas (até 30 mil, 30–60 mil, 60–100 mil, 100 mil ou mais) e separada por Manual × Automático. Mostra onde está a oferta e como o automático se distribui em relação ao desgaste (relação km × transmissão da EDA).
- **Preço mediano por idade do carro** (linhas, Manual × Automático): curva de desvalorização. Mostra quanto um carro perde de valor a cada ano de uso e que o automático parte de um preço mais alto (relação idade × preço, Spearman ≈ −0,49 na EDA). Só entram idades com pelo menos 5 anúncios no recorte, para a curva não oscilar por causa de poucos carros. Também responde ao clique no gráfico de marcas.
