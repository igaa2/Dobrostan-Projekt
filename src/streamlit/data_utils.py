import streamlit as st
import pandas as pd
import numpy as np
from time import sleep
from loguru import logger
from src.utils.data_classes import Variable
from src.bdl.bdl_client import BDLClient, DataParams
from src.composite_index.validator import VariableValidator


# ==================== POBIERANIE DANYCH ====================


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


# ==================== WALIDACJA ====================


@st.cache_data
def validate_and_extract_validation(df: pd.DataFrame):
    validation = VariableValidator().validate_dataframe(df)

    validation_infos = {v.variable_id: v.validation_info() for v in validation}
    validation_cv = {v.variable_id: v.cv for v in validation}

    return validation_infos, validation_cv


# ==================== NORMALIZACJA ====================


def vector_normalize(series: pd.Series) -> list[float]:
    """Normalizacja wektorowa: x / √(Σx²)."""
    sum_squared = (series**2).sum()
    sqrt_sum = np.sqrt(sum_squared)

    if abs(sqrt_sum) < 1e-10:
        logger.warning("sqrt_sum equals 0, returning zero vector for normalization.")
        return [0.0] * len(series)

    return (series / sqrt_sum).tolist()


@st.cache_data
def normalize_per_variable(
    df: pd.DataFrame,
    value_col_name: str = "value",
    variable_col_name: str = "variable_id",
) -> pd.DataFrame:
    """Normalizuje dane dla każdej zmiennej (grupując po variable_col_name)."""
    df = df.copy()

    df[value_col_name] = df.groupby(variable_col_name)[value_col_name].transform(
        vector_normalize
    )

    logger.info("Vector normalization completed.")
    return df


if __name__ == "__main__":
    from src.utils.utils import get_project_root, load_yaml

    root = get_project_root()
    config = load_yaml(root / "config.yaml")

    data_params = DataParams.from_dict(config["data"]["params"])
    variables = [Variable.from_dict(dictionary=d) for d in config["data"]["variables"]][
        :3
    ]

    df = fetch_most_recent_year_data_for_variables(
        variables=variables,
        params=data_params,
        sleep_between_requests=1.0,
    )
    print(df.head(3))

    df_result = normalize_per_variable(df)
    print(df_result.head(3))
