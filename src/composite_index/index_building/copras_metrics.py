# analytics/index_building/copras.py
import pandas as pd
import numpy as np
from enum import Enum
from dataclasses import dataclass


class VariableDirection(Enum):
    """Kierunek zmiennej."""

    STIMULANT = "stimulant"
    DESTIMULANT = "destimulant"

    def __repr__(self) -> str:
        return self.value


@dataclass
class CoprasResult:
    """Wynik COPRAS dla jednego roku."""

    year: int
    scores: pd.DataFrame  # unit_id, S_plus, S_minus, Q, U, rank
    weights: dict[int, float]
    directions: dict[int, VariableDirection]


class CoprasCalculator:
    """
    Kalkulator wskaźnika kompozytowego metodą COPRAS.

    Wzory:
        S_i+ = Σ (w_j × x_ij) dla stymulant
        S_i- = Σ (w_j × x_ij) dla destymulant
        Q_i = S_i+ + (Σ S_k-) / (S_i- × Σ(1/S_k-))
        U_i = Q_i / Q_max × 100%
    """

    def __init__(
        self,
        directions: dict[int, VariableDirection],  # {var_id: kierunek}
        weights: dict[int, float],  # {var_id: waga}
    ):
        """
        Args:
            directions: kierunki zmiennych {var_id: STIMULANT/DESTIMULANT}
            weights: wagi zmiennych {var_id: waga} (suma = 1)
        """
        self.directions = directions
        self.weights = weights
        self._validate_weights()

    def _validate_weights(self) -> None:
        """Sprawdza czy wagi sumują się do 1."""
        total = sum(self.weights.values())
        if not np.isclose(total, 1.0, atol=0.01):
            print(f"Uwaga: suma wag = {total:.4f}, normalizuję do 1")
            self.weights = {k: v / total for k, v in self.weights.items()}

    def _get_stimulants(self) -> list[int]:
        """Zwraca listę var_id stymulant."""
        return [
            var_id
            for var_id, direction in self.directions.items()
            if direction == VariableDirection.STIMULANT
        ]

    def _get_destimulants(self) -> list[int]:
        """Zwraca listę var_id destymulant."""
        return [
            var_id
            for var_id, direction in self.directions.items()
            if direction == VariableDirection.DESTIMULANT
        ]

    def calculate_weighted_values(self, df: pd.DataFrame, year: int) -> pd.DataFrame:
        """
        Krok 1: Oblicza wartości ważone.

        d_ij = x_ij × w_j
        """
        data = df[df["year"] == year].copy()
        data["weight"] = data["var_id"].map(self.weights)
        data["value_weighted"] = data["value_normalized"] * data["weight"]

        return data

    def calculate_s_plus(self, df_weighted: pd.DataFrame) -> pd.Series:
        """
        Krok 2: Oblicza S_i+ (suma ważonych stymulant).

        S_i+ = Σ d_ij dla j ∈ stymulanty
        """
        stimulants = self._get_stimulants()

        if not stimulants:
            # Brak stymulant - S+ = 0
            return df_weighted.groupby("unit_id").size() * 0

        mask = df_weighted["var_id"].isin(stimulants)
        s_plus = df_weighted[mask].groupby("unit_id")["value_weighted"].sum()
        s_plus.name = "S_plus"

        return s_plus

    def calculate_s_minus(self, df_weighted: pd.DataFrame) -> pd.Series:
        """
        Krok 3: Oblicza S_i- (suma ważonych destymulant).

        S_i- = Σ d_ij dla j ∈ destymulanty
        """
        destimulants = self._get_destimulants()

        if not destimulants:
            # Brak destymulant - S- = 0
            units = df_weighted["unit_id"].unique()
            return pd.Series(0.0, index=units, name="S_minus")

        mask = df_weighted["var_id"].isin(destimulants)
        s_minus = df_weighted[mask].groupby("unit_id")["value_weighted"].sum()
        s_minus.name = "S_minus"

        return s_minus

    def calculate_q(self, s_plus: pd.Series, s_minus: pd.Series) -> pd.Series:
        """
        Krok 4: Oblicza Q_i (znaczenie względne).

        Q_i = S_i+ + (Σ S_k-) / (S_i- × Σ(1/S_k-))

        Jeśli S_i- = 0: Q_i = S_i+
        """
        # Suma wszystkich S-
        sum_s_minus = s_minus.sum()

        # Suma 1/S- (unikamy dzielenia przez 0)
        s_minus_safe = s_minus.replace(0, np.nan)
        sum_inverse_s_minus = (1 / s_minus_safe).sum()

        if sum_s_minus == 0 or pd.isna(sum_inverse_s_minus) or sum_inverse_s_minus == 0:
            # Brak destymulant lub wszystkie S- = 0
            q = s_plus.copy()
        else:
            # Pełny wzór COPRAS
            # Q_i = S_i+ + (Σ S_k-) / (S_i- × Σ(1/S_k-))
            denominator = s_minus * sum_inverse_s_minus
            denominator = denominator.replace(0, np.nan)

            q = s_plus + sum_s_minus / denominator

            # Dla jednostek z S- = 0, Q = S+
            q = q.fillna(s_plus)

        q.name = "Q"
        return q

    def calculate_u(self, q: pd.Series) -> pd.Series:
        """
        Krok 5: Oblicza U_i (stopień użyteczności).

        U_i = Q_i / Q_max × 100%
        """
        q_max = q.max()

        if q_max == 0:
            u = q * 0
        else:
            u = (q / q_max) * 100

        u.name = "U"
        return u

    def calculate_rank(self, u: pd.Series) -> pd.Series:
        """
        Krok 6: Oblicza ranking (1 = najlepszy).
        """
        rank = u.rank(ascending=False, method="min").astype(int)
        rank.name = "rank"
        return rank

    def calculate(self, df: pd.DataFrame, year: int) -> CoprasResult:
        """
        Wykonuje pełną kalkulację COPRAS dla danego roku.

        Args:
            df: dane znormalizowane (var_id, unit_id, year, value_normalized)
            year: rok do analizy

        Returns:
            CoprasResult z wynikami
        """
        # Krok 1: Wartości ważone
        df_weighted = self.calculate_weighted_values(df, year)

        # Krok 2: S+
        s_plus = self.calculate_s_plus(df_weighted)

        # Krok 3: S-
        s_minus = self.calculate_s_minus(df_weighted)

        # Krok 4: Q
        q = self.calculate_q(s_plus, s_minus)

        # Krok 5: U
        u = self.calculate_u(q)

        # Krok 6: Ranking
        rank = self.calculate_rank(u)

        # Złóż wyniki
        scores = (
            pd.DataFrame(
                {
                    "unit_id": s_plus.index,
                    "S_plus": s_plus.values,
                    "S_minus": s_minus.values,
                    "Q": q.values,
                    "U": u.values,
                    "rank": rank.values,
                }
            )
            .sort_values("rank")
            .reset_index(drop=True)
        )

        return CoprasResult(
            year=year,
            scores=scores,
            weights=self.weights.copy(),
            directions=self.directions.copy(),
        )

    def calculate_all_years(self, df: pd.DataFrame) -> dict[int, CoprasResult]:
        """
        Oblicza COPRAS dla wszystkich lat w danych.

        Returns:
            {year: CoprasResult}
        """
        years = sorted(df["year"].unique())
        results = {}

        for year in years:
            results[year] = self.calculate(df, year)

        return results

    def get_ranking(self, df: pd.DataFrame, year: int) -> pd.DataFrame:
        """
        Zwraca ranking dla danego roku.

        Returns:
            DataFrame: unit_id, Q, U, rank
        """
        result = self.calculate(df, year)
        return result.scores[["unit_id", "Q", "U", "rank"]]

    def get_available_years(self, df: pd.DataFrame) -> list[int]:
        """Zwraca dostępne lata w danych."""
        return sorted(df["year"].unique().tolist())


