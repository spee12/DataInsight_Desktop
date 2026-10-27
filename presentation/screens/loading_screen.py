import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)

class LoadingScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        l = QVBoxLayout(self)
        l.setAlignment(Qt.AlignCenter)
        self.status_label = QLabel("Инициализация...", alignment=Qt.AlignCenter, objectName="StatusLabel")
        l.addWidget(self.status_label)
        self.progress_bar = QProgressBar(objectName="ProgressBar")
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        l.addWidget(self.progress_bar, alignment=Qt.AlignCenter)
        logger.debug("LoadingScreen.__init__: UI initialized")

    def start(self, indeterminate=True):
        if indeterminate: self.progress_bar.setRange(0, 0)
        self.status_label.setText("Чтение и валидация данных...")

    def update(self, val: int, txt: str):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(val)
        self.status_label.setText(txt)
        logger.debug(f"LoadingScreen.update: {val}% - {txt}")

    def finish(self):
        self.status_label.setText("Формирование дашборда...")