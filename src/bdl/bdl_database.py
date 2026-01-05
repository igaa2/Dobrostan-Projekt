import sqlite3
import pandas as pd
from src.utils.utils import get_project_root, get_current_time_string


class BDLDatabase:
    """Klasa do obsługi tabel z danymi z BDL."""

    def __init__(self, config: dict):
        db_name = config.get("database_name", f"db_{get_current_time_string()}")
        self.db_path = get_project_root() / "bdl" / "database" / db_name
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Tworzy strukturę bazy danych."""
        with self._get_connection() as conn:
            conn.executescript(
                """
                -- Wojewodztwa
                CREATE TABLE IF NOT EXISTS units (
                    unit_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                );
                
                -- Zmienne
                CREATE TABLE IF NOT EXISTS variables (
                    var_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                );

                -- Dane
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
            """
            )

    def insert_units(self, id_name_tuples: list[tuple]) -> None:
        """Wstawia dane jednostek."""
        with self._get_connection() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO units (unit_id, name)
                VALUES (?, ?)
                """,
                id_name_tuples,
            )

    def insert_variables(self, id_name_tuples: list[tuple]) -> None:
        """Wstawia dane jednostek."""
        with self._get_connection() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO units (var_id, name)
                VALUES (?, ?)
                """,
                id_name_tuples,
            )

    def insert_raw_data(
        self, var_id: str, unit_id: str, year: int, value: float
    ) -> None:
        """Wstawia lub aktualizuje dane."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO raw_data 
                (var_id, unit_id, year, value)
                VALUES (?, ?, ?, ?)
                """,
                (var_id, unit_id, year, value),
            )

    def get_df(
        self, var_id: str = None, unit_id: str = None, years: list = None
    ) -> pd.DataFrame:
        """Pobiera dane z filtrami."""
        query = """
            SELECT v.name, u.name, d.year, d.value
            FROM raw_data d
            JOIN variables v ON d.var_id = v.var_id
            JOIN units u ON d.unit_id = u.unit_id
            WHERE 1=1
        """

        if var_id:
            query += f" AND d.var_id = {var_id}"
        if unit_id:
            query += f" AND d.unit_id = {unit_id}"
        if years:
            query += f" AND d.year IN ({', '.join(years)})"

        with self._get_connection() as conn:
            return pd.read_sql_query(query, conn)


if __name__ == "__main__":
    from src.utils.utils import load_yaml

    config_path = get_project_root() / "bdl" / "config" / "config.yaml"
    config = load_yaml(config_path)

    bdl_db = BDLDatabase(config)
