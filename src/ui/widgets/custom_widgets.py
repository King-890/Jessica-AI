from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QIcon

class ModernCard(QFrame):
    """A styled card container with shadow and hover effect"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

class StatCard(ModernCard):
    """Card displaying a specific metric (e.g. Memory Usage)"""
    def __init__(self, title, value, icon_name=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #8b9bb4; font-size: 12px; font-weight: bold;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        if icon_name:
            # Placeholder for icon
            pass
            
        layout.addLayout(header_layout)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: #e0e6ed; font-size: 24px; font-weight: bold;")
        layout.addWidget(self.value_label)
        
    def update_value(self, new_value):
        self.value_label.setText(new_value)

class SidebarButton(QPushButton):
    """Custom button for Sidebar navigation"""
    def __init__(self, text, icon_name=None, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setFixedHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-left: 3px solid transparent;
                text-align: left;
                padding-left: 20px;
                color: #8b9bb4;
                font-size: 14px;
            }
            QPushButton:checked {
                background-color: #1a1d2d;
                border-left: 3px solid #00d4ff;
                color: #00d4ff;
            }
            QPushButton:hover {
                background-color: #13151f;
                color: #e0e6ed;
            }
        """)

class ActionButton(QPushButton):
    """Primary action button (Neon)"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setObjectName("PrimaryButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)
