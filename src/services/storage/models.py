from sqlalchemy import Column, String, DateTime, JSON
from .database import Base
from datetime import datetime

class RunDB(Base):
    __tablename__ = "runs"
    
    run_id = Column(String, primary_key=True, index=True)
    state = Column(String, default="DRAFT")
    created_at = Column(DateTime, default=datetime.utcnow)
    target_pdb_id = Column(String, nullable=True)
    target_chain = Column(String, nullable=True)
    artifacts = Column(JSON, default=list)
