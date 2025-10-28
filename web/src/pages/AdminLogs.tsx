import React, { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

type LogRow = {
  id?: number;
  level?: string;
  message: string;
  ts?: string;
};

export default function AdminLogs() {
  const [data, setData] = useState<LogRow[]>([]);
  const [err, setErr] = useState<string | null>(null);

  // 초기 로그 1회 로드
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const r = await fetch(`${API_BASE}/logs/recent?limit=50`);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const json = await r.json();
        setData(json);
      } catch (e: any) {
        setErr(e.message || "fetch failed");
      }
    };
    fetchLogs();
  }, []);

  // SSE 실시간 로그 수신
  useEffect(() => {
    const evt = new EventSource(`${API_BASE}/realtime/logs`);
    evt.onmessage = (e) => {
      setData((prev) => [
        { message: e.data, ts: new Date().toISOString() },
        ...prev.slice(0, 49),
      ]);
    };
    evt.onerror = () => console.warn("SSE connection lost");
    return () => evt.close();
  }, []);

  if (err) return <div className="p-4 text-red-600">Error: {err}</div>;

  return (
    <div className="p-4">
      <h1 className="text-xl font-semibold mb-3">Server Logs (Live)</h1>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm border">
          <thead className="bg-gray-100">
            <tr className="text-left border-b">
              <th className="py-2 px-3">Time</th>
              <th className="py-2 px-3">Message</th>
            </tr>
          </thead>
          <tbody>
            {data.map((log, i) => (
              <tr key={i} className="border-b hover:bg-gray-50">
                <td className="py-2 px-3">
                  {log.ts ? new Date(log.ts).toLocaleString() : "-"}
                </td>
                <td className="py-2 px-3">{log.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
