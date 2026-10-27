import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QGridLayout, QLabel, QFrame, QSizePolicy
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont
from domain.entities import Chart
from .base_chart_widget import BaseChartWidget
from .categorical_charts import BarChartWidget, PieChartWidget
from .temporal_charts import LineChartWidget, AreaChartWidget
from .statistical_charts import HistogramWidget, BoxPlotWidget
from .relational_charts import ScatterChartWidget, HeatmapWidget

logger = logging.getLogger(__name__)
_CHART_WIDGET_MAP = {"line": LineChartWidget, "area": AreaChartWidget, "bar": BarChartWidget, "pie": PieChartWidget, "scatter": ScatterChartWidget, "heatmap": HeatmapWidget, "histogram": HistogramWidget, "boxplot": BoxPlotWidget}
_PRIORITY_ORDER = ["line", "area", "bar", "pie", "scatter", "heatmap", "histogram", "boxplot"]
_COLS = 2

class _EmptyDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        l = QVBoxLayout(self); l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addStretch(); l.addWidget(QLabel("", alignment=Qt.AlignmentFlag.AlignCenter, font=QFont("Segoe UI", 36)))

class DashboardContainer(QWidget):
    charts_loaded = Signal(int)
    chart_error = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._widgets = {}
        self._empty_widget = _EmptyDashboard(self)
        self._setup_ui()
        logger.debug("DashboardContainer.__init__: Initialized")

    def _setup_ui(self):
        self.setObjectName("DashboardContainer")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        ol = QVBoxLayout(self); ol.setContentsMargins(0, 0, 0, 0); ol.setSpacing(0)
        ol.addWidget(self._build_header())
        self._scroll_area = QScrollArea(objectName="dashboardScrollArea", widgetResizable=True, frameShape=QFrame.Shape.NoFrame)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._grid_widget = QWidget(objectName="dashboardGrid")
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setContentsMargins(12, 12, 12, 12); self._grid_layout.setSpacing(12)
        self._grid_layout.setColumnStretch(0, 1); self._grid_layout.setColumnStretch(1, 1)
        self._grid_layout.addWidget(self._empty_widget, 0, 0, 1, _COLS)
        self._scroll_area.setWidget(self._grid_widget)
        ol.addWidget(self._scroll_area, stretch=1)

    def _build_header(self):
        h = QFrame(objectName="dashboardHeader", frameShape=QFrame.Shape.NoFrame, maximumHeight=44)
        h.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        hl = QHBoxLayout(h); hl.setContentsMargins(16, 0, 16, 0); hl.setSpacing(0)
        hl.addWidget(QLabel("Дашборд аналитики", objectName="dashboardTitle", font=QFont("Segoe UI", 8, QFont.Weight.Bold)))
        hl.addStretch()
        self._charts_count_label = QLabel("   ", objectName="chartsCountLabel")
        hl.addWidget(self._charts_count_label)
        return h

    def load_charts(self, charts: list[Chart]):
        logger.debug(f"DashboardContainer.load_charts: {len(charts)} charts")
        self.clear()
        if not charts: self._show_empty(); return
        type_order = {t: i for i, t in enumerate(_PRIORITY_ORDER)}
        sorted_charts = sorted(charts, key=lambda c: type_order.get(str(c.chart_type).lower().strip(), 99))
        loaded = 0
        for c in sorted_charts:
            if w := self._create_widget(c):
                r, col = divmod(loaded, _COLS)
                self._grid_layout.addWidget(w, r, col)
                self._widgets[c.chart_id] = w
                loaded += 1
            else: logger.warning(f"DashboardContainer.load_charts: Failed to create widget for {c.chart_type}")
        if loaded % 2 == 1 and loaded > 0:
            lw = list(self._widgets.values())[-1]
            lr = (loaded - 1) // _COLS
            self._grid_layout.removeWidget(lw); self._grid_layout.addWidget(lw, lr, 0, 1, _COLS)
        self._charts_count_label.setText(f"{loaded} графиков")
        self.charts_loaded.emit(loaded)
        logger.debug(f"DashboardContainer.load_charts: Loaded {loaded} charts")

    def update_chart(self, chart: Chart):
        if w := self._widgets.get(chart.chart_id): w.update_chart(chart)
        else: logger.warning(f"DashboardContainer.update_chart: {chart.chart_id} not found")

    def clear(self):
        for w in self._widgets.values(): self._grid_layout.removeWidget(w); w.hide(); w.deleteLater()
        self._widgets.clear()
        self._charts_count_label.setText("   ")

    def _create_widget(self, chart: Chart) -> BaseChartWidget | None:
        key = str(chart.chart_type).lower().strip()
        wc = _CHART_WIDGET_MAP.get(key)
        if not wc: logger.warning(f"DashboardContainer._create_widget: Unknown type {key}"); return None
        try:
            w = wc(chart)
            w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            w.setMinimumSize(QSize(380, 300))
            return w
        except Exception as e:
            logger.exception(f"DashboardContainer._create_widget: Error {key}: {e}")
            self.chart_error.emit(f"Ошибка отрисовки {key}: {e}")
            return None

    def _show_empty(self):
        self._grid_layout.addWidget(self._empty_widget, 0, 0, 1, _COLS)
        self._empty_widget.show()
        self._charts_count_label.setText("   ")