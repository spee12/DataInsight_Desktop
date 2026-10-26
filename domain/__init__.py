"""Публичное API доменного слоя.
Responsibility: Экспорт сущностей, value objects, интерфейсов и ошибок для использования в других слоях.
"""
from .errors import DomainError, ColumnDetectionError, ChartBuildError
from .value_objects import ColumnType, ChartRule, ChartType, ChartConditions
from .entities import DatasetProfile, Chart
from .interfaces import IDataLoader, IChartRenderer, IReportExporter

__all__ = [
    "DomainError", "ColumnDetectionError", "ChartBuildError",
    "ColumnType", "ChartRule",
    "DatasetProfile", "Chart",
    "IDataLoader", "IChartRenderer", "ChartType",
    "ChartConditions", "IReportExporter"
]