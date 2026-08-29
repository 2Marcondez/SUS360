import os
import pandas as pd
import plotly.express as px
import streamlit as st

# =============================================================================
# CONFIGURAÇÃO E CONSTANTES
# =============================================================================

st.set_page_config(page_title="SUS360 - Pressão Hospitalar", layout="wide")

# 1. APONTANDO PARA A CAMADA GOLD
DATA_PATH = os.path.join("dados", "gold_hospital_clusters_2022_2025.csv")
LOGO_PATH = os.path.join("imgs", "logo.png")

MONTH_TO_NUM = {
    'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4,
    'Maio': 5, 'Junho': 6, 'Julho': 7, 'Agosto': 8,
    'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12
}
NUM_TO_MONTH = {v: k for k, v in MONTH_TO_NUM.items()}

MAP_COLOR_SCALE = ["#00b050", "#ffc000", "#ff0000"]
MAP_CENTER = {"lat": -22.5, "lon": -46.0}

 
# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def format_number(value: float) -> str:
    return f"{value:,.0f}".replace(",", "_").replace(".", ",").replace("_", ".")


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df = df[df['total_leitos'] > 0].copy()

    df['descricao_esfera_administrativa'] = (
        df['descricao_esfera_administrativa'].fillna('Não Informado')
    )
    
    if 'Cluster' not in df.columns:
        df['Cluster'] = "Sem Perfil Classificado"

    df['taxa_ocupacao'] = (
        (df['total_internacoes'] * df['permanencia_media_dias'])
        / (df['total_leitos'] * 30)
    )
    df['taxa_ocupacao'] = df['taxa_ocupacao'].clip(upper=2.0)

    return df


def get_previous_period(year: int, month: str) -> tuple[int, str]:
    month_num = MONTH_TO_NUM[month]
    if month_num > 1:
        return year, NUM_TO_MONTH[month_num - 1]
    return year - 1, NUM_TO_MONTH[12]


def apply_filters(
    df: pd.DataFrame,
    year: int,
    ufs: list[str],
    esferas: list[str],
    perfis: list[str],
    month: str | None = None,
) -> pd.DataFrame:
    
    mask = (
        (df['ano'] == year)
        & (df['sigla_uf'].isin(ufs))
        & (df['descricao_esfera_administrativa'].isin(esferas))
        & (df['Cluster'].isin(perfis))
    )
    if month is not None:
        mask &= (df['mes'] == month)
    return df[mask].copy()


def apply_search_filters(df: pd.DataFrame, cnes_query: str, name_query: str) -> pd.DataFrame:
    if cnes_query:
        df = df[
            df['id_estabelecimento_cnes'].astype(str)
            .str.contains(cnes_query, case=False, na=False)
        ]
    if name_query:
        df = df[df['nome_fantasia'].str.contains(name_query, case=False, na=False)]
    return df


def render_sidebar(df: pd.DataFrame) -> dict:
    st.sidebar.image(LOGO_PATH, width=250)
    st.sidebar.title("Filtros SUS360")

    year = st.sidebar.selectbox("Selecione o Ano", df['ano'].sort_values().unique())

    months_sorted = sorted(df['mes'].unique(), key=lambda m: MONTH_TO_NUM.get(m, 99))
    month = st.sidebar.selectbox("Selecione o Mês", months_sorted)

    ufs = st.sidebar.multiselect(
        "Filtrar por Estado", df['sigla_uf'].unique(), default=df['sigla_uf'].unique()
    )

    esferas_disponiveis = sorted(df['descricao_esfera_administrativa'].unique())
    esferas = st.sidebar.multiselect(
        "Esfera Administrativa", esferas_disponiveis, default=esferas_disponiveis
    )

    perfis_disponiveis = sorted(df['Cluster'].dropna().unique())
    perfis = st.sidebar.multiselect(
        "Cluster", perfis_disponiveis, default=perfis_disponiveis
    )

    st.sidebar.divider()
    with st.sidebar.expander("Filtros Avançados (Opcionais)"):
        cnes_query = st.text_input("Filtrar por ID CNES:", "")
        name_query = st.text_input("Filtrar por Nome do Hospital:", "")

    return {
        "year": year,
        "month": month,
        "ufs": ufs,
        "esferas": esferas,
        "perfis": perfis,
        "cnes_query": cnes_query,
        "name_query": name_query,
    }


