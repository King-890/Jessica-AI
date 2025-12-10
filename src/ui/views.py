from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class PlaceholderView(QWidget):
    def __init__(self, title, icon, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 64px; color: #3e3e4e;")
        layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 24px; color: #00f3ff; font-weight: bold; margin-top: 20px;")
        layout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        desc_label = QLabel("This module is currently under construction.")
        desc_label.setStyleSheet("font-size: 14px; color: #808080; margin-top: 10px;")
        layout.addWidget(desc_label, 0, Qt.AlignmentFlag.AlignCenter)


class BrainView(PlaceholderView):
    def __init__(self, parent=None):
        super().__init__("BRAIN ACTIVITY", "🧠", parent)


class FilesView(PlaceholderView):
    def __init__(self, parent=None):
        super().__init__("FILE EXPLORER", "📁", parent)


class PipelinesView(PlaceholderView):
    def __init__(self, parent=None):
        super().__init__("PIPELINE MANAGER", "⚡", parent)


class SettingsView(PlaceholderView):
    def __init__(self, parent=None):
        super().__init__("SETTINGS", "⚙️", parent)
