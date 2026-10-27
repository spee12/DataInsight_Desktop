from __future__ import annotations
import matplotlib
matplotlib.use('Qt5Agg')
import logging
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel
from domain.entities import Chart
from .base_chart_widget import BaseChartWidget

logger = logging.getLogger(__name__)
_MPL_STYLE = {"figure.facecolor": "#b5c3ee", "axes.facecolor": "#d9d9ff", "axes.edgecolor": "#000000", "axes.labelcolor": "#000000", "xtick.color": "#000000", "ytick.color": "#000000", "text.color": "#000000", "grid.color": "#000000", "grid.linestyle": "--", "grid.alpha": 0.9}
_ACCENT = "#4a9eff"
_PALETTE = ["#4a9eff", "#e94560", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c", "#e67e22", "#e74c3c"]

def _apply_dark_style(ax):
    ax.set_facecolor(_MPL_STYLE["axes.facecolor"]); ax.tick_params(colors=_MPL_STYLE["xtick.color"])
    ax.spines["bottom"].set_color(_MPL_STYLE["axes.edgecolor"]); ax.spines["left"].set_color(_MPL_STYLE["axes.edgecolor"])
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.grid(True, color=_MPL_STYLE["grid.color"], linestyle=_MPL_STYLE["grid.linestyle"], alpha=_MPL_STYLE["grid.alpha"])

class HistogramWidget(BaseChartWidget):
    def _build_chart(self, chart: Chart):
        logger.debug(f"HistogramWidget._build_chart: {chart.title}")
        col = chart.x_column or (chart.y_columns[0] if chart.y_columns else None)
        if not chart.data or not col: self._show_no_data(); return
        vals = self._extract_numeric_column(chart.data, col)
        if len(vals) < 2: self._show_no_data(); return
        arr = np.array(vals)
        self._fig = Figure(facecolor=_MPL_STYLE["figure.facecolor"], tight_layout=True)
        self._ax = self._fig.add_subplot(111); _apply_dark_style(self._ax)
        n_bins = min(max(int(np.sqrt(len(arr))), 10), 60)
        self._ax.hist(arr, bins=n_bins, color=_ACCENT, alpha=0.85, edgecolor="#4a9eff", linewidth=0.1)
        mean_v, med_v, std_v = np.mean(arr), np.median(arr), np.std(arr)
        self._ax.axvline(mean_v, color="#e94560", linewidth=1.5, linestyle="--", label=f"Среднее: {mean_v:.2f}")
        self._ax.axvline(med_v, color="#2ecc71", linewidth=1.5, linestyle="-.", label=f"Медиана: {med_v:.2f}")
        self._ax.set_xlabel(col, color=_MPL_STYLE["axes.labelcolor"], fontsize=9)
        self._ax.set_ylabel("Частота", color=_MPL_STYLE["axes.labelcolor"], fontsize=9)
        self._ax.tick_params(labelsize=8, colors=_MPL_STYLE["xtick.color"])
        self._ax.text(0.97, 0.97, f"n = {len(arr)}\nσ = {std_v:.2f}\nmin = {arr.min():.2f}\nmax = {arr.max():.2f}", transform=self._ax.transAxes, verticalalignment="top", horizontalalignment="right", fontsize=8, color=_MPL_STYLE["text.color"], bbox=dict(boxstyle="round,pad=0.3", facecolor="#2a2a3e", alpha=0.1, edgecolor="#3a3a5a"))
        leg = self._ax.legend(fontsize=8, facecolor="#2a2a3e", edgecolor="#3a3a5a", labelcolor=_MPL_STYLE["text.color"]); leg.get_frame().set_alpha(0.1)
        self._canvas = FigureCanvasQTAgg(self._fig); self._chart_layout.addWidget(self._canvas)
        logger.debug(f"HistogramWidget._build_chart: {len(arr)} values, {n_bins} bins")

    def _show_no_data(self):
        self._chart_layout.addWidget(QLabel("Нет данных для построения Histogram\n(нужна числовая колонка)", alignment=Qt.AlignmentFlag.AlignCenter, objectName="noDataLabel"))

class BoxPlotWidget(BaseChartWidget):
    MAX_COLS = 8
    def _build_chart(self, chart: Chart):
        logger.debug(f"BoxPlotWidget._build_chart: {chart.title}")
        y_cols = chart.y_columns or ([chart.x_column] if chart.x_column else [])
        if not chart.data or not y_cols: self._show_no_data(); return
        cols_data = [(c, np.array(self._extract_numeric_column(chart.data, c))) for c in y_cols[:self.MAX_COLS] if len(self._extract_numeric_column(chart.data, c)) >= 5]
        if not cols_data: self._show_no_data(); return
        self._fig = Figure(facecolor=_MPL_STYLE["figure.facecolor"], tight_layout=True)
        self._ax = self._fig.add_subplot(111); _apply_dark_style(self._ax)
        arrays = [d[1] for d in cols_data]; labels = [self._truncate_label(d[0], 12) for d in cols_data]


        bp = self._ax.boxplot(arrays, patch_artist=True, vert=True, widths=0.5, showfliers=True, flierprops=dict(marker="o", markersize=3, markerfacecolor="#e94560", markeredgecolor="#e94560", alpha=0.1, linestyle="none"), medianprops=dict(color="#ffffff", linewidth=2), whiskerprops=dict(color=_ACCENT, linewidth=1.2, linestyle="--"), capprops=dict(color=_ACCENT, linewidth=1.5))
        self._ax.set_xticklabels(labels)


        self._ax.tick_params(axis="x", labelsize=8, rotation=20 if len(labels) > 4 else 0, colors=_MPL_STYLE["xtick.color"])
        self._ax.tick_params(axis="y", labelsize=8, colors=_MPL_STYLE["ytick.color"])
        self._canvas = FigureCanvasQTAgg(self._fig); self._chart_layout.addWidget(self._canvas)
        logger.debug(f"BoxPlotWidget._build_chart: {len(cols_data)} boxes")

    def _show_no_data(self):
        self._chart_layout.addWidget(QLabel("Нет данных для построения Box Plot\n(нужны числовые колонки, минимум 5 значений)", alignment=Qt.AlignmentFlag.AlignCenter, objectName="noDataLabel"))