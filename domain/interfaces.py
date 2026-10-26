"""Абстрактные интерфейсы доменного слоя.
Responsibility: Определение контрактов для внешних реализаций (Infrastructure).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from .entities import Chart

class IDataLoader(ABC):
    """Интерфейс загрузчика табличных данных.
    Responsibility: Чтение данных из внешних источников в унифицированный формат.
    """
    @abstractmethod
    def load(self, source: str) -> list[dict[str, Any]]:
        ...

class IChartRenderer(ABC):
    """Интерфейс рендерера графиков.
    Responsibility: Преобразование сущностей Chart в визуальные компоненты GUI.
    """
    @abstractmethod
    def render(self, chart: Chart) -> Any:
        ...

    @abstractmethod
    def export_dashboard_to_html(self, charts: list[Chart], output_path: str) -> str:
        ...

class IReportExporter(ABC):
    """Интерфейс экспортёра отчётов.
    Responsibility: Генерация файлов отчётов (DOCX, HTML, PDF) на основе профиля и графиков.
    """
    @abstractmethod
    def export_to_docx(self, profile: Any, charts: list[Chart], output_path: str) -> str:
        ...