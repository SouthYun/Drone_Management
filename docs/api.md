# Ingest API (센서 → 서버)

- **Method:** `POST /ingest/audio`
- **Content-Type:** `application/json`

## Payload 예시
```json
{
  "sensor_id": "sensor-001",
  "prob_help": 0.93,
  "ts": "2025-10-28T12:34:56Z",
  "battery": 3.82,
  "features": {"rms": 0.12, "mel_band_0": 0.001},
  "meta": {"fw": "1.0.0", "lat": 37.27, "lon": 127.73}
}
