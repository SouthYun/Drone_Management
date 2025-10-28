# server/api/ingest.py
"""
DrownI Main API Server
----------------------
센서 데이터 수집 + 드론 임무 관리 + AI 탐지 + 실시간 관제 + 메트릭 수집 + 예외처리 통합 버전
"""

import asyncio, json
from datetime import datetime, timezone
from typing import Optional, Any, Dict

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

# ───────────────────────────────────────────────
# 내부 모듈 import
# ───────────────────────────────────────────────
from server.db.models import SessionLocal, init_db, AudioEvent
from server.services.audio_event_filter import is_event_accepted
from server.jobs.data_retention import run_scheduler
from server.services.failsafe_monitor import run_failsafe_monitor, update_sensor_heartbeat
from server.services.metrics_collector import METRICS, run_metrics_scheduler
from server.api.realtime import broadcast_event
from server.core.error_handler import register_exception_handlers   # ✅ 전역 예외 핸들러

# ───────────────────────────────────────────────
# FastAPI 초기화 및 미들웨어 등록
# ───────────────────────────────────────────────
app = FastAPI(title="DrownI API Server", version="2.0.0")

# 예외 핸들러 등록 (전역)
register_exception_handlers(app)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ───────────────────────────────────────────────
# 라우터 등록
# ───────────────────────────────────────────────
from server.api.tdoa import router as tdoa_router
from server.api.missions import router as missions_router
from server.api.events import router as events_router
from server.api.drone import router as drone_router
from server.api.logs import router as logs_router
from server.api.detections import router as detections_router
from server.api.realtime import router as realtime_router
from server.api.metrics import router as metrics_router
from server.services import drone_tracker

app.include_router(tdoa_router)
app.include_router(missions_router)
app.include_router(events_router)
app.include_router(drone_router)
app.include_router(logs_router)
app.include_router(detections_router)
app.include_router(realtime_router)
app.include_router(metrics_router)
app.include_router(drone_tracker.router)

# ───────────────────────────────────────────────
# DB 세션 종속성
# ───────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ───────────────────────────────────────────────
# 요청 모델 정의
# ───────────────────────────────────────────────
class IngestPayload(BaseModel):
    sensor_id: str = Field(..., examples=["sensor-001"])
    prob_help: float = Field(..., ge=0.0, le=1.0, examples=[0.95])
    ts: Optional[datetime] = None
    battery: Optional[float] = None
    features: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None

    @field_validator("ts", mode="before")
    @classmethod
    def parse_ts(cls, v):
        if v is None or isinstance(v, datetime):
            return v
        return datetime.fromisoformat(str(v).replace("Z", "+00:00"))

# ───────────────────────────────────────────────
# 서버 시작 시 초기화
# ───────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    """DB 초기화 + 스케줄러 + 페일세이프 + 메트릭 수집기 시작"""
    init_db()
    asyncio.create_task(run_scheduler())          # 데이터 보존 정책
    asyncio.create_task(run_failsafe_monitor())   # 페일세이프 감시
    asyncio.create_task(run_metrics_scheduler())  # 메트릭 분단위 롤링
    print(f"[DrownI] Server started at {datetime.now(timezone.utc).isoformat()}")

# ───────────────────────────────────────────────
# 기본 헬스체크 엔드포인트
# ───────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}

# ───────────────────────────────────────────────
# 센서 업링크 API
# ───────────────────────────────────────────────
@app.post("/ingest/audio", status_code=202)
def ingest_audio(payload: IngestPayload, db: Session = Depends(get_db)):
    """
    센서 → 서버 업링크 처리:
    - prob_help >= threshold → 이벤트 accepted
    - 배터리 상태 업데이트
    - 메트릭 카운트 및 SSE 브로드캐스트
    """
    # ✅ 메트릭 카운트
    METRICS.note_audio_event()

    ts = payload.ts or datetime.now(timezone.utc)
    accepted = is_event_accepted(payload.prob_help)

    # 센서 하트비트 갱신
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

    # SSE 브로드캐스트 (지도용)
    if accepted:
        meta = payload.meta or {}
        broadcast_event(json.dumps({
            "type": "audio_event",
            "id": ev.id,
            "ts": ts.isoformat(),
            "sensor_id": payload.sensor_id,
            "prob_help": payload.prob_help,
            "lat": meta.get("lat"),
            "lon": meta.get("lon"),
        }, default=str))

    return {
        "status": "accepted" if accepted else "queued",
        "event_id": ev.id,
        "accepted": accepted,
    }
