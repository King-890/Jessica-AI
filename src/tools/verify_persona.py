import sys
import os
import asyncio

# Force UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.brain import Brain

async def test_persona_switch():
    print("Testing Persona System...")
    
    config = {"cloud_mode": False} # Use heuristic mode for fast check
    brain = Brain(config, None, None)
    
    # 1. Check Default
    print(f"Initial Persona: {brain.current_persona}")
    assert brain.current_persona == "default"
    
    # 2. Test Command "transform into ide"
    print("\nSending command: 'transform into ide'...")
    resp = await brain.process_input("transform into ide")
    print(f"Response: {resp}")
    
    if brain.current_persona == "ide":
        print("✅ SUCCESS: Transformed to IDE Mode.")
    else:
        print(f"❌ FAILED: Still in {brain.current_persona} mode.")

    # 3. Test Command "switch to friend"
    print("\nSending command: 'switch to friend'...")
    resp = await brain.process_input("switch to friend")
    print(f"Response: {resp}")

    if brain.current_persona == "friend":
        print("✅ SUCCESS: Transformed to Friend Mode.")
    else:
        print(f"❌ FAILED: Still in {brain.current_persona} mode.")

if __name__ == "__main__":
    asyncio.run(test_persona_switch())
