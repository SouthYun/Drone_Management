import React, { useState, useEffect, useRef } from "react";
import ControlBar from "../components/ControlBar";
import DetectionTicker from "../components/DetectionTicker";
import DetectionOverlay from "../components/DetectionOverlay";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";
const DEFAULT_VIDEO_URL = import.meta.env.VITE_VIDEO_URL ?? "http://127.0.0.1:8080/live/stream.m3u8";

type Detection = { stream_id: string; cls: string; conf: number; bbox?: number[]; ts: string; };

export default function VideoPanel() {
  const [url, setUrl] = useState(DEFAULT_VIDEO_URL);
  const [detections, setDetections] = useState<Detection[]>([]);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const es = new EventSource(`${API_BASE}/realtime/detections`);
    es.onmessage = (e) => { try {
      const det: Detection = JSON.parse(e.data);
      setDetections((prev) => [det, ...prev.slice(0, 20)]);
    } catch {} };
    es.onerror = () => console.warn("SSE(detections) disconnected");
    return () => es.close();
  }, []);

  return (
    <div className="p-0">
      <ControlBar />
      <div className="p-4">
        <h1 className="text-xl font-semibold mb-3">Drone Live Video</h1>
        <div className="mb-2 flex gap-2">
          <input type="text" className="border rounded px-2 py-1 text-sm w-96"
            value={url} onChange={(e) => setUrl(e.target.value)}
            placeholder="Enter stream URL" />
          <button className="px-3 py-1.5 border rounded shadow-sm"
            onClick={() => setUrl(DEFAULT_VIDEO_URL)}>Reset</button>
        </div>
        <div className="relative border rounded-lg overflow-hidden bg-black">
          <video ref={videoRef} src={url} controls autoPlay muted
            style={{ width: "100%", height: "70vh", objectFit: "contain" }} />
          <DetectionOverlay videoRef={videoRef} detections={detections} />
        </div>
        <DetectionTicker />
      </div>
    </div>
  );
}
