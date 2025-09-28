import { useEffect, useRef } from "react";
import Hls from "hls.js";


export default function HlsPlayer({ src, autoPlay = true, muted = true }: { src?: string; autoPlay?: boolean; muted?: boolean; }) {
const videoRef = useRef<HTMLVideoElement | null>(null);
useEffect(() => {
const video = videoRef.current;
if (!video || !src) return;
let hls: Hls | undefined;
if (Hls.isSupported()) {
hls = new Hls({ liveDurationInfinity: true });
hls.loadSource(src);
hls.attachMedia(video);
} else if (video.canPlayType("application/vnd.apple.mpegurl")) {
video.src = src;
}
if (autoPlay) video.play().catch(() => {});
return () => { hls?.destroy(); };
}, [src, autoPlay]);
return (
<video ref={videoRef} className="w-full rounded-xl bg-black" controls muted={muted} playsInline />
);
}