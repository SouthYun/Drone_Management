import React, { useState } from "react";

const DEFAULT_VIDEO_URL = import.meta.env.VITE_VIDEO_URL ?? "http://127.0.0.1:8080/live/stream.m3u8";

/**
 * DrownI Video Panel
 * ------------------
 * - HLS / RTSP / WebRTC 등 실시간 스트림 표시
 * - 초기 버전: 단순 <video> 요소로 구현
 */
export default function VideoPanel() {
  const [url, setUrl] = useState(DEFAULT_VIDEO_URL);

  return (
    <div className="p-4">
      <h1 className="text-xl font-semibold mb-3">Drone Live Video</h1>
      <div className="mb-2">
        <input
          type="text"
          className="border rounded px-2 py-1 text-sm w-96"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Enter stream URL"
        />
      </div>
      <div className="border rounded-lg overflow-hidden bg-black">
        <video
          src={url}
          controls
          autoPlay
          muted
          style={{ width: "100%", height: "70vh", objectFit: "contain" }}
        />
      </div>
      <p className="text-xs text-gray-500 mt-1">
        * 기본 URL: {DEFAULT_VIDEO_URL}
      </p>
    </div>
  );
}
