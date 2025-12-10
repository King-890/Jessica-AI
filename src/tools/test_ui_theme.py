import sys
import os
import pytest

# Ensure Qt runs offscreen in CI environments
if os.environ.get("CI"):
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    from src.ui.main_dashboard import MainDashboard
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


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


class MockPipeline:
    def __init__(self, name, enabled=True):
        self.name = name
        self.enabled = enabled
        self.description = "Mock Pipeline"
        self.probes = [type('obj', (object,), {'name': 'Probe1'})]  # Minimal mock probe


pipeline_manager.get_all_pipelines = lambda: [
    MockPipeline("Self-Test"),
    MockPipeline("Data-Ingestion")
]
probe_scheduler = Mock()
probe_scheduler.get_status = lambda: {"running": True, "active_probes": 5}
repair_engine = Mock()
repair_engine.get_status = lambda: {"active_repairs": 0}  # Anticipating repair engine requirement


@pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not installed")
def test_ui():
    if not PYQT_AVAILABLE:
        return

    # Use existing QApplication instance if available (pytest-qt interaction)
    app = QApplication.instance() or QApplication(sys.argv)

    # Create Dashboard with Mocks
    dashboard = MainDashboard(config, brain, pipeline_manager, probe_scheduler, repair_engine)

    # Setup styling manually just in case
    style_path = "src/ui/styles/hud_theme.qss"
    if os.path.exists(style_path):
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())

    print("Launching Dashboard with 'Deep Space' Theme...")
    # Don't actually show window in CI/Test environment to avoid hanging
    # dashboard.show()

    # Just verify instantiation was successful
    assert dashboard is not None
    dashboard.close()


if __name__ == "__main__":
    if not PYQT_AVAILABLE:
        print("PyQt6 not available. Skipping manual UI test.")
        sys.exit(0)
    
    app = QApplication(sys.argv)
    dashboard = MainDashboard(config, brain, pipeline_manager, probe_scheduler, repair_engine)
    style_path = "src/ui/styles/hud_theme.qss"
    if os.path.exists(style_path):
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())
    
    dashboard.show()
    QTimer.singleShot(2000, app.quit)
    sys.exit(app.exec())
