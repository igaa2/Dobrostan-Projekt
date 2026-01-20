from dataclasses import dataclass, astuple, field
from enum import Enum
import pandas as pd


class ValidationStatus(Enum):
    """Etykiety statusu przejścia walidacji."""

    PASSED = "✓ PASSED"
    WARNING = "⚠ WARNING"


class VariableType(Enum):
    """Kierunek zmiennej."""

    STIMULANT = "stimulant"
    DESTIMULANT = "destimulant"


# ==================== Dane ====================


@dataclass
class Unit:
    """Jednostka terytorialna."""

    unit_id: str
    name: str

    def to_tuple(self) -> tuple:
        return astuple(self)


@dataclass
class Variable:
    """Zmienna BDL."""

    variable_id: str
    name: str
    type: VariableType
    weight: int

    def to_tuple(self) -> tuple:
        result = astuple(self)
        return tuple(v.value if isinstance(v, Enum) else v for v in result)

    @property
    def is_stimulant(self) -> bool:
        return self.type == VariableType.STIMULANT

    @property
    def is_destimulant(self) -> bool:
        return self.type == VariableType.DESTIMULANT


@dataclass
class RawData:
    """Surowe dane z BDL."""

    variable_id: str
    unit_id: str
    year: int
    value: float

    def to_tuple(self) -> tuple:
        return astuple(self)


@dataclass
class VariableQuality:
    """Metryki jakości zmiennej."""

    variable_id: str
    year: int
    na: float
    cv: float
    skewness: float
    na_status: ValidationStatus
    cv_status: ValidationStatus
    skewness_status: ValidationStatus
    correlation_status: ValidationStatus
    status: ValidationStatus

    def to_tuple(self) -> tuple:
        result = astuple(self)
        return tuple(v.value if isinstance(v, Enum) else v for v in result)


# ==================== COPRAS ====================


@dataclass
class UnitScore:
    """Wynik COPRAS dla pojedynczej jednostki."""

    unit: Unit
    s_plus: float
    s_minus: float
    q: float
    u: float
    rank: int


@dataclass
class CoprasResult:
    """Wynik COPRAS dla jednego roku."""

    year: int
    unit_scores: list[UnitScore]
    variables: list[Variable]

    @property
    def leader(self) -> Unit:
        """Jednostka na pierwszym miejscu."""
        return self.unit_scores[0].unit

    @property
    def weights(self) -> dict[str, float]:
        """Słownik wag {variable_id: weight}."""
        return {v.variable_id: v.weight for v in self.variables if v.weight}

    @property
    def types(self) -> dict[str, VariableType]:
        """Słownik kierunków {variable_id: type}."""
        return {v.variable_id: v.type for v in self.variables}

    @property
    def stimulants(self) -> list[Variable]:
        """Lista stymulant."""
        return [v for v in self.variables if v.is_stimulant]

    @property
    def destimulants(self) -> list[Variable]:
        """Lista destymulant."""
        return [v for v in self.variables if v.is_destimulant]

    def to_dataframe(self) -> pd.DataFrame:
        """Konwersja do DataFrame (dla kompatybilności)."""
        return pd.DataFrame(
            [
                {
                    "unit_id": score.unit.unit_id,
                    "unit_name": score.unit.name,
                    "S_plus": score.s_plus,
                    "S_minus": score.s_minus,
                    "Q": score.q,
                    "U": score.u,
                    "rank": score.rank,
                }
                for score in self.unit_scores
            ]
        )

    @property
    def ranking(self) -> pd.DataFrame:
        """Uproszczony ranking."""
        return self.to_dataframe()[["unit_id", "unit_name", "U", "rank"]]
