import pandas as pd
from scipy import stats
from loguru import logger

from srcc.utils.dataclasses import VariableQuality, ValidationStatus
from srcc.bdl.bdl_database import BDLDatabase


class VariableValidator:
    """
    Walidacja zmiennych do budowy wskaźnika kompozytowego.

    Kryteria:
    - Braki danych: max 0%
    - Współczynnik zmienności (CV): min 10%
    - Skośność: zakres (-2, 2)
    - Korelacja z innymi zmiennymi: max 70%
    """

    def __init__(
        self,
        na_max: float = 0.0,
        cv_min: float = 0.10,
        skewness_range: tuple[float, float] = (-2.0, 2.0),
        max_correlation: float = 0.7,
        database: BDLDatabase = None,
    ):
        self.na_max = na_max
        self.cv_min = cv_min
        self.skewness_min, self.skewness_max = skewness_range
        self.max_correlation = max_correlation
        self.database = database

        logger.info(
            f"VariableValidator initialized "
            f"(na_max={na_max}, cv_min={cv_min}, "
            f"skewness_range={skewness_range}, "
            f"max_correlation={max_correlation}, "
            f"database_connected={database is not None})"
        )

    # ==================== Obliczenia ====================

    @staticmethod
    def calculate_na(values: pd.Series) -> float:
        """Udział braków (0-1)."""
        if len(values) == 0:
            logger.info("NA calculation: empty series, returning 1.0")
            return 1.0

        na_ratio = values.isna().sum() / len(values)
        logger.info(f"NA ratio calculated: {na_ratio:.2f}")
        return na_ratio

    @staticmethod
    def calculate_cv(values: pd.Series) -> float:
        """Współczynnik zmienności = std / mean."""
        mean = values.mean()

        if abs(mean) < 1e-10:
            logger.info("CV calculation: mean close to zero, returning 0.0")
            return 0.0

        cv = values.std() / abs(mean)
        logger.info(f"CV calculated: {cv:.2f}")
        return cv

    @staticmethod
    def calculate_skewness(values: pd.Series) -> float:
        """Współczynnik skośności (Fisher)."""
        skewness = stats.skew(values, nan_policy="omit")
        logger.info(f"Skewness calculated: {skewness:.2f}")
        return skewness

    # ==================== Walidacja ====================

    def _check_status(self, condition: bool) -> ValidationStatus:
        """Zwraca status na podstawie warunku."""
        status = ValidationStatus.PASSED if condition else ValidationStatus.WARNING
        logger.info(f"Validation check result: {status.name}")
        return status

    def validate(
        self, values: pd.Series, correlations: pd.Series, variable_id: str, year: int
    ) -> VariableQuality:
        """Waliduje zmienną i zwraca wynik."""
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
            f"Validation completed for variable {variable_id}, year {year} "
            f"(status={status.name})"
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
        variable_id_col: str = "variable_id",
        unit_id_col: str = "unit_id",
        year_col: str = "year",
        value_col: str = "value",
        save: bool = False,
    ) -> list[VariableQuality]:
        """Waliduje zmienne dla najświeższego dostępnego roku."""
        logger.info(f"Starting validation (rows={len(df)}, save={save})")

        # Najnowszy rok dla każdej zmiennej
        latest_years = df.groupby(variable_id_col)[year_col].max().reset_index()
        latest_years.columns = [variable_id_col, year_col]
        df_latest = latest_years.merge(df, on=[variable_id_col, year_col], how="inner")

        # Pivot: unit_id jako wiersze, variable_id jako kolumny
        correlation_matrix = df_latest.pivot(
            index=unit_id_col,
            columns=variable_id_col,
            values=value_col,
        ).corr(method="pearson")

        qualities = []

        for variable, group in df_latest.groupby([variable_id_col]):
            variable_id = variable[0]
            values = group[value_col]
            year = group[year_col].iloc[0]
            correlations = correlation_matrix.loc[
                variable_id, correlation_matrix.columns.drop(variable_id)
            ]

            logger.info(
                f"Validating: variable_id={variable_id}, year={year}, records={len(values)}, correlations={[f"{x:.2f}" for x in correlations]}"
            )

            quality = self.validate(values, correlations, str(variable_id), int(year))
            qualities.append(quality)

            if save and self.database:
                self.database.insert_variable_quality(quality=quality)

        logger.info(f"Validation completed ({len(qualities)} variables)")

        return qualities


if __name__ == "__main__":
    from srcc.utils.utils import get_project_root, load_yaml

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
    print(results)
    logger.info(f"Validation finished. Total results: {len(results)}")
