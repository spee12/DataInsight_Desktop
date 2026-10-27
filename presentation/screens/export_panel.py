import os, logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QComboBox, QPushButton, QHBoxLayout, QScrollArea
from PySide6.QtCore import Qt, Signal

logger = logging.getLogger(__name__)

class ExportPanel(QWidget):
    export_requested = Signal(list, bool, str)
    preview_requested = Signal(int)
    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent, objectName="ExportPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.chart_titles, self.checkboxes = [], []
        self._setup_ui()

    def _setup_ui(self):
        l = QVBoxLayout(self)
        l.setContentsMargins(15, 15, 15, 15)
        l.setSpacing(12)
        l.addWidget(QLabel("Выберите данные для экспорта", objectName="PanelTitle"))
        self.scroll = QScrollArea(widgetResizable=True, frameShape=QScrollArea.NoFrame)
        sc = QWidget(objectName="ScrollContent")
        self.sl = QVBoxLayout(sc)
        self.sl.setContentsMargins(0, 0, 0, 0)
        self.scroll.setWidget(sc)
        l.addWidget(self.scroll)
        self.table_cb = QCheckBox("Таблица статистики")
        l.addWidget(self.table_cb)
        fl = QHBoxLayout()
        fl.addWidget(QLabel("Формат:"))
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["PNG (графики)", "DOCX", "PDF", "HTML"])
        fl.addWidget(self.fmt_combo)
        l.addLayout(fl)
        bl = QHBoxLayout()
        bl.addWidget(QPushButton("Предпросмотр", clicked=self._handle_preview))
        bl.addStretch()
        bl.addWidget(QPushButton("Отмена", clicked=self.cancelled.emit))
        bl.addWidget(QPushButton("Экспортировать", clicked=self._handle_export))
        l.addLayout(bl)
        logger.debug("ExportPanel._setup_ui: UI initialized")

    def set_charts(self, charts: list):
        self.chart_titles = [c.title for c in charts]
        for cb in self.checkboxes: cb.deleteLater()
        self.checkboxes.clear()
        for i, t in enumerate(self.chart_titles):
            cb = QCheckBox(f"{i + 1}. {t}")
            cb.setProperty("chart_index", i)
            self.checkboxes.append(cb)
            self.sl.addWidget(cb)
        self.sl.addStretch(1)
        logger.debug(f"ExportPanel.set_charts: Loaded {len(charts)} charts")

    def _handle_export(self):
        idx = [cb.property("chart_index") for cb in self.checkboxes if cb.isChecked()]
        self.export_requested.emit(idx, self.table_cb.isChecked(), self.fmt_combo.currentText().split(" ")[0])

    def _handle_preview(self):
        idx = [cb.property("chart_index") for cb in self.checkboxes if cb.isChecked()]
        if idx: self.preview_requested.emit(idx[0])