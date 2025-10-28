# server/jobs/data_retention.py
"""
데이터 보존 기간 만료 자동 삭제 (Batch Job)
------------------------------------------
- 오래된 audio_events, logs, detections 데이터를 주기적으로 정리.
- 실행 방법:
    python server/jobs/data_retention.py
  또는 FastAPI startup 이벤트에서 asyncio.create_task로 주기 실행.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete
from server.db.models import SessionLocal, AudioEvent, Log
import requests
import os

# 보존 기간 설정 (일 단위)
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "7"))

async def clean_database():
    """보존 기간이 지난 레코드 삭제"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    db = SessionLocal()
    try:
        deleted_events = db.execute(delete(AudioEvent).where(AudioEvent.ts < cutoff))
        deleted_logs = db.execute(delete(Log).where(Log.ts < cutoff))
        db.commit()
        print(
            f"[Retention] {datetime.now(timezone.utc).isoformat()} "
            f"=> audio_events:{deleted_events.rowcount}, logs:{deleted_logs.rowcount}"
        )
    finally:
        db.close()

async def run_scheduler(interval_hours: int = 6):
    """6시간마다 정리 작업 반복"""
    while True:
        await clean_database()
        await asyncio.sleep(interval_hours * 3600)

if __name__ == "__main__":
    # 단독 실행 시 1회 실행
    import asyncio
    asyncio.run(clean_database())
