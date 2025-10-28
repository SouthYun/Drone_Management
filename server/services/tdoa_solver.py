# server/services/tdoa_solver.py
"""
TDOA Solver (Time Difference of Arrival)
----------------------------------------
여러 센서로부터 도달 시각 차이를 기반으로
사운드 이벤트의 대략적 위치를 계산하는 모듈.

초기 버전: 단순 가중 평균(mock solver)
"""

from typing import List, Dict, Tuple

# 예시 센서 좌표 (추후 DB 또는 설정파일로 관리)
SENSOR_POSITIONS = {
    "sensor-001": (37.2771, 127.7352),
    "sensor-002": (37.2780, 127.7335),
    "sensor-003": (37.2765, 127.7340),
    "sensor-004": (37.2775, 127.7360),
}


def estimate_location(arrivals: List[Dict]) -> Tuple[float, float]:
    """
    arrivals 예시:
    [
      {"sensor_id": "sensor-001", "delay": 0.000},
      {"sensor_id": "sensor-002", "delay": 0.003},
      {"sensor_id": "sensor-003", "delay": 0.001}
    ]

    return: (lat, lon)
    """
    valid = [a for a in arrivals if a["sensor_id"] in SENSOR_POSITIONS]
    if not valid:
        raise ValueError("유효한 센서 데이터가 없습니다.")

    # delay 가 짧을수록 소리에 더 가까움 → 가중치 반비례
    weights, lats, lons = [], [], []
    for a in valid:
        sid = a["sensor_id"]
        lat, lon = SENSOR_POSITIONS[sid]
        w = 1.0 / (a["delay"] + 1e-6)
        weights.append(w)
        lats.append(lat * w)
        lons.append(lon * w)

    total_w = sum(weights)
    est_lat = sum(lats) / total_w
    est_lon = sum(lons) / total_w
    return round(est_lat, 6), round(est_lon, 6)


if __name__ == "__main__":
    mock_data = [
        {"sensor_id": "sensor-001", "delay": 0.0},
        {"sensor_id": "sensor-002", "delay": 0.002},
        {"sensor_id": "sensor-003", "delay": 0.004},
    ]
    print("[TEST] Estimated Location:", estimate_location(mock_data))
