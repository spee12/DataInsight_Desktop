"""Эвристический определитель типов колонок.

Responsibility: Анализ значений и присвоение ColumnType без участия пользователя.
Architecture: Infrastructure Layer. Зависит от pandas и domain-контрактов.
"""
import logging
import re
import warnings

import pandas as pd

from domain.value_objects import ColumnType

logger = logging.getLogger(__name__)

_DATE_PATTERNS = (
    r"^\d{4}[-/.]\d{2}[-/.]\d{2}$",       # 2024-05-07
    r"^\d{2}[-/.]\d{2}[-/.]\d{2,4}$",     # 07.05.24 / 07/05/2024
    r"^\d{1,2}\s\w{3,9}\s\d{4}$",         # 07 May 2024
    r"^\d{1,2}:\d{2}(:\d{2})?$",          # 14:30 / 14:30:00
)
_COMPILED_DATE_REGEX = re.compile("|".join(f"(?:{p})" for p in _DATE_PATTERNS))

# Технические имена колонок — не показываем на графиках.
_TECH_COLUMN_NAMES = frozenset({"id", "index", "№", "no", "номер"})
_TECH_COLUMN_SUFFIXES = ("_id",)


class ColumnTypeDetector:
    """Определяет тип данных каждой колонки датасета.

    Пороги вынесены в константы класса — легко переопределить в подклассе
    (OCP), не меняя логику детекции.
    """

    MAX_CATEGORY_UNIQUE = 20
    MIN_SAMPLE_FOR_ID = 5
    CONFIDENCE_THRESHOLD = 0.8
    SAMPLE_SIZE = 100

    def detect(self, data: pd.DataFrame) -> dict[str, ColumnType]:
        """Анализирует DataFrame и возвращает маппинг колонок на типы."""
        if data.empty:
            logger.warning("Пустой DataFrame — пустой профиль")
            return {}

        result: dict[str, ColumnType] = {}
        for column in data.columns:
            series = data[column].dropna()
            if series.empty:
                result[column] = ColumnType.TEXT
                continue

            logger.debug("Анализ колонки '%s' (%d записей)", column, len(series))
            result[column] = self._detect_column(column, series)
            logger.debug("Колонка '%s' → %s", column, result[column].value)
        return result

    def _detect_column(self, column: str, series: pd.Series) -> ColumnType:
        """Проверки идут в порядке бизнес-приоритета."""
        sample = series.head(self.SAMPLE_SIZE).astype(str).str.strip()
        n = len(sample)

        if self._is_technical_id(column):
            return ColumnType.ID
        if self._is_date(sample, n):
            return ColumnType.DATE
        if self._is_numeric(sample, n):
            return ColumnType.NUMERIC
        if self._is_categorical(sample, n):
            return ColumnType.CATEGORICAL
        if self._is_id(sample, n):
            return ColumnType.ID
        return ColumnType.TEXT

    @staticmethod
    def _is_technical_id(column: str) -> bool:
        name = column.lower()
        return name in _TECH_COLUMN_NAMES or name.endswith(_TECH_COLUMN_SUFFIXES)

    def _is_id(self, sample: pd.Series, n: int) -> bool:
        if n < self.MIN_SAMPLE_FOR_ID or sample.nunique() != n:
            return False
        # Все значения — числа ⇒ скорее NUMERIC, чем ID
        if sample.str.match(r"^-?\d+([.,]\d+)?$").sum() == n:
            return False
        # Не путать с датами/временем
        date_like = sample.str.match(_COMPILED_DATE_REGEX, na=False).sum()
        return date_like / n < self.CONFIDENCE_THRESHOLD

    def _is_date(self, sample: pd.Series, n: int) -> bool:
        regex_ratio = sample.str.match(_COMPILED_DATE_REGEX, na=False).sum() / n
        ratio = regex_ratio
        if ratio < self.CONFIDENCE_THRESHOLD:
            ratio = max(ratio, self._pandas_date_ratio(sample, n))

        logger.debug(
            "_is_date: совпадений %.1f%% (порог %.0f%%)",
            ratio * 100, self.CONFIDENCE_THRESHOLD * 100,
        )
        return ratio >= self.CONFIDENCE_THRESHOLD

    @staticmethod
    def _pandas_date_ratio(sample: pd.Series, n: int) -> float:
        """Fallback-парсинг через pandas (без UserWarning)."""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                try:
                    parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
                except TypeError:
                    parsed = pd.to_datetime(sample, errors="coerce")
            return parsed.notna().sum() / n
        except Exception:
            return 0.0

    def _is_numeric(self, sample: pd.Series, n: int) -> bool:
        cleaned = sample.str.replace(",", ".", regex=False).str.strip()
        converted = pd.to_numeric(cleaned, errors="coerce")
        ratio = converted.notna().sum() / n
        logger.debug(
            "_is_numeric: %.1f%% (порог %.0f%%)",
            ratio * 100, self.CONFIDENCE_THRESHOLD * 100,
        )
        return ratio >= self.CONFIDENCE_THRESHOLD

    def _is_categorical(self, sample: pd.Series, n: int) -> bool:
        unique_count = sample.nunique()
        ratio = unique_count / n
        logger.debug(
            "_is_categorical: уникальных %d (%.1f%%), лимит %d",
            unique_count, ratio * 100, self.MAX_CATEGORY_UNIQUE,
        )
        return unique_count <= self.MAX_CATEGORY_UNIQUE and ratio < 0.5