# ai/video_infer_yolo.py — MVP: 랜덤 탐지 푸시 (실제 YOLO 전 단계)
import os, time, random, requests
from datetime import datetime, timezone

API = os.getenv("DROWNI_API", "http://127.0.0.1:8000")
STREAM_ID = os.getenv("STREAM_ID", "drone-1")

CLASSES = ["person", "smoke", "fire"]

def push(cls: str, conf: float):
    payload = {
        "stream_id": STREAM_ID,
        "cls": cls,
        "conf": round(conf, 3),
        "bbox": [random.random()*0.7, random.random()*0.7, 0.2, 0.2],
        "ts": datetime.now(timezone.utc).isoformat()
    }
    r = requests.post(f"{API}/detections/push", json=payload, timeout=5)
    print(r.status_code, r.json())

if __name__ == "__main__":
    print("[infer] sending mock detections… Ctrl+C to stop")
    try:
        while True:
            push(random.choice(CLASSES), random.uniform(0.6, 0.98))
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[infer] stopped")
