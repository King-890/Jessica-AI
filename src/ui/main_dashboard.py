from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, 
    QLabel, QStackedWidget, QLineEdit, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from src.ui.widgets.hud_widgets import HUDFrame, HUDButton, AvatarWidget, NeonSlider
from src.ui.chat_window import ChatWindow
from src.ui.pipeline_dashboard import PipelineDashboard
from src.ui.training_view import TrainingView

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
        
        # --- Middle Left: Chat Window (Embedded HUD Style) ---
        chat_frame = HUDFrame()
        chat_layout = QVBoxLayout(chat_frame)
        chat_header = QLabel("COMMUNICATIONS")
        chat_layout.addWidget(chat_header)
        
        # Embed existing ChatWindow logic??
        # ChatWindow interacts with brain... let's just use it but maybe strip its frame?
        self.chat_view = ChatWindow(config, brain) 
        # Hack: styling will apply recursively
        chat_layout.addWidget(self.chat_view)
        
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
        
        # --- Bottom Center: Input Field ---
        input_frame = HUDFrame()
        input_layout = QHBoxLayout(input_frame)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("How can I help you?")
        self.input_field.returnPressed.connect(self.on_submit_text)
        
        mic_btn = HUDButton("🎤")
        mic_btn.setFixedWidth(50)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(mic_btn)
        
        grid.addWidget(input_frame, 2, 1, 1, 1) # Row 2, Col 1
        
        # --- Bottom Right: Pipelines (Minimized) ---
        pipeline_frame = HUDFrame()
        pipeline_layout = QVBoxLayout(pipeline_frame)
        pipeline_layout.addWidget(QLabel("ACTIVE PIPELINES"))
        self.pipelines_view = PipelineDashboard(pipeline_manager, probe_scheduler, repair_engine)
        self.pipelines_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # We might need to make PipelineDashboard compact...
        pipeline_layout.addWidget(self.pipelines_view)
        grid.addWidget(pipeline_frame, 2, 2, 1, 1) # Row 2, Col 2

        # Grid Stretching
        grid.setColumnStretch(0, 3) # Left
        grid.setColumnStretch(1, 4) # Center (Avatar)
        grid.setColumnStretch(2, 3) # Right

    def on_submit_text(self):
        text = self.input_field.text()
        if text:
            # We need to route this to the ChatWindow or Brain
            # Since ChatWindow is embedded, we can pass it there?
            # Or just use Brain directly.
            self.chat_view.handle_submit(text) # Assuming ChatWindow has this or similar logic
            self.input_field.clear()
