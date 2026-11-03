import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from src.data_loader import load_data

st.set_page_config(
    page_title="Carros Usados na Índia — Dashboards",
    layout="wide",
)

st.title("Análise Exploratória e de Mercado — Carros Usados na Índia")

df = load_data()

# Variáveis quantitativas do estudo (mesma lista VARS_QUANT do notebook de EDA)
VARS_QUANT = [
    "Price",
    "Vehicle_Age",
    "Kilometers_Driven",
    "Mileage_value",
    "Engine_cc",
    "Power_bhp",
    "Seats",
]

ROTULOS_CURTOS = {
    "Price": "Preço (lakh ₹)",
    "Vehicle_Age": "Idade (anos)",
    "Kilometers_Driven": "Quilometragem (km)",
    "Mileage_value": "Consumo (km/l)",
    "Engine_cc": "Cilindrada (cc)",
    "Power_bhp": "Potência (bhp)",
    "Seats": "Assentos",
}

# Classe binária usada para colorir os gráficos: o câmbio (Manual x Automático)
COR_MANUAL = "#e9d4d0"
COR_AUTOMATICO = "#2d223a"
COR_PADRAO = "#c84b31"
CORES_CLASSE = alt.Scale(domain=["Manual", "Automatic"], range=[COR_MANUAL, COR_AUTOMATICO])


# Pré-agrega os intervalos do histograma no pandas (o Altair tem limite de 5.000 linhas)
@st.cache_data
def calcular_histograma_agregado(dados: pd.DataFrame, coluna: str, por_classe: bool, bins: int = 24) -> pd.DataFrame:
    """Conta os carros por faixa no pandas, para o Altair não receber milhares de linhas."""
    serie = dados[coluna].dropna()
    if serie.empty:
        return pd.DataFrame()
    cortes = np.linspace(float(serie.min()), float(serie.max()), bins + 1)
    if cortes[0] == cortes[-1]:
        cortes[-1] = cortes[0] + 1.0
    indices = np.clip(np.digitize(dados[coluna], cortes, right=True) - 1, 0, bins - 1)
    aux = pd.DataFrame({
        "bin_ini": cortes[indices],
        "bin_fim": cortes[indices + 1],
        "Transmission": dados["Transmission"].values,
    })
    cols_grupo = ["bin_ini", "bin_fim", "Transmission"] if por_classe else ["bin_ini", "bin_fim"]
    return aux.groupby(cols_grupo, as_index=False).size().rename(columns={"size": "contagem"})


# Sidebar: filtros globais de variáveis quantitativas e intervalos
with st.sidebar:
    st.header("Filtros — Variáveis Quantitativas")

    variaveis = st.multiselect(
        "Variáveis Quantitativas",
        options=VARS_QUANT,
        default=VARS_QUANT,
        format_func=lambda v: ROTULOS_CURTOS.get(v, v),
        help="Selecione as variáveis quantitativas que deseja analisar no Dashboard 1.",
    )

    separar_por_classe = st.toggle(
        "Distinguir por Câmbio",
        value=False,
        help="Colore a distribuição pelo câmbio (Manual ou Automático).",
    )

    intervalos = {}
    for var in variaveis:
        if pd.api.types.is_integer_dtype(df[var]):
            minimo, maximo, passo = int(df[var].min()), int(df[var].max()), 1
        else:
            minimo, maximo, passo = float(df[var].min()), float(df[var].max()), 0.1
        intervalos[var] = st.slider(
            f"Intervalo de {ROTULOS_CURTOS.get(var, var)}",
            min_value=minimo,
            max_value=maximo,
            value=(minimo, maximo),
            step=passo,
            key=f"intervalo_{var}",
        )

# Aplica os filtros de intervalo da sidebar
df_filtrado = df
for var, (inicio, fim) in intervalos.items():
    df_filtrado = df_filtrado[df_filtrado[var].between(inicio, fim)]

st.caption(
    f"{len(df_filtrado):,} de {len(df):,} carros dentro dos intervalos selecionados na barra lateral.".replace(",", ".")
)

