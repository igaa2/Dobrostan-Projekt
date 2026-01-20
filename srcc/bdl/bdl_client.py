from typing import Iterator
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from time import sleep
from loguru import logger

from srcc.utils.dataclasses import Unit, Variable, RawData, VariableType
from srcc.bdl.bdl_database import BDLDatabase


class BDLClient:
    """Klient do API Banku Danych Lokalnych."""

    BASE_URL: str = "https://bdl.stat.gov.pl/api/v1"

    def __init__(self, config: dict):
        self._config = config
        self._session: Session | None = None

        # Konfiguracja z domyślnymi wartościami
        self._params = config["data"]["params"] | {
            "level": config["data"]["params"]["unit-level"]
        }
        self._variables = config["data"]["variables"]
        self._years_from = config["data"].get("years_from", 2020)

        self._sleep_between_requests = config["request"].get(
            "sleep_between_requests", 3
        )
        retries_config = config["request"].get("retries", {})
        self._retry = Retry(
            total=retries_config.get("max_retries", 3),
            backoff_factor=retries_config.get("backoff_factor", 1),
            status_forcelist=retries_config.get(
                "status_forcelist", [500, 502, 503, 504]
            ),
        )

        self.database = BDLDatabase(
            database_name=config["data"].get("database_name", None)
        ).init_db()

        logger.info("BDLClient initialized.")
        logger.info(f"Variables to fetch: {len(self._variables)}")
        logger.info(f"Years from: {self._years_from}")
        logger.info(f"Sleep between requests: {self._sleep_between_requests}s")

    def open(self) -> "BDLClient":
        """Otwiera sesję HTTP."""
        if self._session is not None:
            self.close()

        self._session = Session()
        adapter = HTTPAdapter(max_retries=self._retry)
        self._session.mount("https://", adapter)
        logger.info("HTTP session opened.")
        return self

    def close(self) -> None:
        """Zamyka sesję HTTP."""
        if self._session:
            self._session.close()
            self._session = None
            logger.info("HTTP session closed.")

    def __enter__(self) -> "BDLClient":
        """Inicjalizuje sesję HTTP (with)."""
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Zamyka sesję HTTP (with); exc_type/exc_val/exc_tb to typ, obiekt i traceback wyjątku (None gdy brak błędu)."""
        self.close()

    # ==================== Pobieranie jednostek ====================

    def fetch_and_insert_units(self) -> list[Unit]:
        """Pobiera listę jednostek terytorialnych."""
        url = f"{self.BASE_URL}/Units"

        logger.info("Fetching units from BDL API...")
        response = self._session.get(url, params=self._params)
        response.raise_for_status()

        results = response.json().get("results", [])
        units = [Unit(unit_id=r["id"], name=r["name"]) for r in results]

        logger.info(f"Fetched {len(units)} units.")
        self.database.insert_units(units=units)

        return units

    # ==================== Pobieranie zmiennych ====================

    def get_and_insert_variables(self) -> list[Variable]:
        """Zwraca listę skonfigurowanych zmiennych."""
        variables = [
            Variable(
                variable_id=str(v["id"]),
                name=v["name"],
                type=(
                    VariableType.STIMULANT
                    if v["type"].lower() == "stymulanta"
                    else VariableType.DESTIMULANT
                ),
                weight=v["weight"],
            )
            for v in self._variables
        ]
        logger.info(f"Prepared {len(variables)} variables from config.")
        self.database.insert_variables(variables=variables)
        return variables

    # ==================== Pobieranie lat ====================

    def fetch_variable_years(self, variable_id: str) -> list[int]:
        """Pobiera dostępne lata dla zmiennej."""
        url = f"{self.BASE_URL}/variables/{variable_id}"

        logger.info(f"Fetching available years for variable {variable_id}...")
        response = self._session.get(url)
        response.raise_for_status()

        all_years = response.json().get("years", [])
        years = [year for year in all_years if year >= self._years_from]

        logger.info(f"Available years for {variable_id}: {years}")
        return years

    # ==================== Pobieranie danych ====================

    def fetch_variable_data(self, variable_id: str) -> list[dict]:
        """Pobiera dane dla pojedynczej zmiennej i poziomu jednostki."""
        url = f"{self.BASE_URL}/data/by-variable/{variable_id}"
        years = self.fetch_variable_years(variable_id=variable_id)

        params = self._params | {"year": years}

        logger.info(f"Fetching data for variable {variable_id} for years: {years}")
        response = self._session.get(url, params=params)
        response.raise_for_status()

        results = response.json().get("results", [])
        logger.info(f"Fetched {len(results)} units for variable {variable_id}.")
        return results

    def fetch_and_insert_all_data(self) -> Iterator[RawData]:
        """Pobiera dane dla wszystkich skonfigurowanych zmiennych."""
        for variable in self._variables:
            variable_id = str(variable["id"])
            logger.info(f"Fetching data for variable: {variable_id}")

            sleep(self._sleep_between_requests)

            try:
                results = self.fetch_variable_data(variable_id=variable_id)

                for unit in results:
                    for value in unit.get("values", []):
                        raw_data = RawData(
                            variable_id=variable_id,
                            unit_id=unit["id"],
                            year=int(value["year"]),
                            value=float(value.get("val", None)),
                        )
                        self.database.insert_raw_data(raw_data=raw_data)

            except Exception as e:
                logger.error(f"Error fetching data for variable {variable_id}: {e}")
                continue


if __name__ == "__main__":
    from srcc.utils.utils import get_project_root, load_yaml

    root = get_project_root()
    config = load_yaml(root / "config.yaml")

    with BDLClient(config) as client:
        client.fetch_and_insert_units()
        client.get_and_insert_variables()
        client.fetch_and_insert_all_data()
