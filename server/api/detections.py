# 파일 요약: 이 파일은 DrownI 시스템의 **객체 감지(Detection) 데이터 수신 및 관리** API 엔드포인트를 담당합니다.
# 시스템 내 위치: 백엔드 API 레이어에서 드론으로부터 전송되는 실시간 감지 결과(예: 사람, 연기, 화재)를 처리하고,
#                 이를 저장하며, 웹소켓을 통해 관제 클라이언트에게 브로드캐스트하는 핵심 역할을 수행합니다.
# 주요 기능: 1. 새로운 감지 데이터를 수신 및 기록합니다.
#         2. 실시간 대시보드 업데이트를 위해 데이터를 브로드캐스트합니다.
#         3. 최근 감지 기록을 조회하는 기능을 제공합니다.

from collections import deque
from datetime import datetime, timezone
from typing import Dict, List
from fastapi import APIRouter
from pydantic import BaseModel, Field
from server.api.realtime import broadcast_detection
from server.services.metrics_collector import METRICS    # ✅ B3: 메트릭 수집 서비스 (시스템 성능 및 감지 통계 기록)
import json

# FastAPI 라우터 인스턴스 생성
router = APIRouter(prefix="/detections", tags=["detections"])

# 최근 감지 결과를 저장하는 데 사용되는 이중 종료 큐(Double-ended Queue, Deque).
# maxlen=200 설정으로, 큐의 크기가 200개를 초과하면 가장 오래된 항목(오른쪽)이 자동으로 제거되어
# 메모리 오버헤드를 방지하고 최근 데이터만 효율적으로 유지 관리합니다.
_RECENT = deque(maxlen=200)

class Detection(BaseModel):
    """
    드론 감지 객체에 대한 데이터 모델을 정의하는 Pydantic 클래스입니다.
    API 요청/응답 데이터의 유효성 검사(Validation) 및 직렬화/역직렬화(Serialization/Deserialization)를 자동 처리합니다.

    Attributes:
        stream_id (str): 감지 데이터를 전송한 드론 스트림의 고유 ID. (예: 'drone-1')
        cls (str): 감지된 객체의 클래스 이름. (예: 'person', 'smoke', 'fire')
        conf (float): 감지 신뢰도 (0.0 ~ 1.0). 데이터 품질 확인 및 필터링에 사용됩니다.
        bbox (List[float] | None): 감지된 객체의 경계 상자(Bounding Box) 좌표. [x1, y1, x2, y2] 형식일 수 있습니다.
        ts (datetime): 감지 데이터가 생성된 UTC 시간 스탬프.
    """
    stream_id: str = Field(..., examples=["drone-1"])
    cls: str = Field(..., examples=["person","smoke","fire"])
    conf: float = Field(..., ge=0, le=1) # 0.0보다 크거나 같고 1.0보다 작거나 같은 값으로 제한합니다.
    bbox: List[float] | None = None
    # default_factory를 사용하여 요청 수신 시 UTC 타임존의 현재 시간을 기본값으로 자동 설정합니다.
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

@router.post("/push")
def push_detection(det: Detection):
    """
    **새로운 드론 감지 데이터를 수신하여 처리합니다.**

    이 엔드포인트는 드론이나 엣지 디바이스로부터 HTTP POST 요청을 통해 실시간 감지 데이터를 받습니다.

    Parameters:
        det (Detection): 요청 본문(Request Body)으로부터 유효성이 검증된 감지 객체 데이터입니다.

    Return Value:
        Dict: 성공 여부를 나타내는 JSON 응답 `{"ok": True}`를 반환합니다.
    """
    # ✅ B3: 시스템 운영 메트릭 카운트
    # 감지 이벤트가 발생할 때마다 METRICS 서비스를 통해 해당 횟수를 기록합니다.
    # 이는 시스템의 처리량(Throughput) 및 드론 활동을 모니터링하는 데 중요합니다.
    METRICS.note_detection()

    # Pydantic 모델을 Python Dict 타입으로 변환합니다.
    item: Dict = det.model_dump()
    
    # 최근 감지 데이터 큐의 맨 앞(가장 최근)에 항목을 추가합니다.
    _RECENT.appendleft(item)
    
    # 웹소켓을 통해 실시간 관제 클라이언트(프론트엔드)에게 감지 데이터를 브로드캐스트합니다.
    # 데이터는 JSON 문자열로 직렬화되며, `default=str`은 datetime 객체와 같은 기본 타입이 아닌 객체를 문자열로 안전하게 변환합니다.
    broadcast_detection(json.dumps(item, default=str))
    
    return {"ok": True}

@router.get("/recent")
def recent(limit: int = 50):
    """
    **가장 최근에 기록된 감지 목록을 조회합니다.**
    이 엔드포인트는 관제 시스템 대시보드 초기 로딩 또는 기록 조회를 위해 사용됩니다.
    
    Parameters:
        limit (int): 반환할 감지 기록의 최대 개수 (기본값: 50).

    Return Value:
        List: 최근 감지 기록 목록 (최대 200개, 요청된 limit 범위 내).
    """
    # _RECENT Deque에서 지정된 limit만큼의 슬라이스를 가져옵니다.
    # max(1, min(limit, 200)) 로직을 통해 limit 값을 1과 200 사이로 안전하게 제한합니다.
    # 이는 불필요하게 많은 데이터를 요청하는 것을 방지하고, 최소 1개의 결과를 보장합니다.
    return list(_RECENT)[:max(1, min(limit, 200))]
