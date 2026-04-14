import { AlertTriangle, CheckCircle2, Clock3, LoaderCircle, RefreshCcw, XCircle } from "lucide-react";


function statusChip(status) {
  const normalized = (status || "").toLowerCase();
  if (normalized === "done") {
    return { label: "Done", className: "bg-emerald-500/15 text-emerald-300", icon: CheckCircle2 };
  }
  if (normalized === "processing") {
    return { label: "Processing", className: "bg-cyan-500/15 text-cyan-300", icon: LoaderCircle };
  }
  if (normalized === "failed" || normalized === "throttled") {
    return { label: normalized, className: "bg-rose-500/15 text-rose-300", icon: XCircle };
  }
  if (normalized === "skipped") {
    return { label: "Skipped", className: "bg-amber-500/15 text-amber-300", icon: AlertTriangle };
  }
  return { label: "Pending", className: "bg-slate-500/15 text-slate-300", icon: Clock3 };
}


export default function KeywordManager({
  keywords,
  maxResultsPerKeyword,
  onResetFailed,
  onResetSkipped,
  onResetAll,
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-slate-950/60 shadow-[0_12px_40px_rgba(15,23,42,0.35)]">
      <div className="flex flex-col gap-4 border-b border-white/10 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-cyan-300/70">
            Queue Overview
          </p>
          <h3 className="mt-2 text-xl font-semibold text-white">
            Keyword execution status
          </h3>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={onResetFailed}
            className="inline-flex items-center gap-2 rounded-2xl border border-rose-400/20 bg-rose-400/10 px-3 py-2 text-sm text-rose-200 transition hover:bg-rose-400/20"
          >
            <RefreshCcw className="h-4 w-4" />
            Reset failed
          </button>
          <button
            onClick={onResetSkipped}
            className="inline-flex items-center gap-2 rounded-2xl border border-amber-400/20 bg-amber-400/10 px-3 py-2 text-sm text-amber-200 transition hover:bg-amber-400/20"
          >
            <RefreshCcw className="h-4 w-4" />
            Reset skipped
          </button>
          <button
            onClick={onResetAll}
            className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 transition hover:bg-white/10"
          >
            <RefreshCcw className="h-4 w-4" />
            Reset queue
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-white/10 text-xs uppercase tracking-[0.18em] text-slate-500">
            <tr>
              <th className="px-6 py-4">Keyword</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Businesses</th>
              <th className="px-6 py-4">Progress</th>
              <th className="px-6 py-4">Time started</th>
              <th className="px-6 py-4">Est. completion</th>
            </tr>
          </thead>
          <tbody>
            {(keywords || []).length > 0 ? (
              keywords.map((keyword) => {
                const chip = statusChip(keyword.status);
                const Icon = chip.icon;
                const scraped = keyword.businesses_scraped ?? 0;
                const percent = keyword.progress_percent ?? 0;
                const etaSeconds = keyword.estimated_completion_seconds;
                const etaText =
                  etaSeconds && etaSeconds > 0
                    ? `${Math.ceil(etaSeconds / 60)} min`
                    : "--";
                return (
                  <tr key={keyword.id} className="border-b border-white/5">
                    <td className="px-6 py-4 text-slate-100">{keyword.text}</td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ${chip.className}`}
                      >
                        <Icon className={`h-3.5 w-3.5 ${chip.label === "Processing" ? "animate-spin" : ""}`} />
                        {chip.label}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-300">
                      {scraped}/{maxResultsPerKeyword || "--"}
                    </td>
                    <td className="px-6 py-4">
                      <div className="w-40">
                        <div className="h-2 overflow-hidden rounded-full bg-white/10">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-cyan-300 to-blue-400"
                            style={{ width: `${Math.max(0, Math.min(100, percent))}%` }}
                          />
                        </div>
                        <p className="mt-1 text-xs text-slate-400">{percent}%</p>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-400">
                      {keyword.started_at
                        ? new Date(keyword.started_at).toLocaleTimeString()
                        : "--"}
                    </td>
                    <td className="px-6 py-4 text-slate-400">
                      {etaText}
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                  No queued keywords yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
