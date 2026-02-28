import os
import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.schemas import RepositorySubmission, RepoAnalysisStatus
from app.services.analysis_orchestrator import AnalysisOrchestrator
from app.db.database import get_db
from app.db.models import RepoAnalysisRecord
from github import RateLimitExceededException

router = APIRouter()
orchestrator = AnalysisOrchestrator()

@router.post("/analyze", response_model=RepoAnalysisStatus)
def analyze_repository(submission: RepositorySubmission, db: Session = Depends(get_db)):
    url = submission.url
    # Extract owner and repo from URL
    # e.g., https://github.com/betaforevers/GitDeep -> betaforevers/GitDeep
    
    parts = url.strip("/").split("/")
    if len(parts) < 2 or "github.com" not in url:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")
        
    owner = parts[-2]
    repo = parts[-1]
    
    # Check for recent analysis in the database (last 6 hours)
    from datetime import datetime, timedelta
    six_hours_ago = datetime.utcnow() - timedelta(hours=6)
    
    recent_record = db.query(RepoAnalysisRecord).filter(
        RepoAnalysisRecord.repo_name == f"{owner}/{repo}",
        RepoAnalysisRecord.created_at >= six_hours_ago
    ).order_by(RepoAnalysisRecord.created_at.desc()).first()

    if recent_record:
        # Return the cached analysis
        details = json.loads(recent_record.metrics_json)
        return {"status": "success", "message": "Loaded from cache", "task_id": "cached", "result": RepoAnalysisStatus(
            status="success",
            message=recent_record.summary_text,
            details=details,
            chart_data={
                "activity_trend": {}, # Could be stored if needed, but not critical for cache
                "intent_breakdown": {}
            },
            pdf_url=recent_record.pdf_url,
            health_score=recent_record.health_score
        )}
    
    try:
        from app.celery_worker import analyze_repo_task
        task = analyze_repo_task.delay(url, owner, repo)
        return {"status": "processing", "message": "Analysis started in background", "task_id": task.id, "result": None}
    except RateLimitExceededException:
        raise HTTPException(status_code=429, detail="GitHub API Rate Limit exceeded! Unauthenticated requests are limited to 60 per hour.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyze/{task_id}")
def get_analysis_status(task_id: str):
    from app.celery_worker import celery_app
    task_result = celery_app.AsyncResult(task_id)
    
    if task_result.state == 'PENDING':
        return {"status": "pending", "message": "Waiting in queue...", "result": None}
    elif task_result.state == 'PROCESSING':
        return {"status": "processing", "message": task_result.info.get('status', 'Processing...'), "result": None}
    elif task_result.state == 'SUCCESS':
        return {"status": "success", "message": "Analysis complete", "result": task_result.result}
    elif task_result.state == 'FAILURE':
        return {"status": "failed", "message": str(task_result.info.get('exc_message', 'Unknown error')), "result": None}
    else:
        return {"status": task_result.state.lower(), "message": "Unknown state", "result": None}

@router.get("/history")
def get_analysis_history(db: Session = Depends(get_db)):
    """Retrieve the 3 most recent historical analyses."""
    records = db.query(RepoAnalysisRecord).order_by(RepoAnalysisRecord.created_at.desc()).limit(3).all()
    history = []
    for r in records:
        history.append({
            "id": r.id,
            "repo_name": r.repo_name,
            "status": r.health_status,
            "score": r.health_score,
            "summary": r.summary_text,
            "analyzed_at": r.created_at.isoformat(),
            "pdf_url": r.pdf_url
        })
    return {"history": history}
