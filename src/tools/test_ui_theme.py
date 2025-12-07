import sys
import os
# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt6.QtWidgets import QApplication
from src.ui.main_dashboard import MainDashboard

# Mock Components for UI Testing
class Mock: 
    def __init__(self):
        self.tokenizer = type('obj', (object,), {'vocab_size': 5000})
        self.device = "cpu"
        self.local_model = type('obj', (object,), {})
        self.model = self.local_model
        
config = {}
brain = Mock()
pipeline_manager = Mock()
pipeline_manager.get_all_pipelines = lambda: {
    "Self-Test": {"status": "success", "last_run": "14:00"},
    "Data-Ingestion": {"status": "running", "last_run": "Now"}
}
probe_scheduler = Mock()
probe_scheduler.get_status = lambda: {"running": True, "active_probes": 5}
repair_engine = Mock()
repair_engine.get_status = lambda: {"active_repairs": 0} # Anticipating repair engine requirement

def test_ui():
    app = QApplication(sys.argv)
    
    # Create Dashboard with Mocks
    dashboard = MainDashboard(config, brain, pipeline_manager, probe_scheduler, repair_engine)
    
    # Setup styling manually just in case
    with open("src/ui/styles/hud_theme.qss", "r") as f:
        app.setStyleSheet(f.read())
        
    print("Launching Dashboard with 'Deep Space' Theme...")
    dashboard.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_ui()
