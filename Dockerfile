# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 필수 패키지 설치
RUN apt-get update && apt-get install -y git ffmpeg libgl1-mesa-glx mosquitto && rm -rf /var/lib/apt/lists/*

# Python 패키지
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY . .

EXPOSE 8000 1883

# 실행 시 스크립트 호출
CMD ["bash", "run_all.sh"]
