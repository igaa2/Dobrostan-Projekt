import streamlit as st
import pandas as pd
from srcc.new_wave.data_classes import SessionStatePrefix


def calculate_weights(validation_cv: dict[str, float]) -> dict[str, float]:
    """Oblicza wagi hybrydowe (CV * waga użytkownika) i normalizuje je do sumy 1."""
    weights = {
        variable_id: cv * st.session_state[SessionStatePrefix.SLIDER.key(variable_id)]
        for variable_id, cv in validation_cv.items()
    }

    total = sum(weights.values())

    if total < 1e-10:
        return {variable_id: 0.0 for variable_id in weights.keys()}

    return {
        str(variable_id): float(weight / total)
        for variable_id, weight in weights.items()
    }


def calculate_copras(
    df: pd.DataFrame,
    weights: dict[str, float],
    destimulants: dict[str, bool],
) -> pd.DataFrame:
    """
    Oblicza COPRAS na znormalizowanej ramce danych.

    Wzory:
        S_i+ = Σ (w_j × x_ij) dla stymulant
        S_i- = Σ (w_j × x_ij) dla destymulant
        q_i = S_i+ + (Σ S_k-) / (S_i- × Σ(1/S_k-))
        Q_i = q_i / q_max × 100

    Zwraca:
        unit_name | Q
    """
    df = df.copy()
    df["variable_id"] = df["variable_id"].astype(str)

    # Ważenie wartości znormalizowanych
    df["value_weighted"] = df["value"] * df["variable_id"].map(weights).fillna(0)

    # S+ i S-
    stimulants = [k for k, v in destimulants.items() if v is False]
    destimulants = [k for k, v in destimulants.items() if v is True]

    s_plus = (
        df[df["variable_id"].isin(stimulants)]
        .groupby("unit_name")["value_weighted"]
        .sum()
    )

    if destimulants:
        s_minus = (
            df[df["variable_id"].isin(destimulants)]
            .groupby("unit_name")["value_weighted"]
            .sum()
        )
    else:
        s_minus = pd.Series(0.0, index=s_plus.index)

    # q
    sum_s_minus = s_minus.sum()
    if sum_s_minus > 0:
        s_minus_safe = s_minus.replace(0, float("nan"))
        sum_minus_inv = (1 / s_minus_safe).sum()
        q = s_plus + sum_s_minus / (s_minus * sum_minus_inv)
        q = q.fillna(s_plus)
    else:
        q = s_plus

    # Q
    Q = (q / q.max() * 100) if q.max() > 0 else q * 0
    print(Q)

    return (
        pd.DataFrame(
            {
                "unit_name": Q.index,
                "value": Q.values,
            }
        )
        .sort_values("value", ascending=False)
        .reset_index(drop=True)
    )
