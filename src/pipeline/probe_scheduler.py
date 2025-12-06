"""
Probe Scheduler - Manages periodic execution of probes
"""

import asyncio
import time
from typing import List, Dict, Callable, Optional
from .probes.base import Probe, ProbeResult, ProbeFactory
from .manager import PipelineManager

class ProbeScheduler:
    """Schedules and runs probes"""
    
    def __init__(self, pipeline_manager: PipelineManager):
        self.pipeline_manager = pipeline_manager
        self.active_probes: List[Probe] = []
        self.running = False
        self.results: Dict[str, ProbeResult] = {}
        self.failure_callbacks: List[Callable[[Probe, ProbeResult], None]] = []
        
    def start(self, loop=None):
        """Start the scheduler"""
        self.running = True
        self._load_probes()
        
        # Schedule the run loop
        if loop:
            asyncio.ensure_future(self._run_loop(), loop=loop)
        else:
            # Try to get the running loop
            try:
                loop = asyncio.get_running_loop()
                asyncio.ensure_future(self._run_loop(), loop=loop)
            except RuntimeError:
                # No running loop, will be started later
                pass
        
        print("Probe scheduler started")
        
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        print("Probe scheduler stopped")
        
    def add_failure_callback(self, callback: Callable[[Probe, ProbeResult], None]):
        """Add a callback to be notified when a probe fails"""
        self.failure_callbacks.append(callback)
        
    def _load_probes(self):
        """Load probes from all enabled pipelines"""
        self.active_probes.clear()
        pipelines = self.pipeline_manager.get_all_pipelines()
        
        for pipeline in pipelines:
            if not pipeline.enabled:
                continue
                
            for probe_config in pipeline.probes:
                probe = ProbeFactory.create_probe(probe_config)
                if probe:
                    self.active_probes.append(probe)
                    print(f"Loaded probe: {probe.name} ({probe.interval}s)")
                    
    async def _run_loop(self):
        """Main execution loop"""
        while self.running:
            for probe in self.active_probes:
                if probe.should_run():
                    try:
                        result = await probe.check()
                        self.results[probe.name] = result
                        
                        if not result.success:
                            print(f"❌ Probe failed: {probe.name} - {result.message}")
                            self._notify_failure(probe, result)
                        else:
                            # Optional: Log success (verbose)
                            # print(f"✅ Probe passed: {probe.name}")
                            pass
                            
                    except Exception as e:
                        print(f"Error running probe {probe.name}: {e}")
            
            await asyncio.sleep(1)  # Check every second
            
    def _notify_failure(self, probe: Probe, result: ProbeResult):
        """Notify listeners of probe failure"""
        for callback in self.failure_callbacks:
            try:
                callback(probe, result)
            except Exception as e:
                print(f"Error in failure callback: {e}")
                
    def get_status(self) -> Dict[str, dict]:
        """Get status of all probes"""
        status = {}
        for probe in self.active_probes:
            result = self.results.get(probe.name)
            status[probe.name] = {
                "interval": probe.interval,
                "last_run": probe.last_run,
                "status": "healthy" if result and result.success else "failed",
                "message": result.message if result else "Not run yet"
            }
        return status
