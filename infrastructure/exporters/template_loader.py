import logging
from pathlib import Path
from docx import Document
from domain.errors import DomainError

logger = logging.getLogger(__name__)

class TemplateNotFoundError(DomainError):
    pass

class TemplateLoader:
    def __init__(self, default_path: Path = None):
        self.default_path = default_path

    def load(self, path: Path = None) -> Document:
        logger.debug(f"{self.__class__.__name__}.load: {path}")
        target = path or self.default_path
        if not target or not target.exists():
            raise TemplateNotFoundError(f"Шаблон не найден: {target}")
        return Document(str(target))