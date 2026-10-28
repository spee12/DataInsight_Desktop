import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QSizePolicy, QScrollArea
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QFont
from domain.entities import Chart
logger = logging.getLogger(__name__)

class BaseChartWidget(QWidget):
    MIN_WIDTH, MIN_HEIGHT = 420, 320

    def __init__(self, chart: Chart, parent=None):
        super().__init__(parent)
        self._chart_entity = chart
        self._title_text = chart.title
        self._setup_ui()
        self._build_chart(chart)
        self._install_scroll_filter_recursive(self._chart_frame)
        logger.debug(f"BaseChartWidget.__init__: {chart.title}")

    def _setup_ui(self):
        self.setObjectName("BaseChartWidget")
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        l = QVBoxLayout(self); l.setContentsMargins(10, 10, 10, 10); l.setSpacing(6)
        self._title_label = QLabel(self._title_text, objectName="chartTitleLabel", alignment=Qt.AlignmentFlag.AlignCenter, font=QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._title_label.setWordWrap(True); self._title_label.setMaximumHeight(36)
        self._chart_frame = QFrame(objectName="chartFrame", frameShape=QFrame.Shape.StyledPanel, sizePolicy=QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))
        self._chart_layout = QVBoxLayout(self._chart_frame); self._chart_layout.setContentsMargins(4, 4, 4, 4)
        l.addWidget(self._title_label); l.addWidget(self._chart_frame, stretch=1)

    def update_chart(self, chart: Chart):
        self._chart_entity = chart; self._title_label.setText(chart.title)
        self.clear_chart(); self._build_chart(chart)

    def clear_chart(self):
        while self._chart_layout.count():
            if (w := self._chart_layout.takeAt(0).widget()): w.hide(); w.deleteLater()

    def _install_scroll_filter_recursive(self, p):
        p.installEventFilter(self)
        for c in p.findChildren(QWidget): c.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel and not event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            if sa := self._find_scroll_area(): sa.wheelEvent(event); return True
        return super().eventFilter(obj, event)

    def _find_scroll_area(self):
        p = self.parent()
        while p:
            if isinstance(p, QScrollArea): return p
            p = p.parent()

    def _build_chart(self, chart: Chart): raise NotImplementedError

    @staticmethod
    def _extract_numeric_column(data, col):
        return [float(str(r.get(col)).replace(",", ".")) for r in data if r.get(col) is not None]

    @staticmethod
    def _extract_string_column(data, col):
        return [str(r[col]) for r in data if r.get(col) is not None]

    @staticmethod
    def _truncate_label(label, max_len=14):
        return label if len(label) <= max_len else f"{label[:max_len-1]}…"