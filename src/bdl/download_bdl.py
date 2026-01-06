from src.bdl.bdl_client import BDLClient
from src.bdl.bdl_database import BDLDatabase
from src.utils.utils import load_yaml, get_project_root


def main():
    config_path = get_project_root() / "bdl" / "config" / "config.yaml"
    config = load_yaml(config_path)

    # pobierz dane z BDL
    client = BDLClient(config)
    units_data = client.get_unit_id_name_tuples()
    vars_data = client.get_var_id_name_tuples()
    raw_data = client.get_variables_tuples()
    client.close_session()

    # zapisz dane w DB
    db = BDLDatabase(config)
    db.init_db()
    db.insert_units(units_data)
    db.insert_variables(vars_data)
    db.insert_raw_data(raw_data)


if __name__ == "__main__":
    main()
