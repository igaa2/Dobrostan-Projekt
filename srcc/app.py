from loguru import logger
from srcc.utils.utils import get_project_root, load_yaml


def main():
    root = get_project_root()
    config = load_yaml(root / "config.yaml")

    variables = config["data"]["variables"]
    logger.info(
        f"Number of variables used: {len(variables)}. "
        f"Id of variables used: {[v['id'] for v in variables]}. "
    )

    # Definicja startowych wag i typów zmiennych
    prefix_weight = config["state_session_keys"].get("prefix_weight", "w_")
    prefix_stim = config["state_session_keys"].get("prefix_stim", "s_")

    weights = {f"{prefix_weight}{v['id']}": v["weight"] for v in variables}
    logger.info(f"Default weights: {weights}")

    types = {f"{prefix_stim}{v['id']}": v["type"] for v in variables}
    logger.info(f"Default types: {types}")


if __name__ == "__main__":
    main()
