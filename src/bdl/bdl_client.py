from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


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

    def close_session(self):
        """Zamyka sesję, jeśli została utworzona."""
        if self.session:
            self.session.close()
            self.session = None

    def _fetch_all_units(self) -> dict:
        """Zwraca wszystkie wybrane do pobrania jednostki."""
        url = f"{BDLClient.BASE_URL}/Units"
        r = self.session.get(url, params=self.params)
        r.raise_for_status()
        return r.json().get("results", [])

    def get_unit_id_name_tuples(self) -> list[tuple]:
        """Zwraca pary z id i nazwą jednostki."""
        json_units = self._fetch_all_units()
        return [(json_unit["id"], json_unit["name"]) for json_unit in json_units]

    def get_var_id_name_tuples(self) -> list[tuple]:
        """Zwraca pary z id i nazwą zmiennej."""
        return [(json_var["id"], json_var["name"]) for json_var in self.variables]

    def _fetch_variable_all_years(self, var_id: int) -> list:
        """Zwraca możliwe do pobrania lata dla zmiennej var_id."""
        url = f"{BDLClient.BASE_URL}/variables/{var_id}"
        r = self.session.get(url)
        r.raise_for_status()
        return r.json().get("years", [])

    def _fetch_variable_year_data(self, var_id: int, year: int) -> dict:
        """Zwraca dane z roku year dla zmiennej var_id."""
        url = f"{BDLClient.BASE_URL}/data/by-variable/{var_id}"
        params = self.params | {"year": year}

        r = self.session.get(url, params=params)
        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    from src.utils.utils import load_yaml, get_project_root

    config_path = get_project_root() / "bdl" / "config" / "config.yaml"
    config = load_yaml(config_path)

    bdl = BDLClient(config)
    print()
    # print(bdl.get_unit_id_name_tuples())
    print()
    # print(bdl.fetch_variable_all_years(7737))
    # print()
    # print(bdl.fetch_variable_year_data(7737, 2024))
    print()
    bdl.close_session()
