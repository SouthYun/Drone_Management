# server/api/missions.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict

from server.services.waypoint_builder import (
    build_waypoint, enqueue_waypoint, get_next_waypoint, peek_queue_size
)

router = APIRouter(prefix="/missions", tags=["missions"])


class EnqueueReq(BaseModel):
    lat: float = Field(..., description="위도")
    lon: float = Field(..., description="경도")
    altitude: float = 50.0
    speed_mps: float = 5.0
    loiter_sec: float = 0.0


@router.post("/enqueue")
def enqueue(req: EnqueueReq) -> Dict:
    wp = build_waypoint(req.lat, req.lon, req.altitude, req.speed_mps, req.loiter_sec)
    enqueue_waypoint(wp)
    return {"queued": True, "waypoint": wp, "queue_size": peek_queue_size()}


@router.get("/next")
def next_mission() -> Dict:
    wp = get_next_waypoint()
    if not wp:
        raise HTTPException(status_code=204, detail="No missions")
    return {"waypoint": wp}


@router.get("/queue/size")
def queue_size() -> Dict:
    return {"queue_size": peek_queue_size()}
