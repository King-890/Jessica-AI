from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QStackedWidget
from PyQt6.QtCore import Qt, QTimer
import psutil

class ContextPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ContextPanel")
        self.setFixedWidth(300)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        self.header = QLabel("SYSTEM STATUS")
        self.header.setObjectName("HeaderLabel")
        layout.addWidget(self.header)
        
        # Stacked Widget for dynamic content
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # 1. System Status (Default/Chat)
        self.system_page = QWidget()
        sys_layout = QVBoxLayout(self.system_page)
        sys_layout.setContentsMargins(0, 0, 0, 0)
        
        self.cpu_label = QLabel("CPU")
        self.cpu_label.setObjectName("SectionLabel")
        sys_layout.addWidget(self.cpu_label)
        
        self.cpu_value = QLabel("0%")
        self.cpu_value.setStyleSheet("font-size: 24px; color: #00f3ff;")
        sys_layout.addWidget(self.cpu_value)
        
        self.mem_label = QLabel("MEMORY")
        self.mem_label.setObjectName("SectionLabel")
        sys_layout.addWidget(self.mem_label)
        
        self.mem_value = QLabel("0 GB / 0 GB")
        self.mem_value.setStyleSheet("font-size: 16px; color: #e0e0e0;")
        sys_layout.addWidget(self.mem_value)
        
        sys_layout.addStretch()
        self.stack.addWidget(self.system_page)
        
        # 2. Brain Context
        self.brain_page = QWidget()
        brain_layout = QVBoxLayout(self.brain_page)
        brain_layout.addWidget(QLabel("Active Contexts", objectName="SectionLabel"))
        brain_layout.addWidget(QLabel("• Project: Jessica AI\n• Language: Python\n• Framework: PyQt6", styleSheet="color: #a0a0a0;"))
        brain_layout.addStretch()
        self.stack.addWidget(self.brain_page)
        
        # 3. Files Context
        self.files_page = QWidget()
        files_layout = QVBoxLayout(self.files_page)
        files_layout.addWidget(QLabel("Recent Files", objectName="SectionLabel"))
        files_layout.addWidget(QLabel("• main.py\n• chat_window.py\n• context_panel.py", styleSheet="color: #a0a0a0;"))
        files_layout.addStretch()
        self.stack.addWidget(self.files_page)
        
        # 4. Pipelines Context
        self.pipelines_page = QWidget()
        pipelines_layout = QVBoxLayout(self.pipelines_page)
        pipelines_layout.addWidget(QLabel("Active Pipelines", objectName="SectionLabel"))
        pipelines_layout.addWidget(QLabel("• Health Check: ✅\n• Auto-Repair: ⏳", styleSheet="color: #a0a0a0;"))
        pipelines_layout.addStretch()
        self.stack.addWidget(self.pipelines_page)
        
        # 5. Settings Context
        self.settings_page = QWidget()
        settings_layout = QVBoxLayout(self.settings_page)
        settings_layout.addWidget(QLabel("Quick Settings", objectName="SectionLabel"))
        settings_layout.addWidget(QLabel("• Theme: Neon Horizon\n• Notifications: On", styleSheet="color: #a0a0a0;"))
        settings_layout.addStretch()
        self.stack.addWidget(self.settings_page)
        
        layout.addStretch()
        
        # Timer for updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(2000)
        
        self.update_stats()

    def update_stats(self):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        
        self.cpu_value.setText(f"{cpu}%")
        self.mem_value.setText(f"{mem.used / (1024**3):.1f} GB / {mem.total / (1024**3):.1f} GB")

    def update_mode(self, mode):
        # Update header
        self.header.setText(f"{mode.upper()} STATUS")
        
        # Switch stack page
        if mode == "Chat":
            self.stack.setCurrentIndex(0)
        elif mode == "Brain":
            self.stack.setCurrentIndex(1)
        elif mode == "Files":
            self.stack.setCurrentIndex(2)
        elif mode == "Pipelines":
            self.stack.setCurrentIndex(3)
        elif mode == "Settings":
            self.stack.setCurrentIndex(4)

