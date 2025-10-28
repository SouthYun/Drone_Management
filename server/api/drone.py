# server/api/drone.py
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from server.db.models import SessionLocal, Log
from server.api.realtime import broadcast_status
import json

router = APIRouter(prefix="/drone", tags=["drone"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.post("/rtl")
def return_to_launch(db: Session = Depends(get_db)):
    entry = Log(level="INFO", message="[DRONE] RTL command issued.",
                ts=datetime.now(timezone.utc))
    db.add(entry); db.commit()
    broadcast_status(json.dumps({"type":"rtl_issued",
                                 "ts":datetime.now(timezone.utc).isoformat()}))
    return {"status": "ok", "message": "Drone returning to base."}
