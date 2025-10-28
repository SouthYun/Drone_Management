# tools/sensor_sim.py
import time, random, requests
from datetime import datetime, timezone

URL = "http://127.0.0.1:8000/ingest/audio"
SENSOR_ID = "sensor-001"

def one_shot(prob: float | None = None):
    prob_help = prob if prob is not None else round(random.uniform(0.6, 0.99), 3)
    payload = {
        "sensor_id": SENSOR_ID,
        "prob_help": prob_help,
        "ts": datetime.now(timezone.utc).isoformat(),
        "battery": round(random.uniform(3.4, 4.2), 2),
        "features": {"rms": round(random.random(), 3)},
        "meta": {"fw": "1.0.0", "lat": 37.2775, "lon": 127.7355},
    }
    r = requests.post(URL, json=payload, timeout=5)
    print(f"[{prob_help:.2f}] → {r.status_code}: {r.json()}")

if __name__ == "__main__":
    print("[sensor_sim] Sending 10 events...")
    for _ in range(10):
        one_shot()
        time.sleep(0.5)
    print("[sensor_sim] Done.")
