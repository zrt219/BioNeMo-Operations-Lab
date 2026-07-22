import os
from src.services.orchestrator.models import Capabilities, Capability

def get_capabilities() -> Capabilities:
    has_ngc = bool(os.getenv("NGC_API_KEY")) or bool(os.getenv("NVIDIA_API_KEY"))
    
    # Check if specific URLs are configured, else fallback to standard hosted if NGC key present
    of3_url = os.getenv("NVIDIA_OPENFOLD3_URL")
    rfd_url = os.getenv("NVIDIA_RFDIFFUSION_URL")
    mpnn_url = os.getenv("NVIDIA_PROTEINMPNN_URL")
    
    return Capabilities(
        openfold3=Capability(
            configured=has_ngc,
            available=has_ngc,
            mode="hosted" if has_ngc else "unavailable"
        ),
        rfdiffusion=Capability(
            configured=has_ngc,
            available=has_ngc,
            mode="hosted" if has_ngc else "unavailable"
        ),
        proteinmpnn=Capability(
            configured=has_ngc,
            available=has_ngc,
            mode="hosted" if has_ngc else "unavailable"
        )
    )
