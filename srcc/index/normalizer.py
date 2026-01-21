import pandas as pd
import numpy as np
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


def normalize_per_variable_and_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizuje dane dla każdej kombinacji variable_id + year.

    Wejście:  variable_id | unit_id | year | value
    Wyjście:  variable_id | unit_id | year | value_normalized
    """
    n_vars = df["variable_id"].nunique()
    n_years = df["year"].nunique()

    logger.info(f"Normalizing: {len(df)} rows, {n_vars} variables, {n_years} years")

    df = df.copy()
    df["value_normalized"] = df.groupby(["variable_id", "year"])["value"].transform(
        vector_normalize
    )

    logger.success("Vector normalization completed.")
    return df[["variable_id", "unit_id", "year", "value_normalized"]]


if __name__ == "__main__":
    df1 = pd.DataFrame(
        {
            "variable_id": [1, 1, 1, 1, 1, 1],
            "unit_id": ["M", "S", "W", "M", "S", "W"],
            "year": [2022, 2022, 2022, 2023, 2023, 2023],
            "value": [72, 40, 25, 75, 45, 55],
        }
    )

    df2 = pd.DataFrame(
        {
            "variable_id": [1, 1, 1],  # 1, 1, 1],
            "unit_id": ["M", "S", "W"],  # "M", "S", "W"],
            "year": [2022, 2022, 2022],  # 2023, 2023, 2023],
            "value": [72, 40, 25],  # 75, 45, 55],
        }
    )

    result1 = normalize_per_variable_and_year(df1)
    print(result1)
    result2 = normalize_per_variable_and_year(df2)
    print(result2)
