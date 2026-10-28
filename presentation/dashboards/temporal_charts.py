from __future__ import annotations
import logging
from typing import Any
from PySide6.QtWidgets import QGraphicsTextItem
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QCategoryAxis, QAreaSeries, QDateTimeAxis
from PySide6.QtGui import QColor, QPainter, QBrush, QLinearGradient, QGradient, QPen
from domain.entities import Chart
from .base_chart_widget import BaseChartWidget
logger = logging.getLogger(__name__)
_CHART_BG, _TEXT_COLOR, _GRID_COLOR = QColor("#b5c3ee"), QColor("#000000"), QColor("#000000")


def _format_axis_label(val: Any) -> str:
    s = str(val).strip()
    if " " in s:
        dp, tp = s.split(" ", 1)
        if tp.endswith(":00"): tp = tp.rsplit(":", 1)[0]
        return f"{dp} {tp}" if tp else dp
    return s.rsplit(":", 1)[0] if ":" in s and s.endswith(":00") else s


def _try_numeric(vals):
    try: return [float(str(v).replace(",", ".")) for v in vals]
    except (TypeError, ValueError): return None


_DT_FMTS = ("yyyy-MM-dd HH:mm:ss", "yyyy-MM-dd HH:mm", "yyyy-MM-ddTHH:mm:ss", "yyyy-MM-dd",
            "dd.MM.yyyy HH:mm:ss", "dd.MM.yyyy HH:mm", "dd.MM.yyyy")

def _to_ms(v):
    s = str(v).strip()
    return next((float(dt.toMSecsSinceEpoch()) for f in _DT_FMTS if (dt := QDateTime.fromString(s, f)).isValid()), None)

def _try_datetime(vals):
    r = [_to_ms(v) for v in vals]
    return r if r and None not in r else None


def _style_axis(ax):
    ax.setLabelsColor(_TEXT_COLOR); ax.setGridLineVisible(True); ax.setGridLineColor(_GRID_COLOR)
    return ax


class _ZoomChartView(QChartView):
    def __init__(self, chart: QChart):
        super().__init__(chart)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRubberBand(QChartView.RubberBand.HorizontalRubberBand)

    def mouseDoubleClickEvent(self, e):
        self.chart().zoomReset()


