import { useEffect, useMemo, useRef, useState } from "react";
import type { Point } from "../types";


export default function PolygonOverlay({
width,
height,
points = [],
editable = false,
onChange = () => {}
}: { width: number; height: number; points?: Point[]; editable?: boolean; onChange?: (pts: Point[]) => void; }) {
const [localPts, setLocalPts] = useState<Point[]>(points);
const svgRef = useRef<SVGSVGElement | null>(null);


useEffect(() => { setLocalPts(points || []); }, [points]);


const path = useMemo(() => {
if (!localPts?.length) return "";
return localPts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ") + " Z";
}, [localPts]);


function addPoint(e: React.MouseEvent<SVGRectElement, MouseEvent>) {
if (!editable || !svgRef.current) return;
const rect = svgRef.current.getBoundingClientRect();
const x = Math.round(e.clientX - rect.left);
const y = Math.round(e.clientY - rect.top);
const next = [...localPts, { x, y }];
setLocalPts(next); onChange(next);
}


function dragPoint(idx: number, e: MouseEvent) {
if (!editable || !svgRef.current) return;
const rect = svgRef.current.getBoundingClientRect();
const x = Math.max(0, Math.min(width, Math.round(e.clientX - rect.left)));
const y = Math.max(0, Math.min(height, Math.round(e.clientY - rect.top)));
const next = localPts.map((p, i) => (i === idx ? { x, y } : p));
setLocalPts(next); onChange(next);
}


return (
<svg ref={svgRef} width={width} height={height} className="absolute inset-0 w-full h-full">
{localPts.length >= 2 && (
<path d={path} fill="rgba(59,130,246,0.15)" stroke="rgba(59,130,246,0.9)" strokeWidth={2} />
)}
{localPts.map((p, i) => (
<circle key={i} cx={p.x} cy={p.y} r={6}
className={editable ? "cursor-move fill-blue-500" : "fill-blue-400"}
onMouseDown={(e) => {
if (!editable) return;
e.preventDefault();
const move = (ev: MouseEvent) => dragPoint(i, ev);
const up = () => { window.removeEventListener("mousemove", move); window.removeEventListener("mouseup", up); };
window.addEventListener("mousemove", move);
window.addEventListener("mouseup", up);
}}
/>
))}
{editable && (
<rect x={0} y={0} width={width} height={height} fill="transparent" onClick={addPoint} />
)}
</svg>
);
}