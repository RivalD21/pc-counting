import { Link, useLocation } from "react-router-dom";
import { Film, Database, Settings } from "lucide-react";


export default function Nav() {
const { pathname } = useLocation();
const Item = ({ to, icon: Icon, label }: { to: string; icon: any; label: string }) => (
<Link
to={to}
className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition ${
pathname === to ? "bg-zinc-900 text-white" : "bg-white hover:bg-zinc-100"
}`}
>
<Icon size={18} /> {label}
</Link>
);
return (
<div className="w-full flex items-center gap-2 p-2">
<Item to="/" icon={Film} label="Streaming" />
<Item to="/data" icon={Database} label="Data" />
<Item to="/settings" icon={Settings} label="Settings" />
</div>
);
}