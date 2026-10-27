import logging
from pathlib import Path
import pandas as pd
from domain.errors import DomainError
from domain.interfaces import IDataLoader

logger = logging.getLogger(__name__)

class ExcelLoaderError(DomainError): pass

class ExcelLoader(IDataLoader):
    def load(self, source: str, sheet_name=0, **kwargs) -> list[dict]:
        logger.debug(f"ExcelLoader.load: {source}")
        path = Path(source)
        if not path.exists() or path.suffix.lower() not in (".xlsx", ".xls"):
            raise ExcelLoaderError(f"Невалидный Excel: {source}")
        try:
            df = pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")
            return df.astype(object).where(pd.notna(df), None).to_dict("records")
        except Exception as e:
            raise ExcelLoaderError(f"Ошибка Excel: {e}")