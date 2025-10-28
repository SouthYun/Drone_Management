# server/services/waypoint_builder.py
"""
웨이포인트 빌더 (스텁)
- 입력: lat, lon (TDOA 결과)
- 출력: 드론 임무용 웨이포인트 dict
- 보관: 모듈 내부 메모리 큐 (차후 DB로 교체 예정)
"""
from __future__ import annotations
from datetime import datetime, timezone
from collections import deque
from typing import Deque, Dict, Optional
import uuid

# 간단한 임무 큐 (프로토타입 단계에서는 메모리 큐로 운영)
_MISSION_QUEUE: Deque[Dict] = deque(maxlen=1000)

def build_waypoint(lat: float, lon: float,
                   altitude: float = 50.0,
                   speed_mps: float = 5.0,
                   loiter_sec: float = 0.0) -> Dict:
    """TDOA 좌표로 웨이포인트 객체 생성"""
    return {
        "id": str(uuid.uuid4()),
        "lat": round(lat, 7),
        "lon": round(lon, 7),
        "alt": float(altitude),
        "speed_mps": float(speed_mps),
        "loiter_sec": float(loiter_sec),
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

def enqueue_waypoint(wp: Dict) -> None:
    """웨이포인트를 임무 큐에 추가"""
    _MISSION_QUEUE.append(wp)

def get_next_waypoint() -> Optional[Dict]:
    """다음 임무 하나를 반환(큐에서 제거)"""
    if not _MISSION_QUEUE:
        return None
    wp = _MISSION_QUEUE.popleft()
    wp["status"] = "dispatched"
    return wp

def peek_queue_size() -> int:
    return len(_MISSION_QUEUE)
