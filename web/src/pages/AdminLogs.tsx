import React, { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

type LogRow = {
  id: number;
  level: string;
  message: string;
  ts: string;
};

export default function AdminLogs() {
  const [data, setData] = useState<LogRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const r = await fetch(`${API_BASE}/logs/recent?limit=100`);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const json = await r.json();
        setData(json);
      } catch (e: any) {
        setErr(e.message || "fetch failed");
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, []);

  if (loading) return <div className="p-4">Loading logs…</div>;
  if (err) return <div className="p-4 text-red-600">Error: {err}</div>;

  return (
    <div className="p-4">
      <h1 className="text-xl font-semibold mb-3">Server Logs</h1>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm border">
          <thead className="bg-gray-100">
            <tr className="text-left border-b">
              <th className="py-2 px-3">Time (UTC)</th>
              <th className="py-2 px-3">Level</th>
              <th className="py-2 px-3">Message</th>
            </tr>
          </thead>
          <tbody>
            {data.map((log) => (
              <tr key={log.id} className="border-b hover:bg-gray-50">
                <td className="py-2 px-3">{new Date(log.ts).toLocaleString()}</td>
                <td className="py-2 px-3 font-medium">{log.level}</td>
                <td className="py-2 px-3">{log.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
