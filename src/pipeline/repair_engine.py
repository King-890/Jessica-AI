import asyncio
from typing import Dict, Any, Optional, Callable
from .probes.base import Probe, ProbeResult
from src.core.brain import Brain

class RepairEngine:
    """Analyzes failures and suggests repairs using the Custom Brain"""
    
    def __init__(self, brain: Brain):
        self.brain = brain
        self.active_repairs: Dict[str, Any] = {}
        self.repair_callback: Optional[Callable[[str, str, str], None]] = None
        
    def set_repair_callback(self, callback: Callable[[str, str, str], None]):
        """Set callback to notify UI of repair suggestions"""
        self.repair_callback = callback
        
    async def handle_failure(self, probe: Probe, result: ProbeResult):
        """Handle a probe failure"""
        if probe.name in self.active_repairs:
            return
            
        print(f"🔧 Repair Engine analyzing failure: {probe.name}")
        self.active_repairs[probe.name] = {"status": "analyzing", "timestamp": result.timestamp}
        
        # Ask Brain for repair suggestion
        suggestion = await self._generate_suggestion(probe, result)
        
        # Auto-Approval Logic (Low Risk)
        is_safe = self._is_safe_repair(suggestion)
        
        if suggestion:
            print(f"🔧 Suggestion ({'Safe' if is_safe else 'Risk'}): {suggestion}")
            self.active_repairs[probe.name]["suggestion"] = suggestion
            self.active_repairs[probe.name]["status"] = "suggested"
            self.active_repairs[probe.name]["is_safe"] = is_safe
            
            # Notify UI
            if self.repair_callback:
                self.repair_callback(probe.name, result.message, suggestion)
        else:
            self.active_repairs[probe.name]["status"] = "no_suggestion"
            
    async def _generate_suggestion(self, probe: Probe, result: ProbeResult) -> str:
        """Generate repair suggestion using the Brain"""
        prompt = f"""SYSTEM REPAIR REQUEST
The system probe '{probe.name}' has FAILED.
Error: {result.message}
Details: {result.details}
Task: Suggest a specific shell command to fix this.
Constraint: Return ONLY the command if possible, or a 1-sentence description.
"""
        try:
            # Use Brain's process_input (simulating a system user)
            # We don't want to trigger confirmation dialogs for the *generation* part
            response = await self.brain.process_input(prompt)
            return response.strip()
        except Exception as e:
            print(f"Error generating repair suggestion: {e}")
            return "Check logs manually."

    def _is_safe_repair(self, suggestion: str) -> bool:
        """Determine if a repair is safe to auto-approve"""
        safe_keywords = ["restart", "echo", "mkdir", "touch", "ping"]
        suggestion_lower = suggestion.lower()
        
        # Check for dangerous things first
        if "rm " in suggestion_lower or "del " in suggestion_lower or "format" in suggestion_lower:
            return False
            
        # Check for safe keywords
        for keyword in safe_keywords:
            if keyword in suggestion_lower:
                return True
                
        return False
        
    def clear_repair(self, probe_name: str):
        if probe_name in self.active_repairs:
            del self.active_repairs[probe_name]
