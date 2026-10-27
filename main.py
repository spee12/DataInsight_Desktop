import sys
import logging
from PySide6.QtWidgets import QApplication

# Infrastructure
from infrastructure.loaders.csv_loader import CsvLoader
from infrastructure.loaders.excel_loader import ExcelLoader
from infrastructure.loaders.db_loader import SqliteLoader
from infrastructure.analysis.column_type_detector import ColumnTypeDetector
from infrastructure.analysis.statistic_calculator import StatisticCalculator
from infrastructure.analysis.chart_rule_engine import ChartRuleEngine
from infrastructure.exporters.docx_exporter import DocxExporter

# Application
from application.services.data_service import DataService
from application.services.analysis_service import AnalysisService
from application.services.chart_builder_service import ChartBuilderService
from application.services.report_service import ReportService

# Presentation
from presentation.main_window import MainWindow
from presentation.theme_loader import load_all_qss

logger = logging.getLogger(__name__)



def setup_logging(level=logging.DEBUG):
    """Настройка логирования"""

    # 1. Настраиваем формат
    log_format = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(filename)s:%(lineno)d | %(message)s"
    formatter = logging.Formatter(log_format)

    # 2. Настраиваем handler для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    # 3. Получаем корневой логгер и настраиваем его
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)

    # --- ВОТ ЭТА ЧАСТЬ УБИРАЕТ ШУМ ОТ БИБЛИОТЕК ---

    # Ставим высокий уровень (WARNING или ERROR) для всех внешних библиотек
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)  # Pillow
    logging.getLogger("fontTools").setLevel(logging.WARNING)  # Часто шумит вместе с matplotlib
    logging.getLogger("openpyxl").setLevel(logging.WARNING)  # Excel
    logging.getLogger("pandas").setLevel(logging.WARNING)  # Pandas

    # Если хотите оставить DEBUG только для ВАШЕГО проекта:
    # Сначала поставим WARNING для всех, а потом вернем DEBUG для своего пакета
    logging.getLogger().setLevel(logging.WARNING)
    logging.getLogger("DataInsight").setLevel(logging.DEBUG)  # Или ваше имя пакета, если оно другое
    # Если у вас нет единого имени пакета, можно перечислить ваши модули:
    logging.getLogger("__main__").setLevel(logging.DEBUG)
    logging.getLogger("presentation").setLevel(logging.DEBUG)
    logging.getLogger("application").setLevel(logging.DEBUG)
    logging.getLogger("infrastructure").setLevel(logging.DEBUG)
    logging.getLogger("domain").setLevel(logging.DEBUG)
    # --------------------------------------------------

    logging.debug(f"Logging initialized to {logging.getLevelName(level)} level")


def main():
    setup_logging()
    logger.debug("main: Creating QApplication instance")
    app = QApplication(sys.argv)

    logger.debug("main: Loading QSS styles via theme_loader")
    load_all_qss(app)

    logger.debug("main: Initializing Infrastructure layer")
    csv_loader = CsvLoader()
    excel_loader = ExcelLoader()
    sqlite_loader = SqliteLoader()
    type_detector = ColumnTypeDetector()
    stat_calc = StatisticCalculator()
    rule_engine = ChartRuleEngine()
    docx_exporter = DocxExporter()

    logger.debug("main: Injecting Infrastructure into Application services")
    data_service = DataService(
        loaders={".csv": csv_loader, ".xlsx": excel_loader, ".xls": excel_loader,
                 ".db": sqlite_loader, ".sqlite": sqlite_loader, ".sqlite3": sqlite_loader})
    analysis_service = AnalysisService(detector=type_detector, calculator=stat_calc)
    chart_service = ChartBuilderService(rule_engine=rule_engine)

    # Исправлено: передаем экспортер напрямую (убран словарь exporters)
    report_service = ReportService(exporter=docx_exporter)

    logger.debug("main: Initializing Presentation layer (MainWindow)")
    window = MainWindow(
        data_service=data_service,
        analysis_service=analysis_service,
        chart_service=chart_service,
        report_service=report_service,
        author_fio="DataInsight Test"
    )
    window.show()
    logger.debug("main: MainWindow shown, starting Qt event loop")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()