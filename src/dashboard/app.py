import streamlit as st
import pandas as pd

# ----------------------------
# Konfiguracja strony
# ----------------------------
st.set_page_config(
    page_title="Composite Index Dashboard",
    layout="wide",
)

st.title("Composite Index Dashboard")

# ----------------------------
# Dane wejściowe
# ----------------------------
df = pd.DataFrame(
    {
        "A": [1, 2, 3],
        "B": [4, 5, 6],
        "C": [7, 8, 9],
    }
)

st.subheader("Dane wejściowe")
st.dataframe(df)

# ----------------------------
# Sidebar – wagi
# ----------------------------
st.sidebar.header("Wagi (user input)")

w_A = st.sidebar.slider("Waga A", 0.0, 1.0, 0.3)
w_B = st.sidebar.slider("Waga B", 0.0, 1.0, 0.3)
w_C = st.sidebar.slider("Waga C", 0.0, 1.0, 0.4)

weights = {
    "A": w_A,
    "B": w_B,
    "C": w_C,
}

# ----------------------------
# Normalizacja wag
# ----------------------------
total_weight = sum(weights.values())

if total_weight == 0:
    st.error("Suma wag nie może być równa 0.")
    st.stop()

weights = {k: v / total_weight for k, v in weights.items()}

st.sidebar.markdown("### Znormalizowane wagi")
st.sidebar.write(weights)


# ----------------------------
# Funkcja obliczająca indeks
# ----------------------------
@st.cache_data
def compute_index(df: pd.DataFrame, weights: dict) -> pd.DataFrame:
    df_w = df.copy()
    for col, w in weights.items():
        df_w[col] = df_w[col] * w
    df_w["composite_index"] = df_w.sum(axis=1)
    return df_w


# ----------------------------
# Obliczenia
# ----------------------------
df_weighted = compute_index(df, weights)

# ----------------------------
# Wyniki
# ----------------------------
st.subheader("Dane po uwzględnieniu wag")
st.dataframe(df_weighted)

st.subheader("Composite Index")
st.bar_chart(df_weighted["composite_index"])
