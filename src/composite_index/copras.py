import pandas as pd


def calculate_hybrid_weights(
    validation_cv: dict[int, float],
    slider_weights: dict[int, float],
) -> dict[int, float]:
    """Oblicza wagi hybrydowe (CV * waga użytkownika) i normalizuje je do sumy 1."""

    hybrid_weights = {
        variable_id: validation_cv.get(variable_id, 0.0)
        * slider_weights.get(variable_id, 0.0)
        for variable_id in validation_cv.keys()
    }

    total = sum(hybrid_weights.values())

    if total < 1e-10:
        return {variable_id: 0.0 for variable_id in hybrid_weights.keys()}

    return {
        variable_id: float(weight / total)
        for variable_id, weight in hybrid_weights.items()
    }


def calculate_copras(
    df: pd.DataFrame,
    weights: dict[int, float],
    stimulants: dict[int, bool],
    unit_col_name: str = "unit_name",
    variable_col_name: str = "variable_id",
    value_col_name: str = "value",
    output_col_name: str = "value",
) -> pd.DataFrame:
    """
    Oblicza COPRAS na znormalizowanej ramce danych.

    Wzory:
        S_i+ = Σ (w_j × x_ij) dla stymulant (False w stimulants)
        S_i- = Σ (w_j × x_ij) dla destymulant (True w stimulants)
        q_i = S_i+ + (Σ S_k-) / (S_i- × Σ(1/S_k-))
        Q_i = q_i / q_max × 100

    Zwraca:
        DataFrame: unit_col_name | output_col_name
    """

    df = df.copy()
    df[variable_col_name] = df[variable_col_name].astype(int)

    # Ważenie wartości znormalizowanych
    df["value_weighted"] = df[value_col_name] * df[variable_col_name].map(
        weights
    ).fillna(0.0)

    # Podział na stymulanty i destymulanty
    plus = [k for k, v in stimulants.items() if v is False]
    minus = [k for k, v in stimulants.items() if v is True]

    # S+
    s_plus = (
        df[df[variable_col_name].isin(plus)]
        .groupby(unit_col_name)["value_weighted"]
        .sum()
    )

    # S-
    if minus:
        s_minus = (
            df[df[variable_col_name].isin(minus)]
            .groupby(unit_col_name)["value_weighted"]
            .sum()
        )
    else:
        s_minus = pd.Series(0.0, index=s_plus.index)

    # q
    sum_s_minus = s_minus.sum()
    if sum_s_minus > 0:
        s_minus_safe = s_minus.replace(0, pd.NA)
        sum_minus_inv = (1 / s_minus_safe).sum()
        q = s_plus + sum_s_minus / (s_minus * sum_minus_inv)
        q = q.fillna(s_plus)
    else:
        q = s_plus

    # Q
    Q = (q / q.max() * 100) if q.max() > 0 else q * 0

    return (
        pd.DataFrame(
            {
                unit_col_name: Q.index,
                output_col_name: Q.values,
            }
        )
        .sort_values(output_col_name, ascending=False)
        .reset_index(drop=True)
    )


if __name__ == "__main__":
    df = pd.DataFrame(
        {
            "unit_name": ["A", "A", "B", "B", "C", "C"],
            "variable_id": [1, 2, 1, 2, 1, 2],
            "value": [0.5, 0.8, 0.3, 0.9, 0.7, 0.4],
        }
    )

    weights = {
        1: 0.6,
        2: 0.4,
    }

    stimulants = {
        1: False,
        2: True,
    }

    copras_result = calculate_copras(df, weights, stimulants)

    print("Wynik COPRAS:")
    print(copras_result)
