import React, { useEffect, useRef } from "react";

type Detection = {
  stream_id: string;
  cls: string;
  conf: number;
  bbox?: number[]; // [x, y, w, h], 0~1 정규화 좌표
  ts: string;
};

interface Props {
  videoRef: React.RefObject<HTMLVideoElement>;
  detections: Detection[];
}

/**
 * 비디오 위에 탐지 결과 박스를 그리는 오버레이 컴포넌트
 */
export default function DetectionOverlay({ videoRef, detections }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // 캔버스 크기를 비디오에 맞게 조정
    const resize = () => {
      canvas.width = video.clientWidth;
      canvas.height = video.clientHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    detections.forEach((det) => {
      if (!det.bbox) return;
      const [x, y, w, h] = det.bbox;
      const bx = x * canvas.width;
      const by = y * canvas.height;
      const bw = w * canvas.width;
      const bh = h * canvas.height;

      // 클래스별 색상
      let color = "#00ff00";
      if (det.cls === "fire") color = "#ff0000";
      else if (det.cls === "smoke") color = "#ffaa00";

      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.strokeRect(bx, by, bw, bh);

      ctx.fillStyle = color;
      ctx.font = "14px sans-serif";
      ctx.fillText(`${det.cls} (${det.conf.toFixed(2)})`, bx + 4, by + 16);
    });

    return () => window.removeEventListener("resize", resize);
  }, [detections, videoRef]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute top-0 left-0 pointer-events-none"
      style={{ width: "100%", height: "100%" }}
    />
  );
}
