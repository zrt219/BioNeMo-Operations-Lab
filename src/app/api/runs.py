from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from src.services.storage.database import get_db
from src.services.orchestrator.workflows import create_run, get_run
from src.services.storage.models import RunDB
from src.services.orchestrator.models import ResearchRun
from src.services.orchestrator.runner import run_pipeline_mock
import asyncio

router = APIRouter(prefix="/runs")

@router.post("/", response_model=ResearchRun)
def start_new_run(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_run = create_run(db)
    
    # Fire and forget the mock pipeline in the background
    background_tasks.add_task(run_pipeline_mock, db_run.run_id)
    
    return ResearchRun(
        run_id=db_run.run_id,
        state=db_run.state,
        target_pdb_id=db_run.target_pdb_id,
        artifacts=db_run.artifacts
    )

@router.get("/{run_id}", response_model=ResearchRun)
def get_run_status(run_id: str, db: Session = Depends(get_db)):
    db_run = get_run(db, run_id)
    if not db_run:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Run not found")
    return ResearchRun(
        run_id=db_run.run_id,
        state=db_run.state,
        target_pdb_id=db_run.target_pdb_id,
        artifacts=db_run.artifacts
    )
