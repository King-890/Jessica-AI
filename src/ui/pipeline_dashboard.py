"""
Pipeline Dashboard UI - Visual interface for pipeline monitoring
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QScrollArea, QFrame, QPushButton, QProgressBar)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

class PipelineDashboard(QWidget):
    def __init__(self, pipeline_manager, probe_scheduler, repair_engine):
        super().__init__()
        self.pipeline_manager = pipeline_manager
        self.probe_scheduler = probe_scheduler
        self.repair_engine = repair_engine
        
        self.setWindowTitle("Pipeline Intelligence Dashboard")
        self.resize(800, 600)
        
        # Apply dark theme
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QFrame {
                background-color: #2d2d2d;
                border-radius: 8px;
                padding: 10px;
            }
            QLabel {
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QProgressBar {
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                text-align: center;
                background-color: #1e1e1e;
            }
            QProgressBar::chunk {
                background-color: #4ec9b0;
            }
        """)
        
        self.setup_ui()
        
        # Update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)  # Update every second
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Pipeline Status")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.update_status)
        header.addWidget(self.refresh_btn)
        
        layout.addLayout(header)
        
        # Scroll area for pipelines
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)
        
    def update_status(self):
        # Clear current items
        for i in reversed(range(self.content_layout.count())): 
            self.content_layout.itemAt(i).widget().setParent(None)
            
        pipelines = self.pipeline_manager.get_all_pipelines()
        probe_status = self.probe_scheduler.get_status()
        
        if not pipelines:
            no_pipelines = QLabel("No pipelines configured.")
            no_pipelines.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(no_pipelines)
            return
            
        for pipeline in pipelines:
            if not pipeline.enabled:
                continue
                
            # Pipeline Card
            card = QFrame()
            card_layout = QVBoxLayout(card)
            
            # Pipeline Header
            p_header = QHBoxLayout()
            p_name = QLabel(pipeline.name)
            p_name.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            p_header.addWidget(p_name)
            p_header.addStretch()
            
            # Overall health indicator
            is_healthy = True
            for probe in pipeline.probes:
                status = probe_status.get(probe.name, {})
                if status.get("status") == "failed":
                    is_healthy = False
                    break
            
            health_lbl = QLabel("HEALTHY" if is_healthy else "ISSUES DETECTED")
            health_lbl.setStyleSheet(f"color: {'#4ec9b0' if is_healthy else '#f48771'}; font-weight: bold;")
            p_header.addWidget(health_lbl)
            
            card_layout.addLayout(p_header)
            
            # Description
            if pipeline.description:
                desc = QLabel(pipeline.description)
                desc.setStyleSheet("color: #808080; margin-bottom: 10px;")
                card_layout.addWidget(desc)
            
            # Probes List
            for probe_config in pipeline.probes:
                status = probe_status.get(probe_config.name, {})
                
                probe_row = QHBoxLayout()
                
                # Status Icon
                icon = QLabel("✅" if status.get("status") == "healthy" else "❌")
                probe_row.addWidget(icon)
                
                # Probe Name
                name_lbl = QLabel(probe_config.name)
                name_lbl.setStyleSheet("font-weight: bold;")
                probe_row.addWidget(name_lbl)
                
                # Message
                msg = status.get("message", "Pending...")
                msg_lbl = QLabel(msg)
                msg_lbl.setWordWrap(True)
                if status.get("status") == "failed":
                    msg_lbl.setStyleSheet("color: #f48771;")
                probe_row.addWidget(msg_lbl, 1)
                
                # Repair Button (if failed)
                if status.get("status") == "failed":
                    repair_info = self.repair_engine.active_repairs.get(probe_config.name)
                    if repair_info and repair_info.get("suggestion"):
                        repair_btn = QPushButton("View Repair")
                        repair_btn.setStyleSheet("background-color: #ce9178;")
                        repair_btn.clicked.connect(lambda checked, p=probe_config.name: self.show_repair(p))
                        probe_row.addWidget(repair_btn)
                    elif repair_info and repair_info.get("status") == "analyzing":
                        analyzing_lbl = QLabel("Analyzing...")
                        analyzing_lbl.setStyleSheet("color: #ce9178; font-style: italic;")
                        probe_row.addWidget(analyzing_lbl)
                
                card_layout.addLayout(probe_row)
                
            self.content_layout.addWidget(card)
            
    def show_repair(self, probe_name):
        """Show repair suggestion dialog"""
        repair_info = self.repair_engine.active_repairs.get(probe_name)
        if not repair_info:
            return
            
        from .confirmation_dialog import ConfirmationDialog
        
        suggestion = repair_info.get("suggestion")
        
        # Create a custom dialog for repair
        # For now, we reuse ConfirmationDialog or create a simple message box
        # Let's use a simple message box for MVP or reuse ConfirmationDialog if adaptable
        
        # Since ConfirmationDialog is designed for operations, let's create a simple RepairDialog here or inline
        # For simplicity, I'll use the ConfirmationDialog with a custom type
        
        dialog = ConfirmationDialog(
            operation_type="repair_suggestion",
            details={
                "command": suggestion,
                "cwd": ".",
                "risk": "UNKNOWN" # Let user decide
            },
            parent=self
        )
        dialog.setWindowTitle("🔧 Repair Suggestion")
        
        if dialog.exec():
            # User accepted repair
            # In a real implementation, we would execute the suggestion
            # For now, we can just copy it to clipboard or try to execute if it's a command
            pass
