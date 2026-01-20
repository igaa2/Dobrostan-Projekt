import yaml
from pathlib import Path
from datetime import datetime
from loguru import logger


def get_project_root() -> Path:
    """Zwraca ścieżkę do katalogu głównego projektu."""
    root = Path(__file__).resolve().parent.parent
    logger.info(f"Project root resolved: {root}")
    return root


def load_yaml(path: str | Path) -> dict:
    """Wczytuje plik YAML i zwraca jego zawartość jako słownik."""
    path = Path(path)
    logger.info(f"Loading YAML file from path: {path}")

    if not path.exists():
        logger.info(f"YAML file does not exist: {path}")
        raise FileNotFoundError(f"YAML file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    logger.info("YAML file loaded successfully.")
    return data


def load_md(path: str | Path) -> str:
    """Wczytuje plik Markdown i zwraca jego zawartość jako string."""
    path = Path(path)
    logger.info(f"Loading Markdown file from path: {path}")

    if not path.exists():
        logger.info(f"Markdown file does not exist: {path}")
        raise FileNotFoundError(f"Markdown file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    logger.info("Markdown file loaded successfully.")
    return content


def get_current_time() -> str:
    """Zwraca aktualny czas w formacie 'YYYY-MM-DD HH:MM:SS'."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Current time generated: {current_time}")
    return current_time


def get_current_year() -> int:
    """Zwraca aktualny rok."""
    year = datetime.now().year
    logger.info(f"Current year retrieved: {year}")
    return year