# Abas separando Dashboard 1 e Dashboard 2
tab_dash1, tab_dash2 = st.tabs([
    "Dashboard 1 — Correlação e Distribuição",
    "Dashboard 2 — KPIs do Mercado",
])

# =========================================================================
# ABA 1: DASHBOARD 1 (Correlação de Spearman + Distribuição em Altair)
# =========================================================================
with tab_dash1:
    col_correlacao, col_distribuicao = st.columns([1.1, 1.2], gap="large")

    with col_correlacao:
        st.subheader("Correlação (Spearman)")

        if len(variaveis) < 2:
            st.warning("Selecione pelo menos 2 variáveis para calcular a correlação.")
        elif len(df_filtrado) < 30:
            st.warning("Poucos carros nos intervalos escolhidos para calcular a correlação.")
        else:
            # Spearman, como na EDA: preço, potência e quilometragem são assimétricos e têm outliers.
            # Mostra só o triângulo inferior da matriz (sem a diagonal e sem repetir pares).
            corr = (
                df_filtrado[variaveis]
                .corr(method="spearman")
                .rename_axis(index="var_y", columns="var_x")
                .stack()
                .rename("correlacao")
                .reset_index()
            )
            ordem = {var: i for i, var in enumerate(variaveis)}
            corr = corr[corr["var_y"].map(ordem) > corr["var_x"].map(ordem)].copy()
            corr["label_x"] = corr["var_x"].map(ROTULOS_CURTOS)
            corr["label_y"] = corr["var_y"].map(ROTULOS_CURTOS)
            ordem_x = [ROTULOS_CURTOS[v] for v in variaveis[:-1]]
            ordem_y = [ROTULOS_CURTOS[v] for v in variaveis[1:]]

            base = alt.Chart(corr).encode(
                x=alt.X("label_x:N", title=None, sort=ordem_x, axis=alt.Axis(labelAngle=-35, labelFontSize=11)),
                y=alt.Y("label_y:N", title=None, sort=ordem_y, axis=alt.Axis(labelFontSize=11)),
            )
            heatmap = base.mark_rect().encode(
                color=alt.Color(
                    "correlacao:Q",
                    title="Spearman (r)",
                    scale=alt.Scale(scheme="redblue", domain=[-1, 1], reverse=True),
                ),
                tooltip=[
                    alt.Tooltip("label_y:N", title="Variável Y"),
                    alt.Tooltip("label_x:N", title="Variável X"),
                    alt.Tooltip("correlacao:Q", title="Correlação (r)", format=".2f"),
                ],
            )
            valores = base.mark_text(fontSize=13).encode(
                text=alt.Text("correlacao:Q", format=".2f"),
                color=alt.condition("abs(datum.correlacao) > 0.5", alt.value("white"), alt.value("black")),
            )

            st.altair_chart(
                (heatmap + valores).properties(height=470),
                width="stretch",
            )

    with col_distribuicao:
        st.subheader("Distribuição")

        if not variaveis:
            st.warning("Selecione pelo menos 1 variável para ver a distribuição.")
        elif df_filtrado.empty:
            st.warning("Nenhum carro dentro dos intervalos escolhidos.")
        else:
            var_hist = st.selectbox(
                "Variável para o histograma",
                options=variaveis,
                format_func=lambda v: ROTULOS_CURTOS.get(v, v),
                help="Escolha a variável quantitativa cuja distribuição será exibida.",
            )

            df_bins = calcular_histograma_agregado(df_filtrado, var_hist, separar_por_classe, bins=24)

            histograma = (
                alt.Chart(df_bins)
                .mark_bar(opacity=0.85)
                .encode(
                    x=alt.X("bin_ini:Q", bin="binned", title=ROTULOS_CURTOS[var_hist]),
                    x2="bin_fim:Q",
                    y=alt.Y("contagem:Q", title="Quantidade de Carros"),
                )
                .properties(height=400)
            )
            if separar_por_classe:
                histograma = histograma.encode(
                    color=alt.Color("Transmission:N", title="Câmbio", scale=CORES_CLASSE),
                    tooltip=[
                        alt.Tooltip("Transmission:N", title="Câmbio"),
                        alt.Tooltip("bin_ini:Q", title="Intervalo inicial", format=",.1f"),
                        alt.Tooltip("bin_fim:Q", title="Intervalo final", format=",.1f"),
                        alt.Tooltip("contagem:Q", title="Carros", format=","),
                    ],
                )
            else:
                histograma = histograma.mark_bar(color=COR_PADRAO).encode(
                    tooltip=[
                        alt.Tooltip("bin_ini:Q", title="Intervalo inicial", format=",.1f"),
                        alt.Tooltip("bin_fim:Q", title="Intervalo final", format=",.1f"),
                        alt.Tooltip("contagem:Q", title="Carros", format=","),
                    ]
                )

            st.altair_chart(histograma, width="stretch")

    # Um histograma para cada variável quantitativa selecionada na sidebar
    if variaveis and not df_filtrado.empty:
        st.subheader("Histogramas de Todas as Variáveis Selecionadas")
        grade = st.columns(3, gap="medium")
        for i, var in enumerate(variaveis):
            bins_var = calcular_histograma_agregado(df_filtrado, var, separar_por_classe, bins=20)
            mini = (
                alt.Chart(bins_var)
                .mark_bar(opacity=0.85)
                .encode(
                    x=alt.X("bin_ini:Q", bin="binned", title=ROTULOS_CURTOS[var]),
                    x2="bin_fim:Q",
                    y=alt.Y("contagem:Q", title="Carros"),
                    tooltip=[
                        alt.Tooltip("bin_ini:Q", title="De", format=",.1f"),
                        alt.Tooltip("bin_fim:Q", title="Até", format=",.1f"),
                        alt.Tooltip("contagem:Q", title="Carros", format=","),
                    ],
                )
                .properties(height=220)
            )
            if separar_por_classe:
                mini = mini.encode(color=alt.Color("Transmission:N", title="Câmbio", scale=CORES_CLASSE))
            else:
                mini = mini.mark_bar(color=COR_PADRAO)
            with grade[i % 3]:
                st.altair_chart(mini, width="stretch")

