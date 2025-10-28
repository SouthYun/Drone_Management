# server/api/missions.py
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Dict

from server.services.waypoint_builder import (
    build_waypoint, enqueue_waypoint, get_next_waypoint, peek_queue_size
)
from server.services.failsafe_monitor import mark_mission_start, mark_mission_end

router = APIRouter(prefix="/missions", tags=["missions"])

# -----------------------------
# 요청 모델 정의
# -----------------------------
class EnqueueReq(BaseModel):
    lat: float = Field(..., description="위도")
    lon: float = Field(..., description="경도")
    altitude: float = 50.0
    speed_mps: float = 5.0
    loiter_sec: float = 0.0


class AckReq(BaseModel):
    mission_id: str
    reason: str = "completed"  # completed|aborted|rtl


# -----------------------------
# API
# -----------------------------
@router.post("/enqueue")
def enqueue(req: EnqueueReq) -> Dict:
    """새 웨이포인트 등록"""
    wp = build_waypoint(req.lat, req.lon, req.altitude, req.speed_mps, req.loiter_sec)
    enqueue_waypoint(wp)
    return {"queued": True, "waypoint": wp, "queue_size": peek_queue_size()}


@router.get("/next")
def next_mission() -> Dict:
    """드론이 다음 임무를 요청할 때"""
    wp = get_next_waypoint()
    if not wp:
        return {"waypoint": None}
    mark_mission_start(wp["id"])  # ✅ 임무 시작 시각 기록
    return {"waypoint": wp}


@router.post("/ack")
def ack(req: AckReq) -> Dict:
    """드론이 임무 완료/중단/복귀 시 보고"""
    mark_mission_end(req.mission_id, reason=req.reason)
    return {"ok": True}
