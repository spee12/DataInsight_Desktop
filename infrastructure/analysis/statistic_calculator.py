import logging
import pandas as pd
from typing import Any
from domain.value_objects import ColumnType

logger = logging.getLogger(__name__)

class StatisticCalculator:
    def calculate(self, data: list[dict], types: dict[str, ColumnType]) -> tuple[dict[str, dict], dict[str, str]]:
        logger.debug(f"{self.__class__.__name__}.calculate: {len(data)} строк")
        if not data:
            return {}, {}
        df = pd.DataFrame(data)
        stats, formats = {}, {}
        for col in df.columns:
            series = df[col]
            base = {"missing": int(series.isna().sum()), "unique": int(series.dropna().nunique())}
            ct = types.get(col)
            if ct == ColumnType.NUMERIC:
                num = pd.to_numeric(series, errors="coerce")
                base |= {k: round(float(getattr(num, k)()), 2) if not num.isna().all() else None for k in ("mean", "min", "max", "std")}
            elif ct == ColumnType.DATE:
                dates = pd.to_datetime(series, errors="coerce").dropna()
                base |= {"min": str(dates.min()) if len(dates) else None, "max": str(dates.max()) if len(dates) else None}
                formats[col] = self._infer_format(series)
            stats[col] = base
        return stats, formats

    def _infer_format(self, series: pd.Series) -> str:
        dates = pd.to_datetime(series, errors="coerce").dropna()
        if dates.empty:
            return "date_only"
        days = dates.dt.normalize().nunique()
        times = (dates.dt.hour * 3600 + dates.dt.minute * 60 + dates.dt.second).nunique()
        if days > 1 and times <= 1:
            return "date_only"
        if days <= 1 and times > 1:
            return "time_only"
        return "datetime"