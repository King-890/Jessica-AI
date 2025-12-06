"""
Pipeline Manager - Manages pipeline configurations and execution
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import asyncio

@dataclass
class PipelineStep:
    name: str
    command: str
    working_dir: str = "."
    timeout: int = 300

@dataclass
class ProbeConfig:
    type: str
    name: str
    interval: int = 60
    params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Pipeline:
    name: str
    description: str
    steps: List[PipelineStep] = field(default_factory=list)
    probes: List[ProbeConfig] = field(default_factory=list)
    enabled: bool = True

class PipelineManager:
    """Loads and manages pipelines"""
    
    def __init__(self, pipelines_dir: Path):
        self.pipelines_dir = Path(pipelines_dir)
        self.pipelines_dir.mkdir(parents=True, exist_ok=True)
        self.pipelines: Dict[str, Pipeline] = {}
        
    def load_pipelines(self):
        """Load all pipelines from the pipelines directory"""
        print(f"Loading pipelines from {self.pipelines_dir}")
        self.pipelines.clear()
        
        if not self.pipelines_dir.exists():
            return
            
        for file_path in self.pipelines_dir.glob("*.json"):
            try:
                self._load_pipeline_file(file_path)
            except Exception as e:
                print(f"Error loading pipeline {file_path}: {e}")
                
        print(f"Loaded {len(self.pipelines)} pipelines")
        
    def _load_pipeline_file(self, file_path: Path):
        """Load a single pipeline file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Parse steps
        steps = []
        for step_data in data.get('steps', []):
            steps.append(PipelineStep(
                name=step_data['name'],
                command=step_data['command'],
                working_dir=step_data.get('working_dir', '.'),
                timeout=step_data.get('timeout', 300)
            ))
            
        # Parse probes
        probes = []
        for probe_data in data.get('probes', []):
            # Extract params (everything except type, name, interval)
            params = {k: v for k, v in probe_data.items() 
                     if k not in ['type', 'name', 'interval']}
            
            probes.append(ProbeConfig(
                type=probe_data['type'],
                name=probe_data['name'],
                interval=probe_data.get('interval', 60),
                params=params
            ))
            
        pipeline = Pipeline(
            name=data['name'],
            description=data.get('description', ''),
            steps=steps,
            probes=probes,
            enabled=data.get('enabled', True)
        )
        
        self.pipelines[pipeline.name] = pipeline
        print(f"  - Loaded: {pipeline.name}")
        
    def get_pipeline(self, name: str) -> Optional[Pipeline]:
        """Get a pipeline by name"""
        return self.pipelines.get(name)
        
    def get_all_pipelines(self) -> List[Pipeline]:
        """Get all loaded pipelines"""
        return list(self.pipelines.values())
        
    def create_example_pipeline(self):
        """Create an example pipeline file if none exist"""
        if list(self.pipelines_dir.glob("*.json")):
            return
            
        example_path = self.pipelines_dir / "example.json"
        
        example_data = {
            "name": "Jessica AI Development",
            "description": "Monitor Jessica AI project health",
            "enabled": True,
            "steps": [
                {
                    "name": "check_syntax",
                    "command": "python -m py_compile src/main.py",
                    "working_dir": ".",
                    "timeout": 30
                }
            ],
            "probes": [
                {
                    "type": "file_exists",
                    "name": "Config File Check",
                    "path": "config.yaml",
                    "interval": 60
                },
                {
                    "type": "process_running",
                    "name": "App Running Check",
                    "process_name": "python.exe",
                    "interval": 30
                }
            ]
        }
        
        with open(example_path, 'w') as f:
            json.dump(example_data, f, indent=2)
            
        print(f"Created example pipeline at {example_path}")
