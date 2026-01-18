import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from streamlit.delta_generator import DeltaGenerator


def generate_slider(
    container: DeltaGenerator, prefix: str, var_id: int, name: str
) -> float:
    """Tworzy suwak od 0% do 100% w pasku bocznym Streamlit."""
    return container.slider(
        label=name,
        min_value=0,
        max_value=100,
        step=1,
        format="%d%%",
        key=f"{prefix}{var_id}",
        label_visibility="collapsed",
    )


def generate_toggle(container: DeltaGenerator, prefix: str, var_id: int) -> bool:
    """Tworzy przełącznik na destymulantę w pasku bocznym Streamlit."""
    return container.toggle(
        label="📉",
        key=f"{prefix}{var_id}",
        label_visibility="visible",
        help="OFF = stymulanta, ON = destymulanta",
    )


def reset(prefix: str) -> None:
    """Ustawia default_value kluczą rozpoczynającym się od prefix w słowniku session_state."""
    for key in list(st.session_state.keys()):
        if key.startswith(prefix):
            del st.session_state[key]


def get_keys(prefix: str) -> dict:
    """Pobiera wszystkie wagi z session_state, których klucze zaczynają się od prefix."""
    return {k: v for k, v in st.session_state.items() if k.startswith(prefix)}


def generate_barplot(
    df: pd.DataFrame,
    data_col_name: str,
    data_label: str,
    unit_col_name: str,
    unit_label: str,
) -> px.bar:
    """Tworzy wykres słupkowy z danych DataFrame."""
    df_sorted = df.sort_values(data_col_name, ascending=True)
    mean = df_sorted[data_col_name].mean()

    # Kolory: zielony powyżej średniej, czerwony poniżej
    colors = [
        "#00ff6a" if val >= mean else "#ff1900" for val in df_sorted[data_col_name]
    ]

    fig = px.bar(
        df_sorted,
        x=data_col_name,
        y=unit_col_name,
        orientation="h",
        title="",
        labels={data_col_name: data_label, unit_col_name: unit_label},
    )

    fig.update_traces(marker_color=colors)

    fig.add_vline(
        x=mean,
        line_dash="dash",
        line_color="navy",
        line_width=2,
        annotation_text=f"Średnia: {mean:.2f}",
        annotation_position="top",
    )

    fig.update_layout(
        height=600, showlegend=False, xaxis_range=[0, 100], font=dict(size=12)
    )

    return fig


import plotly.graph_objects as go
import plotly.express as px


def create_radar_chart(
    df: pd.DataFrame, wybrane_wojewodztwa: list[str], zmienne: dict[str, str]
) -> go.Figure:
    """Tworzy wykres radarowy dla wybranych województw."""

    fig = go.Figure()

    kategorie = list(zmienne.values())
    klucze = list(zmienne.keys())

    # Paleta kolorów
    kolory = px.colors.qualitative.Plotly

    for idx, woj in enumerate(wybrane_wojewodztwa):
        woj_data = df[df["wojewodztwo"] == woj]

        if woj_data.empty:
            continue

        wartosci = [woj_data[klucz].values[0] for klucz in klucze]
        wartosci += [wartosci[0]]  # Zamknięcie

        kolor = kolory[idx % len(kolory)]

        fig.add_trace(
            go.Scatterpolar(
                r=wartosci,
                theta=kategorie + [kategorie[0]],
                fill="toself",
                name=woj,
                opacity=0.4,  # Alpha = 0.4
                line=dict(width=2),
            )
        )

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        title="Porównanie województw - profil wskaźników",
        height=600,
    )

    return fig


import json
import urllib.request

# URLs do GeoJSON
GEOJSON_URLS = {
    "wojewodztwa": "https://raw.githubusercontent.com/ppatrzyk/polska-geojson/master/wojewodztwa/wojewodztwa-medium.geojson",
    "powiaty": "https://raw.githubusercontent.com/ppatrzyk/polska-geojson/master/powiaty/powiaty-medium.geojson",
}


@st.cache_data
def load_geojson(jednostka: str) -> dict:
    """Pobiera i cachuje GeoJSON."""
    url = GEOJSON_URLS[jednostka]
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read())


def create_map(
    df: pd.DataFrame,
    jednostka: str,
    kolumna_wartosci: str = "wskaznik",
    kolumna_nazwy: str = "wojewodztwo",
) -> go.Figure:
    """
    Tworzy mapę choropleth Polski.

    Args:
        df: DataFrame z danymi
        jednostka: 'wojewodztwa' lub 'powiaty'
        kolumna_wartosci: nazwa kolumny z wartościami do wizualizacji
        kolumna_nazwy: nazwa kolumny z nazwami jednostek

    Returns:
        Wykres Plotly
    """

    geojson = load_geojson(jednostka)

    # Klucz w GeoJSON zależy od jednostki
    if jednostka == "wojewodztwa":
        featureidkey = "properties.nazwa"
    else:  # powiaty
        featureidkey = "properties.nazwa"

    fig = px.choropleth(
        df,
        geojson=geojson,
        locations=kolumna_nazwy,
        featureidkey=featureidkey,
        color=kolumna_wartosci,
        color_continuous_scale="RdYlGn",
        range_color=[0, 100],
        labels={kolumna_wartosci: "Wskaźnik"},
        hover_name=kolumna_nazwy,
        hover_data={kolumna_wartosci: ":.1f"},
    )

    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")

    fig.update_layout(
        title=f"Wskaźnik dobrostanu - {jednostka}",
        height=600,
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        coloraxis_colorbar=dict(title="Wskaźnik", ticksuffix="%"),
    )

    return fig


def create_line_chart_with_avg(
    df: pd.DataFrame, wybrane_wojewodztwa: list[str]
) -> go.Figure:
    """Wykres liniowy ze średnią krajową."""

    df_filtered = df[df["wojewodztwo"].isin(wybrane_wojewodztwa)]

    # Średnia krajowa per rok
    df_avg = df.groupby("rok")["wskaznik"].mean().reset_index()
    df_avg["wojewodztwo"] = "Średnia krajowa"

    # Połącz dane
    df_combined = pd.concat([df_filtered, df_avg], ignore_index=True)

    fig = px.line(
        df_combined,
        x="rok",
        y="wskaznik",
        color="wojewodztwo",
        markers=True,
        title="Wskaźnik dobrostanu w czasie",
    )

    # Średnia jako linia przerywana
    fig.for_each_trace(
        lambda t: (
            t.update(line=dict(dash="dash", width=3))
            if t.name == "Średnia krajowa"
            else t.update(line=dict(width=2))
        )
    )

    fig.update_layout(
        height=500,
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis=dict(range=[0, 100]),
        hovermode="x unified",
    )

    return fig
