
from __future__ import annotations
from typing import Optional
import logging
logger = logging.getLogger(__name__)
class DomainError(Exception):
    def __init__(self, message: str, details: Optional[str] = None) -> None:
        self.message = message
        self.details = details
        super().__init__(self.message)

class ColumnDetectionError(DomainError):

    pass

class ChartBuildError(DomainError):

    pass