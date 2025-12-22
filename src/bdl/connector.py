import pandas as pd
import json
import yaml
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class BDLConnector:
    """API connector for BDL."""
    def __init__(self, config_dict: dict):
        self.base_var_data_url = config_dict["base_var_data_url"]
        self.base_var_meta_url = config_dict["base_var_metadata_url"]

        self.session = Session()
        self.retries = Retry(
            total=config_dict["max_retries"],
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )
        self.adapter = HTTPAdapter(max_retries=self.retries)
        self.session.mount("https://", self.adapter)

        self.params = config_dict["params"]
        self.var_id_list = config_dict["var_ids"]
    
    def _fetch_var_last_year(self, var_id: int) -> int:
        """Fetch metadata for variable and return max year."""
        url = f"{self.base_var_meta_url}/{var_id}"
        r = self.session.get(url)
        r.raise_for_status()

        max_year = max(r.json().get("years", None))
        return max_year
    
    def _fetch_var_data_for_last_year(self, var_id: int) -> dict:
        """Fetch BDL variable data using auto-detected latest year."""
        url = f"{self.base_url_data}/{var_id}"
        params = self.params | {"year": self._fetch_var_last_year(var_id)}

        r = self.session.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        return data


if __name__ == "__main__":
    with open("C:/Users/gange/OneDrive/Pulpit/Dobrostan-Projekt/src/bdl/config.yaml", "r") as f:
        config_dict = yaml.safe_load(f) 
    bdl = BDLConnector(config_dict)
    print(bdl.params)
    print(bdl._fetch_var_data_for_last_year(bdl.var_id_list[0]))