import pandas as pd
import numpy as np
from enum import Enum
from src.composite_index.index_building.normalizer import Scope
from src.composite_index.data_preprocessing.variable_validator import VariableValidator


class WeightsMethod(Enum):
    """Metody ważenia zmiennych."""

    CUSTOM = "własne wagi"
    CV_BASED = "wagi według udziału współczynnika zmienności"


class WeightsCalculator:
    """Klasa do obliczania wag dla zmiennej."""

    def __init__(
        self,
        scope: Scope = Scope.PER_YEAR,
        method: WeightsMethod = WeightsMethod.CV_BASED,
    ):
        self.scope = scope
        self.method = method

    @staticmethod
    def _custom_weights(series: pd.Series) -> list:
        pass

    @staticmethod
    def _cv_based_weights(series: pd.Series) -> list:
        cv = VariableValidator.calculate_cv(series)
        return cv / cv.sum()

    def _weigh_series(
        self,
        series: pd.Series,
    ) -> list:
        """Waży serię wybraną metodą."""
        if self.method == WeightsMethod.CUSTOM:
            return WeightsCalculator._custom_weights(series)
        elif self.method == WeightsMethod.CV_BASED:
            return WeightsCalculator._cv_based_weights(series)
        else:
            pass

    def weigh_normalized_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Waży dane dla wszystkich zmiennych.

        Oczekiwany format:
            var_id | unit_id | year | value_normalized | scope | method

        Zwracany format:
            var_id | unit_id | year | value_weighted | method
        """
        df = df.copy()
        df["value_weighted"] = np.nan

        if self.scope == Scope.PER_YEAR:
            # Ważenie dla każdej kombinacji var_id + year
            df["value_weighted"] = df.groupby(["var_id", "year"])[
                "value_normalized"
            ].transform(self._weigh_series)
        elif self.scope == Scope.PER_VARIABLE:
            # Ważenie dla każdej zmiennej (wszystkie lata razem)
            df["value_weighted"] = df.groupby(["var_id"])["value_normalized"].transform(
                self._weigh_series
            )
        else:
            pass

        df.drop(columns=["value_normalized"], inplace=True)
        df["scope"] = self.scope.value
        df["method"] = self.method.value
        return df


# # analytics/index_building/weights.py
# import pandas as pd
# import numpy as np
# from enum import Enum


# class Scope(Enum):
#     """Zakres obliczeń."""
#     PER_YEAR = "per_year"
#     PER_VARIABLE = "per_variable"


# class WeightsMethod(Enum):
#     """Metody ważenia zmiennych."""
#     CUSTOM = "custom"
#     CV_BASED = "cv_based"


# class WeightsCalculator:
#     """Klasa do obliczania i aplikowania wag."""

#     def __init__(
#         self,
#         scope: Scope = Scope.PER_YEAR,
#         method: WeightsMethod = WeightsMethod.CV_BASED,
#         custom_weights: dict[int, float] = None,  # {var_id: waga}
#     ):
#         self.scope = scope
#         self.method = method
#         self.custom_weights = custom_weights
#         self.calculated_weights: dict = {}  # wynik obliczeń

#     def _calculate_cv(self, series: pd.Series) -> float:
#         """Oblicza współczynnik zmienności."""
#         mean = series.mean()
#         if mean == 0:
#             return 0.0
#         return float(series.std() / mean)

#     def _calculate_cv_weights(self, df: pd.DataFrame, year: int = None) -> dict:
#         """
#         Oblicza wagi na podstawie CV.

#         Wzór: w_j = CV_j / Σ CV
#         """
#         if year is not None:
#             data = df[df["year"] == year]
#         else:
#             data = df

#         # CV dla każdej zmiennej
#         cv_per_var = data.groupby("var_id")["value_normalized"].agg(self._calculate_cv)

#         total_cv = cv_per_var.sum()

#         if total_cv == 0:
#             # Równe wagi jeśli CV = 0
#             n = len(cv_per_var)
#             return {var_id: 1/n for var_id in cv_per_var.index}

#         weights = (cv_per_var / total_cv).to_dict()
#         return weights

#     def _normalize_custom_weights(self, var_ids: list) -> dict:
#         """Normalizuje własne wagi do sumy = 1."""
#         if self.custom_weights is None:
#             raise ValueError("Brak custom_weights")

#         # Filtruj tylko zmienne z danych
#         weights = {k: v for k, v in self.custom_weights.items() if k in var_ids}

#         if not weights:
#             raise ValueError("Brak wag dla podanych zmiennych")

#         total = sum(weights.values())

#         if total == 0:
#             raise ValueError("Suma wag = 0")

#         return {k: v / total for k, v in weights.items()}

#     def calculate_weights(self, df: pd.DataFrame, year: int = None) -> dict:
#         """Oblicza wagi wybraną metodą."""
#         var_ids = df["var_id"].unique().tolist()

#         if self.method == WeightsMethod.CV_BASED:
#             weights = self._calculate_cv_weights(df, year)
#         else:  # CUSTOM
#             weights = self._normalize_custom_weights(var_ids)

#         self.calculated_weights = weights
#         return weights

#     def apply_weights(self, df: pd.DataFrame) -> pd.DataFrame:
#         """
#         Oblicza i aplikuje wagi do danych.

#         Wejście: var_id | unit_id | year | value_normalized
#         Wyjście: var_id | unit_id | year | value_normalized | weight | value_weighted
#         """
#         df = df.copy()

#         if self.scope == Scope.PER_YEAR:
#             # Wagi osobno dla każdego roku
#             all_weights = []

#             for year in df["year"].unique():
#                 weights = self.calculate_weights(df, year=year)

#                 for var_id, weight in weights.items():
#                     all_weights.append({
#                         "var_id": var_id,
#                         "year": year,
#                         "weight": weight
#                     })

#             weights_df = pd.DataFrame(all_weights)
#             df = df.merge(weights_df, on=["var_id", "year"])

#         else:  # PER_VARIABLE
#             # Wagi dla wszystkich lat razem
#             weights = self.calculate_weights(df, year=None)
#             df["weight"] = df["var_id"].map(weights)

#         # Aplikuj wagi
#         df["value_weighted"] = df["value_normalized"] * df["weight"]

#         return df

#     def get_weights_summary(self) -> pd.DataFrame:
#         """Zwraca podsumowanie wag."""
#         return pd.DataFrame([
#             {"var_id": k, "weight": v}
#             for k, v in self.calculated_weights.items()
#         ])


if __name__ == "__main__":
    df = pd.DataFrame(
        {
            "var_id": [1, 1, 1, 2, 2, 2, 1, 1, 1, 2, 2, 2],
            "unit_id": ["M", "S", "W", "M", "S", "W", "M", "S", "W", "M", "S", "W"],
            "year": [2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3],
            "value": [72, 40, 25, 3.2, 9.8, 5.2, 75, 45, 55, 5.2, 7.8, 4.5],
        }
    )
    MMN = WeightsCalculator(scope=Scope.PER_VARIABLE, method=WeightsMethod.CUSTOM)
    print(MMN.weigh_normalized_data(df))
