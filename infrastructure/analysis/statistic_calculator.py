"""Калькулятор статистического профиля датасета.

Responsibility: Вычисление сырых (неформатированных) метрик по колонкам DataFrame.
Architecture: Infrastructure Layer. Зависит от pandas.
Форматирование (округление, приведение к строкам) — ответственность Presentation.
"""
import logging
from typing import Any

import pandas as pd

from domain.value_objects import ColumnType

logger = logging.getLogger(__name__)


class StatisticCalculator:
    """Вычисляет статистики по колонкам DataFrame.

    Возвращает сырые значения (float, Timestamp) без округления —
    Presentation сам выбирает формат отображения.
    """

    def calculate(
        self,
        data: pd.DataFrame,
        types: dict[str, ColumnType],
    ) -> dict[str, dict[str, Any]]:
        """Считает статистики для каждой колонки.

        Returns:
            {column_name: {stat_name: raw_value, ...}}.
            Для NUMERIC: mean/min/max/std (float | None).
            Для DATE: min/max (pandas.Timestamp | None) + format
                ("date_only" | "time_only" | "datetime").
            Для остальных: только missing/unique.
        """
        if data.empty:
            logger.warning("Пустой DataFrame — статистики не вычисляются")
            return {}

        stats: dict[str, dict[str, Any]] = {}
        for column in data.columns:
            series = data[column]
            column_stats: dict[str, Any] = {
                "missing": int(series.isna().sum()),
                "unique": int(series.dropna().nunique()),
            }

            column_type = types.get(column)
            if column_type == ColumnType.NUMERIC:
                column_stats.update(self._numeric_stats(series))
            elif column_type == ColumnType.DATE:
                column_stats.update(self._date_stats(series))

            stats[column] = column_stats
        return stats

    @staticmethod
    def _numeric_stats(series: pd.Series) -> dict[str, Any]:
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.isna().all():
            return {"mean": None, "min": None, "max": None, "std": None}
        return {
            "mean": float(numeric.mean()),
            "min": float(numeric.min()),
            "max": float(numeric.max()),
            "std": float(numeric.std()),
        }

    @staticmethod
    def _date_stats(series: pd.Series) -> dict[str, Any]:
        dates = pd.to_datetime(series, errors="coerce")
        valid = dates.dropna()
        if valid.empty:
            return {"min": None, "max": None, "format": "date_only"}
        return {
            "min": valid.min(),
            "max": valid.max(),
            "format": StatisticCalculator._infer_format(valid),
        }

    @staticmethod
    def _infer_format(dates: pd.Series) -> str:
        """Определяет гранулярность: date_only | time_only | datetime."""
        unique_days = dates.dt.normalize().nunique()
        unique_seconds = (
            dates.dt.hour * 3600 + dates.dt.minute * 60 + dates.dt.second
        ).nunique()
        if unique_days > 1 and unique_seconds <= 1:
            return "date_only"
        if unique_days <= 1 and unique_seconds > 1:
            return "time_only"
        return "datetime"