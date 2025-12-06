"""
Base Probe Class and Probe Types
"""

import os
import time
import psutil
import socket
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ProbeResult:
    success: bool
    message: str
    timestamp: float
    details: Dict[str, Any]

class Probe(ABC):
    """Base class for all probes"""
    
    def __init__(self, name: str, interval: int):
        self.name = name
        self.interval = interval
        self.last_run = 0
        self.last_result: Optional[ProbeResult] = None
        
    @abstractmethod
    async def check(self) -> ProbeResult:
        """Run the probe check"""
        pass
        
    def should_run(self) -> bool:
        """Check if it's time to run the probe"""
        return time.time() - self.last_run >= self.interval

class FileExistsProbe(Probe):
    """Checks if a file exists"""
    
    def __init__(self, name: str, interval: int, path: str):
        super().__init__(name, interval)
        self.path = path
        
    async def check(self) -> ProbeResult:
        exists = os.path.exists(self.path)
        self.last_run = time.time()
        
        if exists:
            return ProbeResult(
                success=True,
                message=f"File exists: {self.path}",
                timestamp=self.last_run,
                details={"path": self.path, "size": os.path.getsize(self.path)}
            )
        else:
            return ProbeResult(
                success=False,
                message=f"File missing: {self.path}",
                timestamp=self.last_run,
                details={"path": self.path}
            )

class ProcessRunningProbe(Probe):
    """Checks if a process is running"""
    
    def __init__(self, name: str, interval: int, process_name: str):
        super().__init__(name, interval)
        self.process_name = process_name.lower()
        
    async def check(self) -> ProbeResult:
        found = False
        pid = None
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if self.process_name in proc.info['name'].lower():
                    found = True
                    pid = proc.info['pid']
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        self.last_run = time.time()
        
        if found:
            return ProbeResult(
                success=True,
                message=f"Process running: {self.process_name} (PID: {pid})",
                timestamp=self.last_run,
                details={"process": self.process_name, "pid": pid}
            )
        else:
            return ProbeResult(
                success=False,
                message=f"Process not found: {self.process_name}",
                timestamp=self.last_run,
                details={"process": self.process_name}
            )

class PortOpenProbe(Probe):
    """Checks if a TCP port is open"""
    
    def __init__(self, name: str, interval: int, port: int, host: str = "localhost"):
        super().__init__(name, interval)
        self.port = int(port)
        self.host = host
        
    async def check(self) -> ProbeResult:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        
        try:
            result = sock.connect_ex((self.host, self.port))
            is_open = (result == 0)
            msg = f"Port {self.host}:{self.port} is open" if is_open else f"Port {self.host}:{self.port} is closed"
        except Exception as e:
            is_open = False
            msg = f"Error checking port: {e}"
        finally:
            sock.close()
            
        self.last_run = time.time()
        
        return ProbeResult(
            success=is_open,
            message=msg,
            timestamp=self.last_run,
            details={"host": self.host, "port": self.port}
        )

class ProbeFactory:
    """Factory to create probes from config"""
    
    @staticmethod
    def create_probe(config) -> Optional[Probe]:
        probe_type = config.type
        name = config.name
        interval = config.interval
        params = config.params
        
        if probe_type == "file_exists":
            return FileExistsProbe(name, interval, params.get("path"))
        elif probe_type == "process_running":
            return ProcessRunningProbe(name, interval, params.get("process_name"))
        elif probe_type == "port_open":
            return PortOpenProbe(name, interval, params.get("port"), params.get("host", "localhost"))
        
        return None
