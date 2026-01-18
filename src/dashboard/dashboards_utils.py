import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


def generate_slider(prefix: str, var_id: int, name: str) -> float:
    """Tworzy suwak od 0% do 100% w pasku bocznym Streamlit."""
    return st.sidebar.slider(
        label=name,
        min_value=0,
        max_value=100,
        step=1,
        format="%d%%",
        key=f"{prefix}{var_id}",
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
