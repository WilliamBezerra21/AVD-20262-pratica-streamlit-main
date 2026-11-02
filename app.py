import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from src.data_loader import load_data

st.set_page_config(
    page_title="Carros Usados na Índia",
    layout="wide",
)

st.title("Análise de Carros Usados na Índia")

df = load_data()

# Variáveis quantitativas do estudo (mesma lista VARS_QUANT do notebook de EDA) e o nome exibido de cada uma
ROTULOS = {
    "Price": "Preço (lakh ₹)",
    "Vehicle_Age": "Idade (anos)",
    "Kilometers_Driven": "Quilometragem (km)",
    "Mileage_value": "Consumo (km/l)",
    "Engine_cc": "Cilindrada (cc)",
    "Power_bhp": "Potência (bhp)",
    "Seats": "Assentos",
}
VARS_QUANT = list(ROTULOS)

# Variáveis categóricas que podem colorir a distribuição
CLASSES = {
    "Transmission": "Câmbio",
    "Fuel_Type": "Combustível",
    "Owner_Type": "Nº de donos",
}


@st.cache_data
def histograma_agregado(dados: pd.DataFrame, coluna: str, classe: str | None, bins: int = 30) -> pd.DataFrame:
    """Conta os valores por faixa no pandas, para o Altair não receber milhares de linhas."""
    bordas = np.histogram_bin_edges(dados[coluna], bins=bins)
    grupos = dados.groupby(classe) if classe else [(None, dados)]
    partes = []
    for nome, grupo in grupos:
        quantidade, _ = np.histogram(grupo[coluna], bins=bordas)
        parte = pd.DataFrame({"inicio": bordas[:-1], "fim": bordas[1:], "quantidade": quantidade})
        if classe:
            parte[classe] = nome
        partes.append(parte)
    return pd.concat(partes, ignore_index=True)


# Sidebar: filtros (variáveis + intervalo)
with st.sidebar:
    st.header("Filtros")

    variaveis = st.multiselect(
        "Variáveis Quantitativas",
        options=VARS_QUANT,
        default=VARS_QUANT,
        format_func=lambda v: ROTULOS[v],
        help="Selecione as variáveis quantitativas que deseja analisar no dashboard.",
    )

    classe = st.selectbox(
        "Distinguir por",
        options=[None, *CLASSES],
        format_func=lambda c: "Nenhuma" if c is None else CLASSES[c],
        help="Colore a distribuição por uma variável categórica.",
    )

    # Um slider de intervalo para cada variável selecionada
    intervalos = {}
    for var in variaveis:
        if pd.api.types.is_integer_dtype(df[var]):
            minimo, maximo, passo = int(df[var].min()), int(df[var].max()), 1
        else:
            minimo, maximo, passo = float(df[var].min()), float(df[var].max()), 0.1
        intervalos[var] = st.slider(
            ROTULOS[var],
            min_value=minimo,
            max_value=maximo,
            value=(minimo, maximo),
            step=passo,
            key=f"intervalo_{var}",
        )

# Mantém só os carros dentro de todos os intervalos escolhidos
df_filtrado = df
for var, (inicio, fim) in intervalos.items():
    df_filtrado = df_filtrado[df_filtrado[var].between(inicio, fim)]

st.caption(f"{len(df_filtrado)} de {len(df)} carros dentro dos intervalos escolhidos.")

if df_filtrado.empty:
    st.warning("Nenhum carro dentro dos intervalos escolhidos. Amplie os filtros.")
    st.stop()

tab_dash1, tab_dash2 = st.tabs(["Dashboard 1 — Correlação e Distribuição", "Dashboard 2 — KPIs"])

