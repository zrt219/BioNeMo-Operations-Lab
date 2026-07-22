from fastapi import APIRouter
from src.lib.capabilities.service import get_capabilities
from src.services.orchestrator.models import Capabilities

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/capabilities", response_model=Capabilities)
def capabilities():
    return get_capabilities()
