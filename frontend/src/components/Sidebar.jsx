import { Database, LayoutDashboard, Radar, Settings } from "lucide-react";


const NAV_ITEMS = [
  { id: "dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { id: "keywords", icon: Database, label: "Keywords" },
  { id: "settings", icon: Settings, label: "Settings" },
];


export function Sidebar({ activeTab, setActiveTab }) {
  return (
    <aside className="hidden w-72 shrink-0 border-r border-white/10 bg-slate-950/80 p-6 lg:flex lg:flex-col">
      <div className="flex items-center gap-3">
        <div className="rounded-2xl bg-cyan-400/10 p-3">
          <Radar className="h-6 w-6 text-cyan-300" />
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-cyan-300/60">
            Maps Scraper
          </p>
          <h1 className="mt-1 text-xl font-semibold text-white">Ops Console</h1>
        </div>
      </div>

      <nav className="mt-10 space-y-2">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = item.id === activeTab;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm font-medium transition ${
                active
                  ? "bg-cyan-400/10 text-cyan-200 shadow-[0_8px_30px_rgba(8,145,178,0.16)]"
                  : "text-slate-400 hover:bg-white/5 hover:text-white"
              }`}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="mt-auto rounded-3xl border border-white/10 bg-white/[0.03] p-5">
        <p className="text-xs uppercase tracking-[0.24em] text-slate-500">
          Status
        </p>
        <div className="mt-4 flex items-center gap-3">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 shadow-[0_0_20px_rgba(74,222,128,0.9)]" />
          <span className="text-sm text-slate-200">Backend health visible</span>
        </div>
      </div>
    </aside>
  );
}