def render_kpi_card(column, label: str, value: str, delta: str | None = None,
                    delta_color: str = "gray", extra_lines: list[str] | None = None) -> None:
 
    display_text = delta if delta else "_"
    text_color = delta_color if delta else "transparent"
    
    delta_html = f'<div style="font-size: 13px; color: {text_color}; margin-top: 2px; margin-bottom: 10px;">{display_text}</div>'
    
    column.markdown(
        f"""
        <div style="font-size: 14px; color: gray; margin-bottom: -10px;">{label}</div>
        <div style="font-size: 36px; font-weight: bold; line-height: 1.2;">{value}</div>
        {delta_html}
        """,
        unsafe_allow_html=True,
    )
    
    if extra_lines:
        with column.expander("Ver detalhamento por UF"):
            extra_html = "".join(
                f"<div style='font-size: 13px; color: gray; padding: 2px 0;'>{line}</div>"
                for line in extra_lines
            )
            st.markdown(extra_html, unsafe_allow_html=True)


def render_kpis(df_current: pd.DataFrame, df_previous: pd.DataFrame, ufs: list[str]) -> None:
    col1, col2, col3 = st.columns(3)

    total_current = df_current['total_internacoes'].sum()
    total_previous = df_previous['total_internacoes'].sum() if not df_previous.empty else 0
    variation = (
        (total_current - total_previous) / total_previous * 100 if total_previous > 0 else 0
    )
    breakdown = [
        f"Total de internações {uf}: {format_number(df_current[df_current['sigla_uf'] == uf]['total_internacoes'].sum())}"
        for uf in sorted(ufs)
    ]
    render_kpi_card(
        col1, "Total de Internações", format_number(total_current),
        delta=f"{variation:+.1f}% vs mês ant.",
        delta_color="green" if variation <= 0 else "red",
        extra_lines=breakdown,
    )

    total_beds = df_current['total_leitos'].sum()
    beds_breakdown = [
        f"Leitos ativos {uf}: {format_number(df_current[df_current['sigla_uf'] == uf]['total_leitos'].sum())}"
        for uf in sorted(ufs)
    ]
    render_kpi_card(col2, "Leitos Ativos", format_number(total_beds), extra_lines=beds_breakdown)

    occupancy_current = df_current['taxa_ocupacao'].mean() * 100 if not df_current.empty else 0
    occupancy_previous = df_previous['taxa_ocupacao'].mean() * 100 if not df_previous.empty else 0
    occupancy_variation = occupancy_current - occupancy_previous
    render_kpi_card(
        col3, "Ocupação Média Estadual", f"{occupancy_current:.1f}%",
        delta=f"{occupancy_variation:+.1f}% vs mês ant.",
        delta_color="green" if occupancy_variation <= 0 else "red",
    )


