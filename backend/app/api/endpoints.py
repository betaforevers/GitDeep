import os
import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.schemas import RepositorySubmission, RepoAnalysisStatus
from app.services.github_service import GitHubService
from app.services.metrics_engine import MetricsEngine
from app.services.nlp_engine import NLPEngine
from app.services.reasoning_engine import ReasoningEngine
from app.services.report_generator import PDFReportGenerator
from app.services.file_metrics_engine import FileMetricsEngine
from app.services.git_analyzer import GitAnalyzer
from app.db.database import get_db
from app.db.models import RepoAnalysisRecord
from github import RateLimitExceededException

router = APIRouter()
github_service = GitHubService()
metrics_engine = MetricsEngine()
nlp_engine = NLPEngine()
reasoning_engine = ReasoningEngine()
report_generator = PDFReportGenerator()
file_metrics_engine = FileMetricsEngine()
git_analyzer = GitAnalyzer()

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
    
    # In Phase 1, we just do a dry-run check to see if we can fetch it
    try:
        repo_data = github_service.get_repo_info(owner, repo)
        commits_data = github_service.get_recent_commits(owner, repo, limit=200)
        releases_data = github_service.get_recent_releases(owner, repo, limit=10)
        
        bus_factor_res = metrics_engine.calculate_bus_factor(commits_data)
        decay_res = metrics_engine.calculate_activity_decay(commits_data)
        nlp_res = nlp_engine.analyze_commits(commits_data)
        
        # Fast local file extraction mapped over complete history
        local_commits_data = git_analyzer.clone_and_extract_file_history(url)
        file_metrics_res = file_metrics_engine.calculate_file_metrics(local_commits_data)
        
        reasoning_res = reasoning_engine.synthesize_report(
            repo_data, bus_factor_res, decay_res, nlp_res, releases_data, file_metrics_res, language=submission.language
        )
        
        details = {
            "stars": repo_data["stars"], 
            "open_issues": repo_data["open_issues"],
            "bus_factor": bus_factor_res["bus_factor"],
            "is_stagnant": decay_res["is_stagnant"],
            "commits_analyzed": len(commits_data),
            "tech_debt_ratio": nlp_res.get("tech_debt_ratio", 0),
            "file_metrics": file_metrics_res
        }
        
        pdf_path = report_generator.generate_report(f"{owner}/{repo}", details, reasoning_res, nlp_res, decay_res, language=submission.language)
        filename = os.path.basename(pdf_path)
        # Point to the backend server's reports directory
        pdf_url = f"http://localhost:8000/reports/{filename}"
        
        # Save to SQLite Database
        db_record = RepoAnalysisRecord(
            repo_name=f"{owner}/{repo}",
            health_status=reasoning_res.get("status", "UNKNOWN"),
            health_score=reasoning_res.get("health_score", 0),
            summary_text=reasoning_res.get("summary", ""),
            metrics_json=json.dumps(details),
            pdf_url=pdf_url
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        
        return RepoAnalysisStatus(
            status="success",
            message=reasoning_res["summary"],
            details=details,
            chart_data={
                "activity_trend": decay_res.get("activity_trend", {}),
                "intent_breakdown": nlp_res.get("raw_breakdown", {})
            },
            pdf_url=pdf_url,
            health_score=reasoning_res["health_score"]
        )
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
