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

API_BASE = "http://127.0.0.1:8000"  # 필요 시 환경변수로 교체
HEARTBEAT_TIMEOUT = 60              # 초 단위: 센서 미응답 허용 시간
LOW_BATTERY_THRESHOLD = 3.5         # V 기준
MISSION_TIMEOUT = 10 * 60           # 10분 (드론 임무 최대 지속 시간)
CHECK_INTERVAL = 30                 # 주기 (초)

# 최근 센서 하트비트 기록
SENSOR_STATUS: Dict[str, float] = {}
# 드론 임무 상태
DRONE_MISSION_START: float | None = None
DRONE_MISSION_ID: str | None = None


# --------------------------------------------------------
# 센서 관련
# --------------------------------------------------------
def update_sensor_heartbeat(sensor_id: str, battery: float):
    """센서가 이벤트 전송 시 마지막 수신시각 갱신"""
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


# --------------------------------------------------------
# 드론 관련
# --------------------------------------------------------
def mark_mission_start(mission_id: str):
    """드론이 미션을 수령한 시점 기록"""
    global DRONE_MISSION_START, DRONE_MISSION_ID
    DRONE_MISSION_START = time.time()
    DRONE_MISSION_ID = mission_id
    print(f"[DRONE] Mission START id={mission_id} at {DRONE_MISSION_START}")


def mark_mission_end(mission_id: str | None = None, reason: str = "ack"):
    """미션 종료(정상 완료/중단/RTL)"""
    global DRONE_MISSION_START, DRONE_MISSION_ID
    print(f"[DRONE] Mission END id={mission_id or DRONE_MISSION_ID} reason={reason}")
    DRONE_MISSION_START = None
    DRONE_MISSION_ID = None


async def monitor_drone():
    """드론 임무 감시 및 자동 복귀"""
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
                mark_mission_end(DRONE_MISSION_ID, reason="timeout")
        await asyncio.sleep(CHECK_INTERVAL)


# --------------------------------------------------------
# 실행 루프
# --------------------------------------------------------
async def run_failsafe_monitor():
    """센서 + 드론 감시 태스크 병렬 실행"""
    print("[Failsafe] Monitor started at", datetime.now(timezone.utc).isoformat())
    await asyncio.gather(monitor_sensors(), monitor_drone())


if __name__ == "__main__":
    asyncio.run(run_failsafe_monitor())
