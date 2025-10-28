import React, { useEffect, useState } from "react";

type EventRow = {
  id: number;
  ts: string;
  sensor_id: string;
  prob_help: number;
  accepted: boolean;
  battery?: number | null;
};

export default function EventsPage() {
  const [data, setData] = useState<EventRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const r = await fetch("http://127.0.0.1:8000/events/recent?limit=50");
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const json = await r.json();
        setData(json);
      } catch (e: any) {
        setErr(e.message || "fetch failed");
      } finally {
        setLoading(false);
      }
    };
    fetchEvents();
  }, []);

  if (loading) return <div className="p-4">Loading…</div>;
  if (err) return <div className="p-4 text-red-600">Error: {err}</div>;

  return (
    <div className="p-4">
      <h1 className="text-xl font-semibold mb-3">Recent Audio Events</h1>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left border-b">
              <th className="py-2 pr-4">ID</th>
              <th className="py-2 pr-4">Time (UTC)</th>
              <th className="py-2 pr-4">Sensor</th>
              <th className="py-2 pr-4">Prob</th>
              <th className="py-2 pr-4">Accepted</th>
              <th className="py-2 pr-4">Battery</th>
            </tr>
          </thead>
          <tbody>
            {data.map((e) => (
              <tr key={e.id} className="border-b hover:bg-gray-50">
                <td className="py-2 pr-4">{e.id}</td>
                <td className="py-2 pr-4">{new Date(e.ts).toLocaleString()}</td>
                <td className="py-2 pr-4">{e.sensor_id}</td>
                <td className="py-2 pr-4">{e.prob_help.toFixed(2)}</td>
                <td className="py-2 pr-4">{e.accepted ? "✅" : "—"}</td>
                <td className="py-2 pr-4">{e.battery ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
