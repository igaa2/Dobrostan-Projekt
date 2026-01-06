import pandas as pd
from scipy import stats
from dataclasses import dataclass, astuple
from enum import Enum


class ValidationStatus(Enum):
    """Etykiety statusu przejścia walidacji."""

    PASSED = "✓ PASSED"
    WARNING = "⚠ WARNING"

    def __repr__(self) -> str:
        return self.value


@dataclass
class VariableValidationResult:
    """Wynik walidacji jednej zmiennej."""

    var_id: int
    year: int
    na: float
    cv: float
    skewness: float
    na_status: ValidationStatus
    cv_status: ValidationStatus
    skewness_status: ValidationStatus
    overall_status: ValidationStatus

    def to_tuple(self) -> tuple:
        """Konwersja do tuple z obsługą Enum (jak astuple)."""
        result = astuple(self)
        # Zamiana Enum na value
        return tuple(v.value if isinstance(v, Enum) else v for v in result)


class VariableValidator:
    """
    Walidacja zmiennych do budowy wskaźnika kompozytowego.

    Kryteria zmiennej:
    - Istnienie braków: maksimum 0%
    - Współczynnik zmienności (CV): minimum 10% (zmienność)
    - Współczynnik skośności: zakres (-2, 2)
    """

    def __init__(
        self,
        na_max: float = 0.0,
        cv_min: float = 0.10,
        skewness_min: float = -2.0,
        skewness_max: float = 2.0,
    ):
        self.na_max = na_max
        self.cv_min = cv_min
        self.skewness_min = skewness_min
        self.skewness_max = skewness_max

    def _calculate_na(self, values: pd.Series) -> float:
        """Oblicza udział braków"""
        n = len(values)
        return 1.0 if n == 0 else float(values.isna().sum() / n)

    def _calculate_cv(self, values: pd.Series) -> float:
        """Oblicza współczynnik zmienności = odchylenie std / średnia."""
        mean = values.mean()
        return float("nan") if mean < 1e-10 else float(values.std() / abs(mean))

    def _calculate_skewness(self, values: pd.Series) -> float:
        """
        Oblicza współczynnik skośności (Fisher).
        0 - rozkład symetryczny
        > 0 - rozkład prawostronny
        < 0 - rozkład lewostronny
        """
        return float(stats.skew(values, nan_policy="omit"))

    def validate_variable(
        self, values: pd.Series, var_id: int, year: int
    ) -> VariableValidationResult:
        """Pełna walidacja."""
        clean_values = values.dropna()
        na = self._calculate_na(clean_values)
        cv = self._calculate_cv(clean_values)
        skewness = self._calculate_skewness(clean_values)

        na_status = (
            ValidationStatus.PASSED if na <= self.na_max else ValidationStatus.WARNING
        )

        cv_status = (
            ValidationStatus.PASSED if cv >= self.cv_min else ValidationStatus.WARNING
        )

        skewness_status = (
            ValidationStatus.PASSED
            if self.skewness_min <= skewness <= self.skewness_max
            else ValidationStatus.WARNING
        )

        # Status ogólny
        if (
            na_status == ValidationStatus.PASSED
            and cv_status == ValidationStatus.PASSED
            and skewness_status == ValidationStatus.PASSED
        ):
            overall_status = ValidationStatus.PASSED
        else:
            overall_status = ValidationStatus.WARNING

        return VariableValidationResult(
            var_id=var_id,
            year=year,
            na=na,
            cv=cv,
            skewness=skewness,
            na_status=na_status,
            cv_status=cv_status,
            skewness_status=skewness_status,
            overall_status=overall_status,
        )

    # TODO chyba wolalabym by tez miec w sql baze z var_id, years i efektem validacji tak by moc z tego zaciagnąc dane do streamlita
    # wtedy pytanie czy insert calej na raz bazy czy kolejno
    # def validate_raw_data(self, df: pd.DataFrame) -> pd.DataFrame:
    #     """Waliduje wszystkie zmienne w df."""
    #     results = []

    #     for var_id in df.columns:
    #         result = self.screen_variable(df[var_id], var_id)
    #         results.append(result.to_dict())

    #     return pd.DataFrame(results)


if __name__ == "__main__":
    VV = VariableValidator()
    result = VV.validate_variable(pd.Series([12.3, 15.7, 19.0, 54.2, 32.12]), 123, 1999)
    print(result.to_dict())
    print(result.to_dict()["overall_status"])
