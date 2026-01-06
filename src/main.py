from src.bdl.download_bdl import main as download
from src.composite_index.data_preprocessing.validate_variables import main as valid
from src.composite_index.index_building.run_copras import main as copras
from loguru import logger

if __name__ == "__main__":
    logger.info("Krok 1: API.")
    download()
    logger.info("Krok 2: VALID.")
    valid()
    logger.info("Krok 3: COPRAS.")
    copras()
    logger.info("Koniec skryptu.")
