import sys
import os

# Force UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.brain import Brain

def test_brain_init():
    print("Testing Brain Initialization (Cloud Arch)...")
    
    config = {"cloud_mode": True} 
    # MCP Host is typed, pass None for test
    try:
        brain = Brain(config, None, None)
        print(f"✅ Brain Initialized. Cloud Mode: {brain.use_cloud_llm}")
        
        # Test Heuristic Response
        resp = brain._heuristic_tool_check("hello", None, None)
        # We need async run for process_input, let's just check init state for now
        
        if brain.use_cloud_llm:
            print("🚀 RUNNING ON GEMINI (Smart Mode)")
        else:
            print("🔋 RUNNING ON HEURISTIC (Low Power Mode) - Expected if no Key")
            
    except Exception as e:
        print(f"❌ Brain Init Failed: {e}")

if __name__ == "__main__":
    test_brain_init()
