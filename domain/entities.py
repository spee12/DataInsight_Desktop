"""Сущности предметной области."""
from dataclasses import dataclass, field
from typing import Any
import logging

from .value_objects import ColumnType, ChartType

logger = logging.getLogger(__name__)   # ← это единственное, что нужно для логов


@dataclass(frozen=True)
class DatasetProfile:
    row_count: int
    column_count: int
    column_types: dict[str, ColumnType]
    statistics: dict[str, dict[str, Any]]
    missing_values: dict[str, int]
    temporal_formats: dict[str, str] = field(default_factory=dict)

    def get_column_type(self, column_name: str) -> ColumnType:
        # было: logger.debug(f"...{sys._getframe()...}...")
        # стало: имя функции подставится само через %(funcName)s
        logger.debug("Ищу тип колонки %r", column_name)
        col_type = self.column_types.get(column_name)
        if col_type is None:
            logger.error("Колонка %r отсутствует в профиле", column_name)
            raise ValueError(f"Колонка '{column_name}' отсутствует в профиле.")
        logger.debug("Тип колонки %r → %s", column_name, col_type.value)
        return col_type


@dataclass(frozen=True)
class Chart:
    chart_id: str
    chart_type: ChartType
    title: str
    x_column: str
    y_columns: list[str]
    data: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)