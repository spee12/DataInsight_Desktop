"""Ошибки предметной области.
Responsibility: Определение иерархии кастомных исключений для доменного слоя.
"""
from __future__ import annotations
from typing import Optional

class DomainError(Exception):
    """Базовое исключение для всех ошибок домена."""
    def __init__(self, message: str, details: Optional[str] = None) -> None:
        self.message = message
        self.details = details
        super().__init__(self.message)

class ColumnDetectionError(DomainError):
    """Ошибка при автоматическом определении типа колонки."""
    pass

class ChartBuildError(DomainError):
    """Ошибка при построении графика на основе данных."""
    pass