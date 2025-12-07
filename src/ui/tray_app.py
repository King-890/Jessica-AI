from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from src.ui.chat_window import ChatWindow
from src.ui.pipeline_dashboard import PipelineDashboard
import os

class SystemTrayApp(QSystemTrayIcon):
    def __init__(self, app, dashboard):
        super().__init__()
        self.app = app
        self.dashboard = dashboard
        
        # Set up icon
        self.setIcon(QIcon.fromTheme("system-help")) 
        self.setToolTip("Jessica AI Command Center")
        
        # Create menu
        self.menu = QMenu()
        
        self.show_action = QAction("🖥️ Open Dashboard", self)
        self.show_action.triggered.connect(self.show_dashboard)
        self.menu.addAction(self.show_action)
        
        self.menu.addSeparator()
        
        self.quit_action = QAction("❌ Quit", self)
        self.quit_action.triggered.connect(self.quit_app)
        self.menu.addAction(self.quit_action)
        
        self.setContextMenu(self.menu)
        
        # Handle click on tray icon
        self.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_dashboard()

    def show_dashboard(self):
        self.dashboard.show()
        self.dashboard.activateWindow()
        
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
