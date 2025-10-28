import React, { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export default function TdoaTestButton() {
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const handleClick = async () => {
    setLoading(true);
    setMsg(null);
    try {
      // 데모용 arrivals (지금은 딜레이 임의값)
      const body = {
        arrivals: [
          { sensor_id: "sensor-001", delay: 0.000 },
          { sensor_id: "sensor-002", delay: 0.002 },
          { sensor_id: "sensor-003", delay: 0.004 },
        ],
      };
      const r = await fetch(`${API_BASE}/tdoa/solve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const json = await r.json();
      setMsg(
        `OK: lat=${json.lat}, lon=${json.lon}, waypoint_id=${json.waypoint_id}, queue_size=${json.queue_size}`
      );
    } catch (e: any) {
      setMsg(`Error: ${e.message || e}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={handleClick}
        disabled={loading}
        className="px-3 py-1.5 rounded-lg border shadow-sm disabled:opacity-60"
      >
        {loading ? "Solving…" : "TDOA Solve & Enqueue"}
      </button>
      {msg && <span className="text-sm">{msg}</span>}
    </div>
  );
}
