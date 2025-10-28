# server/services/drone_tracker.py
"""
Drone Tracker Service
---------------------
드론의 실시간 위치/상태 업데이트 API 및 SSE 브로드캐스트 헬퍼.
 - 드론 클라이언트(OSDK 등) → /tracker/update 로 주기적 보고
 - 서버는 상태를 저장 후 /realtime/status 로 브로드캐스트
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from server.api.realtime import broadcast_status
import json

router = APIRouter(prefix="/tracker", tags=["tracker"])

# 메모리 기반 현재 상태
DRONE_STATE: dict[str, dict] = {}

class DroneState(BaseModel):
    drone_id: str = Field(..., examples=["drone-001"])
    lat: float
    lon: float
    alt: float = 0.0
    speed_mps: Optional[float] = None
    battery: Optional[float] = None
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

@router.post("/update")
def update_state(state: DroneState):
    """
    드론이 주기적으로 자신의 상태(좌표, 고도, 속도 등)를 보고.
    """
    DRONE_STATE[state.drone_id] = state.model_dump()
    msg = json.dumps({
        "type": "drone_update",
        "drone_id": state.drone_id,
        "lat": state.lat, "lon": state.lon,
        "alt": state.alt, "speed_mps": state.speed_mps,
        "battery": state.battery,
        "ts": state.ts.isoformat(),
    }, default=str)
    broadcast_status(msg)
    return {"ok": True}

@router.get("/current")
def get_current():
    """현재 저장된 모든 드론 상태 조회"""
    return list(DRONE_STATE.values())
