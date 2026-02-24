import os
import json
from datetime import datetime, timedelta
from app.services.github_service import GitHubService
from app.services.metrics_engine import MetricsEngine
from app.services.nlp_engine import NLPEngine
from app.services.reasoning_engine import ReasoningEngine
from app.services.report_generator import PDFReportGenerator
from app.services.file_metrics_engine import FileMetricsEngine
from app.services.git_analyzer import GitAnalyzer
from app.services.plagiarism_engine import PlagiarismEngine
from app.db.models import RepoAnalysisRecord

class AnalysisOrchestrator:
    def __init__(self):
        self.github_service = GitHubService()
        self.metrics_engine = MetricsEngine()
        self.nlp_engine = NLPEngine()
        self.reasoning_engine = ReasoningEngine()
        self.report_generator = PDFReportGenerator()
        self.file_metrics_engine = FileMetricsEngine()
        self.git_analyzer = GitAnalyzer()
        self.plagiarism_engine = PlagiarismEngine(self.git_analyzer.tmp_dir)

    def analyze_repository(self, url: str, owner: str, repo: str, db):
        # In Phase 1, we just do a dry-run check to see if we can fetch it
        repo_data = self.github_service.get_repo_info(owner, repo)
        commits_data = self.github_service.get_recent_commits(owner, repo, limit=200)
        releases_data = self.github_service.get_recent_releases(owner, repo, limit=10)
        
        bus_factor_res = self.metrics_engine.calculate_bus_factor(commits_data)
        decay_res = self.metrics_engine.calculate_activity_decay(commits_data)
        nlp_res = self.nlp_engine.analyze_commits(commits_data)
        
        # Fast local file extraction mapped over complete history
        local_commits_data = self.git_analyzer.clone_and_extract_file_history(url)
        file_metrics_res = self.file_metrics_engine.calculate_file_metrics(local_commits_data)
        
        # Plagiarism / Originality Check
        duplication_pct, dupe_pairs = self.plagiarism_engine.calculate_internal_duplication(self.git_analyzer.tmp_dir)
        originality_res = self.plagiarism_engine.check_external_originality(repo_data, self.git_analyzer.tmp_dir, file_metrics_res.get('hotspots', []))
        
        plagiarism_res = {
            "internal_duplication_pct": duplication_pct,
            "high_duplication_pairs": dupe_pairs,
            "originality": originality_res
        }
        
        reasoning_res = self.reasoning_engine.synthesize_report(
            repo_data, bus_factor_res, decay_res, nlp_res, releases_data, file_metrics_res
        )
        
        details = {
            "stars": repo_data["stars"], 
            "open_issues": repo_data["open_issues"],
            "bus_factor": bus_factor_res["bus_factor"],
            "bus_factor_data": bus_factor_res,
            "is_stagnant": decay_res["is_stagnant"],
            "commits_analyzed": len(commits_data),
            "tech_debt_ratio": nlp_res.get("tech_debt_ratio", 0),
            "file_metrics": file_metrics_res,
            "plagiarism": plagiarism_res
        }
        
        pdf_path = self.report_generator.generate_report(f"{owner}/{repo}", details, reasoning_res, nlp_res, decay_res)
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
        
        return {
            "status": "success",
            "message": reasoning_res["summary"],
            "details": details,
            "chart_data": {
                "activity_trend": decay_res.get("activity_trend", {}),
                "intent_breakdown": nlp_res.get("raw_breakdown", {})
            },
            "pdf_url": pdf_url,
            "health_score": reasoning_res["health_score"]
        }
