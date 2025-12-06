from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ProbeConfigModel(BaseModel):
    type: str = Field(..., description="Type of probe (e.g., 'file_exists', 'process_running')")
    name: str = Field(..., description="Human-readable name for the probe")
    interval: int = Field(60, description="Check interval in seconds")
    params: Dict[str, Any] = Field(default_factory=dict, description="Specific parameters for the probe")

class PipelineStepModel(BaseModel):
    name: str
    command: str
    working_dir: str = "."
    timeout: int = 300

class PipelineConfigModel(BaseModel):
    name: str
    description: str = ""
    steps: List[PipelineStepModel] = []
    probes: List[ProbeConfigModel] = []
    enabled: bool = True
