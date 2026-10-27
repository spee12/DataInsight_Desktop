import logging
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QLabel, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QPushButton, QHBoxLayout, QFrame, QDialog
from PySide6.QtCore import QThread, QObject, Signal, Qt, QSize, QBuffer, QIODevice, QPoint
from PySide6.QtGui import QImage, QPainter
from PySide6.QtCharts import QChartView, QChart
from presentation.screens.welcome_screen import WelcomeScreen
from presentation.screens.loading_screen import LoadingScreen
from presentation.screens.export_panel import ExportPanel
from presentation.dashboards import DashboardContainer
from presentation.dashboards.categorical_charts import PieChartWidget, BarChartWidget
from presentation.dashboards.statistical_charts import HistogramWidget, BoxPlotWidget
from presentation.dashboards.relational_charts import ScatterChartWidget, HeatmapWidget
from presentation.dashboards.temporal_charts import LineChartWidget, AreaChartWidget

logger = logging.getLogger(__name__)

class PipelineWorker(QObject):
    progress = Signal(int, str)
    finished = Signal(object, object)
    error = Signal(str)
    def __init__(self, fp, ds, as_, cs):
        super().__init__()
        self.fp, self.ds, self.as_, self.cs = fp, ds, as_, cs
    def run(self):
        try:
            self.progress.emit(10, "Чтение файла...")
            raw = self.ds.load_data(self.fp)
            self.progress.emit(40, "Анализ структуры...")
            profile = self.as_.analyze_dataset(raw)
            self.progress.emit(70, "Подбор графиков...")
            charts = self.cs.build_suggested_charts(profile, data=raw)
            self.progress.emit(100, "Готово")
            self.finished.emit(charts, profile)
            logger.debug("PipelineWorker.run: Pipeline finished")
        except Exception as e:
            self.error.emit(str(e))
            logger.error(f"PipelineWorker.run: {e}")

class ExportWorker(QObject):
    finished = Signal(str)
    error = Signal(str)
    def __init__(self, rs, charts, profile, idx, stats, fmt, path, imgs=None):
        super().__init__()
        self.rs, self.charts, self.profile, self.idx, self.stats, self.fmt, self.path, self.imgs = rs, charts, profile, idx, stats, fmt, path, imgs or {}
    def run(self):
        try:
            res = self.rs.generate_report(self.charts, self.profile, self.idx, self.stats, self.fmt, self.path, captured_images=self.imgs)
            self.finished.emit(res)
            logger.debug("ExportWorker.run: Report generated")
        except Exception as e:
            self.error.emit(str(e))
            logger.error(f"ExportWorker.run: {e}")

