import asyncio
from app.db.database import SessionLocal
from app.api.endpoints import get_db

async def run_debug():
    # just print recent record
    db = SessionLocal()
    from app.db.models import RepoAnalysisRecord
    r = db.query(RepoAnalysisRecord).order_by(RepoAnalysisRecord.id.desc()).first()
    if r:
        print("LATEST METRICS JSON:")
        print(r.metrics_json)
    db.close()

asyncio.run(run_debug())
