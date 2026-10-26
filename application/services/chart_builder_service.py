import logging
import uuid
from typing import Any, Dict, List
from domain.entities import Chart, DatasetProfile
from domain.interfaces import IChartRuleEngine
from domain.value_objects import ChartRule, ChartConditions, ChartType, ColumnType

logger = logging.getLogger(__name__)

class ChartBuilderService:
    MAX_HISTOGRAMS = 25

    def __init__(self, rule_engine: IChartRuleEngine):
        self._engine = rule_engine
        self._rules = [
            ChartRule("R1", ChartConditions.TEMPORAL, ChartType.LINE, "Тренды во времени", 10),
            ChartRule("R2", ChartConditions.CATEGORICAL_NUMERIC, ChartType.BAR, "Сравнение по категориям", 9),
            ChartRule("R3", ChartConditions.CATEGORICAL_NUMERIC, ChartType.PIE, "Доли по категориям", 8),
            ChartRule("R4", ChartConditions.CATEGORICAL_NUMERIC, ChartType.BOXPLOT, "Распределение и выбросы", 7),
            ChartRule("R5", ChartConditions.TEMPORAL, ChartType.AREA, "Накопленные тренды", 6),
            ChartRule("R6", ChartConditions.NUMERIC_DISTRIBUTION, ChartType.HISTOGRAM, "Распределение данных", 5),
            ChartRule("R7", ChartConditions.RELATIONAL, ChartType.SCATTER, "Корреляция показателей", 4),
            ChartRule("R8", ChartConditions.CORRELATION, ChartType.HEATMAP, "Матрица корреляции", 3)
        ]

    def build_suggested_charts(self, profile: DatasetProfile, data: List[Dict[str, Any]] = None) -> List[Chart]:
        logger.debug(f"build_suggested_charts: {profile.column_count} колонок")
        data = data or []
        cols = {t.value: [c for c, ct in profile.column_types.items() if ct == t] for t in ColumnType}
        rules = self._engine.apply(profile.column_types, self._rules)
        charts = []
        date = cols.get(ColumnType.DATE.value, [])
        num = cols.get(ColumnType.NUMERIC.value, [])
        cat = cols.get(ColumnType.CATEGORICAL.value, [])

        for rule in rules:
            ct = rule.target_chart_type
            if ct in (ChartType.LINE, ChartType.AREA) and date and num:
                charts.append(self._chart(rule, date[0], num, data))
            elif ct in (ChartType.BAR, ChartType.PIE, ChartType.BOXPLOT) and cat and num:
                charts.extend(self._chart(rule, c, [num[0]], data, f"{rule.description}: {c}") for c in cat)
            elif ct == ChartType.HISTOGRAM and num:
                charts.extend(self._hist_charts(rule, num, data))
            elif ct == ChartType.SCATTER and len(num) >= 2:
                charts.append(self._chart(rule, num[0], [num[1]], data))
            elif ct == ChartType.HEATMAP and len(num) >= 3:
                charts.append(self._chart(rule, "matrix", num, data))

        logger.debug(f"build_suggested_charts: {len(charts)} графиков")
        return charts

    def _chart(self, rule: ChartRule, x: str, y: List[str], data: List[Dict[str, Any]], title: str = None) -> Chart:
        return Chart(
            chart_id=str(uuid.uuid4()),
            chart_type=rule.target_chart_type,
            title=title or rule.description,
            x_column=x,
            y_columns=y,
            data=data,
            metadata={"rule_id": rule.rule_id, "priority": rule.priority}
        )

    def _hist_charts(self, rule: ChartRule, numeric: List[str], data: List[Dict[str, Any]]) -> List[Chart]:
        if len(numeric) > self.MAX_HISTOGRAMS:
            return [self._chart(rule, "aggregate", numeric, data, "Сводное распределение всех признаков")]
        return [self._chart(rule, c, [], data, f"Распределение: {c}") for c in numeric]