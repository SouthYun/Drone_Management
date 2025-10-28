# server/services/metrics_collector.py
"""
Metrics Collector
-----------------
- 오디오 이벤트/탐지/미션/RTL 등을 카운팅
- 분 단위 타임시리즈(최근 30분) 집계
"""

from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List

WINDOW_MINUTES = 30

@dataclass
class MinuteBucket:
  ts: str
  audio_events: int = 0
  detections: int = 0
  missions_enqueued: int = 0
  missions_completed: int = 0
  rtl_issued: int = 0

@dataclass
class Metrics:
  # 누적 카운터
  total_audio_events: int = 0
  total_detections: int = 0
  total_missions_enqueued: int = 0
  total_missions_completed: int = 0
  total_rtl_issued: int = 0
  # 최근 30분 타임시리즈
  series: List[MinuteBucket] = field(default_factory=list)
  # 현재 분 카운터
  cur_audio: int = 0
  cur_det: int = 0
  cur_msq: int = 0
  cur_msc: int = 0
  cur_rtl: int = 0

  def _roll_minute(self):
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0).isoformat()
    self.series.append(MinuteBucket(
      ts=now,
      audio_events=self.cur_audio,
      detections=self.cur_det,
      missions_enqueued=self.cur_msq,
      missions_completed=self.cur_msc,
      rtl_issued=self.cur_rtl,
    ))
    if len(self.series) > WINDOW_MINUTES:
      self.series.pop(0)
    self.cur_audio = self.cur_det = self.cur_msq = self.cur_msc = self.cur_rtl = 0

  def note_audio_event(self):
    self.total_audio_events += 1
    self.cur_audio += 1

  def note_detection(self):
    self.total_detections += 1
    self.cur_det += 1

  def note_mission_enqueued(self):
    self.total_missions_enqueued += 1
    self.cur_msq += 1

  def note_mission_completed(self):
    self.total_missions_completed += 1
    self.cur_msc += 1

  def note_rtl(self):
    self.total_rtl_issued += 1
    self.cur_rtl += 1

  def snapshot(self) -> Dict:
    return {
      "totals": {
        "audio_events": self.total_audio_events,
        "detections": self.total_detections,
        "missions_enqueued": self.total_missions_enqueued,
        "missions_completed": self.total_missions_completed,
        "rtl_issued": self.total_rtl_issued,
      },
      "series": [b.__dict__ for b in self.series],
      "generated_at": datetime.now(timezone.utc).isoformat(),
    }

METRICS = Metrics()

async def run_metrics_scheduler():
  # 60초마다 분 버킷 롤링
  while True:
    await asyncio.sleep(60)
    METRICS._roll_minute()
