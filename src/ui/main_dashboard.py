from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QLabel, QApplication
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction
from src.ui.widgets.custom_widgets import SidebarButton
from src.ui.chat_window import ChatWindow
from src.ui.pipeline_dashboard import PipelineDashboard
from src.ui.training_view import TrainingView

class MainDashboard(QMainWindow):
    def __init__(self, config, brain, pipeline_manager, probe_scheduler, repair_engine):
        super().__init__()
        self.config = config
        self.brain = brain
        self.pipeline_manager = pipeline_manager
        
        self.setWindowTitle("Jessica AI - Command Center")
        self.resize(1200, 800)
        
        # Load Theme
        with open("src/ui/styles/theme.qss", "r") as f:
            self.setStyleSheet(f.read())
            
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Sidebar ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Logo
        logo = QLabel("JESSICA AI")
        logo.setObjectName("LogoLabel")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedHeight(80)
        sidebar_layout.addWidget(logo)
        
        # Navigation
        self.nav_buttons = []
        self.btn_chat = self._add_nav_btn("Chat Interface", sidebar_layout, 0)
        self.btn_pipelines = self._add_nav_btn("Pipelines", sidebar_layout, 1)
        self.btn_brain = self._add_nav_btn("Brain Status", sidebar_layout, 2)
        
        sidebar_layout.addStretch()
        
        # --- Content Area ---
        self.stack = QStackedWidget()
        
        # View 1: Chat
        self.chat_view = ChatWindow(config, brain)
        # Embed chat window logic (hack: ChatWindow is a QWidget/QMainWindow)
        # We might need to adjust ChatWindow to be embeddable if it's a Window
        self.stack.addWidget(self.chat_view) 
        
        # View 2: Pipelines
        self.pipeline_view = PipelineDashboard(pipeline_manager, probe_scheduler, repair_engine)
        self.stack.addWidget(self.pipeline_view)
        
        # View 3: Brain Status (Training Dashboard)
        self.brain_view = TrainingView(brain)
        self.stack.addWidget(self.brain_view)
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)
        
        # Default View
        self.btn_chat.setChecked(True)
        self.stack.setCurrentIndex(0)
        
    def _add_nav_btn(self, text, layout, index):
        btn = SidebarButton(text)
        btn.clicked.connect(lambda: self.switch_view(index, btn))
        layout.addWidget(btn)
        self.nav_buttons.append(btn)
        return btn
        
    def switch_view(self, index, active_btn):
        self.stack.setCurrentIndex(index)
        for btn in self.nav_buttons:
            btn.setChecked(False)
        active_btn.setChecked(True)
