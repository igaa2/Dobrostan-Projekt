from src.bdl.bdl_client import BDLClient
from src.bdl.bdl_database import BDLDatabase
from src.utils.utils import load_yaml, get_project_root

config_path = get_project_root() / "bdl" / "config" / "config.yaml"
config = load_yaml(config_path)

client = BDLClient(config)
db = BDLDatabase(config)
