# server/api/metrics.py
from fastapi import APIRouter
from server.services.metrics_collector import METRICS

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/summary")
def summary():
    return METRICS.snapshot()
