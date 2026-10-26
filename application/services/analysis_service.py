import logging
from typing import Any, Dict, List
from domain.entities import DatasetProfile
from domain.interfaces import IColumnTypeDetector, IStatisticCalculator

logger = logging.getLogger(__name__)

class AnalysisService:
    def __init__(self, detector: IColumnTypeDetector, calculator: IStatisticCalculator):
        self._detector = detector
        self._calculator = calculator

    def analyze_dataset(self, data: List[Dict[str, Any]]) -> DatasetProfile:
        logger.debug(f"analyze_dataset: {len(data)} строк")
        column_types = self._detector.detect(data)
        stats, _ = self._calculator.calculate(data, column_types)
        return DatasetProfile(
            row_count=len(data),
            column_count=len(data[0]) if data else 0,
            column_types=column_types,
            statistics=stats,
            missing_values={}
        )