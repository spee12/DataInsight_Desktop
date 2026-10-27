from __future__ import annotations
import logging
from PySide6.QtWidgets import QGraphicsTextItem
from typing import List, Any
from PySide6.QtCore import Qt
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QCategoryAxis, QAreaSeries
from PySide6.QtGui import QColor, QPainter, QBrush, QLinearGradient, QGradient, QPen
from domain.entities import Chart
from .base_chart_widget import BaseChartWidget

logger = logging.getLogger(__name__)
_CHART_BG, _TEXT_COLOR, _GRID_COLOR = QColor("#b5c3ee"), QColor("#000000"), QColor("#000000")

def _format_axis_label(val: Any) -> str:
    s = str(val).strip()
    if "  " in s:
        dp, tp = s.split("  ", 1)
        if tp.endswith(":00"): tp = tp.rsplit(":", 1)[0]
        return f"{dp} {tp}" if tp else dp
    elif ":" in s:
        return s.rsplit(":", 1)[0] if s.endswith(":00") else s
    return s

class LineChartWidget(BaseChartWidget):
    def __init__(self, chart: Chart, parent=None):
        self._series_list, self._axis_x, self._axis_y, self._qt_chart, self._chart_view = [], None, None, None, None
        super().__init__(chart, parent)

    def _build_chart(self, chart: Chart):
        logger.debug(f"LineChartWidget._build_chart: {chart.title}")
        if not chart.data or not chart.x_column: return
        self._qt_chart = QChart(); self._qt_chart.setBackgroundBrush(QBrush(_CHART_BG)); self._qt_chart.setTitle(chart.title); self._qt_chart.setTitleBrush(QBrush(_TEXT_COLOR))
        min_y, max_y, all_labels = float('inf'), float('-inf'), []
        for y_col in chart.y_columns:
            s = QLineSeries(); s.setName(str(y_col)); pts = 0
            for i, r in enumerate(chart.data):
                try:
                    yv = float(str(r.get(y_col)).replace(",", "."))
                    if y_col == chart.y_columns[0]: all_labels.append(_format_axis_label(r.get(chart.x_column)))
                    s.append(i, yv); pts += 1; min_y, max_y = min(min_y, yv), max(max_y, yv)
                except: continue
            if pts > 0: self._qt_chart.addSeries(s); self._series_list.append(s)
        if not self._series_list: return
        self._axis_x = QCategoryAxis(); self._axis_x.setLabelsColor(_TEXT_COLOR); self._axis_x.setGridLineVisible(True); self._axis_x.setGridLineColor(_GRID_COLOR)
        total = len(all_labels); step = max(1, total // 15) if total > 15 else 1
        for i, lbl in enumerate(all_labels):
            if i % step == 0: self._axis_x.append(lbl[:15] + "…" if len(lbl) > 15 else lbl, i)
        self._qt_chart.addAxis(self._axis_x, Qt.AlignBottom)
        self._axis_y = QValueAxis(); self._axis_y.setLabelsColor(_TEXT_COLOR); self._axis_y.setGridLineVisible(True); self._axis_y.setGridLineColor(_GRID_COLOR)
        if min_y != float('inf'): self._axis_y.setRange(min_y - (pad := (max_y - min_y) * 0.1 if max_y != min_y else 1), max_y + pad)
        self._qt_chart.addAxis(self._axis_y, Qt.AlignLeft)
        for s in self._series_list: s.attachAxis(self._axis_x); s.attachAxis(self._axis_y)
        self._chart_view = QChartView(self._qt_chart); self._chart_view.setRenderHint(QPainter.Antialiasing); self._chart_layout.addWidget(self._chart_view)
        logger.debug(f"LineChartWidget._build_chart: {sum(s.count() for s in self._series_list)} points")

class AreaChartWidget(BaseChartWidget):
    def __init__(self, chart: Chart, parent=None):
        self._area_series, self._upper_series, self._lower_series, self._axis_x, self._axis_y, self._qt_chart, self._chart_view = None, None, None, None, None, None, None
        super().__init__(chart, parent)
        self.setToolTip("Отклонение от медианы. Зелёный: выше нормы. Красный: ниже нормы.")

    def _build_chart(self, chart: Chart):
        logger.debug(f"AreaChartWidget._build_chart: {chart.title}")
        if not chart.data or not chart.x_column or not chart.y_columns: return
        self._qt_chart = QChart(); self._qt_chart.setBackgroundBrush(QBrush(_CHART_BG)); self._qt_chart.setTitle("Отклонение от базовой линии"); self._qt_chart.setTitleBrush(QBrush(_TEXT_COLOR))
        y_col = next((c for c in chart.y_columns if c == "avg_power"), chart.y_columns[0])
        pts, labels, min_y, max_y = [], [], float('inf'), float('-inf')
        for i, r in enumerate(chart.data):
            try:
                yv = float(str(r.get(y_col)).replace(",", "."))
                xr = str(r.get(chart.x_column)).strip()
                if "  " in xr:
                    dp, tp = xr.split("  ", 1)
                    if tp.endswith(":00"): tp = tp.rsplit(":", 1)[0]
                    xr = f"{dp} {tp}" if tp else dp
                labels.append(xr); pts.append((i, yv)); min_y, max_y = min(min_y, yv), max(max_y, yv)
            except: continue
        if not pts: return
        vals = sorted([p[1] for p in pts]); n = len(vals)
        baseline = vals[n // 2] if n % 2 == 1 else (vals[n // 2 - 1] + vals[n // 2]) / 2
        pts = [(x, y - baseline) for x, y in pts]
        min_s, max_s = min(p[1] for p in pts), max(p[1] for p in pts)
        grad = QLinearGradient(0, 0, 0, 1); grad.setCoordinateMode(QGradient.ObjectBoundingMode)
        has_pos, has_neg = any(y > 0 for _, y in pts), any(y < 0 for _, y in pts)
        if has_pos and has_neg: grad.setColorAt(0.0, QColor("#4ade80")); grad.setColorAt(0.5, QColor("#89b4fa")); grad.setColorAt(1.0, QColor("#f38ba8"))
        elif has_pos: grad.setColorAt(0.0, QColor("#4ade80")); grad.setColorAt(1.0, QColor("#4ade80").darker(150))
        else: grad.setColorAt(0.0, QColor("#f38ba8")); grad.setColorAt(1.0, QColor("#f38ba8").darker(150))
        self._upper_series = QLineSeries(); self._upper_series.setName(f"Δ {y_col}")
        self._lower_series = QLineSeries(); self._lower_series.setPen(QPen(QColor(0, 0, 0, 0), 0))
        for x, y in pts: self._upper_series.append(x, y); self._lower_series.append(x, 0.0)
        self._area_series = QAreaSeries(self._upper_series, self._lower_series); self._area_series.setBrush(QBrush(grad)); self._area_series.setPen(QPen(QColor("#000000"), 1))
        self._qt_chart.addSeries(self._area_series)
        bl = QLineSeries(); bl.append(-1, 0); bl.append(len(pts), 0); bl.setPen(QPen(QColor("#000000"), 1, Qt.DashLine)); self._qt_chart.addSeries(bl)
        self._axis_x = QCategoryAxis(); self._axis_x.setLabelsColor(_TEXT_COLOR); self._axis_x.setGridLineVisible(True); self._axis_x.setGridLineColor(_GRID_COLOR)
        total = len(labels); step = max(1, total // 15) if total > 15 else 1
        for i, lbl in enumerate(labels):
            if i % step == 0: self._axis_x.append(lbl[:15] + "…" if len(lbl) > 15 else lbl, i)
        self._qt_chart.addAxis(self._axis_x, Qt.AlignBottom)
        self._axis_y = QValueAxis(); self._axis_y.setLabelsColor(_TEXT_COLOR); self._axis_y.setGridLineVisible(True); self._axis_y.setGridLineColor(_GRID_COLOR)
        pad = (max_s - min_s) * 0.1 if max_s != min_s else 1
        self._axis_y.setRange(min(min_s - pad, 0), max(max_s + pad, 0)); self._qt_chart.addAxis(self._axis_y, Qt.AlignLeft)
        for s in [self._upper_series, self._lower_series, bl]: s.attachAxis(self._axis_x); s.attachAxis(self._axis_y)
        self._chart_view = QChartView(self._qt_chart); self._chart_view.setRenderHint(QPainter.Antialiasing); self._chart_layout.addWidget(self._chart_view)
        pos_v, neg_v = sum(y for _, y in pts if y > 0), sum(y for _, y in pts if y < 0)
        net = pos_v + neg_v
        html = f"<div style='background-color: #2a2a3e; padding: 5px; border-radius: 4px; border: 1px solid #3a3a5a;'><span style='color: #cdd6f4; font-family: sans-serif; font-size: 9pt;'>Медиана: <b>{baseline:.1f}</b><br/>▲ +{pos_v:.0f} | ▼ {neg_v:.0f}<br/>Баланс: <b style='color: {'#4ade80' if net >= 0 else '#f38ba8'};'>{net:+.0f}</b></span></div>"
        ann = QGraphicsTextItem(); ann.setHtml(html); ann.setPos(8, 8); ann.setTextWidth(170); ann.setZValue(10)
        self._chart_view.scene().addItem(ann)
        logger.debug(f"AreaChartWidget._build_chart: {self._upper_series.count()} points")