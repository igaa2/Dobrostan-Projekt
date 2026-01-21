import pandas as pd
import numpy as np
import streamlit as st
from loguru import logger


# ==================== NORMALIZACJA ====================


def vector_normalize(series: pd.Series) -> np.ndarray:
    """Normalizacja wektorowa: x / √(Σx²)"""
    sum_squared = (series**2).sum()
    sqrt_sum = np.sqrt(sum_squared)

    if abs(sqrt_sum) < 1e-10:
        logger.warning("sqrt_sum equals 0, returning zero vector for normalization.")
        return np.zeros(len(series))
    return (series / sqrt_sum).values


@st.cache_data
def normalize_per_variable(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizuje dane dla każdej zmiennej."""
    df = df.copy()
    df["value"] = df.groupby(["variable_id"])["value"].transform(vector_normalize)

    logger.success("Vector normalization completed.")
    return df


if __name__ == "__main__":
    df = pd.DataFrame(
        {
            "variable_id": [1, 1, 1],
            "unit_id": ["M", "S", "W"],
            "year": [2022, 2022, 2022],
            "value": [72, 40, 25],
        }
    )

    result = normalize_per_variable(df)
    print(result)