# =========================================================================
# ABA 2: DASHBOARD 2 (KPIs + Gráficos de Barras com Cross-Filter)
# As métricas usam mediana porque preço e quilometragem são assimétricos (ver EDA)
# =========================================================================
with tab_dash2:
    st.subheader("Painel de Indicadores do Mercado (KPIs)")

    # Controles dedicados do Dashboard 2
    f_col1, f_col2, f_col3 = st.columns([1.3, 1.3, 1])

    opcoes_cidades = sorted(df["Location"].dropna().unique().tolist())
    opcoes_combustivel = sorted(df["Fuel_Type"].dropna().unique().tolist())

    with f_col1:
        cidades_filtro = st.multiselect(
            "Cidade (Location)",
            options=opcoes_cidades,
            default=opcoes_cidades,
            key="d2_cidades",
        )
    with f_col2:
        combustivel_filtro = st.multiselect(
            "Combustível (Fuel_Type)",
            options=opcoes_combustivel,
            default=opcoes_combustivel,
            key="d2_combustivel",
        )
    with f_col3:
        filtro_dono = st.selectbox(
            "Histórico de Donos (Owner_Type)",
            options=["Todos", "Apenas 1º dono", "2 donos ou mais"],
            index=0,
            key="d2_dono",
        )

    df_d2 = df_filtrado[
        df_filtrado["Location"].isin(cidades_filtro) & df_filtrado["Fuel_Type"].isin(combustivel_filtro)
    ]
    if filtro_dono == "Apenas 1º dono":
        df_d2 = df_d2[df_d2["Owner_Type"] == "First"]
    elif filtro_dono == "2 donos ou mais":
        df_d2 = df_d2[df_d2["Owner_Type"] != "First"]

    if df_d2.empty:
        st.warning("Nenhum carro encontrado para os filtros selecionados no Dashboard 2.")
    else:
        # Agregação por marca (15 marcas com mais anúncios) para o gráfico com seleção cruzada
        top_marcas = df_d2["Brand"].value_counts().head(15).index
        resumo_marca = (
            df_d2[df_d2["Brand"].isin(top_marcas)]
            .groupby("Brand", as_index=False)
            .agg(
                anuncios=("Price", "size"),
                preco_mediano=("Price", "median"),
                pct_automatico=("Transmission", lambda s: (s == "Automatic").mean() * 100),
            )
            .sort_values("preco_mediano", ascending=False)
        )

        selecao_marca = alt.selection_point(name="selecao_marca", fields=["Brand"])

        grafico_barras_marca = (
            alt.Chart(resumo_marca)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("Brand:N", sort="-y", title="Marca", axis=alt.Axis(labelAngle=-35)),
                y=alt.Y("preco_mediano:Q", title="Preço Mediano (lakh ₹)"),
                color=alt.condition(
                    selecao_marca,
                    alt.Color("preco_mediano:Q", title="Preço (lakh)", scale=alt.Scale(scheme="orangered")),
                    alt.value("#d5d1cd"),
                ),
                opacity=alt.condition(selecao_marca, alt.value(1.0), alt.value(0.45)),
                tooltip=[
                    alt.Tooltip("Brand:N", title="Marca"),
                    alt.Tooltip("preco_mediano:Q", title="Preço Mediano (lakh)", format=".2f"),
                    alt.Tooltip("pct_automatico:Q", title="Automáticos (%)", format=".1f"),
                    alt.Tooltip("anuncios:Q", title="Anúncios", format=","),
                ],
            )
            .add_params(selecao_marca)
            .properties(height=360, title="Preço Mediano por Marca (clique em uma barra para filtrar)")
        )

        # Container para os KPIs no topo (preenchido depois de ler o clique no gráfico abaixo)
        container_kpis = st.container()

        st.markdown("#### Preço por Marca e Quilometragem por Câmbio")
        g_col1, g_col2 = st.columns([1.1, 1.1], gap="large")

        with g_col1:
            evento_marca = st.altair_chart(
                grafico_barras_marca,
                key="chart_barras_marca",
                on_select="rerun",
                width="stretch",
            )

        # Marcas clicadas no gráfico de barras
        itens_clicados = []
        if evento_marca and hasattr(evento_marca, "selection"):
            itens_clicados = evento_marca.selection.get("selecao_marca", [])
        marcas_selecionadas = [item["Brand"] for item in itens_clicados if "Brand" in item]

        df_kpis = df_d2[df_d2["Brand"].isin(marcas_selecionadas)] if marcas_selecionadas else df_d2

        # Referências do mercado inteiro (para o delta comparativo)
        preco_base = df["Price"].median()
        auto_base = (df["Transmission"] == "Automatic").mean() * 100
        idade_base = df["Vehicle_Age"].median()
        km_base = df["Kilometers_Driven"].median()

        # As 4 métricas sobre o recorte ativo (df_kpis)
        preco = df_kpis["Price"].median()
        pct_auto = (df_kpis["Transmission"] == "Automatic").mean() * 100
        idade = df_kpis["Vehicle_Age"].median()
        km = df_kpis["Kilometers_Driven"].median()

        with container_kpis:
            if marcas_selecionadas:
                st.info(
                    f"Filtro interativo ativo no gráfico: **{', '.join(marcas_selecionadas)}** "
                    f"({len(df_kpis):,} carros). Clique em uma área vazia do gráfico para limpar.".replace(",", ".")
                )

            k1, k2, k3, k4 = st.columns(4, gap="small")
            k1.metric(
                "Preço Mediano",
                f"{preco:.2f} lakh",
                delta=f"{preco - preco_base:+.2f} lakh vs mercado",
                delta_color="off",
                border=True,
                help="Preço do meio dos carros do recorte (Price, em lakh ₹; 1 lakh = 100.000 ₹).",
            )
            k2.metric(
                "Carros Automáticos",
                f"{pct_auto:.1f}%",
                delta=f"{pct_auto - auto_base:+.1f} p.p. vs mercado",
                delta_color="off",
                border=True,
                help="Proporção de anúncios com câmbio automático (Transmission == Automatic).",
            )
            k3.metric(
                "Idade Mediana",
                f"{idade:.0f} anos",
                delta=f"{idade - idade_base:+.0f} anos vs mercado",
                delta_color="inverse",
                border=True,
                help="Idade típica dos carros do recorte (Vehicle_Age, referência 2019).",
            )
            k4.metric(
                "Quilometragem Mediana",
                f"{km:,.0f} km".replace(",", "."),
                delta=f"{km - km_base:+,.0f} km vs mercado".replace(",", "."),
                delta_color="inverse",
                border=True,
                help="Quilometragem típica dos carros do recorte (Kilometers_Driven).",
            )

        with g_col2:
            # Discretização da quilometragem combinada com o câmbio
            ordem_faixas = ["Até 30 mil", "30–60 mil", "60–100 mil", "100 mil ou mais"]
            faixas = pd.cut(
                df_kpis["Kilometers_Driven"],
                bins=[-1, 30_000, 60_000, 100_000, float("inf")],
                labels=ordem_faixas,
            )
            resumo_km = (
                df_kpis.assign(faixa_km=faixas)
                .groupby(["faixa_km", "Transmission"], observed=True, as_index=False)
                .agg(anuncios=("Price", "size"), preco_mediano=("Price", "median"))
            )

            grafico_km = (
                alt.Chart(resumo_km)
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("faixa_km:N", sort=ordem_faixas, title="Faixa de Quilometragem", axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("anuncios:Q", title="Quantidade de Anúncios"),
                    color=alt.Color("Transmission:N", title="Câmbio", scale=CORES_CLASSE),
                    xOffset="Transmission:N",
                    tooltip=[
                        alt.Tooltip("faixa_km:N", title="Quilometragem"),
                        alt.Tooltip("Transmission:N", title="Câmbio"),
                        alt.Tooltip("anuncios:Q", title="Anúncios", format=","),
                        alt.Tooltip("preco_mediano:Q", title="Preço Mediano (lakh)", format=".2f"),
                    ],
                )
                .properties(height=360, title="Anúncios por Faixa de Quilometragem e Câmbio")
            )
            st.altair_chart(grafico_km, width="stretch")

        # Visual 3: como o preço cai com a idade, separado por câmbio (relação idade × preço da EDA)
        st.markdown("#### Desvalorização com a Idade")
        resumo_idade = (
            df_kpis.groupby(["Vehicle_Age", "Transmission"], as_index=False)
            .agg(anuncios=("Price", "size"), preco_mediano=("Price", "median"))
        )
        resumo_idade = resumo_idade[resumo_idade["anuncios"] >= 5]  # evita pontos com poucos anúncios

        grafico_idade = (
            alt.Chart(resumo_idade)
            .mark_line(point=True, strokeWidth=2.5)
            .encode(
                x=alt.X("Vehicle_Age:Q", title="Idade do Carro (anos)", axis=alt.Axis(tickMinStep=1)),
                y=alt.Y("preco_mediano:Q", title="Preço Mediano (lakh ₹)"),
                color=alt.Color(
                    "Transmission:N",
                    title="Câmbio",
                    scale=alt.Scale(domain=["Manual", "Automatic"], range=[COR_PADRAO, COR_AUTOMATICO]),
                ),
                tooltip=[
                    alt.Tooltip("Vehicle_Age:Q", title="Idade (anos)"),
                    alt.Tooltip("Transmission:N", title="Câmbio"),
                    alt.Tooltip("preco_mediano:Q", title="Preço Mediano (lakh)", format=".2f"),
                    alt.Tooltip("anuncios:Q", title="Anúncios", format=","),
                ],
            )
            .properties(height=320, title="Preço Mediano por Idade do Carro (Manual × Automático)")
        )
        if resumo_idade.empty:
            st.info("Poucos anúncios no recorte para traçar a curva de desvalorização.")
        else:
            st.altair_chart(grafico_idade, width="stretch")
