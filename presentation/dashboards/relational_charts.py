import logging
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCharts import QChart, QChartView, QScatterSeries, QValueAxis
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QLabel
from domain.entities import Chart
from .base_chart_widget import BaseChartWidget

logger = logging.getLogger(__name__)
_PALETTE = ["#4a9eff", "#e94560", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]
_CHART_BG, _PLOT_BG, _TITLE_COLOR, _AXIS_COLOR, _GRID_COLOR = QColor("#d9d9ff"), QColor("#d9d9ff"), QColor("#000000"), QColor("#000000"), QColor("#000000")
_MPL_STYLE = {"figure.facecolor": "#d9d9ff", "axes.facecolor": "#d9d9ff", "axes.edgecolor": "#000000", "axes.labelcolor": "#000000", "xtick.color": "#000000", "ytick.color": "#000000"}

def _apply_dark_style(ax):
    ax.set_facecolor(_MPL_STYLE["axes.facecolor"]); ax.tick_params(colors=_MPL_STYLE["xtick.color"])
    ax.spines["bottom"].set_color(_MPL_STYLE["axes.edgecolor"]); ax.spines["left"].set_color(_MPL_STYLE["axes.edgecolor"])
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

def _style_qt_chart(c):
    c.setBackgroundBrush(_CHART_BG); c.setPlotAreaBackgroundBrush(_PLOT_BG); c.setPlotAreaBackgroundVisible(True)
    c.setTitleBrush(_TITLE_COLOR); c.setDropShadowEnabled(False); c.legend().setLabelColor(_TITLE_COLOR)

