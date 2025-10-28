import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import ControlBar from "../components/ControlBar";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

// 빨간색 마커 아이콘
const redIcon = new L.Icon({
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x-red.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
  shadowSize: [41, 41],
});

type EventRow = {
  id: number;
  ts: string;
  sensor_id: string;
  prob_help: number;
  accepted: boolean;
  battery?: number;
  meta?: { lat?: number; lon?: number };
};

export default function MapView() {
  const [event, setEvent] = useState<EventRow | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const fetchLatest = async () => {
      try {
        const r = await fetch(`${API_BASE}/events/recent?limit=1`);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const json = await r.json();
        if (json.length > 0) setEvent(json[0]);
      } catch (e: any) {
        setErr(e.message || "fetch failed");
      }
    };
    fetchLatest();
  }, []);

  if (err) return <div className="p-4 text-red-600">Error: {err}</div>;
  if (!event) return <div className="p-4">Loading map…</div>;

  // 기본 위치: 이벤트 meta에 좌표 없으면 서울 시청
  const lat = event.meta?.lat ?? 37.5665;
  const lon = event.meta?.lon ?? 126.9780;

  return (
    <div className="p-0">
      {/* 상단 관제 제어바 연결 */}
      <ControlBar />

      {/* 지도 영역 */}
      <div className="h-[80vh] w-full">
        <MapContainer center={[lat, lon]} zoom={15} className="h-full w-full">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Marker position={[lat, lon]} icon={redIcon}>
            <Popup>
              <div>
                <strong>ID:</strong> {event.id}
                <br />
                <strong>Sensor:</strong> {event.sensor_id}
                <br />
                <strong>Prob:</strong> {event.prob_help.toFixed(2)}
                <br />
                <strong>Time:</strong> {new Date(event.ts).toLocaleString()}
              </div>
            </Popup>
          </Marker>
        </MapContainer>
      </div>
    </div>
  );
}
