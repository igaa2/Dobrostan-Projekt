"""
Metoda COPRAS do budowy wskaźnika kompozytowego.

Zawiera:
- Normalizację wektorową
- Obliczanie wag CV-based
- Kalkulator COPRAS
"""

import pandas as pd
import numpy as np
from loguru import logger
from dataclasses import replace

from srcc.utils.dataclasses import (
    Unit,
    Variable,
    VariableType,
    UnitScore,
    CoprasResult,
)
from srcc.index.weights_calculator import calculate_weights_for_year
from srcc.index.normalizer import normalize


# ==================== COPRAS ====================


class Copras:
    """
    Kalkulator wskaźnika kompozytowego metodą COPRAS.

    Wzory:
        S_i+ = Σ (w_j × x_ij) dla stymulant
        S_i- = Σ (w_j × x_ij) dla destymulant
        Q_i = S_i+ + (Σ S_k-) / (S_i- × Σ(1/S_k-))
        U_i = Q_i / Q_max × 100%
    """

    def __init__(self, variables: list[Variable], units: list[Unit] = None):
        """
        Args:
            variables: lista zmiennych z kierunkami (type)
            units: lista jednostek (opcjonalnie, do wzbogacenia wyników)
        """
        self.variables = variables
        self._units_map = {u.unit_id: u for u in units} if units else {}

        stim = sum(1 for v in variables if v.is_stimulant)
        dest = len(variables) - stim

        logger.info(
            f"COPRAS initialized: {len(variables)} variables ({stim} stim, {dest} dest)"
        )

    @property
    def stimulant_ids(self) -> list[str]:
        """Lista ID stymulant."""
        return [v.variable_id for v in self.variables if v.is_stimulant]

    @property
    def destimulant_ids(self) -> list[str]:
        """Lista ID destymulant."""
        return [v.variable_id for v in self.variables if v.is_destimulant]

    def _get_unit(self, unit_id: str) -> Unit:
        """Zwraca Unit lub tworzy placeholder."""
        if unit_id in self._units_map:
            return self._units_map[unit_id]
        return Unit(unit_id=str(unit_id), name=str(unit_id))

    def _apply_weights(
        self,
        df: pd.DataFrame,
        weights: dict[str, float],
    ) -> pd.DataFrame:
        """Stosuje wagi do znormalizowanych wartości."""
        df = df.copy()
        df["variable_id"] = df["variable_id"].astype(str)
        df["weight"] = df["variable_id"].map(weights)
        df["value_weighted"] = df["value_normalized"] * df["weight"]
        return df

    def _calculate_s_plus(self, df: pd.DataFrame) -> pd.Series:
        """S_i+ = Σ (w_j × x_ij) dla stymulant."""
        if not self.stimulant_ids:
            return pd.Series(0.0, index=df["unit_id"].unique())

        mask = df["variable_id"].isin(self.stimulant_ids)
        return df[mask].groupby("unit_id")["value_weighted"].sum()

    def _calculate_s_minus(self, df: pd.DataFrame) -> pd.Series:
        """S_i- = Σ (w_j × x_ij) dla destymulant."""
        if not self.destimulant_ids:
            return pd.Series(0.0, index=df["unit_id"].unique())

        mask = df["variable_id"].isin(self.destimulant_ids)
        return df[mask].groupby("unit_id")["value_weighted"].sum()

    def _calculate_q(self, s_plus: pd.Series, s_minus: pd.Series) -> pd.Series:
        """
        Q_i = S_i+ + (Σ S_k-) / (S_i- × Σ(1/S_k-))

        Jeśli S_i- = 0 → Q_i = S_i+
        """
        sum_s_minus = s_minus.sum()

        s_minus_safe = s_minus.replace(0, np.nan)
        sum_inverse = (1 / s_minus_safe).sum()

        if sum_s_minus == 0 or pd.isna(sum_inverse) or sum_inverse == 0:
            return s_plus

        denominator = s_minus * sum_inverse
        denominator = denominator.replace(0, np.nan)

        q = s_plus + sum_s_minus / denominator
        return q.fillna(s_plus)

    def _calculate_u(self, q: pd.Series) -> pd.Series:
        """U_i = Q_i / Q_max × 100%"""
        q_max = q.max()
        if q_max == 0:
            return q * 0
        return (q / q_max) * 100

    def _calculate_rank(self, u: pd.Series) -> pd.Series:
        """Ranking (1 = najlepszy)."""
        return u.rank(ascending=False, method="min").astype(int)

    def calculate(
        self,
        df: pd.DataFrame,
        year: int,
        custom_weights: dict[str, float] = None,
    ) -> CoprasResult:
        """
        Wykonuje kalkulację COPRAS dla danego roku.

        Args:
            df: dane (variable_id, unit_id, year, value, value_normalized)
            year: rok do analizy
            custom_weights: własne wagi, jeśli None → oblicza CV-based

        Returns:
            CoprasResult z wynikami
        """
        logger.info(f"Calculating COPRAS for year {year}")

        df_year = df[df["year"] == year].copy()
        df_year["variable_id"] = df_year["variable_id"].astype(str)

        # Wagi
        if custom_weights is not None:
            weights = custom_weights
        else:
            if "value" not in df_year.columns:
                raise ValueError("Need 'value' column to calculate CV-based weights")
            weights = calculate_weights_for_year(df_year, year)

        # Normalizuj wagi do sumy = 1
        total = sum(weights.values())
        if not np.isclose(total, 1.0, atol=0.01):
            logger.warning(f"Weights sum = {total:.4f}, normalizing to 1")
            weights = {k: v / total for k, v in weights.items()}

        # Utwórz kopie Variable z wagami
        variables_with_weights = [
            replace(v, weight=weights.get(v.variable_id, 0.0)) for v in self.variables
        ]

        # Obliczenia COPRAS
        df_weighted = self._apply_weights(df_year, weights)

        s_plus = self._calculate_s_plus(df_weighted)
        s_minus = self._calculate_s_minus(df_weighted)
        q = self._calculate_q(s_plus, s_minus)
        u = self._calculate_u(q)
        rank = self._calculate_rank(u)

        # Twórz UnitScore dla każdej jednostki
        unit_scores = []
        for unit_id in s_plus.index:
            unit_id_str = str(unit_id)
            score = UnitScore(
                unit=self._get_unit(unit_id_str),
                s_plus=float(s_plus.get(unit_id, 0)),
                s_minus=float(s_minus.get(unit_id, 0)),
                q=float(q.get(unit_id, 0)),
                u=float(u.get(unit_id, 0)),
                rank=int(rank.get(unit_id, 0)),
            )
            unit_scores.append(score)

        # Sortuj po rankingu
        unit_scores.sort(key=lambda x: x.rank)

        result = CoprasResult(
            year=year,
            unit_scores=unit_scores,
            variables=variables_with_weights,
        )

        logger.success(
            f"COPRAS {year}: leader = {result.leader.name} (U={unit_scores[0].u:.1f})"
        )

        return result

    def calculate_all_years(
        self,
        df: pd.DataFrame,
        custom_weights: dict[str, float] = None,
    ) -> dict[int, CoprasResult]:
        """Oblicza COPRAS dla wszystkich lat."""
        years = sorted(df["year"].unique())
        logger.info(f"Calculating COPRAS for {len(years)} years")

        results = {}
        for year in years:
            results[int(year)] = self.calculate(df, int(year), custom_weights)

        return results

    def process(
        self,
        df: pd.DataFrame,
        custom_weights: dict[str, float] = None,
    ) -> dict[int, CoprasResult]:
        """
        Pełny pipeline: normalizacja → COPRAS.

        Wejście:  variable_id | unit_id | year | value

        Returns:
            {year: CoprasResult}
        """
        logger.info("Starting COPRAS pipeline")

        # Normalizacja
        df_normalized = normalize(df)

        # Połącz z oryginalnymi wartościami (potrzebne do CV)
        df_full = df_normalized.merge(
            df[["variable_id", "unit_id", "year", "value"]],
            on=["variable_id", "unit_id", "year"],
        )

        # COPRAS dla wszystkich lat
        results = self.calculate_all_years(df_full, custom_weights)

        logger.success(f"COPRAS pipeline completed: {len(results)} years")

        return results


