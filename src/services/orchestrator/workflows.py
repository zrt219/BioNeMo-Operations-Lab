from typing import Optional
from sqlalchemy.orm import Session
from src.services.storage.models import RunDB
from src.services.orchestrator.models import WorkflowState, ResearchRun
import uuid

def create_run(db: Session, target_pdb: str = "2W5B") -> RunDB:
    run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
    db_run = RunDB(
        run_id=run_id,
        state=WorkflowState.TARGET_FETCHING.value,
        target_pdb_id=target_pdb
    )
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    return db_run

def get_run(db: Session, run_id: str) -> Optional[RunDB]:
    return db.query(RunDB).filter(RunDB.run_id == run_id).first()
