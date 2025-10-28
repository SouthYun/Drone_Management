# server/api/realtime.py
"""
서버 로그 실시간 스트리밍 (SSE)
--------------------------------
- 클라이언트는 /realtime/logs 로 연결
- 새 로그가 생길 때마다 즉시 전송
"""

import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/realtime", tags=["realtime"])

# 간단한 pub/sub 구조 (메모리 기반)
_subscribers: list[asyncio.Queue] = []

async def event_generator(queue: asyncio.Queue):
    try:
        while True:
            msg = await queue.get()
            yield f"data: {msg}\n\n"
    except asyncio.CancelledError:
        pass

@router.get("/logs")
async def stream_logs(request: Request):
    """서버 로그 스트림 (text/event-stream)"""
    queue: asyncio.Queue = asyncio.Queue()
    _subscribers.append(queue)
    async def cleanup():
        _subscribers.remove(queue)
    # 클라이언트가 연결 종료할 때 정리
    request.add_event_handler("shutdown", cleanup)
    return StreamingResponse(event_generator(queue), media_type="text/event-stream")

def broadcast_log(message: str):
    """다른 API에서 새 로그 발생 시 호출"""
    for q in _subscribers:
        q.put_nowait(message)
