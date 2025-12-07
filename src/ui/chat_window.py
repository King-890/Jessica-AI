from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTextEdit, QLineEdit, QPushButton, QLabel, QStackedWidget)
from PyQt6.QtCore import Qt
from qasync import asyncSlot
import asyncio
from src.ui.confirmation_dialog import ConfirmationDialog
from src.ui.sidebar import Sidebar
from src.ui.context_panel import ContextPanel
from src.ui.training_view import TrainingView
from src.ui.views import BrainView, FilesView, PipelinesView, SettingsView

class ChatWindow(QWidget):
    def __init__(self, config, brain):
        super().__init__()
        self.config = config
        self.brain = brain
        # self.setWindowTitle("Jessica AI - Engineering Deskboard") # Removed window title logic
        # self.resize(1200, 800) # Removed resize logic
        
        # Central widget & Main Layout
        # central_widget = QWidget() # No longer needed
        # self.setCentralWidget(central_widget) # No longer needed
        main_layout = QHBoxLayout(self) # Layout directly on self
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Sidebar (Left)
        self.sidebar = Sidebar()
        self.sidebar.mode_changed.connect(self.switch_view)
        main_layout.addWidget(self.sidebar)
        
        # 2. Central Content (Stack)
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, stretch=1)
        
        # -- View 0: Chat --
        self.chat_container = QWidget()
        chat_layout = QVBoxLayout(self.chat_container)
        chat_layout.setContentsMargins(20, 20, 20, 20)
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11pt;
                border: none;
                padding: 10px;
            }
        """)
        chat_layout.addWidget(self.chat_history)
        
        input_layout = QHBoxLayout()
        
        # Status Label for Model
        self.model_status = QLabel("⚠️ Untrained Mode")
        self.model_status.setStyleSheet("color: #ffcc00; font-weight: bold; margin-right: 10px;")
        input_layout.addWidget(self.model_status)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a message...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 8px;
                font-size: 10pt;
            }
            QLineEdit:focus { border: 1px solid #007acc; }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #007acc; color: white; border: none; border-radius: 4px;
                padding: 8px 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #005a9e; }
        """)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        chat_layout.addLayout(input_layout)
        
        self.stack.addWidget(self.chat_container) # Index 0
        
        # -- View 1: Brain --
        self.brain_view = BrainView()
        self.stack.addWidget(self.brain_view)
        
        # -- View 2: Files --
        self.files_view = FilesView()
        self.stack.addWidget(self.files_view)
        
        # -- View 3: Pipelines --
        self.pipelines_view = PipelinesView()
        self.stack.addWidget(self.pipelines_view)
        
        # -- View 4: Settings --
        self.settings_view = SettingsView()
        self.stack.addWidget(self.settings_view)
        
        # -- View 5: Training --
        self.training_view = TrainingView(self.brain)
        self.stack.addWidget(self.training_view)
        
        # 3. Context Panel (Right)
        self.context_panel = ContextPanel()
        main_layout.addWidget(self.context_panel)
        
        # Status Bar (Replaced with internal label or removed for embedding)
        # self.status_label = QLabel("Ready") # Can't add to statusBar
        # self.statusBar().addWidget(self.status_label)
        
        self.current_assistant_message = None

    def switch_view(self, mode):
        """Switch the central stack based on sidebar selection"""
        if mode == "Chat":
            self.stack.setCurrentIndex(0)
            self.context_panel.update_mode("Chat")
        elif mode == "Brain":
            self.stack.setCurrentIndex(1)
            self.context_panel.update_mode("Brain")
        elif mode == "Files":
            self.stack.setCurrentIndex(2)
        elif mode == "Pipelines":
            self.stack.setCurrentIndex(3)
        elif mode == "Settings":
            self.stack.setCurrentIndex(4)
        elif mode == "Training":
            self.stack.setCurrentIndex(5)
            self.context_panel.update_mode("Training") # Assuming ContextPanel handles generic string

    @asyncSlot()
    async def send_message(self):
        message = self.input_field.text().strip()
        if not message:
            return
            
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)
        self.append_message("You", message, "#4ec9b0")
        self.input_field.clear()
        
        # self.status_label.setText("Jessica (Local) is thinking...")
        
        self.current_assistant_message = ""
        self.append_message("Jessica", "", "#569cd6", is_streaming=True)
        
        try:
            def update_callback(text: str):
                self.current_assistant_message += text
                self.update_streaming_message(self.current_assistant_message)
            
            def confirmation_callback(operation_type: str, details: dict) -> bool:
                dialog = ConfirmationDialog(operation_type, details, self)
                return dialog.exec() == dialog.DialogCode.Accepted
            
            print(f"\n[Chat] Processing: {message}")
            response = await self.brain.process_input(message, update_callback, confirmation_callback)
            
            if response and response != self.current_assistant_message:
                self.current_assistant_message = response
                self.update_streaming_message(response)
                
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.append_message("System", error_msg, "#f48771")
            
        # self.status_label.setText("Ready")
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.input_field.setFocus()
        self.current_assistant_message = None

    def append_message(self, sender, text, color="#d4d4d4", is_streaming=False):
        cursor = self.chat_history.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.chat_history.setTextCursor(cursor) # Set it first
        cursor.insertHtml(f'<p style="margin-top: 12px; margin-bottom: 4px;"><b style="color: {color};">{sender}:</b></p>')
        formatted_text = self.format_message(text)
        cursor.insertHtml(f'<div style="color: #d4d4d4; margin-left: 10px; margin-bottom: 8px;" id="streaming">{formatted_text}</div>')
        
        # transform cursor to end again to ensure view follows
        cursor.movePosition(cursor.MoveOperation.End)
        self.chat_history.setTextCursor(cursor)
        self.chat_history.ensureCursorVisible()

    def update_streaming_message(self, text):
        html = self.chat_history.toHtml()
        formatted_text = self.format_message(text)
        if 'id="streaming">' in html:
            parts = html.rsplit('id="streaming">', 1)
            if len(parts) == 2:
                before = parts[0] + 'id="streaming">'
                after = parts[1].split('</div>', 1)
                if len(after) == 2:
                    new_html = before + formatted_text + '</div>' + after[1]
                    self.chat_history.setHtml(new_html)
                    cursor = self.chat_history.textCursor()
                    cursor.movePosition(cursor.MoveOperation.End)
                    self.chat_history.setTextCursor(cursor)
                    self.chat_history.ensureCursorVisible()

    def format_message(self, text):
        if not text:
            return '<span style="color: #808080; font-style: italic;">...</span>'
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        text = text.replace('\n', '<br>')
        if text.startswith('[Calling tool'):
            return f'<span style="color: #ce9178; font-style: italic;">🔧 {text}</span>'
        return text
