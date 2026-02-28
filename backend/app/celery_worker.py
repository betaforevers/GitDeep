import os
from celery import Celery
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.services.analysis_orchestrator import AnalysisOrchestrator
import json

# Initialize Celery
# We will use Redis as the message broker and backend
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "gitdeep_worker",
    broker=redis_url,
    backend=redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

orchestrator = AnalysisOrchestrator()

@celery_app.task(bind=True, name="analyze_repo_task")
def analyze_repo_task(self, url: str, owner: str, repo: str):
    db: Session = SessionLocal()
    try:
        # Update state to processing
        self.update_state(state='PROCESSING', meta={'status': 'Started analysis...'})
        
        result = orchestrator.analyze_repository(url, owner, repo, db)
        
        return result
    except Exception as e:
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e
    finally:
        db.close()
