# server/services/waypoint_builder.py
from __future__ import annotations
from datetime import datetime, timezone
from collections import deque
from typing import Deque, Dict, Optional
import uuid

_MISSION_QUEUE: Deque[Dict] = deque(maxlen=1000)

def build_waypoint(lat: float, lon: float, altitude: float = 50.0,
                   speed_mps: float = 5.0, loiter_sec: float = 0.0) -> Dict:
    return {
        "id": str(uuid.uuid4()),
        "lat": round(lat, 7), "lon": round(lon, 7),
        "alt": float(altitude), "speed_mps": float(speed_mps),
        "loiter_sec": float(loiter_sec),
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

def enqueue_waypoint(wp: Dict) -> None:
    _MISSION_QUEUE.append(wp)

def get_next_waypoint() -> Optional[Dict]:
    if not _MISSION_QUEUE: return None
    wp = _MISSION_QUEUE.popleft(); wp["status"] = "dispatched"; return wp

def peek_queue_size() -> int:
    return len(_MISSION_QUEUE)
