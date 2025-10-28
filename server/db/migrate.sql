-- ===============================
-- DrownI 초기 데이터베이스 스키마
-- ===============================

-- 오디오 이벤트 테이블
CREATE TABLE IF NOT EXISTS audio_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sensor_id TEXT NOT NULL,
  prob_help REAL NOT NULL,
  accepted INTEGER NOT NULL DEFAULT 0,
  ts TEXT NOT NULL,
  battery REAL,
  features TEXT,
  meta TEXT,
  created_at TEXT NOT NULL
);

-- 로그 테이블
CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  level TEXT NOT NULL,
  message TEXT NOT NULL,
  ts TEXT NOT NULL
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_audio_events_ts ON audio_events(ts);
CREATE INDEX IF NOT EXISTS idx_audio_events_accepted ON audio_events(accepted);