class PreviewWindow(QDialog):
    def __init__(self, chart_entity, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Предпросмотр: {chart_entity.title}")
        self.resize(1000, 700)
        l = QVBoxLayout(self)
        w_map = {'line': LineChartWidget, 'area': AreaChartWidget, 'bar': BarChartWidget, 'pie': PieChartWidget, 'histogram': HistogramWidget, 'boxplot': BoxPlotWidget, 'scatter': ScatterChartWidget, 'heatmap': HeatmapWidget}
        w_cls = w_map.get(str(getattr(chart_entity, 'chart_type', '')).lower())
        if w_cls:
            w = w_cls(chart_entity)
            l.addWidget(w)
            for c in w.findChildren(QChartView): c.chart().setAnimationOptions(QChart.NoAnimation)
            logger.debug(f"PreviewWindow.__init__: Rendered {chart_entity.chart_type}")
        else:
            l.addWidget(QLabel(f"Тип графика '{chart_entity.chart_type}' не поддерживается"))

class MainWindow(QMainWindow):
    def __init__(self, data_service, analysis_service, chart_service, report_service, author_fio="Автор", parent=None):
        super().__init__(parent, objectName="MainWindow")
        self.data_service, self.analysis_service, self.chart_service, self.report_service = data_service, analysis_service, chart_service, report_service
        self.current_charts, self.current_profile = [], None
        self._setup_ui(author_fio)
        self._setup_threads()
        logger.debug("MainWindow.__init__: Initialized")

    def _setup_ui(self, author):
        self.setWindowTitle(f"DataInsight — {author}")
        self.resize(1280, 900)
        header = QWidget(objectName="AppHeader")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(10, 5, 10, 5)
        hl.addWidget(QLabel("DataInsight v1.0", objectName="HeaderLabel", alignment=Qt.AlignLeft))
        hl.addStretch()
        self.btn_back = QPushButton("На главную", objectName="HeaderBtn", clicked=self._go_home, visible=False)
        self.btn_export = QPushButton("Экспорт", objectName="HeaderBtn", clicked=self._show_export_panel, visible=False)
        hl.addWidget(self.btn_export)
        hl.addWidget(self.btn_back)
        self.stack = QStackedWidget(frameShape=QFrame.Shape.NoFrame)
        if self.stack.layout(): self.stack.layout().setContentsMargins(0, 0, 0, 0); self.stack.layout().setSpacing(0)
        self.welcome, self.loading, self.dashboard = WelcomeScreen(), LoadingScreen(), DashboardContainer()
        self.stack.addWidget(self.welcome)
        self.stack.addWidget(self.loading)
        self.stack.addWidget(self.dashboard)
        central = QWidget()
        cl = QVBoxLayout(central)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)
        cl.addWidget(header)
        cl.addWidget(self.stack)
        self.setCentralWidget(central)
        self.export_panel = ExportPanel(self)
        self.export_panel.resize(420, 480)
        self.export_panel.setHidden(True)
        self.export_panel.export_requested.connect(self._start_export)
        self.export_panel.cancelled.connect(self.export_panel.setHidden)
        self.export_panel.preview_requested.connect(self._show_chart_preview)
        self.welcome.file_selected.connect(self._handle_file_trigger)

    def _setup_threads(self):
        self.pipeline_thread, self.export_thread = QThread(), QThread()
        self.pipeline_worker, self.export_worker = None, None

    def _handle_file_trigger(self, fp):
        if not fp: fp, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "Data Files (*.csv *.xlsx *.xls *.db *.sqlite *.sqlite3)")
        if fp: self._start_pipeline(fp)

    def _start_pipeline(self, fp):
        logger.debug(f"MainWindow._start_pipeline: {fp}")
        self.stack.setCurrentWidget(self.loading)
        self.loading.start()
        if self.pipeline_thread.isRunning(): self.pipeline_thread.quit(); self.pipeline_thread.wait()
        self.pipeline_worker = PipelineWorker(fp, self.data_service, self.analysis_service, self.chart_service)
        self.pipeline_worker.moveToThread(self.pipeline_thread)
        self.pipeline_thread.started.connect(self.pipeline_worker.run)
        self.pipeline_worker.progress.connect(self.loading.update)
        self.pipeline_worker.finished.connect(self._on_pipeline_success)
        self.pipeline_worker.error.connect(self._on_error)
        self.pipeline_worker.finished.connect(self.pipeline_thread.quit)
        self.pipeline_worker.error.connect(self.pipeline_thread.quit)
        self.pipeline_thread.start()

    def _on_pipeline_success(self, charts, profile):
        logger.debug(f"MainWindow._on_pipeline_success: {len(charts)} charts")
        self.loading.finish()
        self.current_charts, self.current_profile = charts, profile
        self.dashboard.clear()
        self.dashboard.load_charts(charts)
        self.stack.setCurrentWidget(self.dashboard)
        self.btn_back.setVisible(True)
        self.btn_export.setVisible(True)

    def _go_home(self):
        logger.debug("MainWindow._go_home: Resetting state")
        self.current_charts, self.current_profile = [], None
        self.btn_back.setVisible(False)
        self.btn_export.setVisible(False)
        self.stack.setCurrentWidget(self.welcome)

    def _show_export_panel(self):
        if not self.current_charts: return
        logger.debug("MainWindow._show_export_panel: Opening panel")
        self.export_panel.set_charts(self.current_charts)
        self.export_panel.move((self.width() - self.export_panel.width()) // 2, (self.height() - self.export_panel.height()) // 2)
        self.export_panel.show()
        self.export_panel.raise_()

    def _start_export(self, idx, stats, fmt):
        path, _ = QFileDialog.getSaveFileName(self, f"Сохранить отчёт ({fmt})", "", f"Files (*.{fmt.lower()})")
        if not path: self.export_panel.setHidden(True); return
        self.export_panel.setHidden(True)
        logger.debug(f"MainWindow._start_export: Saving to {path}")
        imgs = {i: self._capture_widget_preview(self.current_charts[i]) for i in idx if i < len(self.current_charts)}
        if self.export_thread.isRunning(): self.export_thread.quit(); self.export_thread.wait()
        self.export_worker = ExportWorker(self.report_service, self.current_charts, self.current_profile, idx, stats, fmt, path, imgs)
        self.export_worker.moveToThread(self.export_thread)
        self.export_thread.started.connect(self.export_worker.run)
        self.export_worker.finished.connect(self._on_export_success)
        self.export_worker.error.connect(self._on_error)
        self.export_worker.finished.connect(self.export_thread.quit)
        self.export_worker.error.connect(self.export_thread.quit)
        self.export_thread.start()

    def _on_export_success(self, path):
        logger.debug(f"MainWindow._on_export_success: {path}")
        QMessageBox.information(self, "Успех", f"Отчёт сохранён:\n{path}")

    def _on_error(self, msg):
        logger.error(f"MainWindow._on_error: {msg}")
        QMessageBox.critical(self, "Ошибка", msg)

    def closeEvent(self, e):
        for t in [self.pipeline_thread, self.export_thread]:
            if t.isRunning(): t.quit(); t.wait()
        super().closeEvent(e)

    def _show_chart_preview(self, i):
        if not self.current_charts: return
        self.preview_dlg = PreviewWindow(self.current_charts[i], self)
        self.preview_dlg.exec()

    def _capture_widget_preview(self, chart_entity, w=1000, h=750) -> bytes:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QThread
        w_map = {'line': LineChartWidget, 'area': AreaChartWidget, 'pie': PieChartWidget, 'bar': BarChartWidget, 'histogram': HistogramWidget, 'boxplot': BoxPlotWidget, 'scatter': ScatterChartWidget, 'heatmap': HeatmapWidget}
        w_cls = w_map.get(getattr(chart_entity, 'chart_type', None))
        if not w_cls: return b""
        widget = w_cls(chart_entity)
        widget.resize(w, h)
        for v in widget.findChildren(QChartView):
            if v.chart(): v.chart().setAnimationOptions(QChart.NoAnimation)
        widget.show()
        QApplication.processEvents()
        widget.update()
        QApplication.processEvents()
        QThread.msleep(200)
        QApplication.processEvents()
        img = QImage(QSize(w, h), QImage.Format_ARGB32)
        img.fill(Qt.white)
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        widget.render(p, QPoint(0, 0))
        p.end()
        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        img.save(buf, "PNG")
        widget.close()
        logger.debug(f"MainWindow._capture_widget_preview: Captured {chart_entity.title}")
        return buf.data().data()