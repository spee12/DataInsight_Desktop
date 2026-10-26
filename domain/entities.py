"""Сущности предметной области.
Responsibility: Представление профиля набора данных и сущности графика.
"""
from dataclasses import dataclass, field  # ✅ Добавлен field
import logging
import sys
logger = logging.getLogger(__name__)
from .value_objects import ColumnType, ChartType
from typing import Any

@dataclass(frozen=True)
class DatasetProfile:
    row_count: int
    column_count: int
    column_types: dict[str, ColumnType]
    statistics: dict[str, dict[str, Any]]
    missing_values: dict[str, int]
    temporal_formats: dict[str, str] = field(default_factory=dict)  # ✅ НОВОЕ ПОЛЕ

    def get_column_type(self, column_name: str) -> ColumnType:
        logger.debug(f"{self.__class__.__name__}.{sys._getframe().f_code.co_name}: Начало работы с данными")
        col_type = self.column_types.get(column_name)
        if col_type is None:
            raise ValueError(f"Колонка '{column_name}' отсутствует в профиле.")
        return col_type

@dataclass(frozen=True)
class Chart:
    """Сущность графика для передачи в слой Presentation.
    Responsibility: Хранение конфигурации и подготовленных данных для отрисовки.
    """
    chart_id: str
    chart_type: ChartType
    title: str
    x_column: str
    y_columns: list[str]
    data: list[dict[str, Any]]
    metadata: dict[str, Any]