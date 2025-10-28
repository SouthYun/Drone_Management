# server/api/ingest.py
from datetime import datetime, timezone
from typing import Optional, Any, Dict
import asyncio
import json

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from server.db.models import SessionLocal, init_db, AudioEvent
from server.services.audio_event_filter import is_event_accepted
from server.jobs.data_retention import run_scheduler
from server.services.failsafe_monitor import run_failsafe_monitor

# -----------------------------
# App & Middleware
# -----------------------------
app = FastAPI(title="DrownI API Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# -----------------------------
# Routers
# -----------------------------
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

# -----------------------------
# DB Session dependency
# -----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------
# Models
# -----------------------------
class IngestPayload(BaseModel):
    sensor_id: str = Field(..., examples=["sensor-001"])
    prob_help: float = Field(..., ge=0.0, le=1.0, examples=[0.93])
    ts: Optional[datetime] = None  # ISO8601(UTC) 권장
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

# -----------------------------
# Lifecycle
# -----------------------------
@app.on_event("startup")
def on_startup():
    init_db()
    asyncio.create_task(run_scheduler())  # 6시간마다 보존기간 초과 데이터 정리
    asyncio.create_task(run_failsafe_monitor()) # 페일세이프 모니터 병렬 실행
    print("[DrownI] API server started at", datetime.now(timezone.utc).isoformat())

# -----------------------------
# Endpoints
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}

@app.post("/ingest/audio", status_code=202)
def ingest_audio(payload: IngestPayload, db: Session = Depends(get_db)):
    ts = payload.ts or datetime.now(timezone.utc)
    accepted = is_event_accepted(payload.prob_help)

    ev = AudioEvent(
        sensor_id=payload.sensor_id,
        prob_help=payload.prob_help,
        accepted=accepted,
        ts=ts,
        battery=payload.battery,
        features=json.dumps(payload.features) if payload.features is not None else None,
        meta=json.dumps(payload.meta) if payload.meta is not None else None,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    return {
        "status": "accepted" if accepted else "queued",
        "event_id": ev.id,
        "accepted": accepted,
    }
