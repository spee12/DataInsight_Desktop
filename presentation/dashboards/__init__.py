"""
presentation/dashboards/__init__.py

Публичный API пакета дашбордов.

Использование из MainWindow:
    from presentation.dashboards import DashboardContainer
    from presentation.dashboards import BarChartWidget, HeatmapWidget  # для отдельных виджетов

Архитектура файлов:
    base_chart_widget.py    — Базовый класс (фундамент для всех 8 виджетов)
    categorical_charts.py   — BarChartWidget, PieChartWidget
    temporal_charts.py      — LineChartWidget, AreaChartWidget
    statistical_charts.py   — HistogramWidget, BoxPlotWidget
    relational_charts.py    — ScatterChartWidget, HeatmapWidget
    dashboard_container.py  — DashboardContainer (сборка и компоновка)
"""

from .base_chart_widget import BaseChartWidget
from .categorical_charts import BarChartWidget, PieChartWidget
from .temporal_charts import LineChartWidget, AreaChartWidget
from .statistical_charts import HistogramWidget, BoxPlotWidget
from .relational_charts import ScatterChartWidget, HeatmapWidget
from .dashboard_container import DashboardContainer

__all__ = [
    # Базовый класс
    "BaseChartWidget",
    # Категориальные
    "BarChartWidget",
    "PieChartWidget",
    # Временны́е
    "LineChartWidget",
    "AreaChartWidget",
    # Статистические
    "HistogramWidget",
    "BoxPlotWidget",
    # Реляционные
    "ScatterChartWidget",
    "HeatmapWidget",
    # Контейнер
    "DashboardContainer",
]