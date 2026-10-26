"""Value Objects доменного слоя.
Responsibility: Хранение неизменяемых типов данных и правил визуализации.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum

class ColumnType(StrEnum):
    """Тип данных колонки в таблице."""
    DATE = "date"
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEXT = "text"
    ID = "id"

# Добавить после класса ColumnType
class ChartType(StrEnum):
    """Все 8 поддерживаемых видов диаграмм."""
    LINE = "line"
    BAR = "bar"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    PIE = "pie"
    AREA = "area"
    HEATMAP = "heatmap"
    BOXPLOT = "boxplot"

class ChartConditions:
    """Предопределенные условия для правил (ChartRule)."""
    TEMPORAL = "DATE>=1 AND NUMERIC>=1"
    CATEGORICAL_SINGLE = "CATEGORICAL>=1"
    CATEGORICAL_NUMERIC = "CATEGORICAL>=1 AND NUMERIC>=1"
    NUMERIC_DISTRIBUTION = "NUMERIC>=1"
    RELATIONAL = "NUMERIC>=2"
    CORRELATION = "NUMERIC>=3"

@dataclass(frozen=True)
class ChartRule:
    """Правило выбора типа графика.
    Responsibility: Описание условия и целевого типа визуализации.
    """
    rule_id: str
    condition: str
    target_chart_type: str
    description: str
    priority: int = 0