import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from src.dashboard.dashboards_utils import (
    generate_slider,
    generate_barplot,
    generate_toggle,
    get_keys,
    reset,
)
from src.utils.utils import get_project_root, load_md, load_yaml

config = load_yaml(get_project_root() / "dashboard" / "config" / "config.yaml")
prefix_weights = config["state_session_key"]["weight_prefix"]
prefix_stim = config["state_session_key"]["stim_prefix"]


# ==================== KONFIGURACJA STRONY ====================
st.set_page_config(
    page_title="Dobrostan Województw Polski",
    page_icon="📊",
    layout="wide",  # page elements use the entire screen width
    initial_sidebar_state="expanded",
    menu_items={"About": load_md(get_project_root() / "dashboard" / "about.md")},
)

# ==================== DEFINICJE ZMIENNYCH ====================
ZMIENNE = {
    "zdrowie": "Zdrowie publiczne",
    "edukacja": "Poziom edukacji",
    "zatrudnienie": "Zatrudnienie",
    "dochody": "Dochody gospodarstw",
    "bezpieczenstwo": "Bezpieczeństwo",
    "srodowisko": "Jakość środowiska",
    "mieszkalnictwo": "Warunki mieszkaniowe",
    "kultura": "Dostęp do kultury",
    "transport": "Infrastruktura transportowa",
    "cyfryzacja": "Cyfryzacja",
    "spoleczenstwo": "Kapitał społeczny",
}

WOJEWODZTWA = [
    "dolnośląskie",
    "kujawsko-pomorskie",
    "lubelskie",
    "lubuskie",
    "łódzkie",
    "małopolskie",
    "mazowieckie",
    "opolskie",
    "podkarpackie",
    "podlaskie",
    "pomorskie",
    "śląskie",
    "świętokrzyskie",
    "warmińsko-mazurskie",
    "wielkopolskie",
    "zachodniopomorskie",
]


def generuj_dane() -> pd.DataFrame:
    """
    Generuje przykładowe dane dla województw.

    Returns:
        DataFrame z danymi województw
    """
    np.random.seed(42)

    dane = {"wojewodztwo": WOJEWODZTWA}

    # Generuj losowe wartości dla każdej zmiennej
    for klucz in ZMIENNE.keys():
        dane[klucz] = np.random.uniform(30, 90, size=len(WOJEWODZTWA))

    return pd.DataFrame(dane)


def oblicz_wskaznik(df: pd.DataFrame) -> pd.DataFrame:
    """
    Oblicza wskaźnik kompozytowy na podstawie wag.

    Args:
        df: DataFrame z danymi
        wagi: słownik z wagami dla każdej zmiennej

    Returns:
        DataFrame z obliczonym wskaźnikiem
    """
    df_wynik = df.copy()
    wagi = get_keys(prefix=prefix_weights)
    print("Wagi:", wagi)

    # Normalizacja wag do sumy 1
    suma_wag = sum(wagi.values())
    if suma_wag == 0:
        suma_wag = 1

    # Oblicz ważoną średnią
    df_wynik["wskaznik"] = 0
    for klucz in ZMIENNE.keys():
        waga = wagi[f"{prefix_weights}{klucz}"] / suma_wag
        df_wynik["wskaznik"] += df_wynik[klucz] * waga

    return df_wynik


# ==================== PANEL BOCZNY ====================
st.sidebar.title("⚙️ Ustawienia zmiennych")
st.sidebar.caption("Waga | Typ (📈 stymulanta / 📉 destymulanta)")
st.sidebar.markdown(
    "Ustal ważność zmiennych i wskaż, czy ich wpływ na wynik jest pozytywny (stymulanta) czy negatywny (destymulanta)."
)
st.sidebar.markdown("---")

# Tworzenie wszystkich suwaków
for var_id, name in ZMIENNE.items():
    status = "✅"
    st.sidebar.markdown(f"**{name}** {status}")
    slider_col, toggle_col = st.sidebar.columns([2, 1])

    if f"{prefix_weights}{var_id}" not in st.session_state:
        st.session_state[f"{prefix_weights}{var_id}"] = 50
    generate_slider(
        container=slider_col, prefix=prefix_weights, var_id=var_id, name=name
    )

    if f"{prefix_stim}{var_id}" not in st.session_state:
        st.session_state[f"{prefix_stim}{var_id}"] = False
    generate_toggle(container=toggle_col, prefix=prefix_stim, var_id=var_id)

# Przyciski resetów
st.sidebar.markdown("---")
reset_weight_col, reset_toggle_col = st.sidebar.columns(2)

with reset_weight_col:
    if st.button(
        "🔄⚖️ Resetuj wagi",
        use_container_width=True,
        on_click=reset,
        kwargs={"prefix": prefix_weights},
    ):
        st.rerun()

with reset_toggle_col:
    if st.button(
        "🔄📉 Resetuj typy",
        use_container_width=True,
        on_click=reset,
        kwargs={"prefix": prefix_stim},
    ):
        st.rerun()

weights = get_keys(prefix=prefix_weights)
if weights and all(v == 0 for v in weights.values()):
    st.warning(
        "⚠️ Wszystkie wagi mają wartość 0. "
        "Nie można porównać jednostek — ustaw co najmniej jedną wagę większą od 0."
    )

# ==================== GŁÓWNY PANEL ====================
st.title("📊 Dobrostan Województw Polski")
st.markdown("---")

print(st.session_state)
# Generuj i przelicz dane
df = generuj_dane()
df_z_wskaznikiem = oblicz_wskaznik(df)

# Wyświetl wykres
fig = generate_barplot(
    df_z_wskaznikiem, "wskaznik", "Wartość wskaźnika", "wojewodztwo", "Województwo"
)
st.plotly_chart(fig, use_container_width=True)

# Tabela statystyk
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "🏆 Najlepsze",
        df_z_wskaznikiem.loc[df_z_wskaznikiem["wskaznik"].idxmax(), "wojewodztwo"],
    )

with col2:
    st.metric("📈 Max", f"{df_z_wskaznikiem['wskaznik'].max():.1f}")

with col3:
    st.metric("📉 Min", f"{df_z_wskaznikiem['wskaznik'].min():.1f}")

with col4:
    st.metric("📊 Średnia", f"{df_z_wskaznikiem['wskaznik'].mean():.1f}")
