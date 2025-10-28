# server/api/realtime.py
import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/realtime", tags=["realtime"])

# 구독 큐
_log_subs: list[asyncio.Queue] = []
_det_subs: list[asyncio.Queue] = []
_status_subs: list[asyncio.Queue] = []
_event_subs: list[asyncio.Queue] = []

async def _gen(q: asyncio.Queue):
    try:
        while True:
            msg = await q.get()
            yield f"data: {msg}\n\n"
    except asyncio.CancelledError:
        pass

@router.get("/logs")
async def stream_logs(request: Request):
    q = asyncio.Queue(); _log_subs.append(q)
    return StreamingResponse(_gen(q), media_type="text/event-stream")

@router.get("/detections")
async def stream_detections(request: Request):
    q = asyncio.Queue(); _det_subs.append(q)
    return StreamingResponse(_gen(q), media_type="text/event-stream")

@router.get("/status")
async def stream_status(request: Request):
    q = asyncio.Queue(); _status_subs.append(q)
    return StreamingResponse(_gen(q), media_type="text/event-stream")

@router.get("/events")
async def stream_events(request: Request):
    q = asyncio.Queue(); _event_subs.append(q)
    return StreamingResponse(_gen(q), media_type="text/event-stream")

def broadcast_log(message: str):
    for q in _log_subs: q.put_nowait(message)

def broadcast_detection(message: str):
    for q in _det_subs: q.put_nowait(message)

def broadcast_status(message: str):
    for q in _status_subs: q.put_nowait(message)

def broadcast_event(message: str):
    for q in _event_subs: q.put_nowait(message)
