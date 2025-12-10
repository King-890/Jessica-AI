import sys
import os
# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop
from src.ui.tray_app import SystemTrayApp
from src.ui.main_dashboard import MainDashboard
from src.core.mcp_host import MCPHost
from src.core.brain import Brain
from src.rag.rag_manager import RAGManager
from src.pipeline.manager import PipelineManager
from src.pipeline.probe_scheduler import ProbeScheduler
from src.pipeline.repair_engine import RepairEngine
from src.pipeline.probe_scheduler import ProbeScheduler
from src.pipeline.repair_engine import RepairEngine
from src.audio.voice_manager import VoiceManager
import yaml
import threading
import uvicorn

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("Config file not found. Using defaults.")
        # Try example config if main config is missing
        example_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.example.yaml')
        try:
            with open(example_path, 'r') as f:
                print("Using config.example.yaml")
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}

def start_backend_server(config):
    """Start FastAPI backend server in background thread"""
    try:
        # Import backend app
        from src.backend.app import app as backend_app
        
        # Get API settings from config
        api_config = config.get('api', {})
        host = api_config.get('host', '127.0.0.1')
        port = api_config.get('port', 5050)
        
        print(f"\n🚀 Starting FastAPI backend on {host}:{port}")
        print(f"   API docs available at: http://{host}:{port}/docs\n")
        
        # Run uvicorn server
        uvicorn.run(
            backend_app,
            host=host,
            port=port,
            log_level="info",
            access_log=False  # Reduce console noise
        )
    except Exception as e:
        print(f"⚠️  Backend server failed to start: {e}")
        print("   Continuing with UI only...\n")

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Load config
    config = load_config()
    
    # Define project root
    project_root = Path(os.path.dirname(os.path.dirname(__file__)))
    
    # Start Backend API Server in background thread
    backend_thread = threading.Thread(
        target=start_backend_server,
        args=(config,),
        daemon=True  # Thread will exit when main program exits
    )
    backend_thread.start()
    
    # RAG Manager - Enabled for Training/RAG flow
    # RAG Manager - Enabled for Training/RAG flow
    print("\nInitializing RAG system (Cloud Mode)...")
    rag_manager = RAGManager(
        index_dir=project_root / ".jessica" / "rag_index",
        enable_training=False  # Disable local indexing for fast startup
    )
    
    # Check if indexing is needed (informational only now)
    try:
        stats = rag_manager.get_stats()
        # needs_indexing = 'Jessica AI' not in stats.get('indexed_projects', [])
    except:
        pass
        # needs_indexing = True
        
    # if needs_indexing:
    #    print("\nRAG indexing will run in background...")
    # else:
    print(f"RAG system ready (Cloud Connected)\n")
    print(f"RAG system ready (Cloud Connected)\n")
    needs_indexing = False
    
    # Initialize Core
    mcp_host = MCPHost(config)
    brain = Brain(config, mcp_host, rag_manager)
    
    # Initialize Pipeline System
    print("Initializing Pipeline System...")
    pipelines_dir = project_root / "pipelines"
    pipeline_manager = PipelineManager(pipelines_dir)
    pipeline_manager.create_example_pipeline()
    pipeline_manager.load_pipelines()
    
    probe_scheduler = ProbeScheduler(pipeline_manager)
    repair_engine = RepairEngine(brain)
    
    # Initialize Voice Manager
    print("Initializing Voice System...")
    voice_manager = VoiceManager()
    
    # --- Thread-Safe Voice Bridge ---
    from PyQt6.QtCore import QObject, pyqtSignal
    
    class VoiceSignals(QObject):
        command_received = pyqtSignal(str)
        
    voice_signals = VoiceSignals()
    
    def handle_command(text):
        print(f"🎤 Voice Command (Main Thread): {text}")
        async def process_async():
            response = await brain.process_input(text, update_callback=lambda x: None)
            if response:
                pass # voice_manager.speak(response) 
        loop.create_task(process_async())
        
    voice_signals.command_received.connect(handle_command)
    
    # Connect Voice -> Signal -> Main Thread
    def on_voice_command(text: str):
        # Emit signal from background thread (Safe)
        voice_signals.command_received.emit(text)
        
    voice_manager.start_listening(on_voice_command)
    
    # Connect components
    # repair_engine needs to know about probe failures? 
    # The scheduler notifies via callback.
    probe_scheduler.add_failure_callback(repair_engine.handle_failure)
    
    # Create Main Dashboard
    print("Initializing Dashboard...")
    dashboard = MainDashboard(config, brain, pipeline_manager, probe_scheduler, repair_engine)
    
    # Create system tray app
    tray = SystemTrayApp(app, dashboard)
    tray.show()
    
    # Auto-show dashboard on startup
    print("\nOpening Dashboard...")
    dashboard.show()
    
    # Background indexing disabled (RAG is off)
    
    # Start Probe Scheduler
    probe_scheduler.start(loop)
    
    # Start MCP host
    try:
        loop.run_until_complete(mcp_host.start())
        loop.run_forever()
    finally:
        probe_scheduler.stop()
        loop.run_until_complete(mcp_host.stop())

if __name__ == '__main__':
    main()

