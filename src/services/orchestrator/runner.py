import asyncio
from src.services.storage.database import SessionLocal
from src.services.storage.models import RunDB
from src.services.orchestrator.models import WorkflowState

async def run_pipeline_mock(run_id: str):
    """Mock execution of the pipeline state machine."""
    states = [
        (WorkflowState.TARGET_FETCHING, 2),
        (WorkflowState.TARGET_READY, 1),
        (WorkflowState.POCKET_DETECTION, 2),
        (WorkflowState.AWAITING_POCKET_APPROVAL, 2),
        (WorkflowState.BACKBONE_GENERATION, 3),
        (WorkflowState.BACKBONES_READY, 1),
        (WorkflowState.SEQUENCE_DESIGN, 3),
        (WorkflowState.SEQUENCES_READY, 1),
        (WorkflowState.COMPLEX_PREDICTION, 4),
        (WorkflowState.STRUCTURES_READY, 1),
        (WorkflowState.INTERFACE_ANALYSIS, 2),
        (WorkflowState.APPROVED, 0)
    ]
    
    for state, delay in states:
        await asyncio.sleep(delay)
        with SessionLocal() as db:
            run = db.query(RunDB).filter(RunDB.run_id == run_id).first()
            if run:
                run.state = state.value
                artifacts = list(run.artifacts) if run.artifacts else []
                artifacts.append({
                    "stage": state.value,
                    "status": "COMPLETED",
                    "timestamp": str(asyncio.get_event_loop().time())
                })
                run.artifacts = artifacts
                db.commit()
                print(f"[{run_id}] Transitioned to {state.value}")