def print_copras_result(result: CoprasResult) -> None:
    """Wyświetla wynik COPRAS."""
    print("=" * 70)
    print(f"COPRAS - ROK {result.year}")
    print("=" * 70)

    # Kierunki
    stim = [k for k, v in result.directions.items() if v == VariableDirection.STIMULANT]
    dest = [
        k for k, v in result.directions.items() if v == VariableDirection.DESTIMULANT
    ]

    print(f"\nStymulanty: {stim}")
    print(f"Destymulanty: {dest}")

    # Wagi
    print(f"\nWagi:")
    for var_id, weight in result.weights.items():
        direction = result.directions.get(var_id, "?")
        print(f"  {var_id}: {weight:.4f} ({direction})")

    # Wyniki
    print(
        f"\n{'unit_id':>12} | {'S+':>8} | {'S-':>8} | {'Q':>8} | {'U':>8} | {'rank':>4}"
    )
    print("-" * 60)

    for _, row in result.scores.iterrows():
        print(
            f"{row['unit_id']:>12} | "
            f"{row['S_plus']:>8.4f} | "
            f"{row['S_minus']:>8.4f} | "
            f"{row['Q']:>8.4f} | "
            f"{row['U']:>8.2f} | "
            f"{row['rank']:>4}"
        )

    print("=" * 70)


if __name__ == "__main__":
    import pandas as pd
    from copras import CoprasCalculator, VariableDirection, print_copras_result

    # Dane znormalizowane
    df = pd.DataFrame(
        {
            "var_id": [1, 1, 1, 2, 2, 2, 3, 3, 3] * 2,
            "unit_id": ["MAZ", "SLA", "WLK"] * 6,
            "year": [2022] * 9 + [2023] * 9,
            "value_normalized": [
                # 2022
                0.85,
                0.45,
                0.65,  # var 1 (PKB - stymulanta)
                0.30,
                0.80,
                0.50,  # var 2 (bezrobocie - destymulanta)
                0.70,
                0.60,
                0.75,  # var 3 (edukacja - stymulanta)
                # 2023
                0.90,
                0.50,
                0.70,
                0.25,
                0.75,
                0.45,
                0.75,
                0.65,
                0.80,
            ],
        }
    )

    # Konfiguracja
    directions = {
        1: VariableDirection.STIMULANT,  # PKB
        2: VariableDirection.DESTIMULANT,  # bezrobocie
        3: VariableDirection.STIMULANT,  # edukacja
    }

    weights = {
        1: 0.5,  # PKB - 50%
        2: 0.3,  # bezrobocie - 30%
        3: 0.2,  # edukacja - 20%
    }

    # Kalkulator
    calc = CoprasCalculator(directions=directions, weights=weights)

    # Dostępne lata
    print("Dostępne lata:", calc.get_available_years(df))

    # Wynik dla 2022
    result_2022 = calc.calculate(df, year=2022)
    print_copras_result(result_2022)

    # Wynik dla 2023
    result_2023 = calc.calculate(df, year=2023)
    print_copras_result(result_2023)

    # Tylko ranking
    ranking = calc.get_ranking(df, year=2022)
    print("\nRanking 2022:")
    print(ranking)

    # Wszystkie lata
    all_results = calc.calculate_all_years(df)
    for year, result in all_results.items():
        print(f"\nRok {year}: Lider = {result.scores.iloc[0]['unit_id']}")
