import logging
from domain.errors import ChartBuildError
from domain.interfaces import IChartRuleEngine
from domain.value_objects import ChartRule, ColumnType

logger = logging.getLogger(__name__)

class ChartRuleEngine(IChartRuleEngine):
    def apply(self, column_types: dict[str, ColumnType], rules: list[ChartRule]) -> list[ChartRule]:
        logger.debug(f"{self.__class__.__name__}.apply: {len(column_types)} колонок")
        if not column_types:
            raise ChartBuildError("Список типов колонок пуст")
        counts = {}
        for t in column_types.values():
            counts[t.value.upper()] = counts.get(t.value.upper(), 0) + 1
        return sorted([r for r in rules if self._match(r.condition, counts)], key=lambda r: -r.priority)

    def _match(self, condition: str, counts: dict[str, int]) -> bool:
        for part in condition.split("AND"):
            part = part.strip()
            if not part:
                continue
            op = ">=" if ">=" in part else ">"
            typ, val = part.split(op)
            req = int(val.strip()) if op == ">=" else int(val.strip()) + 1
            if counts.get(typ.strip().upper(), 0) < req:
                return False
        return True