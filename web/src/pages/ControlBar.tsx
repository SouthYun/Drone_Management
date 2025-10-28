import React, { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export default function ControlBar() {
  const [msg, setMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleDispatch = async () => {
    setLoading(true);
    setMsg(null);
    try {
      // 임시: 샘플 좌표(학교 캠퍼스 기준)
      const body = { lat: 37.2775, lon: 127.7355 };
      const r = await fetch(`${API_BASE}/missions/enqueue`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const json = await r.json();
      setMsg(`🚁 Mission queued (ID=${json.waypoint.id})`);
    } catch (e: any) {
      setMsg(`Error: ${e.message || e}`);
    } finally {
      setLoading(false);
    }
  };

  const handleNextMission = async () => {
    setLoading(true);
    setMsg(null);
    try {
      const r = await fetch(`${API_BASE}/missions/next`);
      if (r.status === 204) {
        setMsg("No missions in queue.");
        return;
      }
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const json = await r.json();
      setMsg(`🎯 Next mission: lat=${json.waypoint.lat}, lon=${json.waypoint.lon}`);
    } catch (e: any) {
      setMsg(`Error: ${e.message || e}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReturnHome = async () => {
    setLoading(true);
    setMsg(null);
    try {
      // 현재는 임시: 서버에 복귀 요청 시뮬레이션
      const r = await fetch(`${API_BASE}/drone/rtl`, { method: "POST" });
      setMsg(r.ok ? "🛬 Drone returning to base." : `HTTP ${r.status}`);
    } catch (e: any) {
      setMsg(`Error: ${e.message || e}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-wrap gap-2 p-4 border-b bg-gray-50">
      <button
        onClick={handleDispatch}
        disabled={loading}
        className="px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-60"
      >
        출동 (Enqueue Mission)
      </button>
      <button
        onClick={handleNextMission}
        disabled={loading}
        className="px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-60"
      >
        다음 임무 보기
      </button>
      <button
        onClick={handleReturnHome}
        disabled={loading}
        className="px-3 py-1.5 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-60"
      >
        복귀 (Return Home)
      </button>
      {msg && <span className="ml-3 text-sm">{msg}</span>}
    </div>
  );
}
