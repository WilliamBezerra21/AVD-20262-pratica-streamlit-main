# Declaração de Uso de IA

**Nome:** William de Souza Bezerra
**Data:** 02/11/2026

## Ferramenta

- **Claude Code** (modelo Claude Opus 5.5, Anthropic): construção do app Streamlit (Aulas 21 a 23).
- **ChatGPT**: apoio na EDA da Aula 11 (declarado no próprio `notebooks/eda.ipynb`).

## Prompt usado

Conversa em sequência no Claude Code, na raiz do projeto:

1. "quero que você leia todos os arquivos e me responda uma coisa, consegue ler repositórios de github?"
2. "aqui o path e leia e me explique o que fazer com base nesse repositório: https://github.com/Lucasmenezes08/AVD-20262-pratica-streamlit" (repositório de outro aluno, usado só como referência da estrutura da atividade; nenhum código ou texto dele foi copiado)
3. "eu tenho um dataset aqui: https://www.kaggle.com/code/ceydalgz/car-dataset/notebook"
4. "sim, pode seguir"
5. "o que falta agora"
6. "o notebook foi baixado agora, ele está em downloads" (EDA da Aula 11)
7. "não teria como você fazer tudo isso para mim?"

## O que foi aceito, modificado ou rejeitado e por quê

- **Aceito:**
  - `notebooks/tratamento-carros.ipynb`, que reproduz as decisões de tratamento da minha EDA e exporta `data/clean/dataset.csv`.
  - `app.py`: sidebar com seletor de variáveis e sliders de intervalo; Dashboard 1 (heatmap de correlação de Spearman e histograma em Altair, com opção de colorir por câmbio, combustível ou nº de donos); Dashboard 2 (filtros de cidade, combustível e câmbio, quatro KPIs com `st.metric` e gráficos Altair com cross-filter pelo clique na marca).
  - `@st.cache_data` no `src/data_loader.py` e o tema em `.streamlit/config.toml`.
  - Rascunho do texto de `entregas/justificativa-metricas.md`, revisado por mim.
- **Modificado:**
  - O primeiro tratamento proposto pela IA removia outliers de quilometragem e linhas com valores ausentes. Foi refeito para seguir as decisões da minha EDA: outliers mantidos, imputação pela mediana e os mesmos nomes de colunas e a mesma lista `VARS_QUANT`.
- **Rejeitado:**
  - Gerar os rascunhos de layout por IA: os rascunhos em `entregas/` foram desenhados por mim.

<!-- Revise e ajuste esta declaração com as suas próprias palavras antes de entregar. -->