# Dashboard 1: correlação (heatmap) à esquerda, distribuição (histograma) à direita
with tab_dash1:
    col_correlacao, col_distribuicao = st.columns([1, 1.5])

    with col_correlacao:
        st.subheader("Correlação (Spearman)")

        if len(variaveis) < 2:
            st.warning("Selecione pelo menos 2 variáveis para calcular a correlação.")
        else:
            # Spearman, como na EDA: preço, potência e quilometragem são assimétricos e têm
            # outliers (mantidos), e a correlação por postos é mais robusta que a de Pearson
            correlacao = df_filtrado[variaveis].corr(method="spearman").rename(index=ROTULOS, columns=ROTULOS)
            correlacao_longa = correlacao.reset_index(names="var_x").melt(
                id_vars="var_x", var_name="var_y", value_name="correlacao"
            )
            ordem = [ROTULOS[v] for v in variaveis]

            base = alt.Chart(correlacao_longa).encode(
                x=alt.X("var_x:N", sort=ordem, title=None, axis=alt.Axis(labelAngle=-45)),
                y=alt.Y("var_y:N", sort=ordem, title=None),
            )
            celulas = base.mark_rect().encode(
                color=alt.Color(
                    "correlacao:Q",
                    scale=alt.Scale(scheme="redblue", domain=[-1, 1], reverse=True),
                    title="ρ",
                ),
                tooltip=[
                    alt.Tooltip("var_x:N", title="Variável 1"),
                    alt.Tooltip("var_y:N", title="Variável 2"),
                    alt.Tooltip("correlacao:Q", title="Correlação", format=".2f"),
                ],
            )
            textos = base.mark_text(fontSize=12).encode(
                text=alt.Text("correlacao:Q", format=".2f"),
                color=alt.condition(
                    "abs(datum.correlacao) > 0.6", alt.value("white"), alt.value("black")
                ),
            )
            st.altair_chart((celulas + textos).properties(height=420), width="stretch")

    with col_distribuicao:
        st.subheader("Distribuição")

        if not variaveis:
            st.warning("Selecione pelo menos 1 variável na barra lateral.")
        else:
            var_hist = st.selectbox(
                "Variável do histograma",
                options=variaveis,
                format_func=lambda v: ROTULOS[v],
            )
            if df_filtrado[var_hist].nunique() < 2:
                st.info("O intervalo escolhido tem um único valor; não há distribuição para mostrar.")
            else:
                contagem = histograma_agregado(df_filtrado, var_hist, classe)

                histograma = alt.Chart(contagem).mark_bar(opacity=0.8).encode(
                    x=alt.X("inicio:Q", bin="binned", title=ROTULOS[var_hist]),
                    x2="fim:Q",
                    y=alt.Y("quantidade:Q", title="Quantidade de carros", stack=bool(classe)),
                    tooltip=[
                        alt.Tooltip("inicio:Q", title="De", format=",.1f"),
                        alt.Tooltip("fim:Q", title="Até", format=",.1f"),
                        alt.Tooltip("quantidade:Q", title="Carros"),
                    ],
                )
                if classe:
                    histograma = histograma.encode(
                        color=alt.Color(f"{classe}:N", title=CLASSES[classe]),
                        tooltip=[
                            alt.Tooltip(f"{classe}:N", title=CLASSES[classe]),
                            alt.Tooltip("inicio:Q", title="De", format=",.1f"),
                            alt.Tooltip("fim:Q", title="Até", format=",.1f"),
                            alt.Tooltip("quantidade:Q", title="Carros"),
                        ],
                    )
                st.altair_chart(histograma.properties(height=420), width="stretch")

                serie = df_filtrado[var_hist]
                c1, c2, c3 = st.columns(3)
                c1.metric("Média", f"{serie.mean():,.1f}")
                c2.metric("Mediana", f"{serie.median():,.1f}")
                c3.metric("Desvio padrão", f"{serie.std():,.1f}")

