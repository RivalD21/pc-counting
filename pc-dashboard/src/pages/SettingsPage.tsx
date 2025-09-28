import { useEffect, useRef, useState } from "react";
import HlsPlayer from "../components/HlsPlayer";
import PolygonOverlay from "../components/PolygonOverlay";
import type { Camera, Point } from "../types";
import axios from "axios";

export default function SettingsPage() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
      <CameraSettings />
      <AreaSettings />
    </div>
  );
}

function CameraSettings() {
  const [rows, setRows] = useState<Camera[]>([]);
  const [form, setForm] = useState<{
    name: string;
    source_url: string;
    location_note: string;
  }>({ name: "", source_url: "", location_note: "" });

  useEffect(() => {
    getCamera();
  }, []);

  const editCamera = async () => {
    await axios.put(`http://localhost:3000/api/cameras/1`, form);
  };

  const getCamera = async () => {
    const response = await axios.get(`http://localhost:3000/api/cameras`);
    setRows(response.data);
    setForm({
      name: response.data[0].name,
      source_url: response.data[0].source_url,
      location_note: response.data[0].location_note,
    });
  };

  return (
    <div className="bg-white rounded-2xl shadow p-3">
      <h3 className="font-semibold mb-2">Cameras</h3>
      <div className="flex gap-2 flex-wrap mb-3">
        <input
          className="border rounded-lg px-3 py-2"
          placeholder="Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />
        <input
          className="border rounded-lg px-3 py-2 min-w-[260px]"
          placeholder="RTSP/HLS URL"
          value={form.source_url}
          onChange={(e) => setForm({ ...form, source_url: e.target.value })}
        />
        <input
          className="border rounded-lg px-3 py-2"
          placeholder="Location note"
          value={form.location_note}
          onChange={(e) => setForm({ ...form, location_note: e.target.value })}
        />
        <button
          onClick={editCamera}
          className="px-4 py-2 rounded-lg bg-zinc-900 text-white"
        >
          Edit
        </button>
      </div>

      <div className="overflow-auto max-h-[380px] pr-1">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left bg-zinc-100">
              <th className="p-2">ID</th>
              <th className="p-2">Name</th>
              <th className="p-2">Source</th>
              <th className="p-2">Note</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.camera_id} className="border-b">
                <td className="p-2">{r.camera_id}</td>
                <td className="p-2">{r.name}</td>
                <td className="p-2 break-all">{r.source_url}</td>
                <td className="p-2">{r.location_note ?? ""}</td>
              </tr>
            ))}
            {!rows.length && (
              <tr>
                <td className="p-2" colSpan={4}>
                  Belum ada kamera.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AreaSettings() {
  const [points, setPoints] = useState<Point[]>([]);
  const [hlsUrl, sethlsUrl] = useState<string>("");
  const boxRef = useRef<HTMLDivElement | null>(null);

  async function load() {
    const response = await axios.get(`http://localhost:3000/api/areas/1`);
    setPoints(response.data[0].polygon);
  }
  async function getRtsp() {
    const response = await axios.get(`http://localhost:3000/api/cameras/1`);
    sethlsUrl(response.data[0].source_url);
  }

  useEffect(() => {
    load();
    getRtsp();
  }, []);

  async function save() {
    await axios.put(`http://localhost:3000/api/polygon/1`, { polygon: points });
  }

  const W = 640,
    H = 360;

  return (
    <div className="bg-white rounded-2xl shadow p-3">
      <h3 className="font-semibold mb-2">Polygon (ROI) Editor</h3>
      <div className="flex gap-2 mb-2">
        <button
          onClick={() => setPoints([])}
          className="px-3 py-2 rounded-lg bg-zinc-200"
        >
          Clear
        </button>
        <button
          onClick={save}
          className="px-3 py-2 rounded-lg bg-zinc-900 text-white"
        >
          Save
        </button>
      </div>

      <div ref={boxRef} className="relative" style={{ width: W, height: H }}>
        <HlsPlayer src={hlsUrl} />
        <PolygonOverlay
          width={W}
          height={H}
          points={points}
          editable={true}
          onChange={setPoints}
        />
      </div>
      <p className="mt-2 text-xs text-zinc-500">
        Tip: klik di area untuk menambah titik. Clear untuk ulang.
      </p>
    </div>
  );
}
