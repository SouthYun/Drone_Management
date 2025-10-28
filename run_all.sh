#!/bin/bash
# run_all.sh
# ---------------------------------------------
# DrownI All-in-One Launcher
# ---------------------------------------------

echo "[DrownI] Starting full stack..."
cd "$(dirname "$0")"

# 1️⃣ MQTT Broker (백그라운드)
echo "[MQTT] Starting broker..."
mosquitto -d

# 2️⃣ FastAPI 서버
echo "[SERVER] Launching API server..."
uvicorn server.api.ingest:app --host 0.0.0.0 --port 8000 --reload &
SERVER_PID=$!

# 3️⃣ YOLO AI 모듈
echo "[AI] Launching video inference service..."
python3 ai/video_infer_yolo.py &
AI_PID=$!

# 4️⃣ Frontend (선택)
if [ -d "web" ]; then
  echo "[WEB] Starting frontend (React)..."
  cd web && npm run dev &
  WEB_PID=$!
  cd ..
fi

# 상태 확인
echo "[DrownI] Server PID=$SERVER_PID, AI PID=$AI_PID, Web PID=$WEB_PID"
echo "[DrownI] System running. Press Ctrl+C to stop."

# 프로세스 유지
wait
