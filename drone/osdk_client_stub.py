# drone/osdk_client_stub.py
"""
OSDK 클라이언트 스텁
--------------------
서버에서 미션을 받아 시뮬레이션하며, 이동 중 주기적으로 위치 업데이트 전송.
"""
import os, time, math, random, requests
from typing import Dict

API = os.getenv("DROWNI_API", "http://127.0.0.1:8000")

def fetch_next_waypoint() -> Dict | None:
    try:
        r = requests.get(f"{API}/missions/next", timeout=5)
        if not r.ok:
            return None
        return r.json().get("waypoint")
    except Exception:
        return None

def send_tracker_update(lat: float, lon: float, alt: float, spd: float):
    try:
        requests.post(f"{API}/tracker/update", json={
            "drone_id": "drone-001",
            "lat": lat, "lon": lon,
            "alt": alt, "speed_mps": spd,
            "battery": round(random.uniform(3.6, 4.2), 2)
        }, timeout=3)
    except requests.RequestException:
        pass

def simulate_flight(wp: Dict):
    lat, lon, alt, spd = wp["lat"], wp["lon"], wp["alt"], wp["speed_mps"]
    loiter = wp.get("loiter_sec", 0.0)
    print(f"[DRONE] TAKEOFF → target=({lat:.6f},{lon:.6f}), alt={alt}m")

    def deg2m_lat(d): return d * 111_000.0
    def deg2m_lon(d, phi): return d * 111_000.0 * math.cos(math.radians(phi))
    dist_m = math.hypot(deg2m_lat(lat), deg2m_lon(lon, lat))
    travel_sec = min(max(dist_m / max(spd, 0.1), 1.0), 15.0)

    for i in range(10):
        frac = (i + 1) / 10.0
        send_tracker_update(lat * frac, lon * frac, alt * frac, spd)
        time.sleep(travel_sec / 10.0)

    if loiter > 0:
        print(f"[DRONE] LOITER {loiter:.1f}s")
        time.sleep(min(loiter, 10.0))

    print("[DRONE] RTL → Base"); send_tracker_update(lat, lon, 0, 0)
    time.sleep(1.0)
    print("[DRONE] MISSION COMPLETE")

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
