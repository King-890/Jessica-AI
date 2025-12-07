from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, 
    QLabel, QStackedWidget, QLineEdit, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from src.ui.widgets.hud_widgets import HUDFrame, HUDButton, AvatarWidget, NeonSlider
from src.ui.widgets.chat_widget import ChatWidget
from src.ui.pipeline_dashboard import PipelineDashboard
from src.ui.training_view import TrainingView
from src.ui.confirmation_dialog import ConfirmationDialog
import asyncio

class MainDashboard(QMainWindow):
    def __init__(self, config, brain, pipeline_manager, probe_scheduler, repair_engine):
        super().__init__()
        self.config = config
        self.brain = brain
        
        self.setWindowTitle("Jessica AI - HUD System")
        self.resize(1300, 850)
        
        # Load HUD Theme
        with open("src/ui/styles/hud_theme.qss", "r") as f:
            self.setStyleSheet(f.read())
            
        # Main Container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Use Grid Layout for the "HUD" feel
        grid = QGridLayout(central_widget)
        grid.setContentsMargins(20, 20, 20, 20)
        grid.setSpacing(20)
        
        # --- Top Left: Header ---
        header_frame = HUDFrame()
        header_layout = QHBoxLayout(header_frame)
        logo = QLabel("JU  JESSICA AI")
        logo.setStyleSheet("font-size: 24px; font-weight: bold; letter-spacing: 2px;")
        header_layout.addWidget(logo)
        grid.addWidget(header_frame, 0, 0, 1, 1) # Row 0, Col 0
        
        # --- Center: Avatar ---
        self.avatar = AvatarWidget()
        avatar_container = QWidget() # Wrapper to center it
        avatar_layout = QVBoxLayout(avatar_container)
        avatar_layout.addWidget(self.avatar, 0, Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(avatar_container, 0, 1, 2, 1) # Row 0-1, Col 1 (Center)

        # --- Top Right: Images/Media ---
        media_frame = HUDFrame()
        media_layout = QVBoxLayout(media_frame)
        media_label = QLabel("IMAGES / MEDIA")
        media_label.setStyleSheet("font-weight: bold;")
        media_layout.addWidget(media_label)
        media_layout.addWidget(QLabel("[Visual Feed Inactive]"))
        grid.addWidget(media_frame, 0, 2, 1, 1) # Row 0, Col 2
        
        # --- Middle Left: Chat Widget (HUD Style) ---
        chat_frame = HUDFrame()
        chat_layout = QVBoxLayout(chat_frame)
        chat_header = QLabel("COMMUNICATIONS")
        chat_layout.addWidget(chat_header)
        
        self.chat_view = ChatWidget()
        chat_layout.addWidget(self.chat_view)
        
        # Move Input Field Here
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("How can I help you?")
        self.input_field.returnPressed.connect(self.on_submit_text)
        
        mic_btn = HUDButton("🎤")
        mic_btn.setFixedWidth(40)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(mic_btn)
        
        chat_layout.addWidget(input_container)
        
        grid.addWidget(chat_frame, 1, 0, 2, 1) # Row 1-2, Col 0
        
        # --- Middle Right: Settings ---
        settings_frame = HUDFrame()
        settings_layout = QVBoxLayout(settings_frame)
        settings_label = QLabel("SYSTEM SETTINGS")
        settings_layout.addWidget(settings_label)
        
        # Sliders
        settings_layout.addWidget(QLabel("Voice Volume"))
        settings_layout.addWidget(NeonSlider(Qt.Orientation.Horizontal))
        settings_layout.addWidget(QLabel("Processing Power"))
        settings_layout.addWidget(NeonSlider(Qt.Orientation.Horizontal))
        
        grid.addWidget(settings_frame, 1, 2, 1, 1) # Row 1, Col 2
        
        # --- Bottom Right: Pipelines (Minimized) ---
        pipeline_frame = HUDFrame()
        pipeline_layout = QVBoxLayout(pipeline_frame)
        pipeline_layout.addWidget(QLabel("ACTIVE PIPELINES"))
        self.pipelines_view = PipelineDashboard(pipeline_manager, probe_scheduler, repair_engine)
        self.pipelines_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        pipeline_layout.addWidget(self.pipelines_view)
        grid.addWidget(pipeline_frame, 2, 2, 1, 1) # Row 2, Col 2

        # Grid Stretching
        grid.setColumnStretch(0, 3) # Left
        grid.setColumnStretch(1, 4) # Center (Avatar)
        grid.setColumnStretch(2, 3) # Right
        
        self.current_assistant_message = ""

    def on_submit_text(self):
        text = self.input_field.text().strip()
        if not text:
            return
            
        # UI Updates
        self.chat_view.append_message("You", text, "#00f0ff")
        self.input_field.clear()
        
        # Async Processing (Fire and Forget task)
        # In PyQt + Asyncio (qasync), we need to schedule this on the loop
        asyncio.create_task(self.process_brain_response(text))

    async def process_brain_response(self, text):
        self.current_assistant_message = ""
        self.chat_view.append_message("Jessica", "", "#ffffff")
        
        def update_callback(token):
            self.current_assistant_message += token
            self.chat_view.update_streaming_message(self.current_assistant_message)
            
        def confirmation_callback(op_type, details):
            # Simple synchronous dialog execution
            dialog = ConfirmationDialog(op_type, details, self)
            return dialog.exec() == dialog.DialogCode.Accepted
            
        try:
            await self.brain.process_input(text, update_callback, confirmation_callback)
        except Exception as e:
            self.chat_view.append_message("System", f"Error: {e}", "#ff0055")
