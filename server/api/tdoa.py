# server/api/tdoa.py
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from server.services.tdoa_solver import estimate_location, SENSOR_POSITIONS

router = APIRouter(prefix="/tdoa", tags=["tdoa"])

class Arrival(BaseModel):
    sensor_id: str = Field(..., examples=["sensor-001"])
    delay: float = Field(..., ge=0.0, examples=[0.002])  # seconds

class SolveRequest(BaseModel):
    arrivals: List[Arrival]

class SolveResponse(BaseModel):
    lat: float
    lon: float
    used_sensors: List[str]

@router.post("/solve", response_model=SolveResponse)
def solve(req: SolveRequest):
    if len(req.arrivals) < 3:
        raise HTTPException(status_code=400, detail="At least 3 arrivals required.")
    # unknown sensor는 걸러냄
    arrivals = [a.model_dump() for a in req.arrivals if a.sensor_id in SENSOR_POSITIONS]
    if len(arrivals) < 3:
        raise HTTPException(status_code=400, detail="Need 3+ known sensors.")
    lat, lon = estimate_location(arrivals)
    return SolveResponse(lat=lat, lon=lon, used_sensors=[a["sensor_id"] for a in arrivals])
