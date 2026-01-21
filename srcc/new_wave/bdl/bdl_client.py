import pandas as pd
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from loguru import logger
from srcc.new_wave.data_classes import DataParams


class BDLClient:
    """Klient do API Banku Danych Lokalnych."""

    BASE_URL: str = "https://bdl.stat.gov.pl/api/v1"

    def __init__(self, params: DataParams):
        self.params = params

        self.session: Session | None = None
        self.retry = Retry(
            total=3,  # Ile razy ponowić próbę po błędzie
            backoff_factor=1,  # Mnożnik czasu między próbami, wzór: {backoff_factor} × (2 ^ {numer_próby})
            status_forcelist=[  # Kody HTTP które wymuszają ponowienie
                500,  # Internal Server Error (błąd serwera)
                502,  # Bad Gateway (serwer proxy nie może połączyć się z serwerem)
                503,  # Service Unavailable (serwer przeciążony/w trakcie maintenance)
                504,  # Gateway Timeout (serwer proxy nie doczekał się odpowiedzi)
            ],
        )

    def open(self) -> "BDLClient":
        """Otwiera sesję HTTP."""
        if self.session is not None:
            self.close()

        self.session = Session()
        adapter = HTTPAdapter(max_retries=self.retry)
        self.session.mount("https://", adapter)
        logger.info("HTTP session opened.")
        return self

    def close(self) -> None:
        """Zamyka sesję HTTP."""
        if self.session:
            self.session.close()
            self.session = None
            logger.info("HTTP session closed.")

    def __enter__(self) -> "BDLClient":
        """Inicjalizuje sesję HTTP (with)."""
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Zamyka sesję HTTP (with); exc_type/exc_val/exc_tb to typ, obiekt i traceback wyjątku (None gdy brak błędu)."""
        self.close()

    # ==================== Pobieranie lat ====================

    def fetch_available_years_for_variable(self, variable_id: int) -> list[int]:
        """Pobiera dostępne lata dla zmiennej."""
        url = f"{self.BASE_URL}/variables/{variable_id}"

        logger.info(f"Fetching available years for variable {variable_id}...")
        response = self.session.get(url)
        response.raise_for_status()

        years = response.json().get("years", [])
        logger.info(f"Available years for {variable_id}: {years}")
        return years

    # ==================== Pobieranie danych ====================

    def fetch_most_recent_year_data(self, variable_id: int) -> pd.DataFrame:
        """Pobiera dane z najnowszego dostępnego roku dla podanej zmiennej."""
        url = f"{self.BASE_URL}/data/by-variable/{variable_id}"
        years = self.fetch_available_years_for_variable(variable_id=variable_id)
        year = max(years)

        logger.info(f"Fetching data for variable {variable_id} for year: {year}")
        params = self.params.to_dict() | {"year": year}
        response = self.session.get(url, params=params)
        response.raise_for_status()

        results = response.json().get("results", [])
        df = pd.DataFrame(
            [
                {
                    "unit_id": d["id"],
                    "unit_name": d["name"],
                    "year": v["year"],
                    "value": v["val"],
                }
                for d in results
                for v in d["values"]
            ]
        )
        logger.info(f"Fetched {len(df)} units for variable {variable_id}.")
        return df


if __name__ == "__main__":
    from srcc.utils.utils import get_project_root, load_yaml

    root = get_project_root()
    config = load_yaml(root / "config.yaml")
    data_params = DataParams.from_dict(config["data"]["params"])

    with BDLClient(params=data_params) as client:
        results = client.fetch_most_recent_year_data(variable_id=7737)
        print(results)
