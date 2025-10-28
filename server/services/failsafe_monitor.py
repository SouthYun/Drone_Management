# server/services/failsafe_monitor.py
import asyncio, time, requests, json
from datetime import datetime, timezone
from typing import Dict
from server.api.realtime import broadcast_status

API_BASE = "http://127.0.0.1:8000"
HEARTBEAT_TIMEOUT = 60
LOW_BATTERY_THRESHOLD = 3.5
MISSION_TIMEOUT = 10 * 60
CHECK_INTERVAL = 30

SENSOR_STATUS: Dict[str, float] = {}
DRONE_MISSION_START: float | None = None
DRONE_MISSION_ID: str | None = None

def update_sensor_heartbeat(sensor_id: str, battery: float):
    SENSOR_STATUS[sensor_id] = time.time()
    if battery < LOW_BATTERY_THRESHOLD:
        print(f"[⚠️][{sensor_id}] Low battery: {battery:.2f}V")

async def monitor_sensors():
    while True:
        now = time.time()
        for sid, last_seen in list(SENSOR_STATUS.items()):
            if now - last_seen > HEARTBEAT_TIMEOUT:
                print(f"[⚠️][{sid}] Heartbeat lost for {int(now - last_seen)}s")
        await asyncio.sleep(CHECK_INTERVAL)

def mark_mission_start(mission_id: str):
    global DRONE_MISSION_START, DRONE_MISSION_ID
    DRONE_MISSION_START = time.time(); DRONE_MISSION_ID = mission_id
    print(f"[DRONE] Mission START id={mission_id} at {DRONE_MISSION_START}")

def mark_mission_end(mission_id: str | None = None, reason: str = "ack"):
    global DRONE_MISSION_START, DRONE_MISSION_ID
    print(f"[DRONE] Mission END id={mission_id or DRONE_MISSION_ID} reason={reason}")
    DRONE_MISSION_START = None; DRONE_MISSION_ID = None

async def monitor_drone():
    global DRONE_MISSION_START, DRONE_MISSION_ID
    while True:
        if DRONE_MISSION_START:
            elapsed = time.time() - DRONE_MISSION_START
            if elapsed > MISSION_TIMEOUT:
                print(f"[⚠️][DRONE] Mission timeout ({elapsed:.0f}s) → auto RTL")
                try:
                    r = requests.post(f"{API_BASE}/drone/rtl", timeout=5)
                    print("[AUTO-RTL]", r.status_code, r.text)
                except Exception as e:
                    print("[AUTO-RTL ERROR]", e)
                broadcast_status(json.dumps({"type":"mission_timeout_rtl",
                                             "mission_id":DRONE_MISSION_ID,
                                             "ts":datetime.now(timezone.utc).isoformat()}))
                mark_mission_end(DRONE_MISSION_ID, reason="timeout")
        await asyncio.sleep(CHECK_INTERVAL)

async def run_failsafe_monitor():
    print("[Failsafe] Monitor started at", datetime.now(timezone.utc).isoformat())
    await asyncio.gather(monitor_sensors(), monitor_drone())
