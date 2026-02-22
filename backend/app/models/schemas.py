from pydantic import BaseModel
from typing import List, Optional

class RepositorySubmission(BaseModel):
    url: str

class CommitData(BaseModel):
    sha: str
    message: str
    author: str
    date: str

class RepoAnalysisStatus(BaseModel):
    status: str
    message: str
    details: Optional[dict] = None
    chart_data: Optional[dict] = None
    pdf_url: Optional[str] = None
    health_score: Optional[int] = None
