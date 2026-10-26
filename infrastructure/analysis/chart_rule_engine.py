"""Движок применения правил визуализации.

Responsibility: Фильтрация и сортировка ChartRule по приоритету для набора колонок.
Architecture: Infrastructure Layer.
DIP: зависит от абстракции IConditionEvaluator, а не от конкретного парсера.
"""
import logging

from domain.errors import ChartBuildError
from domain.interfaces import IConditionEvaluator
from domain.value_objects import ChartRule

logger = logging.getLogger(__name__)


class ChartRuleEngine:
    """Оркестратор применения правил визуализации.

    SRP: единственная ответственность — группировка типов, фильтрация
    правил через IConditionEvaluator и сортировка по приоритету.
    """

    def __init__(self, condition_evaluator: IConditionEvaluator) -> None:
        self._evaluator = condition_evaluator

    def apply(
        self,
        column_types: dict[str, str],
        rules: list[ChartRule],
    ) -> list[ChartRule]:
        """Фильтрует и сортирует правила по приоритету.

        Args:
            column_types: {col_name: "DATE"|"NUMERIC"|...}
            rules: Доступные правила визуализации.

        Returns:
            Отсортированный по убыванию приоритета список применимых правил.

        Raises:
            ChartBuildError: Если column_types пуст.
        """
        if not column_types:
            raise ChartBuildError("Список типов колонок пуст")

        grouped = self._group_by_type(column_types)
        applicable = [
            rule for rule in rules
            if self._evaluator.evaluate(rule.condition, grouped)
        ]
        logger.debug(
            "Применимо правил: %d из %d", len(applicable), len(rules)
        )
        return sorted(applicable, key=lambda r: r.priority, reverse=True)

    @staticmethod
    def _group_by_type(column_types: dict[str, str]) -> dict[str, list[str]]:
        """Группирует имена колонок по типам (ключи — в верхнем регистре)."""
        grouped: dict[str, list[str]] = {}
        for column, column_type in column_types.items():
            grouped.setdefault(column_type.upper(), []).append(column)
        return grouped