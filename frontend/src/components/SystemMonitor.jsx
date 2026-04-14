import { Database, HardDriveDownload, Layers3, Workflow } from "lucide-react";


function InfoRow({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-white/5 bg-white/[0.03] px-4 py-3">
      <div className="flex items-center gap-3 text-slate-300">
        <Icon className="h-4 w-4 text-cyan-300" />
        <span>{label}</span>
      </div>
      <span className="text-right text-sm text-white">{value}</span>
    </div>
  );
}


export default function SystemMonitor({ snapshot, settings, resultsStats }) {
  return (
    <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-6 shadow-[0_12px_40px_rgba(15,23,42,0.35)]">
      <p className="text-xs uppercase tracking-[0.24em] text-cyan-300/70">
        System
      </p>
      <h3 className="mt-2 text-xl font-semibold text-white">Runtime configuration</h3>

      <div className="mt-5 space-y-3">
        <InfoRow
          icon={Workflow}
          label="Parallel workers"
          value={settings?.parallel_workers ?? 1}
        />
        <InfoRow
          icon={Layers3}
          label="Max results / keyword"
          value={settings?.max_results_per_keyword ?? 20}
        />
        <InfoRow
          icon={Database}
          label="Saved rows"
          value={snapshot?.totals?.results ?? 0}
        />
        <InfoRow
          icon={HardDriveDownload}
          label="Local export"
          value={snapshot?.data_saver?.csv_path || resultsStats?.data_saver?.csv_path || "Not created yet"}
        />
      </div>

      <div className="mt-5 rounded-2xl border border-emerald-400/15 bg-emerald-400/10 p-4 text-sm text-emerald-100">
        {snapshot?.data_saver?.google_sheets_connected
          ? "Google Sheets streaming is connected and rows are pushed live."
          : "Google Sheets streaming is currently off or waiting for credentials."}
      </div>
    </div>
  );
}
