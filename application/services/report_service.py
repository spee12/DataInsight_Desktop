import logging
import tempfile
from pathlib import Path
from domain.interfaces import IReportExporter

logger = logging.getLogger(__name__)


def _tmp_png(data: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(data)
    return f.name


class ReportService:
    def __init__(self, exporter: IReportExporter):
        self._exporter = exporter

    def generate_report(self, charts, profile, idx, stats, fmt, path, captured_images=None) -> str:
        logger.debug(f"generate_report: {fmt} -> {path}")
        imgs = captured_images or {}
        if fmt.lower() == "png":
            Path(path).write_bytes(next(iter(imgs.values()), b""))
            return path
        report = {
            "title": f"Аналитический отчёт: {Path(path).stem}",
            "insights": f"Строк: {profile.row_count} | Колонок: {profile.column_count}",
            "statistics": profile.statistics,
            "chart_images": [{"image_path": _tmp_png(b), "title": charts[i].title} for i, b in imgs.items()],
        }
        return self._exporter.export(report, path)