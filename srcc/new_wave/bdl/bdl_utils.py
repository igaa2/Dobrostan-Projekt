import streamlit as st
import pandas as pd
from time import sleep
from loguru import logger
from srcc.new_wave.data_classes import Variable
from srcc.new_wave.bdl.bdl_client import BDLClient, DataParams


@st.cache_data
def fetch_most_recent_year_data_for_variables(
    variables: list[Variable],
    params: DataParams,
    sleep_between_requests: float = 0.5,
) -> pd.DataFrame:
    """Pobiera dane z najnowszego dostępnego roku dla listy zmiennych."""
    df = pd.DataFrame()

    with BDLClient(params=params) as client:
        for variable in variables:
            sleep(sleep_between_requests)

            try:
                df_result = client.fetch_most_recent_year_data(
                    variable_id=variable.variable_id
                )
                df_result["variable_id"] = variable.variable_id
                df_result["name"] = variable.name
                df = pd.concat([df, df_result], ignore_index=True)

            except Exception as e:
                logger.error(
                    f"Error fetching data for variable {variable.variable_id}: {e}"
                )
                continue

    return df


if __name__ == "__main__":
    from srcc.utils.utils import get_project_root, load_yaml

    root = get_project_root()
    config = load_yaml(root / "config.yaml")

    data_params = DataParams.from_dict(config["data"]["params"])
    variables = [Variable.from_dict(dictionary=d) for d in config["data"]["variables"]]

    df = fetch_most_recent_year_data_for_variables(
        variables=variables,
        params=data_params,
        sleep_between_requests=1.0,
    )
    print(df)
