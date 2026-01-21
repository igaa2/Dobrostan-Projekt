import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import json
import urllib.request
from loguru import logger


def create_horizontal_barplot_with_mean_line(
    df: pd.DataFrame,
    value_col_name: str,
    unit_col_name: str,
    value_label: str = "Wskaźnik dobrostanu",
    unit_label: str = "Województwa",
) -> px.bar:
    """Tworzy poziomy wykres słupkowy z linią średniej."""
    df_sorted = df.sort_values(value_col_name, ascending=True)
    mean = df_sorted[value_col_name].mean()

    # Kolory: zielony powyżej średniej, czerwony poniżej
    colors = [
        "#00ff6a" if val >= mean else "#ff1900" for val in df_sorted[value_col_name]
    ]

    fig = px.bar(
        df_sorted,
        x=value_col_name,
        y=unit_col_name,
        orientation="h",
        title="",
        labels={value_col_name: value_label, unit_col_name: unit_label},
    )

    # Ustawienie kolorów bez tworzenia legendy "color"
    fig.update_traces(
        marker_color=colors,
        hovertemplate="Województwo: %{y} <br>Wartość: %{x:.2f}%",
    )

    fig.add_vline(
        x=mean,
        line_color="navy",
        line_width=3,
        annotation_text=f"Średnia: {mean:.0f}%",
        annotation_position="top",
    )

    fig.update_layout(
        autosize=True,
        showlegend=False,
        xaxis=dict(
            tickformat=".0f",
            ticksuffix="%",
            range=[0, 110],
            showgrid=True,
            gridcolor="lightgrey",
            gridwidth=1,
            griddash="dash",
        ),
        font=dict(size=12),
    )

    logger.info(f"Barplot chart created.")
    return fig


def create_radar(
    df: pd.DataFrame,
    value_col_name: str,
    variable_col_name: str,
    unit_col_name: str,
    chosen_units: list[str],
    unit_label: str = "Województwa",
) -> px.line_polar:
    fig = px.line_polar(
        df[df[unit_col_name].isin(chosen_units)],
        r=value_col_name,
        theta=variable_col_name,
        color=unit_col_name,
        line_close=True,
    )

    fig.update_traces(fill="toself")
    fig.update_layout(
        title="🕸️ Wykres radarowy",
        polar=dict(radialaxis=dict(visible=True)),
        autosize=True,
        font=dict(size=12),
        legend_title_text=unit_label,
        coloraxis_colorbar=dict(ticksuffix="%"),
    )

    logger.info(f"Radar char created.")
    return fig


@st.cache_data
def load_voiv_geojson() -> dict:
    """Pobiera i cachuje GeoJSON (nazwy województw wielką literą)."""

    url = "https://raw.githubusercontent.com/ppatrzyk/polska-geojson/master/wojewodztwa/wojewodztwa-medium.geojson"

    with urllib.request.urlopen(url) as response:
        geojson = json.loads(response.read())

    # Zamiana nazw na uppercase
    for feature in geojson["features"]:
        feature["properties"]["nazwa"] = feature["properties"]["nazwa"].upper()

    return geojson


def create_map(
    df: pd.DataFrame,
    value_col_name: str,
    unit_col_name: str,
    value_label: str = "Wskaźnik dobrostanu",
) -> go.Figure:
    """Tworzy mapę natężenia wskaźnika dla województw."""

    geojson = load_voiv_geojson()

    fig = px.choropleth(
        df,
        geojson=geojson,
        locations=unit_col_name,
        featureidkey="properties.nazwa",
        color=value_col_name,
        color_continuous_scale="Blues",
        range_color=[0, 100],
        labels={value_col_name: value_label},
        hover_name=unit_col_name,
        hover_data={value_col_name: ":.2f"},
    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)",
    )

    fig.update_traces(
        hovertemplate="<b>Województwo:</b> %{hovertext}<br><b>Wartość:</b> %{z:.2f}%"
    )

    fig.update_layout(
        autosize=True,
        font=dict(size=12),
        coloraxis_colorbar=dict(
            title=value_label,
            ticksuffix="%",
            orientation="h",
            xanchor="center",
            yanchor="top",
            y=-0.30,
            len=1.0,
        ),
    )

    logger.info("Map chart created.")
    return fig
