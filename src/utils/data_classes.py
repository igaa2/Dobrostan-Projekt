from dataclasses import dataclass, astuple
from typing import Any, Type, Literal
from enum import Enum


class SessionStatePrefix(Enum):
    """Prefiksy wykorzystywane przy tworzeniu kluczy w session_state."""

    SLIDER = "wagi"
    # SLIDER_TMP = "tmpwagi"
    TOGGLE = "typy"
    # TOGGLE_TMP = "tmptypy"

    def key(self, *parts: Any) -> str:
        return f"{self.value}_{'_'.join(map(str, parts))}"

    def extract(self, dictionary: dict[str, Any]) -> dict[str, Any]:
        """Wyciąga z dict tylko klucze z danym prefiksem."""
        return {
            int(k[len(self.value) + 1 :]): v
            for k, v in dictionary.items()
            if isinstance(k, str) and k.startswith(self.value)
        }

    @classmethod
    def extract_sliders_keys(cls, dictionary: dict[str, Any]) -> dict[str, Any]:
        """Zwraca słownik z wagami."""
        return cls.SLIDER.extract(dictionary)

    @classmethod
    def extract_toggles_keys(cls, dictionary: dict[str, Any]) -> dict[str, Any]:
        """Zwraca słownik z indykatorem destymulant."""
        return cls.TOGGLE.extract(dictionary)


class ValidationStatus(Enum):
    """Etykiety statusu przejścia walidacji."""

    PASSED = "✓"
    WARNING = "⚠"


@dataclass(frozen=True)
class Variable:
    variable_id: int
    name: str
    stimulant: bool  # False = stymulanta, True = destymulanta
    weight: int

    def __post_init__(self):
        """Automatyczna walidacja typów po inicjalizacji."""
        errors = [
            e
            for e in (
                self._check_value_type(self.variable_id, int, "variable_id"),
                self._check_value_type(self.name, str, "name"),
                self._check_value_type(self.stimulant, bool, "stimulant"),
                self._check_value_type(self.weight, int, "weight"),
            )
            if e is not None
        ]

        if errors:
            raise TypeError("Invalid types detected:\n- " + "\n- ".join(errors))

    @staticmethod
    def _check_value_type(
        value: Any, expected_type: Type[Any], name: str
    ) -> str | None:
        """Porównuje typ wartości z oczekiwanym typem."""
        if not isinstance(value, expected_type):
            return f"{name} must be {expected_type.__name__}, got {type(value).__name__}: {value!r}"
        return None

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]) -> "Variable":
        """Tworzy Variable z dicta."""

        required = {"variable_id", "name", "stimulant", "weight"}
        missing = required - dictionary.keys()
        if missing:
            raise KeyError(f"Missing keys in dictionary: {missing}")

        return cls(
            variable_id=dictionary["variable_id"],
            name=dictionary["name"],
            stimulant=dictionary["stimulant"],
            weight=dictionary["weight"],
        )


@dataclass
class VariableQuality:
    """Metryki jakości zmiennej."""

    variable_id: int
    year: int
    na: float
    cv: float
    skewness: float
    na_status: ValidationStatus
    cv_status: ValidationStatus
    skewness_status: ValidationStatus
    correlation_status: ValidationStatus
    status: ValidationStatus

    def validation_info(self) -> str:
        """
        Zwraca informację o statusie zmiennej.

        W przypadku negatywnej oceny zwraca informację o wartości metryk, które nie przeszły walidacji.
        """
        if self.status == ValidationStatus.PASSED:
            return ValidationStatus.PASSED.value

        failed = []
        if self.na_status != ValidationStatus.PASSED:
            failed.append(f"udział braków: {self.na:.2%}")
        if self.cv_status != ValidationStatus.PASSED:
            failed.append(f"wsp. zmienności: {self.cv:.2%}")
        if self.skewness_status != ValidationStatus.PASSED:
            failed.append(f"wsp. skośności: {self.skewness:.2%}")
        if self.correlation_status != ValidationStatus.PASSED:
            failed.append(f"wysoka korelacja: {self.correlation_status.value}")
        return f"{ValidationStatus.WARNING.value}: {', '.join(failed)}"


@dataclass(frozen=True)
class DataParams:
    unit_level: Literal[0, 2, 5]
    format: Literal["json", "xml"]
    page_size: int

    def __post_init__(self):
        if self.unit_level not in (0, 2, 5):
            raise ValueError("unit-level must be 0, 2, or 5")

        if self.format not in ("json", "xml"):
            raise ValueError("format must be 'json' or 'xml'")

        if not (0 <= self.page_size <= 100):
            raise ValueError("page-size must be between 0 and 100")

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]) -> "DataParams":
        """Tworzy DataParams z dicta."""

        required = {"unit-level", "format", "page-size"}
        missing = required - dictionary.keys()
        if missing:
            raise KeyError(f"Missing keys in dictionary: {missing}")

        return cls(
            unit_level=dictionary["unit-level"],
            format=dictionary["format"],
            page_size=dictionary["page-size"],
        )

    def to_dict(self) -> dict:
        return {
            "level": self.unit_level,
            "unit-level": self.unit_level,
            "format": self.format,
            "page-size": self.page_size,
        }
