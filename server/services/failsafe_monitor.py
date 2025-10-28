# server/services/failsafe_monitor.py
"""
Failsafe Monitor
----------------
센서·드론 상태를 주기적으로 감시하여 다음을 수행:
 - 센서 하트비트(연결상태) 확인
 - 배터리 저전압 감지
 - 임무 장기 지속 감시
 - 이상 발생 시 자동 복귀(Return-To-Launch) 명령 전송
"""

import asyncio
import time
import requests
from datetime import datetime, timezone
from typing import Dict

API_BASE = "http://127.0.0.1:8000"  # 필요 시 환경변수로 교체 가능
HEARTBEAT_TIMEOUT = 60              # 초 단위: 센서 미응답 허용 시간
LOW_BATTERY_THRESHOLD = 3.5         # V 기준
MISSION_TIMEOUT = 10 * 60           # 10분 (드론 임무 최대 지속 시간)
CHECK_INTERVAL = 30                 # 주기 (초)

# 최근 센서 하트비트 기록
SENSOR_STATUS: Dict[str, float] = {}
# 드론 임무 시작 시각 (가짜 상태)
DRONE_MISSION_START: float | None = None


def update_sensor_heartbeat(sensor_id: str, battery: float):
    """센서가 이벤트 전송 시 호출해 마지막 수신시각 갱신."""
    SENSOR_STATUS[sensor_id] = time.time()
    if battery < LOW_BATTERY_THRESHOLD:
        print(f"[⚠️][{sensor_id}] Low battery: {battery:.2f}V")


async def monitor_sensors():
    """센서 하트비트 감시"""
    while True:
        now = time.time()
        for sid, last_seen in list(SENSOR_STATUS.items()):
            if now - last_seen > HEARTBEAT_TIMEOUT:
                print(f"[⚠️][{sid}] Heartbeat lost for {int(now - last_seen)}s")
        await asyncio.sleep(CHECK_INTERVAL)


async def monitor_drone():
    """드론 임무 감시"""
    global DRONE_MISSION_START
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
                DRONE_MISSION_START = None
        await asyncio.sleep(CHECK_INTERVAL)


async def run_failsafe_monitor():
    """센서 + 드론 감시 태스크를 병렬로 실행"""
    print("[Failsafe] Monitor started at", datetime.now(timezone.utc).isoformat())
    await asyncio.gather(monitor_sensors(), monitor_drone())


if __name__ == "__main__":
    # 단독 실행 (개발용)
    asyncio.run(run_failsafe_monitor())
