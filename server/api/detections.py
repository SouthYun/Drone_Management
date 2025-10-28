# server/api/detections.py
from collections import deque
from datetime import datetime, timezone
from typing import Dict, List
from fastapi import APIRouter
from pydantic import BaseModel, Field
from server.api.realtime import broadcast_detection
import json

router = APIRouter(prefix="/detections", tags=["detections"])
_RECENT = deque(maxlen=200)

class Detection(BaseModel):
    stream_id: str = Field(..., examples=["drone-1"])
    cls: str = Field(..., examples=["person","smoke","fire"])
    conf: float = Field(..., ge=0, le=1)
    bbox: List[float] | None = None
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

@router.post("/push")
def push_detection(det: Detection):
    item: Dict = det.model_dump()
    _RECENT.appendleft(item)
    broadcast_detection(json.dumps(item, default=str))
    return {"ok": True}

@router.get("/recent")
def recent(limit: int = 50):
    return list(_RECENT)[:max(1, min(limit, 200))]
