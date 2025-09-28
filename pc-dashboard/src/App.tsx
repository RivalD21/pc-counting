import { Routes, Route, Navigate } from "react-router-dom";
import Nav from "./components/Nav";
import StreamingPage from "./pages/StreamingPage";
import DataPage from "./pages/DataPage";
import SettingsPage from "./pages/SettingsPage";


export default function App() {
return (
<div className="max-w-7xl mx-auto p-3">
<h1 className="text-2xl font-semibold mb-2">People Counting Dashboard</h1>
<Nav />
<div className="mt-3">
<Routes>
<Route path="/" element={<StreamingPage />} />
<Route path="/data" element={<DataPage />} />
<Route path="/settings" element={<SettingsPage />} />
<Route path="*" element={<Navigate to="/" />} />
</Routes>
</div>
</div>
);
}