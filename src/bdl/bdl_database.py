import sqlite3
import pandas as pd
from src.utils.utils import get_project_root, get_current_time_string
from src.composite_index.data_preprocessing.variable_validator import (
    VariableValidationResult,
)


class BDLDatabase:
    """Klasa do obsługi tabel z danymi z BDL."""

    def __init__(self, config: dict):
        db_name = config.get("database_name", f"db_{get_current_time_string()}")
        self.db_path = get_project_root() / "bdl" / "database" / db_name

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self) -> None:
        """Tworzy strukturę bazy danych."""
        with self._get_connection() as conn:
            conn.executescript(
                """
                -- Jednostki
                CREATE TABLE IF NOT EXISTS units (
                    unit_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                );
                
                -- Zmienne
                CREATE TABLE IF NOT EXISTS variables (
                    var_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                );

                -- Surowe dane
                CREATE TABLE IF NOT EXISTS raw_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    var_id TEXT NOT NULL,
                    unit_id TEXT NOT NULL,
                    year INTEGER,
                    value REAL,
                    downloaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (var_id) REFERENCES variables(var_id),
                    FOREIGN KEY (unit_id) REFERENCES units(unit_id),
                    UNIQUE(var_id, unit_id, year)
                );

                -- Metryki jakości zmiennych
                CREATE TABLE IF NOT EXISTS variable_quality (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    var_id INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    na REAL, -- udział braków (0 do 1)
                    cv REAL, -- współczynnik zmienności
                    skewness REAL, -- skośność
                    na_status TEXT, -- ✓ PASSED / ✗ FAILED
                    cv_status TEXT, -- ✓ PASSED / ✗ FAILED
                    skewness_status TEXT, -- ✓ PASSED / ✗ FAILED
                    overall_status TEXT, -- ✓ PASSED / ✗ FAILED
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (var_id) REFERENCES variables(var_id),
                    UNIQUE (var_id, year)
                );

                -- Znormalizowane dane
                CREATE TABLE IF NOT EXISTS normalized_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    var_id TEXT NOT NULL,
                    unit_id TEXT NOT NULL,
                    year INTEGER,
                    value REAL,
                    value_normalized REAL,
                    scope TEXT,
                    method TEXT,
                    normalized_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (var_id) REFERENCES variables(var_id),
                    FOREIGN KEY (unit_id) REFERENCES units(unit_id),
                    UNIQUE(var_id, unit_id, year, scope, method)
                );
            """
            )

    def insert_units(self, id_name_tuples: list[tuple[str, str]]) -> None:
        """Wstawia nazwy jednostek."""
        with self._get_connection() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO units (unit_id, name)
                VALUES (?, ?)
                """,
                id_name_tuples,
            )

    def insert_variables(self, id_name_tuples: list[tuple[str, str]]) -> None:
        """Wstawia nazwy zmiennych."""
        with self._get_connection() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO variables (var_id, name)
                VALUES (?, ?)
                """,
                id_name_tuples,
            )

    def insert_raw_data(
        self, raw_data_tuple: list[tuple[str, str, int, float]]
    ) -> None:
        """Wstawia lub aktualizuje dane."""
        with self._get_connection() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO raw_data 
                (var_id, unit_id, year, value)
                VALUES (?, ?, ?, ?)
                """,
                raw_data_tuple,
            )

    def insert_variable_quality(
        self, variable_quality: VariableValidationResult
    ) -> None:
        """Wstawia lub aktualizuje dane."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO variable_quality (
                    var_id, year, na, cv, skewness,
                    na_status, cv_status, skewness_status, overall_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                variable_quality.to_tuple(),
            )

    def insert_normalized_data(self, normalized_data: pd.DataFrame) -> None:
        """Wstawia lub aktualizuje dane."""
        with self._get_connection() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO normalized_data 
                (var_id, unit_id, year, value, value_normalized, scope, method)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                normalized_data[
                    [
                        "var_id",
                        "unit_id",
                        "year",
                        "value",
                        "value_normalized",
                        "scope",
                        "method",
                    ]
                ].itertuples(index=False),
            )

    def get_raw_data(
        self, var_id: str = None, unit_id: str = None, year: int | list[int] = None
    ) -> pd.DataFrame:
        """Pobiera dane z filtrami."""
        query = """
            SELECT v.var_id, v.name, u.unit_id, u.name, d.year, d.value
            FROM raw_data d
            JOIN variables v ON d.var_id = v.var_id
            JOIN units u ON d.unit_id = u.unit_id
            WHERE 1=1
        """

        if var_id:
            query += f" AND d.var_id = {var_id}"
        if unit_id:
            query += f" AND d.unit_id = {unit_id}"
        if year:
            query += f" AND d.year IN ({', '.join(map(str, year)) if type(year) is list else year})"

        with self._get_connection() as conn:
            return pd.read_sql_query(query, conn)

    def get_query(self, query: str) -> pd.DataFrame:
        with self._get_connection() as conn:
            try:
                return pd.read_sql_query(query, conn)
            except TypeError:  # NoneType object, gdy nie zwraca tabeli
                conn.execute(query)

    def get_var_latest_year(self, var_id: int) -> int | None:
        """Zwraca największy dostępny rok dla danej zmiennej."""
        query = "SELECT MAX(year) FROM raw_data WHERE var_id = ?"
        with self._get_connection() as conn:
            result = conn.execute(
                query, (var_id,)
            ).fetchone()  # fetchone() zwraca tuple
        return result[0] if result else None

    def get_available_variables(self) -> list[int]:
        """Zwraca dostępne zmienne."""
        query = "SELECT DISTINCT var_id FROM raw_data ORDER BY var_id"
        with self._get_connection() as conn:
            result = conn.execute(query).fetchall()  # fetchall() zwraca tuple
        return [row[0] for row in result]


if __name__ == "__main__":
    from src.utils.utils import load_yaml

    config_path = get_project_root() / "bdl" / "config" / "config.yaml"
    config = load_yaml(config_path)

    db = BDLDatabase(config)
