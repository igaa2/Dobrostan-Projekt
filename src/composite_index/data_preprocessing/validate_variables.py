# import pandas as pd
from src.composite_index.data_preprocessing.variable_validator import VariableValidator
from src.bdl.bdl_database import BDLDatabase
from src.utils.utils import load_yaml, get_project_root


def main():
    config_path = get_project_root() / "bdl" / "config" / "config.yaml"
    config = load_yaml(config_path)

    # pobierz dane z DB i dokonaj walidacji pojedynczych zmiennych
    db = BDLDatabase(config)
    VV = VariableValidator()

    for var_id in db.get_available_variables():
        year = db.get_var_latest_year(var_id)
        df = db.get_raw_data(year=year)
        pivot_df = df.pivot(index="unit_id", columns="var_id", values="value")

        quality = VV.validate_variable(pivot_df[var_id], var_id, year)
        db.insert_variable_quality(quality)


if __name__ == "__main__":
    main()
