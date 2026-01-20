import sqlite3
import pandas as pd
from loguru import logger

from srcc.utils.utils import get_project_root, get_current_time
from srcc.utils.dataclasses import Unit, Variable, RawData, VariableQuality


class BDLDatabase:
    """Klasa do obsługi bazy danych BDL."""

    SCHEMA = """
        CREATE TABLE IF NOT EXISTS units (
            unit_id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS variables (
            variable_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT,
            weight INTEGER
        );

        CREATE TABLE IF NOT EXISTS raw_data (
            variable_id TEXT NOT NULL,
            unit_id TEXT NOT NULL,
            year INTEGER NOT NULL,
            value REAL,
            downloaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (variable_id, unit_id, year)
        );

        CREATE TABLE IF NOT EXISTS variable_quality (
            variable_id TEXT NOT NULL,
            year INTEGER NOT NULL,
            na REAL,
            cv REAL,
            skewness REAL,
            na_status TEXT,
            cv_status TEXT,
            skewness_status TEXT,
            correlation_status TEXT,
            status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (variable_id, year)
        );
    """

    def __init__(self, database_name: str = None):
        database_name = (
            database_name
            or f"db_{get_current_time().replace(' ', '_').replace(':', '-')}.db"
        )
        self.db_path = get_project_root() / "bdl" / database_name

        logger.info(f"BDLDatabase initialized with database path: {self.db_path}")

    def _connect(self) -> sqlite3.Connection:
        """Tworzy połączenie z bazą danych."""
        logger.info("Opening SQLite database connection.")
        return sqlite3.connect(self.db_path)

    def init_db(self) -> "BDLDatabase":
        """Tworzy strukturę bazy danych."""
        with self._connect() as conn:
            conn.executescript(self.SCHEMA)
        logger.info("Database schema initialized successfully.")
        return self

    # ==================== INSERT ====================

    def insert_units(self, units: list[Unit]) -> None:
        """Wstawia jednostki."""
        with self._connect() as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO units (unit_id, name) VALUES (?, ?)",
                [unit.to_tuple() for unit in units],
            )
        logger.info("Units inserted successfully.")

    def insert_variables(self, variables: list[Variable]) -> None:
        """Wstawia zmienne."""
        with self._connect() as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO variables (variable_id, name, type, weight) VALUES (?, ?, ?, ?)",
                [variable.to_tuple() for variable in variables],
            )
        logger.info("Variables inserted successfully.")

    def insert_raw_data(self, raw_data: RawData) -> None:
        """Wstawia surowe dane."""
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO raw_data (variable_id, unit_id, year, value) VALUES (?, ?, ?, ?)",
                raw_data.to_tuple(),
            )
        logger.info("Raw data inserted successfully.")

    def insert_variable_quality(self, quality: VariableQuality) -> None:
        """Wstawia metryki jakości."""
        with self._connect() as conn:
            conn.execute(
                """
                    INSERT OR REPLACE INTO variable_quality 
                    (variable_id, year, na, cv, skewness, na_status, cv_status, skewness_status, correlation_status, status) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                quality.to_tuple(),
            )
        logger.info("Variable quality inserted successfully.")

    # ==================== SELECT ====================

    def get_raw_data(
        self, variable_id: str = None, unit_id: str = None, year: int | list[int] = None
    ) -> pd.DataFrame:
        """Pobiera surowe dane z filtrami."""
        query = """
            SELECT d.variable_id, v.name as variable_name, 
                   d.unit_id, u.name as unit_name, 
                   d.year, d.value
            FROM raw_data d
            LEFT JOIN variables v ON d.variable_id = v.variable_id
            LEFT JOIN units u ON d.unit_id = u.unit_id
            WHERE 1=1
        """
        params = []

        if variable_id:
            query += " AND d.variable_id = ?"
            params.append(variable_id)
        if unit_id:
            query += " AND d.unit_id = ?"
            params.append(unit_id)
        if year:
            if isinstance(year, list):
                query += f" AND d.year IN ({','.join('?' * len(year))})"
                params.extend(year)
            else:
                query += " AND d.year = ?"
                params.append(year)

        with self._connect() as conn:
            df = pd.read_sql_query(query, conn, params=params)

        logger.info(f"Raw data fetched successfully (rows={len(df)}).")
        return df

    def get_table(self, table_name: str) -> pd.DataFrame:
        """Pobiera całą tabelę."""
        with self._connect() as conn:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        logger.info(f"Table '{table_name}' fetched (rows={len(df)}).")
        return df

    def get_var_latest_year(self, variable_id: str) -> int | None:
        """Zwraca największy rok dla zmiennej."""
        with self._connect() as conn:
            result = conn.execute(
                "SELECT MAX(year) FROM raw_data WHERE variable_id = ?",
                (variable_id,),
            ).fetchone()

        latest_year = result[0] if result and result[0] else None
        logger.info(f"Latest year for variable_id={variable_id}: {latest_year}")
        return latest_year

    def get_available_variables(self) -> list[str]:
        """Zwraca dostępne zmienne."""
        with self._connect() as conn:
            result = conn.execute(
                "SELECT DISTINCT variable_id FROM raw_data ORDER BY variable_id"
            ).fetchall()

        variables = [row[0] for row in result]
        logger.info(f"Available variables fetched (count={len(variables)}).")
        return variables

    def get_query(self, query: str) -> pd.DataFrame:
        with self._connect() as conn:
            try:
                df = pd.read_sql_query(query, conn)
                logger.info(f"Query executed successfully (rows={len(df)}).")
                return df
            except TypeError:  # NoneType object, gdy nie zwraca tabeli
                conn.execute(query)
                logger.info(f"Query executed successfully.")


if __name__ == "__main__":
    BDLDatabase().init_db()
