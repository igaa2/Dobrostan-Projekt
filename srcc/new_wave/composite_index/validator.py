import pandas as pd
from scipy import stats
from loguru import logger

from srcc.new_wave.data_classes import VariableQuality, ValidationStatus


class VariableValidator:
    def __init__(
        self,
        na_max: float = 0.0,
        cv_min: float = 0.10,
        skewness_range: tuple[float, float] = (-2.0, 2.0),
        max_correlation: float = 0.7,
    ):
        self.na_max = na_max
        self.cv_min = cv_min
        self.skewness_min, self.skewness_max = skewness_range
        self.max_correlation = max_correlation

    @staticmethod
    def calculate_na(values: pd.Series) -> float:
        """Oblicza udział braków (0-1))."""
        return float(values.isna().mean())

    @staticmethod
    def calculate_cv(values: pd.Series) -> float:
        """Oblicza współczynnik zmienności."""
        mean = values.mean()
        return 0.0 if abs(mean) < 1e-10 else float(values.std() / abs(mean))

    @staticmethod
    def calculate_skewness(values: pd.Series) -> float:
        """Oblicza współczynnik asymetrii."""
        return float(stats.skew(values.dropna(), nan_policy="omit"))

    def _check_status(self, condition: bool) -> ValidationStatus:
        """Zwraca status na podstawie warunku."""
        status = ValidationStatus.PASSED if condition else ValidationStatus.WARNING
        logger.info(f"Validation check result: {status.name}")
        return status

    def validate(
        self, values: pd.Series, correlations: pd.Series, variable_id: str, year: int
    ) -> VariableQuality:
        """Waliduje zmienną."""
        na = self.calculate_na(values)

        clean = values.dropna()
        cv = self.calculate_cv(clean)
        skewness = self.calculate_skewness(clean)

        na_status = self._check_status(na <= self.na_max)
        cv_status = self._check_status(cv >= self.cv_min)
        skewness_status = self._check_status(
            self.skewness_min <= skewness <= self.skewness_max
        )
        correlation_status = self._check_status(
            all(correlations.abs() <= self.max_correlation)
        )

        all_passed = all(
            s == ValidationStatus.PASSED
            for s in [na_status, cv_status, skewness_status, correlation_status]
        )
        status = ValidationStatus.PASSED if all_passed else ValidationStatus.WARNING

        logger.info(
            f"Validation completed for variable {variable_id} (status={status.name})"
        )

        return VariableQuality(
            variable_id=variable_id,
            year=year,
            na=na,
            cv=cv,
            skewness=skewness,
            na_status=na_status,
            cv_status=cv_status,
            skewness_status=skewness_status,
            correlation_status=correlation_status,
            status=status,
        )

    def validate_dataframe(self, df: pd.DataFrame) -> list[VariableQuality]:
        logger.info(f"Starting validation for DataFrame with {len(df)} rows")

        # Pivot i korelacje
        pivot = df.pivot(index="unit_id", columns="variable_id", values="value")
        corr = pivot.corr()
        print(corr)

        qualities = []
        for variable_id, group in df.groupby("variable_id"):
            year = group["year"]
            values = group["value"]
            correlations = corr.loc[variable_id].drop(variable_id)
            qualities.append(self.validate(values, correlations, variable_id, year))

        logger.info(f"Validation finished for {len(qualities)} variables")
        return qualities


if __name__ == "__main__":
    df = pd.DataFrame(
        data=[
            # zmienna 1 (najświeższy rok 2024)
            {"variable_id": "v1", "unit_id": "u1", "year": 2024, "value": 10},
            {"variable_id": "v1", "unit_id": "u2", "year": 2024, "value": 10},
            # zmienna 2 (najświeższy rok 2024)
            {"variable_id": "v2", "unit_id": "u1", "year": 2024, "value": 30},
            {"variable_id": "v2", "unit_id": "u2", "year": 2024, "value": 40},
        ]
    )
    validator = VariableValidator()
    results = validator.validate_dataframe(df)
    for r in results:
        print(r)
