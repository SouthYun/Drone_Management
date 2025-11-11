# server/api/admin.py

"""
Admin Control API Router
------------------------
이 모듈은 서버 관리자(Administrator)가 시스템 운영 및 유지 보수를 위해 사용하는 
특수 목적의 REST API 엔드포인트를 정의합니다. 
주요 기능으로는 시스템 상태 모니터링, 로그 초기화, 긴급 드론 복귀(RTL) 명령 등이 있습니다.
"""

import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from server.db.models import SessionLocal, Log             # 데이터베이스 세션 및 로그 모델 임포트
from server.services.metrics_collector import METRICS     # 시스템 성능 메트릭 수집기 임포트
from server.api.realtime import broadcast_status          # 실시간 웹소켓 상태 알림 함수 임포트

# 'admin' 태그와 '/admin' 프리픽스를 가진 API 라우터 인스턴스 생성
router = APIRouter(prefix="/admin", tags=["admin"]) 

# --- 의존성 주입 (Dependency Injection) 함수 ---

def get_db():
    """
    FastAPI의 의존성 주입을 위한 함수입니다. 
    요청마다 새로운 DB 세션을 생성하고, 요청 처리가 완료되면 반드시 세션을 닫습니다.
    """
    db = SessionLocal()
    try:
        yield db # 세션을 컨트롤러 함수에 제공
    finally:
        db.close() # 세션 반환 후 반드시 닫음 (Connection Pool 관리)


@router.get("/status")
def system_status():
    """
    GET /admin/status: 시스템의 현재 상태 및 성능 메트릭을 조회합니다.
    
    Returns:
        dict: 서버 시간, 현재 메트릭 스냅샷, 서버 업타임 정보
    """
    return {
        "server_time": datetime.now(timezone.utc).isoformat(), # 현재 UTC 서버 시간
        "metrics": METRICS.snapshot(), # METRICS Collector에서 수집된 성능 데이터 (CPU, 메모리 등)
        # 서버 업타임 명령 실행 (Linux/Unix 환경). Windows(nt) 환경에서는 'N/A' 반환
        "uptime": os.popen("uptime").read().strip() if os.name != "nt" else "N/A", 
    }


@router.post("/clear-logs")
def clear_logs(db: Session = Depends(get_db)):
    """
    POST /admin/clear-logs: 데이터베이스의 Log 테이블과 파일 기반의 로그를 초기화합니다.
    관리자가 시스템 정기 유지보수 시 호출합니다.
    
    Args:
        db (Session): 의존성 주입을 통해 확보된 SQLAlchemy DB 세션
        
    Returns:
        dict: 작업 성공 여부와 삭제된 로그 레코드 수
    """
    # 1. DB 로그 초기화: Log 모델에 해당하는 모든 레코드 삭제 후 커밋
    deleted = db.query(Log).delete() 
    db.commit()
    
    # 2. 파일 로그 초기화: 지정된 로그 파일의 내용을 비웁니다.
    for f in ["logs/error.log", "logs/access.log"]:
        try:
            open(f, "w").close() # 파일을 쓰기 모드("w")로 열고 즉시 닫아 내용을 비웁니다.
        except Exception:
            pass # 파일이 없거나 접근 오류 시 무시
            
    # 3. 실시간 알림: 웹소켓을 통해 클라이언트(관제 대시보드)에 로그 초기화 사실을 알림
    broadcast_status('{"type":"admin_action","message":"Logs cleared"}')
    
    return {"ok": True, "deleted": deleted}


@router.post("/rtl")
def manual_rtl():
    """
    POST /admin/rtl: 모든 드론에게 강제 복귀(Return To Launch, RTL) 명령을 수동으로 내립니다.
    긴급 상황 발생 시 관리자용 비상 제어 기능입니다.
    
    Returns:
        dict: 명령 수행 결과
    """
    # 순환 참조 방지를 위해 함수 내부에서 필요한 모듈 임포트
    from server.api.drone import return_to_launch 
    
    # DB 세션을 수동으로 생성 (Dependencies 사용 불가)
    db = SessionLocal() 
    try:
        # 드론 제어 로직을 수행하는 핵심 서비스 함수 호출
        res = return_to_launch(db) 
        
        # 실시간 알림: 웹소켓을 통해 클라이언트에게 RTL 명령 실행 사실을 알림
        broadcast_status('{"type":"admin_action","message":"Manual RTL executed"}')
        
        return {"ok": True, "action": "rtl", "result": res}
    finally:
        db.close() # 작업 완료 후 DB 세션 반드시 닫기
