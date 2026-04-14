import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  Database,
  LoaderCircle,
  Search,
} from "lucide-react";


const STAT_CARDS = [
  {
    key: "total",
    label: "Queued Keywords",
    icon: Search,
    accent: "from-cyan-500/25 to-blue-500/10",
  },
  {
    key: "done",
    label: "Completed",
    icon: CheckCircle2,
    accent: "from-emerald-500/25 to-green-500/10",
  },
  {
    key: "processing",
    label: "Running",
    icon: LoaderCircle,
    accent: "from-violet-500/25 to-indigo-500/10",
  },
  {
    key: "pending",
    label: "Pending",
    icon: Clock3,
    accent: "from-amber-500/20 to-yellow-500/10",
  },
  {
    key: "failed",
    label: "Failed",
    icon: AlertCircle,
    accent: "from-rose-500/25 to-red-500/10",
  },
  {
    key: "results",
    label: "Saved Businesses",
    icon: Database,
    accent: "from-fuchsia-500/20 to-pink-500/10",
  },
  {
    key: "results_per_min",
    label: "Speed (results/min)",
    icon: Database,
    accent: "from-blue-500/20 to-cyan-500/10",
  },
  {
    key: "success_rate",
    label: "Success Rate %",
    icon: CheckCircle2,
    accent: "from-emerald-500/20 to-teal-500/10",
  },
  {
    key: "active_workers",
    label: "Active Workers",
    icon: LoaderCircle,
    accent: "from-violet-500/20 to-fuchsia-500/10",
  },
];


export default function DashboardStats({ metrics, activeWorkers }) {
  const normalized = {
    ...(metrics || {}),
    active_workers: activeWorkers ?? 0,
  };

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-9">
      {STAT_CARDS.map(({ key, label, icon: Icon, accent }) => (
        <div
          key={key}
          className="rounded-3xl border border-white/10 bg-slate-950/55 p-5 shadow-[0_12px_40px_rgba(15,23,42,0.35)]"
        >
          <div className={`mb-4 inline-flex rounded-2xl bg-gradient-to-br p-3 ${accent}`}>
            <Icon className="h-5 w-5 text-white" />
          </div>
          <p className="text-sm text-slate-400">{label}</p>
          <p className="mt-1 text-3xl font-semibold text-white">
            {normalized?.[key] ?? 0}
          </p>
        </div>
      ))}
    </div>
  );
}
