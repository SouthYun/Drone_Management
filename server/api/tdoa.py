# server/api/tdoa.py
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from server.services.tdoa_solver import estimate_location, SENSOR_POSITIONS
from server.services.waypoint_builder import build_waypoint, enqueue_waypoint, peek_queue_size

router = APIRouter(prefix="/tdoa", tags=["tdoa"])

class Arrival(BaseModel):
    sensor_id: str = Field(..., examples=["sensor-001"])
    delay: float = Field(..., ge=0.0, examples=[0.002])

class SolveRequest(BaseModel):
    arrivals: List[Arrival]

class SolveResponse(BaseModel):
    lat: float
    lon: float
    used_sensors: List[str]
    waypoint_id: str
    queue_size: int

@router.post("/solve", response_model=SolveResponse)
def solve(req: SolveRequest):
    if len(req.arrivals) < 3:
        raise HTTPException(status_code=400, detail="At least 3 arrivals required.")
    arrivals = [a.model_dump() for a in req.arrivals if a.sensor_id in SENSOR_POSITIONS]
    if len(arrivals) < 3:
        raise HTTPException(status_code=400, detail="Need 3+ known sensors.")
    lat, lon = estimate_location(arrivals)

    # 웨이포인트 자동 생성 및 큐 삽입
    wp = build_waypoint(lat, lon)
    enqueue_waypoint(wp)

    return SolveResponse(
        lat=lat,
        lon=lon,
        used_sensors=[a["sensor_id"] for a in arrivals],
        waypoint_id=wp["id"],
        queue_size=peek_queue_size(),
    )
