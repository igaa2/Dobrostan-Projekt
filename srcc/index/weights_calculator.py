import pandas as pd
import numpy as np
from loguru import logger
from srcc.index.validator import VariableValidator


# ==================== WAGI ====================


def calculate_weights_for_year(df: pd.DataFrame, year: int) -> dict[str, float]:
    """
    Oblicza wagi CV-based dla danego roku.

    Wzór: w_j = CV_j / Σ CV
    """
    df_year = df[df["year"] == year]

    cv_per_var = df_year.groupby("variable_id")["value"].agg(
        VariableValidator.calculate_cv
    )
    total_cv = cv_per_var.sum()

    if abs(total_cv) < 1e-10:
        n = len(cv_per_var)
        logger.warning(f"Year {year}: All CV ≈ 0, using equal weights (1/{n})")
        return {str(var_id): 1 / n for var_id in cv_per_var.index}

    weights = {str(var_id): cv / total_cv for var_id, cv in cv_per_var.items()}

    logger.debug(f"Year {year} weights: {weights}")

    return weights


if __name__ == "__main__":
    df = pd.DataFrame(
        {
            "variable_id": [1, 1, 1, 2, 2, 2, 1, 1, 1, 2, 2, 2],
            "unit_id": ["M", "S", "W", "M", "S", "W", "M", "S", "W", "M", "S", "W"],
            "year": [
                2022,
                2022,
                2022,
                2022,
                2022,
                2022,
                2023,
                2023,
                2023,
                2023,
                2023,
                2023,
            ],
            "value_normalized": [
                0.8,
                0.4,
                0.3,
                0.5,
                0.9,
                0.6,
                0.7,
                0.5,
                0.6,
                0.4,
                0.8,
                0.5,
            ],
            "value": [72, 40, 25, 3.2, 9.8, 5.2, 75, 45, 55, 5.2, 7.8, 4.5],
        }
    )

    cv_weights = calculate_weights_for_year(df, year=2022)
    print(cv_weights)
