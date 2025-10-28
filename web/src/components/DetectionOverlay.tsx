import React, { useEffect, useRef } from "react";
type Detection = { stream_id: string; cls: string; conf: number; bbox?: number[]; ts: string; };
export default function DetectionOverlay({ videoRef, detections }:{
  videoRef: React.RefObject<HTMLVideoElement>, detections: Detection[]
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = canvasRef.current, video = videoRef.current;
    if (!canvas || !video) return;
    const ctx = canvas.getContext("2d"); if (!ctx) return;

    const resize = () => { canvas.width = video.clientWidth; canvas.height = video.clientHeight; };
    resize(); window.addEventListener("resize", resize);
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    detections.forEach((det) => {
      if (!det.bbox) return;
      const [x,y,w,h] = det.bbox;
      const bx=x*canvas.width, by=y*canvas.height, bw=w*canvas.width, bh=h*canvas.height;
      let color = "#00ff00"; if (det.cls==="fire") color="#ff0000"; else if (det.cls==="smoke") color="#ffaa00";
      ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.strokeRect(bx, by, bw, bh);
      ctx.fillStyle = color; ctx.font = "14px sans-serif"; ctx.fillText(`${det.cls} (${det.conf.toFixed(2)})`, bx+4, by+16);
    });
    return () => window.removeEventListener("resize", resize);
  }, [detections, videoRef]);

  return <canvas ref={canvasRef} className="absolute top-0 left-0 pointer-events-none" style={{width:"100%",height:"100%"}}/>;
}
