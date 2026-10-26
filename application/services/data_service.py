import logging
import os
from typing import Any, Dict, List
from domain.errors import DomainError
from domain.interfaces import IDataLoader

logger = logging.getLogger(__name__)

class DataService:
    def __init__(self, loaders: Dict[str, IDataLoader]):
        self._loaders = loaders

    def load_data(self, file_path: str, table: str = None) -> List[Dict[str, Any]]:
        logger.debug(f"load_data: {file_path}")
        if not os.path.exists(file_path):
            raise DomainError(f"Файл не найден: {file_path}")
        ext = os.path.splitext(file_path)[1].lower()
        loader = self._loaders.get(ext)
        if not loader:
            raise DomainError(f"Формат {ext} не поддерживается")
        return loader.load(file_path, table=table) if table else loader.load(file_path)