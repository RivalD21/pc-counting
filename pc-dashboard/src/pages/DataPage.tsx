import { useEffect, useState } from "react";
import type { EventRow } from "../types";
import axios from "axios";

export default function DataPage() {
  const [from, setFrom] = useState<string>("");
  const [to, setTo] = useState<string>("");
  const [events, setEvents] = useState<EventRow[]>([]);

  useEffect(() => {
    load();
  }, []);

  async function load() {
    const params: any = { limit: 200 };
    if (from) params.from = from;
    if (to) params.to = to;
    const response = await axios.get(`http://localhost:3000/api/stats`, {
      params,
    });
    setEvents(response.data);
  }

  return (
    <div className="bg-white rounded-2xl shadow p-3">
      <div className="flex gap-2 flex-wrap items-end">
        <input
          type="datetime-local"
          className="border rounded-lg px-3 py-2"
          value={from}
          onChange={(e) => setFrom(e.target.value)}
        />
        <input
          type="datetime-local"
          className="border rounded-lg px-3 py-2"
          value={to}
          onChange={(e) => setTo(e.target.value)}
        />
        <button
          onClick={load}
          className="px-4 py-2 rounded-lg bg-zinc-900 text-white"
        >
          Load
        </button>
      </div>

      <div className="mt-3 overflow-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left bg-zinc-100">
              <th className="p-2">Waktu</th>
              <th className="p-2">Masuk Area</th>
              <th className="p-2">Keluar Area</th>
              <th className="p-2">Didalam Area</th>
            </tr>
          </thead>
          <tbody>
            {events.map((ev) => (
              <tr key={ev.counting_id} className="border-b">
                <td className="p-2 whitespace-nowrap">
                  {new Date(ev.timestamp).toLocaleString()}
                </td>
                <td className="p-2">{ev.masuk ?? "—"}</td>
                <td className="p-2 font-medium">{ev.keluar ?? "—"}</td>
                <td className="p-2">{ev.dalam ?? ""}</td>
              </tr>
            ))}
            {!events.length && (
              <tr>
                <td className="p-2" colSpan={6}>
                  Tidak ada data.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
