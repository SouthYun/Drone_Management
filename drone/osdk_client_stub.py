# drone/osdk_client_stub.py

"""
OSDK (Onboard Software Development Kit) 클라이언트 스텁
------------------------------------------------------
이 스크립트는 실제 드론의 OSDK 클라이언트를 모사(stubbing)하는 역할을 수행합니다.
주요 기능은 관제 서버로부터 비행 임무(Waypoint)를 수신하고, 
해당 임무를 시뮬레이션하며, 비행 중 주기적으로 드론의 위치 및 상태 정보를 서버에 보고하는 것입니다.
이는 관제 시스템의 백엔드 임무 할당 및 위치 추적 로직을 검증하는 데 활용됩니다.
"""
import os, time, math, random, requests
from typing import Dict

# --- 1. 시스템 환경 설정 ---
# 서버 API 주소 설정: 환경 변수 'DROWNI_API'를 우선 사용하고, 없으면 로컬 기본값 사용
API = os.getenv("DROWNI_API", "http://127.0.0.1:8000")

# --- 2. 서버 통신 함수 ---

def fetch_next_waypoint() -> Dict | None:
    """
    관제 서버로부터 다음 비행 임무(Waypoint)를 요청합니다. (임무 Polling)
    
    Returns:
        Dict | None: 다음 임무 정보를 담은 딕셔너리 또는 임무가 없을 경우 None
    """
    try:
        # GET 요청을 통해 서버의 '/missions/next' 엔드포인트에서 임무 정보를 가져옵니다.
        r = requests.get(f"{API}/missions/next", timeout=5)
        if not r.ok:
            # HTTP 응답 코드가 200(OK)이 아닐 경우 임무 없음으로 간주
            return None
        # 응답 JSON에서 'waypoint' 키의 값을 추출하여 반환
        return r.json().get("waypoint")
    except Exception:
        # 네트워크 오류 등 예외 발생 시 임무 없음으로 처리
        return None

def send_tracker_update(lat: float, lon: float, alt: float, spd: float):
    """
    드론의 현재 상태(위치, 속도, 배터리)를 관제 서버에 주기적으로 업데이트합니다.
    
    Args:
        lat (float): 현재 위도 (Latitude)
        lon (float): 현재 경도 (Longitude)
        alt (float): 현재 고도 (Altitude)
        spd (float): 현재 속도 (Speed in m/s)
    """
    try:
        # POST 요청을 통해 '/tracker/update' 엔드포인트로 드론 상태 정보를 전송합니다.
        requests.post(f"{API}/tracker/update", json={
            "drone_id": "drone-001", # 드론 고유 식별자
            "lat": lat, "lon": lon,
            "alt": alt, "speed_mps": spd,
            # 배터리 잔량은 시뮬레이션을 위해 랜덤 값 (3.6V ~ 4.2V)으로 설정
            "battery": round(random.uniform(3.6, 4.2), 2) 
        }, timeout=3)
    except requests.RequestException:
        # 요청 실패 시 예외 처리 (Silent Failure)
        pass

# --- 3. 비행 시뮬레이션 로직 ---

def simulate_flight(wp: Dict):
    """
    수신된 웨이포인트 임무에 따라 드론의 비행 과정을 시뮬레이션하고 상태를 보고합니다.
    
    Args:
        wp (Dict): 수행할 웨이포인트 임무 데이터
    """
    # 임무 데이터 파싱
    lat, lon, alt, spd = wp["lat"], wp["lon"], wp["alt"], wp["speed_mps"]
    loiter = wp.get("loiter_sec", 0.0) # 선회 시간 (Loiter Time) - 기본값 0

    print(f"[DRONE] TAKEOFF → target=({lat:.6f},{lon:.6f}), alt={alt}m")

    # --- 지리 좌표계 변환 함수 (거리 계산) ---
    # 위도/경도 차이를 미터 단위로 변환하는 근사 함수
    def deg2m_lat(d): return d * 111_000.0 # 위도 1도당 약 111km
    def deg2m_lon(d, phi): return d * 111_000.0 * math.cos(math.radians(phi)) 
    
    # 목표 지점까지의 2D 거리(미터) 계산 (대략적인 평면 거리)
    dist_m = math.hypot(deg2m_lat(lat), deg2m_lon(lon, lat))
    # 비행 소요 시간 계산: 거리 / 속도. 최소 1초, 최대 15초로 제한하여 시뮬레이션 속도 제어
    travel_sec = min(max(dist_m / max(spd, 0.1), 1.0), 15.0)

    # --- 웨이포인트 이동 시뮬레이션 ---
    for i in range(10): # 총 10단계로 나누어 이동을 시뮬레이션
        frac = (i + 1) / 10.0 # 현재 이동 진행률 (0.1, 0.2, ..., 1.0)
        
        # 현재 위치를 출발지-목적지 사이의 비율(frac)로 선형 보간하여 서버에 업데이트
        send_tracker_update(lat * frac, lon * frac, alt * frac, spd) 
        time.sleep(travel_sec / 10.0) # 한 단계 이동에 해당하는 시간만큼 대기

    # --- 선회 (Loiter) 시뮬레이션 ---
    if loiter > 0:
        print(f"[DRONE] LOITER {loiter:.1f}s")
        time.sleep(min(loiter, 10.0)) # 최대 10초로 제한하여 선회 대기

    # --- 임무 완료 및 복귀(RTL) 시뮬레이션 ---
    print("[DRONE] RTL → Base")
    # 최종 위치를 목표 위경도, 고도 0 (착륙)으로 서버에 전송
    send_tracker_update(lat, lon, 0, 0) 
    time.sleep(1.0)
    print("[DRONE] MISSION COMPLETE")

    # --- 임무 완료 서버 통보 (Acknowledgement) ---
    try:
        # '/missions/ack' 엔드포인트에 임무 완료 보고
        requests.post(f"{API}/missions/ack",
                      json={"mission_id": wp["id"], "reason": "completed"},
                      timeout=5)
    except requests.RequestException:
        pass

# --- 4. 메인 프로그램 흐름 ---

def main():
    """
    클라이언트 스텁의 메인 루프: 서버를 폴링하여 임무를 받고 처리합니다.
    """
    print(f"[DRONE] polling {API} ... (Ctrl+C to stop)")
    while True:
        try:
            # 4.1. 다음 임무 요청
            wp = fetch_next_waypoint() 
            
            if not wp:
                # 임무가 없으면 2초 대기 후 다시 요청
                time.sleep(2.0)
                continue
                
            # 4.2. 임무 시뮬레이션 및 처리
            simulate_flight(wp)
            
        except KeyboardInterrupt:
            # 사용자 입력(Ctrl+C)으로 안전하게 종료
            print("\n[DRONE] STOP")
            break
        except Exception as e:
            # 예상치 못한 기타 오류 처리
            print(f"[DRONE] error: {e}")
            time.sleep(2.0)

if __name__ == "__main__":
    main()
