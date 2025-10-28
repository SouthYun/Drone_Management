import React, { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

type Det = {
  stream_id: string;
  cls: string;
  conf: number;
  bbox?: number[];
  ts: string;
};

export default function DetectionTicker() {
  const [items, setItems] = useState<Det[]>([]);

  useEffect(() => {
    // 초기 로드
    fetch(`${API_BASE}/detections/recent?limit=20`)
      .then((r) => r.json())
      .then((json) => setItems(json))
      .catch(() => {});

    // SSE 연결
    const es = new EventSource(`${API_BASE}/realtime/detections`);
    es.onmessage = (e) => {
      try {
        const det: Det = JSON.parse(e.data);
        setItems((prev) => [det, ...prev.slice(0, 19)]);
      } catch {}
    };
    es.onerror = () => console.warn("SSE(detections) disconnected");
    return () => es.close();
  }, []);

  return (
    <div className="mt-3 border rounded p-2">
      <div className="font-medium mb-2">Detections (Live)</div>
      <ul className="space-y-1 text-sm max-h-48 overflow-auto">
        {items.map((d, i) => (
          <li key={i} className="flex justify-between">
            <span>[{new Date(d.ts).toLocaleTimeString()}] {d.stream_id}</span>
            <span>{d.cls} ({d.conf.toFixed(2)})</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
