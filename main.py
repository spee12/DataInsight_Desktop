import logging
from logger import setup_logging
from application.dto import DatasetInfoDTO, AnalysisResultDTO
from application.services.data_service import DataService
from application.services.analysis_service import AnalysisService
from application.services.chart_builder_service import ChartBuilderService
from application.services.report_service import ReportService
from infrastructure.loaders.excel_loader import ExcelLoader
from infrastructure.loaders.csv_loader import CsvLoader
from infrastructure.loaders.db_loader import SqliteLoader
from infrastructure.analysis.column_type_detector import ColumnTypeDetector
from infrastructure.analysis.statistic_calculator import StatisticCalculator
from infrastructure.analysis.chart_rule_engine import ChartRuleEngine
from infrastructure.exporters.docx_exporter import DocxExporter

setup_logging()
logger = logging.getLogger(__name__)


def main():
    logger.info("=== Инициализация DI ===")
    data_service = DataService({
        ".xlsx": ExcelLoader(),
        ".xls": ExcelLoader(),
        ".csv": CsvLoader(),
        ".db": SqliteLoader(),
        ".sqlite": SqliteLoader(),
        ".sqlite3": SqliteLoader()
    })
    analysis_service = AnalysisService(ColumnTypeDetector(), StatisticCalculator())
    chart_builder_service = ChartBuilderService(ChartRuleEngine())
    report_service = ReportService(DocxExporter())

    file_path = "test/testai.csv"  # Меняй на test/testai.csv или test/power_plant.db для проверки других форматов
    logger.info(f"=== Загрузка данных: {file_path} ===")
    data = data_service.load_data(file_path)

    logger.info("=== Анализ данных ===")
    profile = analysis_service.analyze_dataset(data)

    logger.info("=== Подбор графиков ===")
    charts = chart_builder_service.build_suggested_charts(profile, data)

    logger.info("=== Формирование отчёта ===")
    info = DatasetInfoDTO(file_path, profile.row_count, profile.column_count, file_path)
    result = AnalysisResultDTO(info, profile, charts)

    output = "test/test_report.docx"
    report_service.create_report(result, output)
    logger.info(f"=== Успешно! Отчёт сохранён: {output} ===")


if __name__ == "__main__":
    main()