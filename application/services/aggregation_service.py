from collections import Counter
from typing import Any, Dict, List

class AggregationService:
    @staticmethod
    def frequency(data: List[Dict[str, Any]], column: str) -> Dict[Any, int]:
        return dict(Counter(row.get(column) for row in data if row.get(column) is not None))

    @staticmethod
    def weighted_sum(data: List[Dict[str, Any]], value_col: str, weight_col: str) -> float:
        return sum((row.get(value_col, 0) or 0) * (row.get(weight_col, 0) or 0) for row in data)

    @staticmethod
    def weighted_avg(data: List[Dict[str, Any]], value_col: str, weight_col: str) -> float:
        total, weight = 0.0, 0.0
        for row in data:
            v, w = row.get(value_col), row.get(weight_col)
            if v is not None and w is not None:
                total += v * w
                weight += w
        return total / weight if weight else 0.0