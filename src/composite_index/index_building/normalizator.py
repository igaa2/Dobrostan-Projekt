import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum


class NormalizationScope(Enum):
    """Zakres normalizacji."""

    PER_YEAR = "per_year"  # normalizacja każdego roku osobno dla pojedynczej zmiennej
    # - ranking statyczy bardziej / relacja pomiedzy jednostkami w danym roku
    PER_VARIABLE = "per_variable"  # normalizacja pojedynczej zmiennej
    # w opraciu o wszytskie wartości dla niej - trend wzrostowy


class MinMaxNormalizer:
    """Normalizacja Min-Max do zakresu [0, 1] według wzoru: (x - min) / (max - min)."""

    def __init__(self, scope: NormalizationScope = NormalizationScope.PER_YEAR):
        self.scope = scope

    def _normalize_series(self, series: pd.Series) -> list:
        """Normalizuje pojedynczą serię do [0, 1]."""
        min_val = series.min()
        max_val = series.max()

        if max_val == min_val:
            return pd.Series(0.5, index=series.index, name=series.name)
        return ((series - min_val) / (max_val - min_val)).values

    def normalize_raw_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalizuje dane dla wszystkich zmiennych.

        Oczekiwany format:
            var_id | unit_id | year | value

        Zwracany format:
            var_id | unit_id | year | value | value_normalized | scope
        """
        df = df.copy()
        df["value_normalized"] = np.nan

        if self.scope == NormalizationScope.PER_YEAR:
            # Normalizacja dla każdej kombinacji var_id + year
            df["value_normalized"] = df.groupby(["var_id", "year"])["value"].transform(
                self._normalize_series
            )
            df["scope"] = NormalizationScope.PER_YEAR.value
        elif self.scope == NormalizationScope.PER_VARIABLE:
            # Normalizacja dla każdej zmiennej (wszystkie lata razem)
            df["value_normalized"] = df.groupby(["var_id"])["value"].transform(
                self._normalize_series
            )
            df["scope"] = NormalizationScope.PER_VARIABLE.value
        else:
            pass

        return df


if __name__ == "__main__":
    df = pd.DataFrame(
        {
            "var_id": [1, 1, 1, 2, 2, 2, 1, 1, 1, 2, 2, 2],
            "unit_id": [
                "M",
                "S",
                "W",
                "M",
                "S",
                "W",
                "M",
                "S",
                "W",
                "M",
                "S",
                "W",
            ],
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
            "value": [
                72000,
                40000,
                35000,
                3.2,
                9.8,
                5.2,
                75000,
                45000,
                55000,
                5.2,
                7.8,
                4.5,
            ],
        }
    )
    MMN = MinMaxNormalizer(scope=NormalizationScope.PER_VARIABLE)
    print(MMN.normalize_raw_data(df))
