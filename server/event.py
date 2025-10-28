# server/api/events.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict

from server.db.models import SessionLocal, AudioEvent

router = APIRouter(prefix="/events", tags=["events"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/recent")
def recent_events(limit: int = Query(20, ge=1, le=200), db: Session = Depends(get_db)) -> List[Dict]:
    rows = (
        db.query(AudioEvent)
        .order_by(AudioEvent.ts.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "ts": r.ts.isoformat(),
            "sensor_id": r.sensor_id,
            "prob_help": r.prob_help,
            "accepted": r.accepted,
            "battery": r.battery,
        }
        for r in rows
    ]
