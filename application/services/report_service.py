import logging
from application.dto import AnalysisResultDTO
from domain.interfaces import IReportExporter

logger = logging.getLogger(__name__)

class ReportService:
    def __init__(self, docx: IReportExporter):
        self._docx = docx

    def create_report(self, result: AnalysisResultDTO, output_path: str) -> str:
        logger.debug(f"create_report: {output_path}")
        report_data = {
            "title": f"Аналитический отчёт: {result.dataset_info.file_name}",
            "insights": f"Строк: {result.profile.row_count} | Колонок: {result.profile.column_count}",
            "statistics": result.profile.statistics,
            "chart_images": []  # Картинки пока не передаем, так как рендерер отключен
        }
        return self._docx.export(report_data, output_path)