# server/api/admin.py
"""
Admin Control API
-----------------
서버 관리용 (로그 초기화, 상태 확인, 수동 RTL 명령 등)
"""

import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from server.db.models import SessionLocal, Log
from server.services.metrics_collector import METRICS
from server.api.realtime import broadcast_status

router = APIRouter(prefix="/admin", tags=["admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/status")
def system_status():
    """시스템 상태 조회 (메트릭 포함)"""
    return {
        "server_time": datetime.now(timezone.utc).isoformat(),
        "metrics": METRICS.snapshot(),
        "uptime": os.popen("uptime").read().strip() if os.name != "nt" else "N/A",
    }


@router.post("/clear-logs")
def clear_logs(db: Session = Depends(get_db)):
    """DB 로그 테이블 초기화"""
    deleted = db.query(Log).delete()
    db.commit()
    for f in ["logs/error.log", "logs/access.log"]:
        try:
            open(f, "w").close()
        except Exception:
            pass
    broadcast_status('{"type":"admin_action","message":"Logs cleared"}')
    return {"ok": True, "deleted": deleted}


@router.post("/rtl")
def manual_rtl():
    """수동 RTL 명령 (관리자용)"""
    from server.api.drone import return_to_launch
    db = SessionLocal()
    try:
        res = return_to_launch(db)
        broadcast_status('{"type":"admin_action","message":"Manual RTL executed"}')
        return {"ok": True, "action": "rtl", "result": res}
    finally:
        db.close()
