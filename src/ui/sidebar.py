from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFrame
from PyQt6.QtCore import pyqtSignal, Qt

class Sidebar(QWidget):
    mode_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(60)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 10, 5, 10)
        layout.setSpacing(10)
        
        # Navigation Buttons
        self.chat_btn = self.create_button("💬", "Chat")
        self.chat_btn.setChecked(True)
        self.brain_btn = self.create_button("🧠", "Brain")
        self.files_btn = self.create_button("📁", "Files")
        self.pipelines_btn = self.create_button("⚡", "Pipelines")
        self.settings_btn = self.create_button("⚙️", "Settings")
        
        layout.addWidget(self.chat_btn)
        layout.addWidget(self.brain_btn)
        layout.addWidget(self.files_btn)
        layout.addWidget(self.pipelines_btn)
        
        self.training_btn = self.create_button("🏋️", "Training")
        layout.addWidget(self.training_btn)
        
        layout.addStretch()
        
        layout.addWidget(self.settings_btn)

    def create_button(self, icon, name):
        btn = QPushButton(icon)
        btn.setObjectName("SidebarButton")
        btn.setCheckable(True)
        btn.setFixedSize(50, 50)
        btn.setToolTip(name)
        btn.clicked.connect(lambda: self.handle_click(btn, name))
        return btn

    def handle_click(self, clicked_btn, name):
        # Uncheck all others
        for btn in [self.chat_btn, self.brain_btn, self.files_btn, self.pipelines_btn, self.settings_btn, self.training_btn]:
            if btn != clicked_btn:
                btn.setChecked(False)
        
        clicked_btn.setChecked(True)
        self.mode_changed.emit(name)
