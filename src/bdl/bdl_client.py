from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time


class BDLClient:
    """Klient do API Banku Danych Lokalnych"""

    BASE_URL = "https://bdl.stat.gov.pl/api/v1"

    def __init__(self, config: dict):
        self.session = Session()
        retries = config.get("retries", {})
        self.retry = Retry(
            total=retries.get("max_retries", 3),
            backoff_factor=retries.get("backoff_factor", 1),
            status_forcelist=retries.get("status_forcelist", []),
        )
        self.adapter = HTTPAdapter(max_retries=self.retry)
        self.session.mount("https://", self.adapter)

        self.params = config["params"]
        self.variables = config["variables"]
        self.years_from = config.get("years_from", 2020)
        self.timeout = (10, 30)
        self.time_to_sleep = 3

    def close_session(self):
        """Zamyka sesję, jeśli została utworzona."""
        if self.session:
            self.session.close()
            self.session = None

    def _fetch_all_units(self) -> dict:
        """Zwraca wszystkie wybrane do pobrania jednostki."""
        url = f"{BDLClient.BASE_URL}/Units"
        r = self.session.get(url, params=self.params, timeout=self.timeout)
        r.raise_for_status()
        return r.json().get("results", [])

    def _get_unit_id(self) -> list[str]:
        """Zwraca id jednostki."""
        json_units = self._fetch_all_units()
        return [json_unit["id"] for json_unit in json_units]

    def get_unit_id_name_tuples(self) -> list[tuple[str, str]]:
        """Zwraca pary z id i nazwą jednostki."""
        json_units = self._fetch_all_units()
        return [(json_unit["id"], json_unit["name"]) for json_unit in json_units]

    def get_var_id_name_tuples(self) -> list[tuple[str, str]]:
        """Zwraca pary z id i nazwą zmiennej."""
        return [(json_var["id"], json_var["name"]) for json_var in self.variables]

    def _fetch_variable_all_years(self, var_id: int) -> list[int]:
        """Zwraca możliwe do pobrania lata dla zmiennej var_id."""
        url = f"{BDLClient.BASE_URL}/variables/{var_id}"
        r = self.session.get(url, timeout=self.timeout)
        r.raise_for_status()
        return r.json().get("years", [])

    def _get_variable_selected_years(self, var_id: int) -> list[int]:
        """Zwraca możliwe do pobrania lata dla zmiennej var_id począwszy od self.years_from."""
        all_years = self._fetch_variable_all_years(var_id)
        return [year for year in all_years if year >= self.years_from]

    def _fetch_variable_data(self, var_id: int, unit_level: int) -> dict:
        """Zwraca dane dla zmiennej var_id z dostępnych do pobrania lat począwszy od self.years_from."""
        url = f"{BDLClient.BASE_URL}/data/by-variable/{var_id}"
        years = self._get_variable_selected_years(var_id)
        params = self.params | {"year": years, "unit-level": unit_level}

        r = self.session.get(url, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # TODO mozna podmienic by do bazy danych od razu wrzucało - a nie po całej pętli
    def _get_variables_data(self) -> dict:
        unit_levels = self.params.get("level", [])
        data = {}
        for var in self.variables:
            var_id = var["id"]
            results = []
            for unit_level in unit_levels:
                time.sleep(self.time_to_sleep)
                try:
                    json = self._fetch_variable_data(var_id, unit_level)
                    print(f"wykonano dla {var_id}, {unit_level}.")
                except Exception as e:
                    json = {}
                    print(f"nie wykonano dla {var_id}, {unit_level}, błąd: {e}")
                results += json.get("results", [])
            data[var_id] = results
        return data

    def get_variables_tuples(self) -> list[tuple[str, str, int, float]]:
        data = self._get_variables_data()
        return [
            (str(var_id), unit["id"], int(v["year"]), float(v["val"]))
            for var_id, units in data.items()
            for unit in units
            for v in unit.get("values", [])
        ]


# TODO można dopisać pobieranie konkretnego roku czy coś
# i odświeżanie wtedy za pomocą strealit też tu (mało zapytań)

if __name__ == "__main__":
    from src.utils.utils import load_yaml, get_project_root

    config_path = get_project_root() / "bdl" / "config" / "config.yaml"
    config = load_yaml(config_path)

    client = BDLClient(config)
    print(client.get_variables_tuples())
    client.close_session()
