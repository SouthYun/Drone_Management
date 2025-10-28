# drone/osdk_client_stub.py
"""
OSDK 클라이언트 스텁 (폴링 방식)
- 서버에서 /missions/next 로 웨이포인트를 가져와 '수행'하는 흉내만 냄.
- 실제 OSDK 연동 전, 서버-드론 흐름 점검용.

실행:
  python drone/osdk_client_stub.py
환경변수:
  DROWNI_API=http://127.0.0.1:8000  (기본값)
"""
import os
import time
import math
import requests
from typing import Dict

API = os.getenv("DROWNI_API", "http://127.0.0.1:8000")

def fetch_next_waypoint() -> Dict | None:
    """
    /missions/next 에서 다음 임무를 가져온다.
    204(No Content)이면 None 반환.
    """
    url = f"{API}/missions/next"
    r = requests.get(url, timeout=5)
    if r.status_code == 204:
        return None
    r.raise_for_status()
    return r.json()["waypoint"]

def simulate_flight(wp: Dict):
    """
    아주 단순한 비행 시뮬레이션:
      - 이륙
      - 목표 지점으로 '이동'(시간 지연으로 대체)
      - loiter_sec만큼 체공
      - RTL
    """
    lat, lon = wp["lat"], wp["lon"]
    alt, spd = wp["alt"], wp["speed_mps"]
    loiter = wp.get("loiter_sec", 0.0)

    print(f"[DRONE] TAKEOFF → target=({lat:.6f}, {lon:.6f}), alt={alt}m, speed={spd}m/s")

    # 이동 시간 간단 추정 (위경도 차이 → 거리 근사)
    # 주의: 실제 구현은 지리좌표-거리 변환 필요. 여기선 간단 근사만.
    def deg2m_lat(d): return d * 111_000.0
    def deg2m_lon(d, phi): return d * 111_000.0 * math.cos(math.radians(phi))

    # 현재 위치를 (0,0)이라 가정 → 거리 근사
    dist_m = math.hypot(deg2m_lat(lat), deg2m_lon(lon, lat))
    travel_sec = max(1.0, dist_m / max(spd, 0.1))
    travel_sec = min(travel_sec, 15.0)  # 데모용 상한

    print(f"[DRONE] ENROUTE ~{travel_sec:.1f}s (demo)")
    time.sleep(travel_sec)

    if loiter > 0:
        print(f"[DRONE] LOITER {loiter:.1f}s")
        time.sleep(min(loiter, 10.0))  # 데모용 상한

    print("[DRONE] RTL (Return-To-Launch)")
    time.sleep(1.0)
    print("[DRONE] MISSION COMPLETE\n")

def main():
    print(f"[DRONE] polling {API} ... (Ctrl+C to stop)")
    while True:
        try:
            wp = fetch_next_waypoint()
            if not wp:
                time.sleep(1.0)
                continue
            simulate_flight(wp)
        except KeyboardInterrupt:
            print("\n[DRONE] STOP")
            break
        except requests.RequestException as e:
            print(f"[DRONE] network error: {e}")
            time.sleep(2.0)
        except Exception as e:
            print(f"[DRONE] error: {e}")
            time.sleep(2.0)

if __name__ == "__main__":
    main()
