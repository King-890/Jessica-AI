import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class DataCollector:
    """
    Collects conversation data for fine-tuning / training.
    Saves interactions in JSONL format suitable for training pipelines.
    """
    def __init__(self, data_dir: str = "training_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.current_session_file = self.data_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        
    def save_interaction(self, user_input: str, assistant_response: str, context: Dict[str, Any] = None):
        """Save a single interaction pair"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "assistant": assistant_response,
            "context": context or {}
        }
        
        with open(self.current_session_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + "\n")
            
    def get_stats(self) -> Dict[str, int]:
        """Return stats about collected data"""
        count = 0
        if self.current_session_file.exists():
            with open(self.current_session_file, 'r', encoding='utf-8') as f:
                count = sum(1 for _ in f)
        return {"current_session_samples": count}
