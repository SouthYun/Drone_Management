# server/api/logs.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict
from server.db.models import SessionLocal, Log

router = APIRouter(prefix="/logs", tags=["logs"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/recent")
def recent_logs(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)) -> List[Dict]:
    rows = (
        db.query(Log)
        .order_by(Log.ts.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "level": r.level,
            "message": r.message,
            "ts": r.ts.isoformat(),
        }
        for r in rows
    ]
