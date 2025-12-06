from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from src.ui.chat_window import ChatWindow
from src.ui.pipeline_dashboard import PipelineDashboard
import os

class SystemTrayApp(QSystemTrayIcon):
    def __init__(self, app, config, brain, pipeline_manager, probe_scheduler, repair_engine):
        super().__init__()
        self.app = app
        self.config = config
        self.brain = brain
        self.pipeline_manager = pipeline_manager
        self.probe_scheduler = probe_scheduler
        self.repair_engine = repair_engine
        
        # Set up repair callback
        self.repair_engine.set_repair_callback(self.on_repair_suggestion)
        
        # Set up icon
        # TODO: Replace with actual icon file
        self.setIcon(QIcon.fromTheme("system-help")) 
        self.setToolTip("Jessica AI")
        
        # Create menu
        self.menu = QMenu()
        
        self.chat_action = QAction("💬 Open Chat", self)
        self.chat_action.triggered.connect(self.show_chat)
        self.menu.addAction(self.chat_action)
        
        self.dashboard_action = QAction("🕵️ Pipeline Dashboard", self)
        self.dashboard_action.triggered.connect(self.show_dashboard)
        self.menu.addAction(self.dashboard_action)

        self.menu.addSeparator()
        
        self.quit_action = QAction("❌ Quit", self)
        self.quit_action.triggered.connect(self.quit_app)
        self.menu.addAction(self.quit_action)
        
        self.setContextMenu(self.menu)
        
        # Initialize windows
        self.chat_window = ChatWindow(config, brain)
        self.dashboard_window = None
        
        # Handle click on tray icon
        self.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_chat()

    def show_chat(self):
        self.chat_window.show()
        self.chat_window.activateWindow()
        
    def show_dashboard(self):
        if not self.dashboard_window:
            self.dashboard_window = PipelineDashboard(
                self.pipeline_manager, 
                self.probe_scheduler, 
                self.repair_engine
            )
        self.dashboard_window.show()
        self.dashboard_window.activateWindow()
        
    def on_repair_suggestion(self, probe_name, message, suggestion):
        """Handle repair suggestion from engine"""
        self.showMessage(
            f"Repair Suggested: {probe_name}",
            f"{message}\nClick to view details.",
            QSystemTrayIcon.MessageIcon.Information,
            5000
        )
        # We could also automatically open the dashboard, but a notification is less intrusive

    def quit_app(self):
        self.app.quit()
