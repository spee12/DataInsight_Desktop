import logging
import re
import pandas as pd
from domain.value_objects import ColumnType

logger = logging.getLogger(__name__)

_DATE_PATTERNS = [
    r"^\d{4}[-/.]\d{2}[-/.]\d{2}$",
    r"^\d{2}[-/.]\d{2}[-/.]\d{2,4}$",
    r"^\d{1,2}\s\w{3,9}\s\d{4}$",
    r"^\d{1,2}:\d{2}(:\d{2})?$",
]
_DATE_RE = re.compile("|".join(f"(?:{p})" for p in _DATE_PATTERNS))

class ColumnTypeDetector:
    MAX_CATEGORY_UNIQUE = 20
    MIN_SAMPLE_FOR_ID = 5
    CONFIDENCE = 0.8

    def detect(self, data: list[dict]) -> dict[str, ColumnType]:
        logger.debug(f"{self.__class__.__name__}.detect: {len(data)} строк")
        if not data:
            return {}
        df = pd.DataFrame(data)
        return {col: self._detect_column(df[col]) for col in df.columns}

    def _detect_column(self, series: pd.Series) -> ColumnType:
        sample = series.dropna().head(100).astype(str).str.strip()
        n = len(sample)
        if n == 0:
            return ColumnType.TEXT
        name = series.name.lower()
        if name in {"id", "index", "№", "no", "номер"} or name.endswith("_id"):
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

    def _is_date(self, sample: pd.Series, n: int) -> bool:
        ratio = sample.str.match(_DATE_RE, na=False).sum() / n
        if ratio < self.CONFIDENCE:
            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    ratio = max(ratio, pd.to_datetime(sample, errors="coerce").notna().sum() / n)
            except Exception:
                pass
        return ratio >= self.CONFIDENCE

    def _is_numeric(self, sample: pd.Series, n: int) -> bool:
        cleaned = sample.str.replace(",", ".", regex=False)
        return pd.to_numeric(cleaned, errors="coerce").notna().sum() / n >= self.CONFIDENCE

    def _is_categorical(self, sample: pd.Series, n: int) -> bool:
        unique = sample.nunique()
        return unique <= self.MAX_CATEGORY_UNIQUE and unique / n < 0.5

    def _is_id(self, sample: pd.Series, n: int) -> bool:
        if n < self.MIN_SAMPLE_FOR_ID or sample.nunique() != n:
            return False
        if sample.str.match(r"^-?\d+([.,]\d+)?$").sum() == n:
            return False
        return sample.str.match(_DATE_RE, na=False).sum() / n < self.CONFIDENCE