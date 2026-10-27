import os, logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent

logger = logging.getLogger(__name__)

class WelcomeScreen(QWidget):
    file_selected = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._setup_ui()

    def _setup_ui(self):
        l = QVBoxLayout(self)
        l.setAlignment(Qt.AlignCenter)
        l.addStretch()
        btn = QPushButton("Загрузить файл", objectName="PrimaryButton")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self.file_selected.emit(""))
        l.addWidget(btn, alignment=Qt.AlignCenter)
        hint = QLabel("Выберите файл в формате xlsx, csv, db или перетащите в окно программы", alignment=Qt.AlignCenter, objectName="HintLabel")
        hint.setWordWrap(True)
        l.addWidget(hint)
        l.addStretch()
        logger.debug("WelcomeScreen._setup_ui: UI initialized")

    def dragEnterEvent(self, e: QDragEnterEvent):
        e.acceptProposedAction() if e.mimeData().hasUrls() else e.ignore()

    def dropEvent(self, e: QDropEvent):
        if e.mimeData().hasUrls():
            fp = e.mimeData().urls()[0].toLocalFile()
            if os.path.exists(fp): self.file_selected.emit(fp)
            logger.debug(f"WelcomeScreen.dropEvent: Dropped {fp}")
        else: e.ignore()