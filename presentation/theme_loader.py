import os
import logging
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

def get_resource_path(rel_path: str) -> str:

    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, rel_path)

def load_all_qss(app: QApplication):
    qss_files = [
        "theme/main.qss",
        "theme/export_panel.qss",
        "theme/dashboard.qss",
    ]
    styles = []
    for rel in qss_files:
        path = get_resource_path(rel)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                styles.append(f.read())
            logger.debug(f"theme_loader.load_all_qss: Loaded {rel} ({path})")
        else:
            logger.warning(f"theme_loader.load_all_qss: Missing {rel} ({path})")
    app.setStyleSheet("\n".join(styles))