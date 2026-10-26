import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from application.dto import AnalysisResultDTO
from domain.entities import Chart, DatasetProfile
from domain.interfaces import IChartRenderer, IReportExporter

logger = logging.getLogger(__name__)

class ReportService:
    def __init__(self, docx: IReportExporter, html: IChartRenderer, pdf: IReportExporter):
        self._docx = docx
        self._html = html
        self._pdf = pdf

    def create_report(self, result: AnalysisResultDTO, output_path: str) -> str:
        logger.debug(f"create_report: {output_path}")
        return self._docx.export({
            "profile": result.profile,
            "charts": result.recommended_charts,
            "dataset_info": result.dataset_info
        }, output_path)

    def generate_report(self, charts: List[Chart], profile: DatasetProfile, selected_indices: List[int],
                        include_stats: bool, fmt: str, output_path: str, captured_images: Dict[int, bytes] = None) -> str:
        logger.debug(f"generate_report: {fmt} -> {output_path}")
        captured_images = captured_images or {}
        temp_dir = Path(tempfile.mkdtemp(prefix="export_"))
        try:
            images = []
            for idx in selected_indices:
                img = captured_images.get(idx)
                if not img or len(img) < 500:
                    logger.warning(f"generate_report: пропуск графика {idx}")
                    continue
                path = temp_dir / f"chart_{idx}.png"
                path.write_bytes(img)
                images.append({"title": charts[idx].title, "image_path": str(path), "image_bytes": img})

            report = {
                "title": f"Аналитический отчёт: {Path(output_path).stem}",
                "insights": f"Строк: {profile.row_count} | Колонок: {profile.column_count}",
                "statistics": profile.statistics if include_stats else {},
                "chart_images": images
            }

            if fmt == "DOCX":
                return self._docx.export(report, output_path)
            if fmt == "HTML":
                return self._html.export_dashboard_to_html(images, output_path)
            if fmt == "PDF":
                html_path = temp_dir / "temp.html"
                self._html.export_dashboard_to_html(images, str(html_path))
                return self._pdf.export({"html": html_path.read_text(encoding="utf-8")}, output_path)
            if fmt == "PNG":
                out_dir = Path(output_path).parent
                for i, img in enumerate(images):
                    (out_dir / f"chart_{selected_indices[i]}.png").write_bytes(img["image_bytes"])
                return str(out_dir)
            raise ValueError(f"Формат '{fmt}' не поддерживается")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)