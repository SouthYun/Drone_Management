# server/api/ingest.py
from datetime import datetime, timezone
from typing import Optional, Any, Dict

from fastapi import FastAPI, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from server.db.models import SessionLocal, init_db, AudioEvent
from server.services.audio_event_filter import is_event_accepted

app = FastAPI(title="DrownI Ingest API", version="0.1.0")
from server.api.tdoa import router as tdoa_router
app.include_router(tdoa_router)
from server.api.missions import router as missions_router
app.include_router(missions_router)
from server.api.events import router as events_router
app.include_router(events_router)
from server.api.drone import router as drone_router
app.include_router(drone_router)
from server.api.logs import router as logs_router
app.include_router(logs_router)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)



class IngestPayload(BaseModel):
    sensor_id: str = Field(..., examples=["sensor-001"])
    prob_help: float = Field(..., ge=0.0, le=1.0, examples=[0.93])
    ts: Optional[datetime] = None  # ISO8601 (UTC) 권장
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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


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
        features=None if payload.features is None else __import__("json").dumps(payload.features),
        meta=None if payload.meta is None else __import__("json").dumps(payload.meta),
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    return {
        "status": "accepted" if accepted else "queued",
        "event_id": ev.id,
        "accepted": accepted,
    }
    
