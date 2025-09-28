import { useEffect, useRef, useState } from "react";
import { WsImageStream } from "../components/WsImageStream";
import axios from "axios";

export default function StreamingPage() {
  const [masuk, setMasuk] = useState<number>(0);
  const [keluar, setKeluar] = useState<number>(0);
  const [didalam, setDidalam] = useState<number>(0);
  const [wsUrl, setWsUrl] = useState<string>("ws://localhost:8080");
  const [wsConnUrl, setWsConnUrl] = useState<string>("");

  const [gambar, setGambar] = useState<string>("");
  const [status, setStatus] = useState<
    "connecting" | "live" | "closed" | "error"
  >("connecting");
  const [isEditing, setIsEditing] = useState(false);

  const fetchedRef = useRef(false);
  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;

    (async () => {
      try {
        const res = await axios.get("http://localhost:3000/api/ws");
        const srv = res.data?.[0]?.websocket;
        if (srv && !isEditing) {
          setWsUrl((prev) =>
            prev === "ws://localhost:8080" || prev === "" ? srv : prev
          );
          setWsConnUrl((prev) => (prev ? prev : srv));
        }
      } catch {}
    })();
  }, [isEditing]);

  useEffect(() => {
    if (!wsConnUrl) return;
    setStatus("connecting");
    const ws = new WebSocket(wsConnUrl);
    ws.binaryType = "arraybuffer";

    ws.onopen = () => setStatus("live");
    ws.onclose = () => setStatus("closed");
    ws.onerror = () => setStatus("error");

    ws.onmessage = (ev) => {
      try {
        let dataStr: string | undefined;

        if (typeof ev.data === "string") {
          try {
            const o = JSON.parse(ev.data);
            if (o.masuk != null) setMasuk(Number(o.masuk));
            if (o.keluar != null) setKeluar(Number(o.keluar));
            if (o.didalam != null) setDidalam(Number(o.didalam));
            dataStr = (o.data || o.frame || o.image) as string | undefined;
          } catch {
            dataStr = ev.data as string;
          }
        } else if (ev.data instanceof ArrayBuffer) {
          const blob = new Blob([ev.data], { type: "image/jpeg" });
          dataStr = URL.createObjectURL(blob);
        }

        if (!dataStr) return;
        if (!dataStr.startsWith("data:")) {
          dataStr = `data:image/jpeg;base64,${dataStr}`;
        }
        setGambar(dataStr);
      } catch {}
    };

    return () => ws.close();
  }, [wsConnUrl]);

  const saveWS = async () => {
    try {
      await axios.put(`http://localhost:3000/api/ws/1`, { wsUrl: wsUrl });
    } catch (e) {
      console.error(e);
    }
  };

  const applyWS = () => {
    setWsConnUrl(wsUrl);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-3">
      <div className="lg:col-span-3">
        <div className="bg-white rounded-2xl shadow p-1">
          <div className="flex gap-2 flex-wrap mb-3">
            <input
              className="border rounded-lg px-3 py-2"
              placeholder="ws://host:port"
              value={wsUrl}
              onFocus={() => setIsEditing(true)}
              onBlur={() => setIsEditing(false)}
              onChange={(e) => setWsUrl(e.target.value)}
            />
            <button
              onClick={applyWS}
              className="px-3 py-2 rounded-lg bg-blue-600 text-white"
            >
              Connect
            </button>
            <button
              onClick={saveWS}
              className="px-3 py-2 rounded-lg bg-zinc-900 text-white"
            >
              Save
            </button>
            <span className="px-2 py-2 text-sm">Status: {status}</span>
          </div>

          <div className="relative" style={{ width: 960, height: 540 }}>
            <WsImageStream gambar={gambar} status={status} />
          </div>
        </div>
      </div>

      <div className="lg:col-span-2">
        <div className="bg-white rounded-2xl shadow p-3 h-fit">
          <h3 className="font-semibold mb-2">Live Status</h3>
          <table>
            <tbody>
              <tr>
                <td className="font-semibold">Masuk Area</td>
                <td>: {masuk}</td>
              </tr>
              <tr>
                <td className="font-semibold">Keluar Area</td>
                <td>: {keluar}</td>
              </tr>
              <tr>
                <td className="font-semibold">Di dalam Area</td>
                <td>: {didalam}</td>
              </tr>
              <tr>
                <td className="font-semibold">WS (aktif)</td>
                <td>: {wsConnUrl || "-"}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
