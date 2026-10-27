import logging
from PySide6.QtCharts import QBarCategoryAxis, QBarSeries, QBarSet, QChart, QChartView, QPieSeries, QValueAxis
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QLabel
from domain.entities import Chart
from application.services.aggregation_service import AggregationService
from .base_chart_widget import BaseChartWidget

logger = logging.getLogger(__name__)
_PALETTE = ["#4a9eff", "#e94560", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c", "#e67e22", "#e74c3c"]
_CHART_BG, _PLOT_BG, _TITLE_COLOR, _AXIS_COLOR, _GRID_COLOR = QColor("#b5c3ee"), QColor("#d9d9ff"), QColor("#000000"), QColor("#000000"), QColor("#000000")

def _style_chart(c, t=""):
    c.setBackgroundBrush(_CHART_BG); c.setPlotAreaBackgroundBrush(_PLOT_BG); c.setPlotAreaBackgroundVisible(True)
    c.setTitleBrush(_TITLE_COLOR); c.setDropShadowEnabled(False); c.legend().setLabelColor(_TITLE_COLOR); c.legend().setVisible(True)

class BarChartWidget(BaseChartWidget):
    MAX_CATEGORIES = 15
    def _build_chart(self, chart: Chart):
        logger.debug(f"BarChartWidget._build_chart: {chart.title}")
        if not chart.data or not chart.x_column: self._show_no_data(); return
        counts = AggregationService.frequency(chart.data, chart.x_column)
        sorted_cats = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_cats) > self.MAX_CATEGORIES:
            main_cats = sorted_cats[:self.MAX_CATEGORIES]; main_cats.append(("Прочие", sum(v for _, v in sorted_cats[self.MAX_CATEGORIES:]))); sorted_cats = main_cats
        cats = [k for k, _ in sorted_cats]; freqs = [v for _, v in sorted_cats]
        if not cats: self._show_no_data(); return
        bs = QBarSeries(); bset = QBarSet("Частота")
        bset.setColor(QColor(_PALETTE[0])); bset.setLabelColor(_TITLE_COLOR)
        for v in freqs: bset.append(v)
        bs.append(bset)
        qc = QChart(); _style_chart(qc, chart.title); qc.addSeries(bs); qc.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        ax = QBarCategoryAxis(); ax.append(cats); ax.setLabelsColor(_AXIS_COLOR); ax.setGridLineColor(_GRID_COLOR); ax.setLabelsAngle(-30 if len(cats) > 7 else 0)
        qc.addAxis(ax, Qt.AlignmentFlag.AlignBottom); bs.attachAxis(ax)
        ay = QValueAxis(); ay.setLabelsColor(_AXIS_COLOR); ay.setGridLineColor(_GRID_COLOR); ay.setTitleText("Количество"); ay.setTitleBrush(_AXIS_COLOR)
        qc.addAxis(ay, Qt.AlignmentFlag.AlignLeft); bs.attachAxis(ay)
        v = QChartView(qc); v.setRenderHint(QPainter.RenderHint.Antialiasing); self._chart_layout.addWidget(v)
        logger.debug(f"BarChartWidget._build_chart: Built {len(cats)} categories")

    def _show_no_data(self):
        self._chart_layout.addWidget(QLabel("Нет данных для построения Bar Chart\n(нужна: категориальная колонка)", alignment=Qt.AlignmentFlag.AlignCenter, objectName="noDataLabel"))

class PieChartWidget(BaseChartWidget):
    MAX_SLICES = 7
    def _build_chart(self, chart: Chart):
        logger.debug(f"PieChartWidget._build_chart: {chart.title}")
        if not chart.data or not chart.x_column: self._show_no_data(); return
        y_col = chart.y_columns[0] if chart.y_columns else None
        if y_col:
            cats = {str(r.get(chart.x_column)) for r in chart.data if r.get(chart.x_column) is not None}
            agg = {c: AggregationService.weighted_sum([r for r in chart.data if str(r.get(chart.x_column)) == c], y_col, y_col) for c in cats}
        else:
            agg = AggregationService.frequency(chart.data, chart.x_column)
        if not agg: self._show_no_data(); return
        sorted_items = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)
        if len(sorted_items) > self.MAX_SLICES:
            main_items = sorted_items[:self.MAX_SLICES - 1]; main_items.append(("Прочие", sum(v for _, v in sorted_items[self.MAX_SLICES - 1:]))); sorted_items = main_items
        total = sum(v for _, v in sorted_items)
        if total == 0: self._show_no_data(); return
        ps = QPieSeries()
        metric_name = f"Вклад в '{y_col}'" if y_col else "Доля по количеству"
        for i, (lbl, val) in enumerate(sorted_items):
            pct = val / total * 100
            sl = ps.append(f"{self._truncate_label(lbl, 12)} ({pct:.1f}%)", val)
            sl.setColor(QColor(_PALETTE[i % len(_PALETTE)])); sl.setLabelColor(_TITLE_COLOR)
            if i == 0: sl.setExploded(True); sl.setExplodeDistanceFactor(0.06)
        ps.setLabelsVisible(True)
        qc = QChart(); _style_chart(qc); qc.addSeries(ps); qc.setAnimationOptions(QChart.AnimationOption.SeriesAnimations); qc.legend().setAlignment(Qt.AlignmentFlag.AlignRight); qc.setTitle(metric_name)
        v = QChartView(qc); v.setRenderHint(QPainter.RenderHint.Antialiasing); self._chart_layout.addWidget(v)
        logger.debug(f"PieChartWidget._build_chart: Built {len(sorted_items)} slices")

    def _show_no_data(self):
        self._chart_layout.addWidget(QLabel("Нет данных для построения Pie Chart\n(нужна: категориальная колонка)", alignment=Qt.AlignmentFlag.AlignCenter, objectName="noDataLabel"))