def render_pressure_map(df: pd.DataFrame, month: str, year: int) -> None:
    st.subheader("Mapa de Pressão e Risco de Colapso")

    if df.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados no mapa.")
        return

    df_map = df.rename(columns={
        'taxa_ocupacao': 'Taxa de Ocupação',
        'total_internacoes': 'Total de Internações',
        'total_leitos': 'Total de Leitos',
        'nome_fantasia': 'Hospital',
        'Cluster': 'Perfil Operacional'
    })

    fig = px.scatter_map(
        df_map,
        lat="latitude",
        lon="longitude",
        size="Total de Internações",
        color="Taxa de Ocupação",
        hover_name="Hospital",
        hover_data={
            "Taxa de Ocupação": ":.1%",
            "Total de Internações": True,
            "Total de Leitos": True,
            "Perfil Operacional": True,
            "latitude": False,
            "longitude": False,
        },
        color_continuous_scale=MAP_COLOR_SCALE,
        range_color=[0, 1.5],
        zoom=5.5,
        center=MAP_CENTER,
        map_style="carto-positron",
        title=f"Ocupação Hospitalar - {month}/{year}",
    )
    fig.update_layout(
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        coloraxis_colorbar=dict(title="Ocupação", tickformat=".0%"),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_monthly_evolution(df_year: pd.DataFrame, year: int) -> None:
    st.subheader(f"Evolução Mensal das Internações por Estado ({year})")

    if df_year.empty:
        return

    df_grouped = (
        df_year.groupby(['ano', 'mes', 'sigla_uf'])['total_internacoes']
        .sum()
        .reset_index()
    )
    df_grouped['mes_num'] = df_grouped['mes'].map(MONTH_TO_NUM)
    df_grouped = df_grouped.sort_values(by=['ano', 'mes_num'])

    df_grouped['Período'] = df_grouped['mes'].str[:3].str.lower()
    df_grouped = df_grouped.rename(columns={
        'sigla_uf': 'UF',
        'total_internacoes': 'Total de Internações',
    })

    fig = px.line(
        df_grouped,
        x="Período",
        y="Total de Internações",
        color="UF",
        markers=True,
        title=f"Comparativo de Internações - {year}",
        labels={"Período": "Mês", "Total de Internações": "Internações", "UF": "Estado"},
    )
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Total de Internações",
        yaxis=dict(rangemode="tozero"),
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        legend_title="Estado",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_ranking_table(df: pd.DataFrame) -> None:
    st.subheader("Ranking e Busca de Hospitais")

    display_columns = [
        'id_estabelecimento_cnes', 'nome_fantasia', 'sigla_uf',
        'descricao_esfera_administrativa', 'Cluster', 'total_leitos', 
        'total_internacoes', 'permanencia_media_dias', 'taxa_ocupacao',
    ]
    df_display = df[display_columns].sort_values(by='taxa_ocupacao', ascending=False).copy()
    df_display['taxa_ocupacao'] = (df_display['taxa_ocupacao'] * 100).round(1).astype(str) + "%"
    
    df_display.columns = [
        'CNES', 'Hospital', 'UF', 'Esfera', 'Cluster', 'Leitos',
        'Internações', 'Permanência Média', 'Taxa de Ocupação',
    ]
    
    st.dataframe(df_display, width="stretch", hide_index=True)


# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================

def main() -> None:
    df_all = load_data()
    filters = render_sidebar(df_all)

    # 6. PASSANDO A NOVA VARIÁVEL 'perfis' PARA OS FILTROS
    df_filtered = apply_filters(df_all, filters["year"], filters["ufs"], filters["esferas"], filters["perfis"], filters["month"])
    df_filtered = apply_search_filters(df_filtered, filters["cnes_query"], filters["name_query"])

    previous_year, previous_month = get_previous_period(filters["year"], filters["month"])
    df_previous = apply_filters(df_all, previous_year, filters["ufs"], filters["esferas"], filters["perfis"], previous_month)

    st.title("SUS360 - Painel de Capacidade e Pressão Hospitalar")
    st.markdown(f"Analisando dados de **{filters['month']} de {filters['year']}**")

    render_kpis(df_filtered, df_previous, filters["ufs"])
    st.divider()

    render_pressure_map(df_filtered, filters["month"], filters["year"])
    st.divider()

    df_year = apply_filters(df_all, filters["year"], filters["ufs"], filters["esferas"], filters["perfis"])
    render_monthly_evolution(df_year, filters["year"])
    st.divider()

    render_ranking_table(df_filtered)


if __name__ == "__main__":
    main()