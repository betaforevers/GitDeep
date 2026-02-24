import os
import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.schemas import RepositorySubmission, RepoAnalysisStatus
from app.services.analysis_orchestrator import AnalysisOrchestrator

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
        return RepoAnalysisStatus(
            status="success",
            message=recent_record.summary_text,
            details=details,
            chart_data={
                "activity_trend": {}, # Could be stored if needed, but not critical for cache
                "intent_breakdown": {}
            },
            pdf_url=recent_record.pdf_url,
            health_score=recent_record.health_score
        )
    
    try:
        result = orchestrator.analyze_repository(url, owner, repo, db)
        return RepoAnalysisStatus(**result)
    except RateLimitExceededException:
        raise HTTPException(status_code=429, detail="GitHub API Rate Limit exceeded! Unauthenticated requests are limited to 60 per hour. Please wait, or add a GITHUB_PAT to your .env file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
