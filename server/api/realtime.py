# server/api/realtime.py  — 일부 추가/수정
import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/realtime", tags=["realtime"])

# 기존 로그용
_log_subs: list[asyncio.Queue] = []
# ▶ 탐지용 추가
_det_subs: list[asyncio.Queue] = []

async def _event_gen(q: asyncio.Queue):
    try:
        while True:
            msg = await q.get()
            yield f"data: {msg}\n\n"
    except asyncio.CancelledError:
        pass

@router.get("/logs")
async def stream_logs(request: Request):
    q: asyncio.Queue = asyncio.Queue()
    _log_subs.append(q)
    return StreamingResponse(_event_gen(q), media_type="text/event-stream")

def broadcast_log(message: str):
    for q in _log_subs:
        q.put_nowait(message)

# ▶ 탐지 SSE 엔드포인트
@router.get("/detections")
async def stream_detections(request: Request):
    q: asyncio.Queue = asyncio.Queue()
    _det_subs.append(q)
    return StreamingResponse(_event_gen(q), media_type="text/event-stream")

# ▶ 탐지 브로드캐스트 함수
def broadcast_detection(message: str):
    for q in _det_subs:
        q.put_nowait(message)
