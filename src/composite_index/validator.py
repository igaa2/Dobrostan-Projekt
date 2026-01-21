import pandas as pd
from scipy import stats
from loguru import logger

from src.utils.data_classes import VariableQuality, ValidationStatus


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
        self, values: pd.Series, correlations: pd.Series, variable_id: int, year: int
    ) -> VariableQuality:
        """Waliduje pojedynczą zmienną."""
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

    def validate_dataframe(
        self,
        df: pd.DataFrame,
        variable_col_name: str = "variable_id",
        unit_col_name: str = "unit_id",
        year_col_name: str = "year",
        value_col_name: str = "value",
    ) -> list[VariableQuality]:
        """Waliduje DataFrame."""

        # Pivot i korelacje
        corr = df.pivot(
            index=unit_col_name, columns=variable_col_name, values=value_col_name
        ).corr(method="pearson")

        qualities = []
        for variable_id, group in df.groupby(variable_col_name):
            year = group[year_col_name].iloc[0]
            values = group[value_col_name]
            correlations = corr.loc[variable_id].drop(variable_id)

            qualities.append(
                self.validate(values, correlations, int(variable_id), int(year))
            )

        logger.info(f"Validated {len(qualities)} variables")
        return qualities


if __name__ == "__main__":
    df = pd.DataFrame(
        [
            (
                "011200000000",
                "MAŁOPOLSKIE",
                2024,
                1659.01,
                7737,
                "Przeciętne miesięczne wydatki",
            ),
            (
                "012400000000",
                "ŚLĄSKIE",
                2024,
                1988.83,
                7737,
                "Przeciętne miesięczne wydatki",
            ),
            (
                "020800000000",
                "LUBUSKIE",
                2024,
                1747.05,
                7737,
                "Przeciętne miesięczne wydatki",
            ),
            (
                "023000000000",
                "WIELKOPOLSKIE",
                2024,
                1815.81,
                7737,
                "Przeciętne miesięczne wydatki",
            ),
            (
                "011200000000",
                "MAŁOPOLSKIE",
                2024,
                47.80,
                1725015,
                "Wskaźnik urbanizacji",
            ),
            ("012400000000", "ŚLĄSKIE", 2024, 75.70, 1725015, "Wskaźnik urbanizacji"),
            ("020800000000", "LUBUSKIE", 2024, 64.00, 1725015, "Wskaźnik urbanizacji"),
            (
                "023000000000",
                "WIELKOPOLSKIE",
                2024,
                52.90,
                1725015,
                "Wskaźnik urbanizacji",
            ),
            (
                "011200000000",
                "MAŁOPOLSKIE",
                2024,
                3.61,
                155037,
                "Poszkodowani w wypadkach przy pracy",
            ),
            (
                "012400000000",
                "ŚLĄSKIE",
                2024,
                6.68,
                155037,
                "Poszkodowani w wypadkach przy pracy",
            ),
            (
                "020800000000",
                "LUBUSKIE",
                2024,
                5.03,
                155037,
                "Poszkodowani w wypadkach przy pracy",
            ),
            (
                "023000000000",
                "WIELKOPOLSKIE",
                2024,
                4.80,
                155037,
                "Poszkodowani w wypadkach przy pracy",
            ),
        ],
        columns=["unit_id", "unit_name", "year", "value", "variable_id", "name"],
    )

    results = VariableValidator().validate_dataframe(df)
    for r in results:
        print(r)
