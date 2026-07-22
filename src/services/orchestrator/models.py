from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import enum

class WorkflowState(str, enum.Enum):
    DRAFT = "DRAFT"
    TARGET_FETCHING = "TARGET_FETCHING"
    TARGET_READY = "TARGET_READY"
    POCKET_DETECTION = "POCKET_DETECTION"
    AWAITING_POCKET_APPROVAL = "AWAITING_POCKET_APPROVAL"
    BACKBONE_GENERATION = "BACKBONE_GENERATION"
    BACKBONES_READY = "BACKBONES_READY"
    SEQUENCE_DESIGN = "SEQUENCE_DESIGN"
    SEQUENCES_READY = "SEQUENCES_READY"
    COMPLEX_PREDICTION = "COMPLEX_PREDICTION"
    STRUCTURES_READY = "STRUCTURES_READY"
    INTERFACE_ANALYSIS = "INTERFACE_ANALYSIS"
    AWAITING_REVIEW = "AWAITING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class ResearchRun(BaseModel):
    run_id: str
    state: WorkflowState = WorkflowState.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    target_pdb_id: Optional[str] = None
    target_chain: Optional[str] = None
    artifacts: List[Dict[str, Any]] = []
    
class Capability(BaseModel):
    configured: bool
    available: bool
    mode: str

class Capabilities(BaseModel):
    openfold3: Capability
    rfdiffusion: Capability
    proteinmpnn: Capability

