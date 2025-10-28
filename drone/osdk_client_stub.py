# drone/osdk_client_stub.py
"""
OSDK 클라이언트 스텁 (폴링 방식)
- 서버의 /missions/next에서 웨이포인트를 가져와 임무 수행 시뮬레이션.
- 완료 시 /missions/ack 로 보고.
"""
import os
import time
import math
import requests
from typing import Dict

API = os.getenv("DROWNI_API", "http://127.0.0.1:8000")


def fetch_next_waypoint() -> Dict | None:
    r = requests.get(f"{API}/missions/next", timeout=5)
    if not r.ok:
        return None
    wp = r.json().get("waypoint")
    if not wp:
        return None
    return wp


def simulate_flight(wp: Dict):
    lat, lon = wp["lat"], wp["lon"]
    alt, spd = wp["alt"], wp["speed_mps"]
    loiter = wp.get("loiter_sec", 0.0)

    print(f"[DRONE] TAKEOFF → target=({lat:.6f}, {lon:.6f}), alt={alt}m, speed={spd}m/s")

    # 단순 거리 근사
    def deg2m_lat(d): return d * 111_000.0
    def deg2m_lon(d, phi): return d * 111_000.0 * math.cos(math.radians(phi))
    dist_m = math.hypot(deg2m_lat(lat), deg2m_lon(lon, lat))
    travel_sec = min(max(dist_m / max(spd, 0.1), 1.0), 15.0)

    print(f"[DRONE] ENROUTE ~{travel_sec:.1f}s")
    time.sleep(travel_sec)

    if loiter > 0:
        print(f"[DRONE] LOITER {loiter:.1f}s")
        time.sleep(min(loiter, 10.0))

    print("[DRONE] RTL (Return-To-Launch)")
    time.sleep(1.0)
    print("[DRONE] MISSION COMPLETE")

    # ✅ 완료 보고
    try:
        requests.post(f"{API}/missions/ack",
                      json={"mission_id": wp["id"], "reason": "completed"},
                      timeout=5)
    except requests.RequestException:
        pass


def main():
    print(f"[DRONE] polling {API} ... (Ctrl+C to stop)")
    while True:
        try:
            wp = fetch_next_waypoint()
            if not wp:
                time.sleep(2.0)
                continue
            simulate_flight(wp)
        except KeyboardInterrupt:
            print("\n[DRONE] STOP")
            break
        except Exception as e:
            print(f"[DRONE] error: {e}")
            time.sleep(2.0)


if __name__ == "__main__":
    main()
