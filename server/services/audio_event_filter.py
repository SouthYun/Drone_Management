# server/services/audio_event_filter.py

THRESHOLD = 0.90  # 요구사항: prob_help ≥ 0.90

def is_event_accepted(prob_help: float) -> bool:
    """
    도움 요청 확률이 기준(0.90) 이상인지 판정.
    """
    return prob_help >= THRESHOLD
