# server/jobs/data_retention.py
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete
from server.db.models import SessionLocal, AudioEvent, Log
import os

RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "7"))

async def clean_database():
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    db = SessionLocal()
    try:
        de = db.execute(delete(AudioEvent).where(AudioEvent.ts < cutoff))
        dl = db.execute(delete(Log).where(Log.ts < cutoff))
        db.commit()
        print(f"[Retention] {datetime.now(timezone.utc).isoformat()} => "
              f"audio_events:{de.rowcount}, logs:{dl.rowcount}")
    finally:
        db.close()

async def run_scheduler(interval_hours: int = 6):
    while True:
        await clean_database()
        await asyncio.sleep(interval_hours * 3600)
