# server/api/ingest.py
"""
DrownI Main API Server
----------------------
센서 데이터 수집 + 드론 관제 + AI 탐지 + 실시간 관제 통합 엔트리 포인트
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Optional, Any, Dict

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

# 내부 모듈 import
from server.db.models import SessionLocal, init_db, AudioEvent
from server.services.audio_event_filter import is_event_accepted
from server.jobs.data_retention import run_scheduler
from server.services.failsafe_monitor import run_failsafe_monitor, update_sensor_heartbeat

# ---------------------------------------------------------
# FastAPI 초기화
# ---------------------------------------------------------
app = FastAPI(title="DrownI API Server", version="1.0.0")

# CORS (개발 및 관제 웹 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# 라우터 등록
# ---------------------------------------------------------
from server.api.tdoa import router as tdoa_router
from server.api.missions import router as missions_router
from server.api.events import router as events_router
from server.api.drone import router as drone_router
from server.api.logs import router as logs_router
from server.api.detections import router as detections_router
from server.api.realtime import router as realtime_router

app.include_router(tdoa_router)
app.include_router(missions_router)
app.include_router(events_router)
app.include_router(drone_router)
app.include_router(logs_router)
app.include_router(detections_router)
app.include_router(realtime_router)

# ---------------------------------------------------------
# DB 세션 관리
# ---------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------
# 요청 데이터 모델
# ---------------------------------------------------------
class IngestPayload(BaseModel):
    sensor_id: str = Field(..., examples=["sensor-001"])
    prob_help: float = Field(..., ge=0.0, le=1.0, examples=[0.93])
    ts: Optional[datetime] = None
    battery: Optional[float] = None
    features: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None

    @field_validator("ts", mode="before")
    @classmethod
    def parse_ts(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        return datetime.fromisoformat(str(v).replace("Z", "+00:00"))

# ---------------------------------------------------------
# 서버 시작 시 초기화
# ---------------------------------------------------------
@app.on_event("startup")
def on_startup():
    """DB 초기화 + 데이터정리 + 페일세이프 모니터"""
    init_db()
    asyncio.create_task(run_scheduler())         # 6시간마다 오래된 데이터 정리
    asyncio.create_task(run_failsafe_monitor())  # 센서/드론 상태 감시 루프 실행
    print(f"[DrownI] Server started at {datetime.now(timezone.utc).isoformat()}")

# ---------------------------------------------------------
# 기본 엔드포인트
# ---------------------------------------------------------
@app.get("/health")
def health():
    """서버 상태 확인"""
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}

# ---------------------------------------------------------
# 센서 데이터 수신 엔드포인트
# ---------------------------------------------------------
@app.post("/ingest/audio", status_code=202)
def ingest_audio(payload: IngestPayload, db: Session = Depends(get_db)):
    """
    센서 → 서버 업링크
    - prob_help ≥ 0.9 인 경우 accepted=True
    - 배터리 정보 및 하트비트 갱신 포함
    """
    ts = payload.ts or datetime.now(timezone.utc)
    accepted = is_event_accepted(payload.prob_help)

    # ✅ 센서 하트비트 및 배터리 상태 업데이트
    update_sensor_heartbeat(payload.sensor_id, payload.battery or 4.0)

    # DB 저장
    ev = AudioEvent(
        sensor_id=payload.sensor_id,
        prob_help=payload.prob_help,
        accepted=accepted,
        ts=ts,
        battery=payload.battery,
        features=json.dumps(payload.features) if payload.features else None,
        meta=json.dumps(payload.meta) if payload.meta else None,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    return {
        "status": "accepted" if accepted else "queued",
        "event_id": ev.id,
        "accepted": accepted,
    }
