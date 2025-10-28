# server/api/drone.py
"""
드론 제어 API (스텁)
--------------------
현재는 실제 OSDK 연동 전, 복귀(Return-To-Launch) 명령을
서버 로그에 기록하고 상태를 반환하는 최소 버전.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from server.db.models import SessionLocal, Log

router = APIRouter(prefix="/drone", tags=["drone"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/rtl")
def return_to_launch(db: Session = Depends(get_db)):
    """드론 복귀 명령"""
    entry = Log(
        level="INFO",
        message="[DRONE] RTL (Return-To-Launch) command issued.",
        ts=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
    return {"status": "ok", "message": "Drone returning to base."}