class _TemporalBase(BaseChartWidget):
    def __init__(self, chart: Chart, parent=None):
        self._series_list, self._axis_x, self._axis_y, self._qt_chart, self._chart_view, self._full_labels = [], None, None, None, None, []
        super().__init__(chart, parent)

    def _new_chart(self, title: str):
        self._qt_chart = QChart()
        self._qt_chart.setBackgroundBrush(QBrush(_CHART_BG)); self._qt_chart.setTitle(title); self._qt_chart.setTitleBrush(QBrush(_TEXT_COLOR))

    def _attach_x(self, raw_xs):
        num, dt = _try_numeric(raw_xs), _try_datetime(raw_xs)
        is_dt = dt and (not num or num[0] > 1e11)
        vals = dt if is_dt else num
        if is_dt:
            self._axis_x = _style_axis(QDateTimeAxis())
            dmin, dmax = QDateTime.fromMSecsSinceEpoch(int(min(dt))), QDateTime.fromMSecsSinceEpoch(int(max(dt)))
            self._axis_x.setRange(dmin, dmax)
            self._tune_dt_fmt(dmin, dmax)
            self._axis_x.rangeChanged.connect(self._tune_dt_fmt)
        elif num:
            self._axis_x = _style_axis(QValueAxis())
            pad = (max(num) - min(num)) * 0.05 or 1
            self._axis_x.setRange(min(num) - pad, max(num) + pad)
        else:
            self._axis_x = _style_axis(QCategoryAxis())
            self._full_labels = [_format_axis_label(v) for v in raw_xs]
        self._qt_chart.addAxis(self._axis_x, Qt.AlignmentFlag.AlignBottom)
        if not vals: self._refresh_x_labels(0, len(self._full_labels) - 1)
        return vals

    def _tune_dt_fmt(self, lo, hi):
        s = lo.msecsTo(hi)
        self._axis_x.setFormat("yyyy" if s > 3.15e10 else "yyyy-MM" if s > 5.18e9 else "dd.MM" if s > 1.73e8
                               else "dd.MM HH:mm" if s > 4.32e7 else "HH:mm" if s > 3.6e6 else "HH:mm:ss")

    def _add_y_axis(self, lo: float, hi: float):
        self._axis_y = _style_axis(QValueAxis())
        pad = (hi - lo) * 0.1 if hi != lo else 1
        self._axis_y.setRange(lo - pad, hi + pad)
        self._qt_chart.addAxis(self._axis_y, Qt.AlignmentFlag.AlignLeft)

    def _finish(self, numeric: bool):
        self._chart_view = _ZoomChartView(self._qt_chart)
        self._chart_layout.addWidget(self._chart_view)
        if not numeric: self._axis_x.rangeChanged.connect(self._refresh_x_labels)

    def _refresh_x_labels(self, lo, hi):
        if not self._full_labels: return
        w = self._chart_view.width() if self._chart_view else 800
        lo_i, hi_i = max(0, int(lo)), min(len(self._full_labels) - 1, int(hi) + 1)
        vis = hi_i - lo_i + 1
        step = max(1, -(-vis // max(2, w // 110)))
        mc = max(4, w // 7 // max(1, vis // step + 1))
        [self._axis_x.remove(l) for l in self._axis_x.categoriesLabels()]
        for i in range(lo_i, hi_i + 1, step):
            lb = self._full_labels[i]
            self._axis_x.append(lb if len(lb) <= mc else f"{lb[:mc - 1]}…", i)


class LineChartWidget(_TemporalBase):
    def _build_chart(self, chart: Chart):
        logger.debug(f"LineChartWidget._build_chart: {chart.title}")
        if not chart.data or not chart.x_column: return
        self._new_chart(chart.title)
        num_x = self._attach_x([r.get(chart.x_column) for r in chart.data])
        lo, hi = float('inf'), float('-inf')
        for y_col in chart.y_columns:
            s = QLineSeries(); s.setName(str(y_col)); n = 0
            for i, r in enumerate(chart.data):
                try:
                    yv = float(str(r.get(y_col)).replace(",", "."))
                    s.append(num_x[i] if num_x else i, yv); n += 1; lo, hi = min(lo, yv), max(hi, yv)
                except (TypeError, ValueError): continue
            if n: self._qt_chart.addSeries(s); self._series_list.append(s)
        if not self._series_list: return
        self._add_y_axis(lo, hi)
        for s in self._series_list: s.attachAxis(self._axis_x); s.attachAxis(self._axis_y)
        self._finish(num_x is not None)
        logger.debug(f"LineChartWidget._build_chart: {sum(s.count() for s in self._series_list)} points")


class AreaChartWidget(_TemporalBase):
    def __init__(self, chart: Chart, parent=None):
        super().__init__(chart, parent)
        self.setToolTip("Отклонение от медианы. Зелёный: выше нормы. Красный: ниже нормы.")

    def _build_chart(self, chart: Chart):
        logger.debug(f"AreaChartWidget._build_chart: {chart.title}")
        if not chart.data or not chart.x_column or not chart.y_columns: return
        self._new_chart("Отклонение от базовой линии")
        num_x = self._attach_x([r.get(chart.x_column) for r in chart.data])
        y_col = next((c for c in chart.y_columns if c == "avg_power"), chart.y_columns[0])
        pts = []
        for i, r in enumerate(chart.data):
            try: pts.append((num_x[i] if num_x else i, float(str(r.get(y_col)).replace(",", "."))))
            except (TypeError, ValueError): continue
        if not pts: return
        vals = sorted(y for _, y in pts); n = len(vals)
        base = vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2
        pts = [(x, y - base) for x, y in pts]
        lo, hi = min(y for _, y in pts), max(y for _, y in pts)
        grad = QLinearGradient(0, 0, 0, 1); grad.setCoordinateMode(QGradient.CoordinateMode.ObjectBoundingMode)
        hp, hn = any(y > 0 for _, y in pts), any(y < 0 for _, y in pts)
        if hp and hn: grad.setColorAt(0.0, QColor("#4ade80")); grad.setColorAt(0.5, QColor("#89b4fa")); grad.setColorAt(1.0, QColor("#f38ba8"))
        elif hp: grad.setColorAt(0.0, QColor("#4ade80")); grad.setColorAt(1.0, QColor("#4ade80").darker(150))
        else: grad.setColorAt(0.0, QColor("#f38ba8")); grad.setColorAt(1.0, QColor("#f38ba8").darker(150))
        up = QLineSeries(); up.setName(f"Δ {y_col}")
        dn = QLineSeries(); dn.setPen(QPen(QColor(0, 0, 0, 0), 0))
        for x, y in pts: up.append(x, y); dn.append(x, 0.0)
        area = QAreaSeries(up, dn); area.setBrush(QBrush(grad)); area.setPen(QPen(QColor("#000000"), 1))
        bl = QLineSeries(); bl.append(pts[0][0], 0.0); bl.append(pts[-1][0], 0.0); bl.setPen(QPen(QColor("#000000"), 1, Qt.PenStyle.DashLine))
        for s in (area, bl): self._qt_chart.addSeries(s)
        self._series_list = [up, dn, bl]
        self._add_y_axis(min(lo, 0.0), max(hi, 0.0))
        for s in self._series_list: s.attachAxis(self._axis_x); s.attachAxis(self._axis_y)
        self._finish(num_x is not None)
        pos, neg = sum(y for _, y in pts if y > 0), sum(y for _, y in pts if y < 0)
        net = pos + neg
        ann = QGraphicsTextItem()
        ann.setHtml(f"<div style='background-color:#2a2a3e;padding:5px;border-radius:4px;border:1px solid #3a3a5a;'><span style='color:#cdd6f4;font-family:sans-serif;font-size:9pt;'>Медиана: <b>{base:.1f}</b><br/>▲ +{pos:.0f} | ▼ {neg:.0f}<br/>Баланс: <b style='color:{'#4ade80' if net >= 0 else '#f38ba8'};'>{net:+.0f}</b></span></div>")
        ann.setPos(8, 8); ann.setTextWidth(170); ann.setZValue(10)
        self._chart_view.scene().addItem(ann)
        logger.debug(f"AreaChartWidget._build_chart: {up.count()} points")