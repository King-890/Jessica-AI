from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class ConfirmationDialog(QDialog):
    def __init__(self, operation_type, details, parent=None):
        """
        Enhanced confirmation dialog for dangerous operations.
        
        Args:
            operation_type: Type of operation (write_file, delete_file, execute_command, etc.)
            details: Dict with operation details (path, content, command, etc.)
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("⚠️ Confirmation Required")
        self.setModal(True)
        self.resize(500, 400)
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: #d4d4d4;
            }
            QLabel {
                color: #d4d4d4;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QCheckBox {
                color: #d4d4d4;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Title with icon
        title_label = QLabel(self._get_title(operation_type))
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #f48771;")
        layout.addWidget(title_label)
        
        # Risk indicator
        risk_level = self._assess_risk(operation_type)
        risk_label = QLabel(f"Risk Level: {risk_level}")
        risk_label.setStyleSheet(self._get_risk_color(risk_level))
        layout.addWidget(risk_label)
        
        # Operation details
        details_text = self._format_details(operation_type, details)
        details_label = QLabel(details_text)
        details_label.setWordWrap(True)
        layout.addWidget(details_label)
        
        # Preview section (if applicable)
        if self._should_show_preview(operation_type, details):
            preview_label = QLabel("Preview:")
            preview_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
            layout.addWidget(preview_label)
            
            preview_text = QTextEdit()
            preview_text.setReadOnly(True)
            preview_text.setMaximumHeight(150)
            preview_text.setPlainText(self._get_preview(operation_type, details))
            layout.addWidget(preview_text)
        
        # Don't ask again checkbox
        self.dont_ask_checkbox = QCheckBox("Don't ask again for this session")
        self.dont_ask_checkbox.setStyleSheet("margin-top: 8px;")
        layout.addWidget(self.dont_ask_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.deny_button = QPushButton("Deny")
        self.deny_button.setStyleSheet("""
            QPushButton {
                background-color: #3e3e3e;
                color: #d4d4d4;
            }
            QPushButton:hover {
                background-color: #4e4e4e;
            }
        """)
        self.deny_button.clicked.connect(self.reject)
        button_layout.addWidget(self.deny_button)
        
        self.allow_button = QPushButton("Allow")
        self.allow_button.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        self.allow_button.clicked.connect(self.accept)
        self.allow_button.setDefault(True)
        button_layout.addWidget(self.allow_button)
        
        layout.addLayout(button_layout)
    
    def _get_title(self, operation_type):
        titles = {
            "write_file": "📝 Write File",
            "delete_file": "🗑️ Delete File",
            "create_directory": "📁 Create Directory",
            "delete_directory": "🗑️ Delete Directory",
            "execute_command": "💻 Execute Shell Command",
            "modify_file": "✏️ Modify File",
            "repair_suggestion": "🔧 Repair Suggestion"
        }
        return titles.get(operation_type, "⚠️ Dangerous Operation")
    
    def _assess_risk(self, operation_type):
        high_risk = ["delete_file", "delete_directory", "execute_command"]
        if operation_type in high_risk:
            return "HIGH"
        if operation_type == "repair_suggestion":
            return "LOW"
        return "MEDIUM"
    
    def _get_risk_color(self, risk_level):
        colors = {
            "HIGH": "color: #f48771; font-weight: bold;",
            "MEDIUM": "color: #ce9178; font-weight: bold;",
            "LOW": "color: #4ec9b0; font-weight: bold;"
        }
        return colors.get(risk_level, "color: #d4d4d4;")
    
    def _format_details(self, operation_type, details):
        if operation_type == "write_file":
            path = details.get("path", "unknown")
            size = len(details.get("content", ""))
            return f"Jessica wants to write to:\n\n{path}\n\nSize: {size} bytes"
        
        elif operation_type == "delete_file":
            path = details.get("path", "unknown")
            return f"Jessica wants to delete:\n\n{path}\n\n⚠️ This action cannot be undone!"
        
        elif operation_type == "delete_directory":
            path = details.get("path", "unknown")
            return f"Jessica wants to delete directory:\n\n{path}\n\n⚠️ All contents will be permanently deleted!"
        
        elif operation_type == "execute_command":
            command = details.get("command", "unknown")
            cwd = details.get("cwd", ".")
            return f"Jessica wants to execute:\n\n{command}\n\nWorking directory: {cwd}"
        
        elif operation_type == "create_directory":
            path = details.get("path", "unknown")
            return f"Jessica wants to create directory:\n\n{path}"
            
        elif operation_type == "repair_suggestion":
            return "Jessica suggests the following repair:"
        
        return "Jessica wants to perform a dangerous operation."
    
    def _should_show_preview(self, operation_type, details):
        return operation_type in ["write_file", "execute_command", "modify_file", "repair_suggestion"]
    
    def _get_preview(self, operation_type, details):
        if operation_type == "write_file":
            content = details.get("content", "")
            # Limit preview to first 500 characters
            if len(content) > 500:
                return content[:500] + "\n\n... (truncated)"
            return content
        
        elif operation_type == "execute_command":
            return details.get("command", "")
        
        elif operation_type == "modify_file":
            return details.get("diff", "No preview available")
            
        elif operation_type == "repair_suggestion":
            return details.get("command", "No suggestion details available")
        
        return ""
    
    def should_skip_future(self):
        """Returns True if user checked 'don't ask again'"""
        return self.dont_ask_checkbox.isChecked()
