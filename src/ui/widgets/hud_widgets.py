from PyQt6.QtWidgets import (
    QWidget, QPushButton, QFrame, QGraphicsDropShadowEffect, QSlider
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
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

        # Draw Main Head Shape (Oval)
        head_gradient = QRadialGradient(center, radius)
        head_gradient.setColorAt(0, QColor("#00f0ff"))  # Bright center
        head_gradient.setColorAt(1, QColor("#005f73"))  # Darker edge

        painter.setBrush(QBrush(head_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        # Draw slightly elongated circle for head
        painter.drawEllipse(center, radius * 0.85, radius)

        # Draw "Eyes" (Simple glowing slits)
        eye_y = center.y() - (radius * 0.1)
        eye_w = radius * 0.2
        eye_h = radius * 0.08
        spacing = radius * 0.3

        painter.setBrush(QBrush(QColor("#ffffff")))  # Bright white eyes

        # Left Eye
        painter.drawEllipse(QPointF(center.x() - spacing, eye_y), eye_w, eye_h)
        # Right Eye
        painter.drawEllipse(QPointF(center.x() + spacing, eye_y), eye_w, eye_h)

        # Scanline Effect (Tech look)
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        for i in range(0, int(radius * 2), 4):
            y = center.y() - radius + i
            if (y > center.y() - radius) and (y < center.y() + radius):
                painter.drawLine(int(center.x() - radius), int(y), int(center.x() + radius), int(y))


class NeonSlider(QSlider):
    """Styled Slider"""
    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setObjectName("NeonSlider")
