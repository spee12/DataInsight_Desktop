from abc import ABC, abstractmethod
from typing import Any, Dict, List

class IDataLoader(ABC):
    @abstractmethod
    def load(self, source: str, **kwargs) -> List[Dict[str, Any]]:
        ...

class IColumnTypeDetector(ABC):
    @abstractmethod
    def detect(self, data: List[Dict[str, Any]]) -> Dict[str, str]:
        ...

class IStatisticCalculator(ABC):
    @abstractmethod
    def calculate(self, data: List[Dict[str, Any]], column_types: Dict[str, str]) -> tuple[Dict[str, Any], Any]:
        ...

class IChartRuleEngine(ABC):
    @abstractmethod
    def apply(self, column_types: Dict[str, str], rules: List[Any]) -> List[Any]:
        ...

class IChartRenderer(ABC):
    @abstractmethod
    def render(self, chart: Any) -> Any:
        ...

    @abstractmethod
    def export_dashboard_to_html(self, charts: List[Any], output_path: str) -> str:
        ...

class IReportExporter(ABC):
    @abstractmethod
    def export(self, report_data: Dict[str, Any], output_path: str) -> str:
        ...