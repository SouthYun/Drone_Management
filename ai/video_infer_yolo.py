# ai/video_infer_yolo.py
"""
YOLO Video Detection Service
----------------------------
드론 영상(HLS, RTSP, mp4)을 YOLO로 실시간 분석해
사람/불/연기 등의 탐지 결과를 /detections/push 로 서버에 전송한다.
"""

import cv2
import time
import json
import requests
from datetime import datetime, timezone
from ultralytics import YOLO

API = "http://127.0.0.1:8000/detections/push"  # 서버 주소
STREAM_URL = "video.mp4"  # mp4 or RTSP/HLS 스트림
MODEL_PATH = "yolov8n.pt"  # 기본 모델 (Ultralytics 제공)
STREAM_ID = "drone-001"

# YOLO 모델 로드
model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(STREAM_URL)
if not cap.isOpened():
    print(f"[ERROR] Unable to open video source: {STREAM_URL}")
    exit(1)

print(f"[AI] YOLO started on {STREAM_URL}")
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 모델 추론
    results = model(frame, verbose=False)

    # 탐지 결과를 서버로 전송
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            if conf < 0.5:
                continue

            # 클래스 이름
            cls_name = model.names[cls_id]
            # bbox 정규화 (x,y,w,h → 0~1)
            xywh = box.xywh[0].cpu().numpy()
            h, w = frame.shape[:2]
            bbox = [float(xywh[0]/w), float(xywh[1]/h), float(xywh[2]/w), float(xywh[3]/h)]

            payload = {
                "stream_id": STREAM_ID,
                "cls": cls_name,
                "conf": round(conf, 3),
                "bbox": bbox,
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            try:
                requests.post(API, json=payload, timeout=3)
            except Exception as e:
                print(f"[WARN] push failed: {e}")

    # (선택) 화면 표시
    cv2.imshow("YOLO Detection", frame)
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
print("[AI] Stopped")
