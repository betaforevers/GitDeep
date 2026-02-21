from sqlalchemy import Column, Integer, String, DateTime, Text
import datetime
from app.db.database import Base

class RepoAnalysisRecord(Base):
    __tablename__ = "repo_analyses"

    id = Column(Integer, primary_key=True, index=True)
    repo_name = Column(String, index=True)
    health_status = Column(String)  # HEALTHY, AT RISK, DEAD
    health_score = Column(Integer)
    summary_text = Column(String)
    metrics_json = Column(Text) # Store all raw json data securely as string
    pdf_url = Column(String, nullable=True) # URL to the generated PDF report
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
