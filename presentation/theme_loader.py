import os, logging
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

def get_resource_path(rel_path: str) -> str:
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, rel_path)

def load_all_qss(app: QApplication):
    qss_files = ["main.qss", "export_panel.qss", "dashboard.qss"]
    styles = []
    for f in qss_files:
        path = get_resource_path(f"theme/{f}")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as file: styles.append(file.read())
            logger.debug(f"theme_loader.load_all_qss: Loaded {f}")
        else:
            logger.warning(f"theme_loader.load_all_qss: Missing {f}")
    app.setStyleSheet("\n".join(styles))