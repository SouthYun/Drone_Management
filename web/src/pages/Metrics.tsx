import React, { useEffect, useState } from "react";
import ControlBar from "../components/ControlBar";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

type Summary = {
  totals: { audio_events: number; detections: number; missions_enqueued: number; missions_completed: number; rtl_issued: number; };
  series: { ts: string; audio_events: number; detections: number; missions_enqueued: number; missions_completed: number; rtl_issued: number; }[];
  generated_at: string;
};

export default function Metrics() {
  const [data, setData] = useState<Summary | null>(null);

  useEffect(() => {
    let stop = false;
    const tick = async () => {
      try {
        const r = await fetch(`${API_BASE}/metrics/summary`);
        if (r.ok) {
          const json = await r.json();
          if (!stop) setData(json);
        }
      } catch {}
    };
    tick();
    const iv = setInterval(tick, 3000);
    return () => { stop = true; clearInterval(iv); };
  }, []);

  const series = data?.series ?? [];

  return (
    <div className="p-0">
      <ControlBar />
      <div className="p-4 space-y-6">
        <h1 className="text-xl font-semibold">System Metrics</h1>

        {/* Totals */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <Card title="Audio Events" value={data?.totals.audio_events ?? 0} />
          <Card title="Detections" value={data?.totals.detections ?? 0} />
          <Card title="Missions Enqueued" value={data?.totals.missions_enqueued ?? 0} />
          <Card title="Missions Completed" value={data?.totals.missions_completed ?? 0} />
          <Card title="RTL Issued" value={data?.totals.rtl_issued ?? 0} />
        </div>

        {/* Line Chart: last 30 minutes */}
        <div className="border rounded p-3">
          <div className="font-medium mb-2">Last 30 minutes (per minute)</div>
          <div style={{ width: "100%", height: 320 }}>
            <ResponsiveContainer>
              <LineChart data={series}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="ts" tickFormatter={(v) => new Date(v).toLocaleTimeString()} />
                <YAxis allowDecimals={false} />
                <Tooltip labelFormatter={(v) => new Date(v).toLocaleTimeString()} />
                <Legend />
                <Line type="monotone" dataKey="audio_events" name="Audio" dot={false} />
                <Line type="monotone" dataKey="detections" name="Detections" dot={false} />
                <Line type="monotone" dataKey="missions_enqueued" name="Enqueued" dot={false} />
                <Line type="monotone" dataKey="missions_completed" name="Completed" dot={false} />
                <Line type="monotone" dataKey="rtl_issued" name="RTL" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

function Card({ title, value }: { title: string; value: number }) {
  return (
    <div className="border rounded p-3">
      <div className="text-sm text-gray-500">{title}</div>
      <div className="text-2xl font-semibold">{value}</div>
    </div>
  );
}
