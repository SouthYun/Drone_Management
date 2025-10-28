# server/services/mqtt_bridge.py
"""
MQTT Bridge Service
-------------------
센서 노드 → (MQTT) → 서버 HTTP /ingest/audio 변환 중계
"""

import asyncio, json, requests
from datetime import datetime, timezone
from paho.mqtt import client as mqtt

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "drowni/audio"

API_URL = "http://127.0.0.1:8000/ingest/audio"

def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected with code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if "sensor_id" not in payload:
            print("[MQTT] Invalid payload, skipping")
            return
        payload.setdefault("ts", datetime.now(timezone.utc).isoformat())
        r = requests.post(API_URL, json=payload, timeout=5)
        print(f"[MQTT→HTTP] {payload['sensor_id']} → {r.status_code}")
    except Exception as e:
        print(f"[MQTT] Error: {e}")

async def run_mqtt_bridge():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    print(f"[MQTT] Bridge listening on {MQTT_BROKER}:{MQTT_PORT}")
    while True:
        await asyncio.sleep(10)