class ScatterChartWidget(BaseChartWidget):
    MAX_POINTS = 800
    def _build_chart(self, chart: Chart):
        logger.debug(f"ScatterChartWidget._build_chart: {chart.title}")
        if not chart.data or not chart.x_column or not chart.y_columns: self._show_no_data(); return
        step = max(1, len(chart.data) // self.MAX_POINTS)
        data_sample = chart.data[::step]
        qc = QChart(); _style_qt_chart(qc); qc.setAnimationOptions(QChart.AnimationOption.NoAnimation)
        all_series = []
        min_x, max_x, min_y, max_y = float('inf'), float('-inf'), float('inf'), float('-inf')
        for i, y_col in enumerate(chart.y_columns):
            s = QScatterSeries(); s.setName(y_col)
            col = QColor(_PALETTE[i % len(_PALETTE)]); s.setColor(col); s.setBorderColor(QColor(col.red(), col.green(), col.blue(), 120)); s.setMarkerSize(7.0)
            x_vals, y_vals = [], []
            for r in data_sample:
                try:
                    xv = float(str(r.get(chart.x_column)).replace(",", ".")); yv = float(str(r.get(y_col)).replace(",", "."))
                    s.append(xv, yv); x_vals.append(xv); y_vals.append(yv)
                    min_x, max_x = min(min_x, xv), max(max_x, xv); min_y, max_y = min(min_y, yv), max(max_y, yv)
                except: pass
            if s.count() > 0: qc.addSeries(s); all_series.append((s, x_vals, y_vals))
        if not all_series: self._show_no_data(); return
        if len(all_series) == 1 and len(all_series[0][1]) >= 3: self._add_trend_line(qc, all_series[0][1], all_series[0][2], min_x, max_x)
        px = (max_x - min_x) * 0.05 if max_x != float('inf') else 1.0
        py = (max_y - min_y) * 0.05 if max_y != float('inf') else 1.0
        ax = QValueAxis(); ax.setLabelsColor(_AXIS_COLOR); ax.setGridLineColor(_GRID_COLOR); ax.setTitleText(chart.x_column); ax.setTitleBrush(_AXIS_COLOR)
        if min_x != float('inf'): ax.setRange(min_x - px, max_x + px)
        qc.addAxis(ax, Qt.AlignmentFlag.AlignBottom)
        ay = QValueAxis(); ay.setLabelsColor(_AXIS_COLOR); ay.setGridLineColor(_GRID_COLOR); ay.setTitleText(chart.y_columns[0] if len(chart.y_columns) == 1 else "Значение"); ay.setTitleBrush(_AXIS_COLOR)
        if min_y != float('inf'): ay.setRange(min_y - py, max_y + py)
        qc.addAxis(ay, Qt.AlignmentFlag.AlignLeft)
        for s, _, _ in all_series: s.attachAxis(ax); s.attachAxis(ay)
        v = QChartView(qc); v.setRenderHint(QPainter.RenderHint.Antialiasing); self._chart_layout.addWidget(v)
        logger.debug(f"ScatterChartWidget._build_chart: {len(all_series)} series")

    def _add_trend_line(self, c, x_vals, y_vals, x_min, x_max):
        try:
            coeffs = np.polyfit(np.array(x_vals), np.array(y_vals), 1); trend = np.poly1d(coeffs)
            from PySide6.QtCharts import QLineSeries
            lt = QLineSeries(); lt.setName(f"Тренд (y={coeffs[0]:.2f}x + {coeffs[1]:.2f})")
            lt.setPen(QPen(QColor("#f39c12"), 2, Qt.PenStyle.DashLine))
            for xv in np.linspace(x_min, x_max, 100): lt.append(float(xv), float(trend(xv)))
            c.addSeries(lt)
        except Exception as e: logger.warning(f"ScatterChartWidget._add_trend_line: {e}")

    def _show_no_data(self):
        self._chart_layout.addWidget(QLabel("Нет данных для построения Scatter Plot\n(нужны: минимум две числовые колонки)", alignment=Qt.AlignmentFlag.AlignCenter, objectName="noDataLabel"))

class HeatmapWidget(BaseChartWidget):
    MAX_COLS = 12
    def _build_chart(self, chart: Chart):
        logger.debug(f"HeatmapWidget._build_chart: {chart.title}")
        if not chart.data: self._show_no_data(); return
        y_cols = chart.y_columns or [c for c in chart.data[0].keys() if len(self._extract_numeric_column(chart.data, c)) >= 5]
        y_cols = y_cols[:self.MAX_COLS]
        if len(y_cols) < 2: self._show_no_data("Для тепловой карты нужно минимум 2 числовые колонки"); return
        arrays, valid_cols = [], []
        for c in y_cols:
            vals = self._extract_numeric_column(chart.data, c)
            if len(vals) >= 5: arrays.append(np.array(vals)); valid_cols.append(c)
        if len(valid_cols) < 2: self._show_no_data(); return
        min_len = min(len(a) for a in arrays)
        matrix = np.corrcoef([a[:min_len] for a in arrays])
        n = len(valid_cols); fs = max(5, n * 0.85)
        fig = Figure(figsize=(fs, fs), facecolor=_MPL_STYLE["figure.facecolor"], tight_layout=True)
        ax = fig.add_subplot(111); _apply_dark_style(ax)
        cmap = self._build_dark_cmap()
        im = ax.imshow(matrix, cmap=cmap, vmin=-1.0, vmax=1.0, aspect="auto", interpolation="nearest")
        short_labels = [self._truncate_label(c, 10) for c in valid_cols]
        ax.set_xticks(range(n)); ax.set_yticks(range(n))
        ax.set_xticklabels(short_labels, rotation=40, ha="right", fontsize=8, color=_MPL_STYLE["xtick.color"])
        ax.set_yticklabels(short_labels, fontsize=8, color=_MPL_STYLE["ytick.color"])
        for i in range(n):
            for j in range(n):
                v = matrix[i, j]; tc = "#ffffff" if abs(v) > 0.5 else "#888aaa"
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7 if n > 8 else 9, color=tc, fontweight="bold" if abs(v) > 0.7 else "normal")
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04); cbar.ax.tick_params(colors=_MPL_STYLE["xtick.color"], labelsize=8); cbar.outline.set_edgecolor(_MPL_STYLE["axes.edgecolor"]); cbar.set_label("Коэф. Пирсона", color=_MPL_STYLE["axes.labelcolor"], fontsize=9)
        self._chart_layout.addWidget(FigureCanvasQTAgg(fig))
        logger.debug(f"HeatmapWidget._build_chart: Matrix {n}x{n}")

    @staticmethod
    def _build_dark_cmap():
        try:
            from matplotlib.colors import LinearSegmentedColormap
            return LinearSegmentedColormap.from_list("dark_coolwarm", [(0.0, "#1a5276"), (0.25, "#2e86c1"), (0.5, "#2a2a3e"), (0.75, "#c0392b"), (1.0, "#7b241c")])
        except: return "coolwarm"

    def _show_no_data(self, msg=None):
        self._chart_layout.addWidget(QLabel(msg or "Нет данных для тепловой карты\n(нужны: минимум 2 числовые колонки)", alignment=Qt.AlignmentFlag.AlignCenter, objectName="noDataLabel"))