import yaml
from pathlib import Path
from datetime import datetime


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_yaml(path: str | Path) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_md(path: str | Path) -> str:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Markdown file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_current_time_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_current_year() -> int:
    return datetime.now().year


if __name__ == "__main__":
    pass