if __name__ == "__main__":
    # Przykładowe dane
    df = pd.DataFrame(
        {
            "variable_id": ["1", "1", "1", "2", "2", "2", "3", "3", "3"] * 2,
            "unit_id": ["MAZ", "SLA", "WLK"] * 6,
            "year": [2022] * 9 + [2023] * 9,
            "value": [
                # 2022
                72,
                45,
                65,  # var 1 (PKB)
                3.2,
                8.0,
                5.0,  # var 2 (bezrobocie)
                70,
                60,
                75,  # var 3 (edukacja)
                # 2023
                78,
                50,
                70,
                2.8,
                7.5,
                4.5,
                75,
                65,
                80,
            ],
        }
    )

    # Zmienne
    variables = [
        Variable("1", "PKB per capita", VariableType.STIMULANT, 50),
        Variable("2", "Stopa bezrobocia", VariableType.DESTIMULANT, 50),
        Variable("3", "Poziom edukacji", VariableType.STIMULANT, 50),
    ]

    # Jednostki (opcjonalnie)
    units = [
        Unit("MAZ", "mazowieckie"),
        Unit("SLA", "śląskie"),
        Unit("WLK", "wielkopolskie"),
    ]

    # COPRAS
    copras = Copras(variables, units)

    # Pełny pipeline
    results = copras.process(df)

    # Wyświetl wyniki
    for year, result in results.items():
        print(f"\n🏆 Lider {year}: {result.leader.name}")
        print(f"📊 Ranking:\n{result.ranking}\n")
