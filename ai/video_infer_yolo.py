# ai/video_infer_yolo.py

"""
객체 탐지 기반 드론 영상 실시간 분석 서비스 (YOLO Inference Service)

본 스크립트는 드론에서 전송되는 비디오 스트림 (HLS, RTSP, mp4 등)을 
Ultralytics YOLOv8 모델을 활용하여 실시간으로 분석하는 모듈입니다.
탐지된 객체 (예: 사람, 화재, 연기 등)의 정보는 정규화된 좌표와 함께 
지정된 서버 API 엔드포인트로 즉시 전송(Push)되어 관제 시스템의 상황 인지 자료로 활용됩니다.
"""

import cv2                                  # OpenCV: 비디오 I/O 및 프레임 처리 라이브러리
import time                                 # 시간 관련 모듈
import requests                             # HTTP 통신 (서버로 탐지 결과 전송) 라이브러리
from datetime import datetime, timezone     # 타임스탬프 기록을 위한 시간 처리 모듈
from ultralytics import YOLO                # YOLO 모델 로딩 및 추론을 위한 핵심 라이브러리

# --- 1. 시스템 설정 변수 (Configuration Parameters) ---
API = "http://127.0.0.1:8000/detections/push"    # 탐지 결과를 전송할 관제 서버의 API 엔드포인트
STREAM_URL = "video.mp4"                         # 분석 대상 비디오 소스 URL 또는 파일 경로 (Source Video Stream)
MODEL_PATH = "yolov8n.pt"                        # 사용할 YOLO 모델 가중치 파일 경로 (YOLOv8 nano 모델)
STREAM_ID = "drone-001"                          # 탐지 이벤트를 식별하기 위한 드론/스트림 고유 ID

# --- 2. 모델 로드 및 초기화 ---
# Ultralytics 라이브러리를 사용하여 지정된 경로의 YOLO 모델을 메모리에 로드합니다.
# 이 모델은 모든 추론 작업에 사용됩니다.
model = YOLO(MODEL_PATH) 

# --- 3. 비디오 스트림 캡처 ---
# OpenCV를 사용하여 STREAM_URL에 해당하는 비디오 스트림을 엽니다.
cap = cv2.VideoCapture(STREAM_URL)

# 비디오 소스 열림 여부 확인 및 예외 처리
if not cap.isOpened():
    print(f"[ERROR] Unable to open video source: {STREAM_URL}")
    exit(1) # 스트림 연결 실패 시 프로그램 종료

print(f"[AI] YOLO inference service started on {STREAM_URL}")

# --- 4. 메인 추론 루프 (Main Inference Loop) ---
while True:
    # 4.1. 프레임 읽기
    ret, frame = cap.read() # ret: 성공 여부, frame: 읽어온 이미지 데이터
    
    # 스트림 종료 또는 프레임 읽기 실패 시 루프 탈출
    if not ret: 
        break 

    # 4.2. 객체 탐지 (Inference)
    # 현재 프레임에 대해 YOLO 모델을 실행합니다. (추론 수행)
    results = model(frame, verbose=False) # verbose=False로 콘솔 출력 최소화

    # 4.3. 탐지 결과 반복 처리
    for r in results: # 하나의 프레임에 대한 결과
        for box in r.boxes: # 탐지된 개별 객체의 바운딩 박스 정보
            
            cls_id = int(box.cls[0])    # 탐지된 객체의 클래스 ID (정수)
            conf = float(box.conf[0])   # 해당 탐지의 신뢰도(Confidence Score)
            
            # 신뢰도 임계값 필터링 (0.5 미만은 낮은 품질로 판단하여 무시)
            if conf < 0.5:
                continue

            # 클래스 이름 추출 (예: 0 -> 'person')
            cls_name = model.names[cls_id] 
            
            # 바운딩 박스 좌표 추출: (중앙 x, 중앙 y, 너비, 높이) 형식의 픽셀 값
            xywh = box.xywh[0].cpu().numpy()
            
            # 프레임의 크기 (높이 h, 너비 w) 획득
            h, w = frame.shape[:2]
            
            # 4.4. 좌표 정규화 (Normalization)
            # 픽셀 좌표를 0.0부터 1.0 사이의 값으로 정규화하여 해상도 독립성을 확보
            bbox = [
                float(xywh[0]/w), # 정규화된 중앙 X
                float(xywh[1]/h), # 정규화된 중앙 Y
                float(xywh[2]/w), # 정규화된 너비 W
                float(xywh[3]/h)  # 정규화된 높이 H
            ]

            # 4.5. 서버 전송용 Payload 구성
            payload = {
                "stream_id": STREAM_ID,                       # 드론 식별자
                "cls": cls_name,                              # 탐지된 객체 클래스
                "conf": round(conf, 3),                       # 신뢰도 (소수점 셋째 자리까지 반올림)
                "bbox": bbox,                                 # 정규화된 바운딩 박스 좌표
                "ts": datetime.now(timezone.utc).isoformat(), # UTC 기준 ISO 8601 형식 타임스탬프
            }
            
            # 4.6. 서버로 탐지 결과 전송 (HTTP POST Request)
            try:
                # 관제 서버 API로 JSON 데이터를 전송하며, 타임아웃을 3초로 설정합니다.
                requests.post(API, json=payload, timeout=3)
            except Exception as e:
                # 네트워크 오류 등 서버 전송 실패 시 경고 출력
                print(f"[WARN] Detection push failed: {e}")

    # 4.7. (선택적) 디버깅 및 시각화를 위한 화면 표시
    cv2.imshow("YOLO Detection", frame)
    # ESC 키 (아스키 코드 27) 입력 시 루프 종료
    if cv2.waitKey(1) == 27:
        break

# --- 5. 자원 해제 (Resource Cleanup) ---
cap.release()               # 비디오 캡처 객체 해제
cv2.destroyAllWindows()     # OpenCV 창 모두 닫기
print("[AI] Stopped")
