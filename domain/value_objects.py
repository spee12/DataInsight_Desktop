
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum

class ColumnType(StrEnum):
    DATE = "date"
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEXT = "text"
    ID = "id"

class ChartType(StrEnum):

    LINE = "line"
    BAR = "bar"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    PIE = "pie"
    AREA = "area"
    HEATMAP = "heatmap"
    BOXPLOT = "boxplot"

class ChartConditions:
    TEMPORAL = "DATE>=1 AND NUMERIC>=1"
    CATEGORICAL_SINGLE = "CATEGORICAL>=1"
    CATEGORICAL_NUMERIC = "CATEGORICAL>=1 AND NUMERIC>=1"
    NUMERIC_DISTRIBUTION = "NUMERIC>=1"
    RELATIONAL = "NUMERIC>=2"
    CORRELATION = "NUMERIC>=3"

@dataclass(frozen=True)
class ChartRule:

    rule_id: str
    condition: str
    target_chart_type: str
    description: str
    priority: int = 0