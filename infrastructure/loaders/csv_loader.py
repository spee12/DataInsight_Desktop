import logging
from pathlib import Path
import pandas as pd
from domain.errors import DomainError
from domain.interfaces import IDataLoader

logger = logging.getLogger(__name__)

class CsvLoaderError(DomainError): pass

class CsvLoader(IDataLoader):
    def load(self, source: str, **kwargs) -> list[dict]:
        logger.debug(f"CsvLoader.load: {source}")
        path = Path(source)
        if not path.exists() or path.suffix.lower() != ".csv":
            raise CsvLoaderError(f"Невалидный CSV: {source}")
        for enc in ["utf-8-sig", "utf-8", "cp1251"]:
            for sep in [",", ";", "\t"]:
                try:
                    df = pd.read_csv(path, encoding=enc, sep=sep, low_memory=False)
                    return df.astype(object).where(pd.notna(df), None).to_dict("records")
                except (UnicodeDecodeError, pd.errors.ParserError):
                    continue
        raise CsvLoaderError("Не удалось прочитать CSV")