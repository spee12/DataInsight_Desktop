import logging
from typing import Any
from PySide6.QtCore import QBuffer, QIODevice, QSize
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication
from PySide6.QtCharts import QChart, QChartView

logger = logging.getLogger(__name__)

class OffscreenChartSnapshotter:
    def __init__(self, size: QSize = QSize(800, 600)):
        self.size = size

    def snapshot(self, chart: QChart) -> bytes:
        logger.debug(f"{self.__class__.__name__}.snapshot: {chart.title()}")
        if not QApplication.instance():
            raise RuntimeError("QApplication required")
        view = QChartView(chart)
        view.setRenderHint(QPainter.RenderHint.Antialiasing)
        view.resize(self.size)
        image = QImage(self.size, QImage.Format.Format_ARGB32)
        image.fill(0xFFFFFFFF)
        painter = QPainter(image)
        view.render(painter)
        painter.end()
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        return bytes(buffer.data())