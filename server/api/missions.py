# server/api/missions.py
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Dict
import json

from server.services.waypoint_builder import (
    build_waypoint, enqueue_waypoint, get_next_waypoint, peek_queue_size
)
from server.services.failsafe_monitor import mark_mission_start, mark_mission_end
from server.api.realtime import broadcast_status
from server.services.metrics_collector import METRICS       # ✅ B3

router = APIRouter(prefix="/missions", tags=["missions"])

class EnqueueReq(BaseModel):
    lat: float = Field(...); lon: float = Field(...)
    altitude: float = 50.0; speed_mps: float = 5.0; loiter_sec: float = 0.0

class AckReq(BaseModel):
    mission_id: str
    reason: str = "completed"  # completed|aborted|rtl

@router.post("/enqueue")
def enqueue(req: EnqueueReq) -> Dict:
    wp = build_waypoint(req.lat, req.lon, req.altitude, req.speed_mps, req.loiter_sec)
    enqueue_waypoint(wp)
    # ✅ B3: 미션 등록 카운트
    METRICS.note_mission_enqueued()

    broadcast_status(json.dumps({"type":"mission_enqueued","waypoint":wp}))
    return {"queued": True, "waypoint": wp, "queue_size": peek_queue_size()}

@router.get("/next")
def next_mission() -> Dict:
    wp = get_next_waypoint()
    if not wp:
        return {"waypoint": None}
    mark_mission_start(wp["id"])
    broadcast_status(json.dumps({"type":"mission_dispatched","waypoint":wp}))
    return {"waypoint": wp}

@router.post("/ack")
def ack(req: AckReq) -> Dict:
    mark_mission_end(req.mission_id, reason=req.reason)

    # ✅ B3: 완료만 성공 카운트
    if req.reason == "completed":
        METRICS.note_mission_completed()

    broadcast_status(json.dumps({"type":"mission_ended",
                                 "mission_id":req.mission_id,"reason":req.reason}))
    return {"ok": True}