# Dashboard 2: widgets no topo → KPIs → gráficos ligados por clique (cross-filter)
# As métricas usam mediana porque preço, potência e quilometragem são assimétricos (ver EDA)
with tab_dash2:
    st.subheader("Painel do Mercado de Carros Usados")

    # Widgets do Dashboard 2 (combinam com os filtros da sidebar)
    w_cidade, w_combustivel, w_cambio = st.columns(3)
    cidades = w_cidade.multiselect(
        "Cidade", options=sorted(df_filtrado["Location"].unique()), placeholder="Todas"
    )
    combustiveis = w_combustivel.multiselect(
        "Combustível", options=sorted(df_filtrado["Fuel_Type"].unique()), placeholder="Todos"
    )
    cambios = w_cambio.multiselect(
        "Câmbio", options=sorted(df_filtrado["Transmission"].unique()), placeholder="Todos"
    )

    df_d2 = df_filtrado
    for coluna, escolhidos in [("Location", cidades), ("Fuel_Type", combustiveis), ("Transmission", cambios)]:
        if escolhidos:
            df_d2 = df_d2[df_d2[coluna].isin(escolhidos)]

    if df_d2.empty:
        st.warning("Nenhum carro para essa combinação de filtros.")
    else:
        # Gráfico de marcas: o clique numa barra filtra os KPIs e os outros gráficos
        top_marcas = df_d2["Brand"].value_counts().head(15).index
        por_marca = (
            df_d2[df_d2["Brand"].isin(top_marcas)]
            .groupby("Brand")
            .agg(preco_mediano=("Price", "median"), anuncios=("Price", "size"))
            .reset_index()
        )
        clique_marca = alt.selection_point(name="marca", fields=["Brand"])
        grafico_marcas = (
            alt.Chart(por_marca)
            .mark_bar()
            .encode(
                x=alt.X("preco_mediano:Q", title="Preço mediano (lakh ₹)"),
                y=alt.Y("Brand:N", sort="-x", title=None),
                opacity=alt.condition(clique_marca, alt.value(1), alt.value(0.3)),
                tooltip=[
                    alt.Tooltip("Brand:N", title="Marca"),
                    alt.Tooltip("preco_mediano:Q", title="Preço mediano", format=".2f"),
                    alt.Tooltip("anuncios:Q", title="Anúncios"),
                ],
            )
            .add_params(clique_marca)
            .properties(height=420)
        )

        # Lê as marcas clicadas antes de desenhar os KPIs (o gráfico é exibido mais abaixo)
        marcas = [item["Brand"] for item in st.session_state.get("grafico_marcas", {}).get("selection", {}).get("marca", [])]
        selecionado = df_d2[df_d2["Brand"].isin(marcas)] if marcas else df_d2

        if marcas:
            st.caption(f"Marcas selecionadas no gráfico: {', '.join(marcas)}. Clique fora das barras para limpar.")

        # KPIs, com a diferença em relação ao recorte sem o clique
        k1, k2, k3, k4 = st.columns(4)
        preco = selecionado["Price"].median()
        k1.metric(
            "Preço mediano",
            f"{preco:.2f} lakh",
            delta=f"{preco - df_d2['Price'].median():+.2f} vs. recorte" if marcas else None,
            delta_color="off",
            border=True,
        )
        k2.metric(
            "Carros automáticos",
            f"{(selecionado['Transmission'] == 'Automatic').mean():.0%}",
            border=True,
        )
        k3.metric("Idade mediana", f"{selecionado['Vehicle_Age'].median():.0f} anos", border=True)
        k4.metric(
            "Quilometragem mediana",
            f"{selecionado['Kilometers_Driven'].median():,.0f} km".replace(",", "."),
            border=True,
        )
        st.caption(f"{len(selecionado)} anúncios no recorte.")

        col_marcas, col_idade = st.columns([1, 1.3])

        with col_marcas:
            st.markdown("**Preço mediano por marca** (15 marcas com mais anúncios)")
            st.altair_chart(grafico_marcas, key="grafico_marcas", on_select="rerun", width="stretch")

        with col_idade:
            st.markdown("**Desvalorização: preço mediano por idade do carro**")
            por_idade = (
                selecionado.groupby(["Vehicle_Age", "Transmission"])
                .agg(preco_mediano=("Price", "median"), anuncios=("Price", "size"))
                .reset_index()
            )
            grafico_idade = (
                alt.Chart(por_idade)
                .mark_line(point=True)
                .encode(
                    x=alt.X("Vehicle_Age:Q", title="Idade (anos)"),
                    y=alt.Y("preco_mediano:Q", title="Preço mediano (lakh ₹)"),
                    color=alt.Color("Transmission:N", title="Câmbio"),
                    tooltip=[
                        alt.Tooltip("Vehicle_Age:Q", title="Idade"),
                        alt.Tooltip("Transmission:N", title="Câmbio"),
                        alt.Tooltip("preco_mediano:Q", title="Preço mediano", format=".2f"),
                        alt.Tooltip("anuncios:Q", title="Anúncios"),
                    ],
                )
                .properties(height=420)
            )
            st.altair_chart(grafico_idade, width="stretch")

        st.markdown("**Anúncios por cidade e combustível**")
        por_cidade = selecionado.groupby(["Location", "Fuel_Type"]).size().reset_index(name="anuncios")
        grafico_cidades = (
            alt.Chart(por_cidade)
            .mark_bar()
            .encode(
                x=alt.X("Location:N", sort="-y", title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("anuncios:Q", title="Anúncios"),
                color=alt.Color("Fuel_Type:N", title="Combustível"),
                tooltip=[
                    alt.Tooltip("Location:N", title="Cidade"),
                    alt.Tooltip("Fuel_Type:N", title="Combustível"),
                    alt.Tooltip("anuncios:Q", title="Anúncios"),
                ],
            )
            .properties(height=320)
        )
        st.altair_chart(grafico_cidades, width="stretch")
