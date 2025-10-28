import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import ControlBar from "../components/ControlBar";
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

const redIcon = new L.Icon({
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x-red.png",
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34],
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
  shadowSize: [41, 41],
});

type AudioPoint = { id: number; ts: string; lat?: number; lon?: number; prob_help: number; sensor_id: string };
type MissionPoint = { id: string; lat: number; lon: number; alt: number; ts?: string; status?: string };

export default function MapView() {
  const [center, setCenter] = useState<[number, number]>([37.5665, 126.9780]);
  const [events, setEvents] = useState<AudioPoint[]>([]);
  const [missions, setMissions] = useState<MissionPoint[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${API_BASE}/events/recent?limit=1`);
        if (r.ok) {
          const [e] = await r.json();
          const meta = e?.meta || {};
          if (meta.lat && meta.lon) setCenter([meta.lat, meta.lon]);
        }
      } catch {}
    })();
  }, []);

  useEffect(() => {
    const esEv = new EventSource(`${API_BASE}/realtime/events`);
    esEv.onmessage = (e) => { try {
      const msg = JSON.parse(e.data);
      if (msg.type === "audio_event" && msg.lat && msg.lon) {
        setEvents((prev) => [{ id: msg.id, ts: msg.ts, lat: msg.lat, lon: msg.lon,
          prob_help: msg.prob_help, sensor_id: msg.sensor_id }, ...prev].slice(0, 100));
      }
    } catch {} };
    const esSt = new EventSource(`${API_BASE}/realtime/status`);
    esSt.onmessage = (e) => { try {
      const msg = JSON.parse(e.data);
      if (msg.type === "mission_enqueued" && msg.waypoint) {
        setMissions((prev) => [{ id: msg.waypoint.id, lat: msg.waypoint.lat, lon: msg.waypoint.lon,
          alt: msg.waypoint.alt, ts: msg.waypoint.created_at, status: "queued" }, ...prev].slice(0, 20));
      } else if (msg.type === "mission_dispatched" && msg.waypoint) {
        setMissions((prev) => prev.map(m => m.id === msg.waypoint.id ? { ...m, status: "dispatched" } : m));
      } else if (msg.type === "mission_ended") {
        setMissions((prev) => prev.map(m => m.id === msg.mission_id ? { ...m, status: msg.reason } : m));
      } else if (msg.type === "mission_timeout_rtl") {
        setMissions((prev) => prev.map(m => m.id === msg.mission_id ? { ...m, status: "timeout_rtl" } : m));
      }
    } catch {} };
    return () => { esEv.close(); esSt.close(); };
  }, []);

  return (
    <div className="p-0">
      <ControlBar />
      <div className="h-[80vh] w-full">
        <MapContainer center={center} zoom={15} className="h-full w-full">
          <TileLayer attribution='&copy; OpenStreetMap'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {events.map(ev => ev.lat && ev.lon ? (
            <Marker key={`ev-${ev.id}`} position={[ev.lat, ev.lon]} icon={redIcon}>
              <Popup>
                <div>
                  <div><b>Audio Event</b> #{ev.id}</div>
                  <div>Sensor: {ev.sensor_id}</div>
                  <div>Prob: {ev.prob_help.toFixed(2)}</div>
                  <div>Time: {new Date(ev.ts).toLocaleString()}</div>
                </div>
              </Popup>
            </Marker>
          ) : null)}
          {missions.map(m => (
            <CircleMarker key={`m-${m.id}`} center={[m.lat, m.lon]} radius={6}>
              <Popup>
                <div>
                  <div><b>Mission</b> {m.id.slice(0,8)}…</div>
                  <div>Alt: {m.alt} m</div>
                  <div>Status: {m.status ?? "-"}</div>
                  {m.ts && <div>Created: {new Date(m.ts).toLocaleString()}</div>}
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}
