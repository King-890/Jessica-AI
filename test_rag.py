
import os
import sys
from dotenv import load_dotenv

load_dotenv(r"d:\Jessica AI\.env")

print("Testing AI Core with RAG...")
try:
    from src.backend.ai_core import jessica_core
    
    # 1. Test basic query (should trigger RAG)
    response = jessica_core("Who are you?")
    print(f"\nResponse: {response}")
    
    # 2. Test specific query (if you have relevant data)
    response = jessica_core("What is the project structure?")
    print(f"\nResponse: {response}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
