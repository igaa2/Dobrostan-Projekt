import pandas as pd
import numpy as np
from enum import Enum


class Scope(Enum):
    """Zakres normalizacji."""

    PER_YEAR = "per_year"  # normalizacja każdego roku osobno dla pojedynczej zmiennej
    # - ranking statyczy bardziej / relacja pomiedzy jednostkami w danym roku
    PER_VARIABLE = "per_variable"  # normalizacja pojedynczej zmiennej
    # w opraciu o wszytskie wartości dla niej - trend wzrostowy


class NormalizationMethod(Enum):
    """Metody normalizacji."""

    MIN_MAX = "min_max"
    VECTOR = "vector"


class Normalizer:
    """Klasa do przeprowadzenia normalizacji zmiennych."""

    def __init__(
        self,
        scope: Scope = Scope.PER_YEAR,
        method: NormalizationMethod = NormalizationMethod.VECTOR,
    ):
        self.scope = scope
        self.method = method

    @staticmethod
    def _min_max_normalize(series: pd.Series) -> list:
        """Normalizuje pojedynczą serię do [0, 1] według wzoru: (x - min) / (max - min)."""
        min_val = series.min()
        max_val = series.max()

        if max_val == min_val:
            return pd.Series(0.5, index=series.index, name=series.name)
        return ((series - min_val) / (max_val - min_val)).values

    @staticmethod
    def _vector_normalize(series: pd.Series) -> list:
        """Normalizacja wektorowa według wzoru: r = x / √(Σx²)"""
        squared = series**2
        sum_squared = squared.sum()
        sqrt_sum = np.sqrt(sum_squared)

        if sqrt_sum == 0:
            return pd.Series(0.0, index=series.index, name=series.name).values
        return (series / sqrt_sum).values

    def _normalize_series(self, series: pd.Series) -> list:
        """Normalizuje serię wybraną metodą."""
        if self.method == NormalizationMethod.VECTOR:
            return Normalizer._vector_normalize(series)
        elif self.method == NormalizationMethod.MIN_MAX:
            return Normalizer._min_max_normalize(series)
        else:
            pass

    def normalize_raw_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalizuje dane dla wszystkich zmiennych.

        Oczekiwany format:
            var_id | unit_id | year | value

        Zwracany format:
            var_id | unit_id | year | value_normalized | scope | method
        """
        df = df.copy()
        df["value_normalized"] = np.nan

        if self.scope == Scope.PER_YEAR:
            # Normalizacja dla każdej kombinacji var_id + year
            df["value_normalized"] = df.groupby(["var_id", "year"])["value"].transform(
                self._normalize_series
            )
        elif self.scope == Scope.PER_VARIABLE:
            # Normalizacja dla każdej zmiennej (wszystkie lata razem)
            df["value_normalized"] = df.groupby(["var_id"])["value"].transform(
                self._normalize_series
            )
        else:
            pass

        df.drop(columns=["value"], inplace=True)
        df["scope"] = self.scope.value
        df["method"] = self.method.value
        return df


if __name__ == "__main__":
    df = pd.DataFrame(
        {
            "var_id": [1, 1, 1, 2, 2, 2, 1, 1, 1, 2, 2, 2],
            "unit_id": ["M", "S", "W", "M", "S", "W", "M", "S", "W", "M", "S", "W"],
            "year": [2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3],
            "value": [72, 40, 25, 3.2, 9.8, 5.2, 75, 45, 55, 5.2, 7.8, 4.5],
        }
    )
    MMN = Normalizer(scope=Scope.PER_VARIABLE, method=NormalizationMethod.VECTOR)
    print(MMN.normalize_raw_data(df))
