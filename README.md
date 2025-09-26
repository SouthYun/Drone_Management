## 파일구조

```
📦rescue-drone
┣ 📜README.md # 1페이지 요약(문서 허브)
┣ 📜LICENSE
┣ 📜.gitignore
┣ 📜docker-compose.yml # 로컬 데모 한번에 띄우기
┣ 📜Makefile # make up / make test / make lint 등
┣ 📂.github
┃ ┣ 📂workflows
┃ ┃ ┣ 📜ci.yml # 빌드/테스트/린트
┃ ┃ ┗ 📜docker-publish.yml # 필요 시 이미지 푸시
┃ ┗ 📜ISSUE_TEMPLATE.md / PULL_REQUEST_TEMPLATE.md
┣ 📂docs
┃ ┣ 📜architecture.md # 아키텍처/데이터 흐름(그림 포함)
┃ ┣ 📜safety_checklist.md # 지오펜스/배터리/RTL 등 안전정책
┃ ┣ 📜demo_guide.md # 평가자용 3분 시연 가이드
┃ ┣ 📜api.md # API 사용법(스니펫) + 링크(OpenAPI)
┃ ┣ 📜results.md # 실험/정확도/한계/개선점
┃ ┗ 📂imgs # 구조도/스크린샷
┣ 📂infra
┃ ┣ 📂k8s or ansible # 선택(배포 스크립트)
┃ ┗ 📜env.example # 예시 환경변수(.env는 커밋 금지)
┣ 📂server # 리눅스 서버(남윤화)
┃ ┣ 📂app # FastAPI/Express 소스
┃ ┣ 📂models # YOLO 추론 서비스
┃ ┣ 📂ingest # 음향 인제스트(UDP/MQTT/gRPC)
┃ ┣ 📂planner # 이벤트→미션 플래너(지오펜스/정책)
┃ ┣ 📂video # FFmpeg/GStreamer 수신, 파이프
┃ ┣ 📂db # SQL 스키마/마이그레이션
┃ ┣ 📂dashboards # React/Leaflet or Grafana
┃ ┣ 📜openapi.yaml # API 스키마(자동 문서화)
┃ ┣ 📂tests
┃ ┣ 📜requirements.txt or package.json
┃ ┗ 📜Dockerfile
┣ 📂osdk-client # 윈도우 OSDK 클라이언트(박재균)
┃ ┣ 📜CMakeLists.txt
┃ ┣ 📂src
┃ ┃ ┣ 📜main.cpp
┃ ┃ ┣ 📜net_client.hpp/cpp # REST/WS/MQTT
┃ ┃ ┣ 📜osdk_adapter.hpp/cpp # activation/obtain/takeoff/goto/rtl
┃ ┃ ┣ 📜state_machine.hpp/cpp # IDLE→TAKEOFF→TRANSIT→SEARCH→RTL
┃ ┃ ┣ 📜geo.hpp/cpp # ENU 변환/도착판정
┃ ┃ ┗ 📜safety.hpp/cpp # 배터리/링크/지오펜스 인터락
┃ ┣ 📂config
┃ ┃ ┣ 📜userconfig.sample.txt # AppID/Key/COM/baud 예시
┃ ┃ ┗ 📜client.yaml # 서버주소/토큰/기본 고도 등
┃ ┗ 📂scripts
┃ ┗ 📜run.ps1
┣ 📂sensor-nodes # 음향 처리(양동선)
┃ ┣ 📂tdoa # GCC-PHAT, trilateration
┃ ┣ 📂firmware # ESP32/STM32 예제(옵션)
┃ ┣ 📂simulator # 가짜 이벤트 발생기(평가용)
┃ ┣ 📜requirements.txt
┃ ┗ 📜README.md
┣ 📂samples
┃ ┣ 📜postman_collection.json # 평가자 클릭용 API 모음
┃ ┣ 📂mock
┃ ┃ ┣ 📜acoustic_event.json
┃ ┃ ┗ 📜telemetry.json
┃ ┗ 📂streams
┃ ┗ 📜README.md # 테스트 스트림 명령 모음
┗ 📂scripts
┣ 📜start_demo.sh / .ps1 # 전 구성요소 한번에 실행
┗ 📜ffmpeg_push_examples.md
```
