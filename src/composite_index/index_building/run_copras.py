from src.composite_index.index_building.normalizer import Normalizer
from src.composite_index.index_building.weights import WeightsCalculator
from src.bdl.bdl_database import BDLDatabase
from src.utils.utils import load_yaml, get_project_root


def main():
    config_path = get_project_root() / "bdl" / "config" / "config.yaml"
    config = load_yaml(config_path)

    # pobierz dane z DB
    db = BDLDatabase(config)
    df = db.get_raw_data()

    # normalizacja danych
    mmn = Normalizer()
    df_normalized = mmn.normalize_raw_data(df)
    db.insert_normalized_data(df_normalized)

    # ważenie danych
    wc = WeightsCalculator()
    df_weighted = wc.weigh_normalized_data(df_normalized)
    db.insert_weighted_data(df_weighted)


if __name__ == "__main__":
    main()
