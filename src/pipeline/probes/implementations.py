import os
import psutil
from typing import Any
from .base import Probe, ProbeResult

class FileProbe(Probe):
    """Checks if a file exists and optionally checks content"""
    def check(self) -> ProbeResult:
        path = self.params.get('path')
        if not path:
            return self.fail("Missing 'path' parameter")
            
        if not os.path.exists(path):
            return self.fail(f"File not found: {path}")
            
        must_contain = self.params.get('must_contain')
        if must_contain:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if must_contain not in content:
                        return self.fail(f"File {path} logic error: Content missing '{must_contain}'")
            except Exception as e:
                return self.fail(f"Error reading file {path}: {e}")
                
        return self.success(f"File {path} exists and is valid.")

class ProcessProbe(Probe):
    """Checks if a process name is running"""
    def check(self) -> ProbeResult:
        proc_name = self.params.get('process_name')
        if not proc_name:
            return self.fail("Missing 'process_name' parameter")
            
        # Iterate over running processes
        found = False
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] == proc_name:
                    found = True
                    break
        except Exception as e:
            return self.fail(f"Error checking processes: {e}")
            
        if found:
            return self.success(f"Process '{proc_name}' is running.")
        else:
            return self.fail(f"Process '{proc_name}' is NOT running.")

class EndpointProbe(Probe):
    """Checks if a local HTTP endpoint returns 200"""
    def check(self) -> ProbeResult:
        url = self.params.get('url')
        if not url:
            return self.fail("Missing 'url' parameter")
            
        import urllib.request
        try:
            code = urllib.request.urlopen(url, timeout=5).getcode()
            if code == 200:
                return self.success(f"Endpoint {url} is UP (200 OK).")
            else:
                return self.fail(f"Endpoint {url} returned status {code}.")
        except Exception as e:
            return self.fail(f"Endpoint {url} check failed: {e}")
