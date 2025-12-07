from PyQt6.QtWidgets import (
    QWidget, QPushButton, QFrame, QLabel, QSlider, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtProperty, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QRadialGradient

class HUDFrame(QFrame):
    """Container with a glowing border effect"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HUDFrame")
        
        # Glow Effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor("#00f0ff"))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

class HUDButton(QPushButton):
    """Tech-styled button"""
    def __init__(self, text, icon=None, parent=None):
        super().__init__(text, parent)
        self.setObjectName("HUDButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(50)

class AvatarWidget(QWidget):
    """Central Avatar with pulsing animation"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 200)
        self._pulse_size = 0.0
        self._direction = 1
        
        # Animation Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)  # 20 FPS
        
    def animate(self):
        self._pulse_size += 0.05 * self._direction
        if self._pulse_size >= 1.0:
            self._direction = -1
        elif self._pulse_size <= 0.0:
            self._direction = 1
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Center point
        center = QRectF(self.rect()).center()
        radius = 80
        
        # Draw Glow Ring (Pulsing)
        glow_radius = radius + (10 * self._pulse_size)
        painter.setPen(QPen(QColor(0, 240, 255, 100), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, glow_radius, glow_radius)
        
        # Draw Main Circle (Head)
        gradient = QRadialGradient(center, radius)
        gradient.setColorAt(0, QColor("#00f0ff"))
        gradient.setColorAt(1, QColor("#005f73"))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius, radius)
        
        # Draw Stylized "Head" Shape (Placeholder for simple visualization)
        painter.setBrush(QColor("#020b14"))
        painter.drawEllipse(center, radius * 0.4, radius * 0.5)

class NeonSlider(QSlider):
    """Styled Slider"""
    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setObjectName("NeonSlider")
