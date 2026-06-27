import { ActivitySquare } from "lucide-react";

import ControlPanel from "@/components/ControlPanel";
import DashboardStats from "@/components/DashboardStats";
import KeywordManager from "@/components/KeywordManager";
import LiveResultsTable from "@/components/LiveResultsTable";
import LogsPanel from "@/components/LogsPanel";
import SystemMonitor from "@/components/SystemMonitor";
import { useKeywords } from "@/hooks/useKeywords";
import { useScraper } from "@/hooks/useScraper";
import { useLeads } from "@/hooks/useLeads";
import { useEffect, useState } from "react";
import { getAuditStats, getPipelineForecast } from "@/services/api";

export default function Dashboard() {
  const {
    snapshot,
    settings,
    resultsStats,
    loading,
    busyAction,
    runControl,
    refreshSnapshot,
  } = useScraper();
  const { resetAll, resetFailed, resetSkipped } = useKeywords();
  const { stats, fetchStats } = useLeads();
  const [auditStats, setAuditStats] = useState({});
  const [forecast, setForecast] = useState(null);

  useEffect(() => {
    fetchStats();
    getAuditStats().then(setAuditStats).catch(console.error);
    getPipelineForecast().then(setForecast).catch(console.error);
  }, [fetchStats]);

  const handleResetFailed = async () => {
    await resetFailed();
    await refreshSnapshot();
  };

  const handleResetSkipped = async () => {
    await resetSkipped();
    await refreshSnapshot();
  };

  const handleResetAll = async () => {
    const confirmed = window.confirm(
      "Reset failed, throttled, skipped, and in-progress keywords back to pending?",
    );
    if (!confirmed) {
      return;
    }
    await resetAll();
    await refreshSnapshot();
  };

  const handleControl = async (action) => {
    await runControl(action);
    await refreshSnapshot();
  };

  if (loading) {
    return <div className="p-6 text-slate-400">Loading dashboard...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-cyan-300/70">
            Production Dashboard
          </p>
          <div className="mt-2 flex items-center gap-3">
            <ActivitySquare className="h-8 w-8 text-cyan-300" />
            <h2 className="text-3xl font-semibold text-white">
              Real-time scraper operations
            </h2>
          </div>
          <p className="mt-3 max-w-3xl text-sm text-slate-400">
            Watch queue health, control execution, and confirm rows are saving while the
            scraper runs.
          </p>
        </div>
        <div className="rounded-3xl border border-white/10 bg-white/[0.03] px-5 py-4 text-sm text-slate-300">
          {snapshot.last_error ? `Last error: ${snapshot.last_error}` : "No active backend errors"}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8">
        <div className="rounded-2xl border border-indigo-500/20 bg-indigo-500/10 p-4">
          <p className="text-sm text-indigo-200">Pipeline</p>
          <p className="mt-2 text-xl font-semibold text-white">{forecast?.pipeline_value || "$0"}</p>
        </div>
        <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4">
          <p className="text-sm text-emerald-200">Likely Rev</p>
          <p className="mt-2 text-xl font-semibold text-emerald-400">{forecast?.likely_revenue || "$0"}</p>
        </div>
        <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-4">
          <p className="text-sm text-rose-200">At Risk</p>
          <p className="mt-2 text-2xl font-semibold text-rose-400">{(forecast?.deals_at_risk || 0) + (forecast?.deals_critical || 0)}</p>
        </div>
        <div className="rounded-2xl border border-amber-500/20 bg-amber-500/10 p-4">
          <p className="text-sm text-amber-200">Calls Due</p>
          <p className="mt-2 text-2xl font-semibold text-white">{stats.calls_due_today || 0}</p>
        </div>
        <div className="rounded-2xl border border-blue-500/20 bg-blue-500/10 p-4">
          <p className="text-sm text-blue-200">Follow Ups</p>
          <p className="mt-2 text-2xl font-semibold text-white">{stats.followups_due || 0}</p>
        </div>
        <div className="rounded-2xl border border-purple-500/20 bg-purple-500/10 p-4">
          <p className="text-sm text-purple-200">Meetings</p>
          <p className="mt-2 text-2xl font-semibold text-white">{stats.total_leads || 0}</p>
        </div>
        <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-4">
          <p className="text-sm text-cyan-200">Won Rev</p>
          <p className="mt-2 text-xl font-semibold text-cyan-400">{forecast?.won_revenue || "$0"}</p>
        </div>
        <div className="rounded-2xl border border-green-500/20 bg-green-500/10 p-4">
          <p className="text-sm text-green-200">Win Rate</p>
          <p className="mt-2 text-2xl font-semibold text-green-400">{forecast?.win_rate || "0%"}</p>
        </div>
      </div>

      <DashboardStats metrics={snapshot.totals} activeWorkers={snapshot.active_workers} />

      <div className="grid gap-6 xl:grid-cols-[1.8fr_1fr]">
        <div className="space-y-6">
          <ControlPanel
            status={snapshot.status}
            currentKeyword={snapshot.current_keyword}
            activeWorkers={snapshot.active_workers}
            busyAction={busyAction}
            onControl={handleControl}
          />
          <KeywordManager
            keywords={snapshot.keyword_progress || []}
            maxResultsPerKeyword={settings?.max_results_per_keyword}
            onResetFailed={handleResetFailed}
            onResetSkipped={handleResetSkipped}
            onResetAll={handleResetAll}
          />
          <LiveResultsTable pollIntervalMs={1500} />
          <LogsPanel logs={snapshot.logs} />
        </div>

        <div className="space-y-6">
          <SystemMonitor
            snapshot={snapshot}
            settings={settings}
            resultsStats={resultsStats}
          />
          <div className="rounded-3xl border border-cyan-400/15 bg-gradient-to-br from-cyan-500/15 to-blue-500/10 p-6">
            <p className="text-xs uppercase tracking-[0.24em] text-cyan-200/70">
              Progress
            </p>
            <h3 className="mt-2 text-2xl font-semibold text-white">
              Queue is {snapshot.status}
            </h3>
            <div className="mt-5 h-3 overflow-hidden rounded-full bg-white/10">
              <div
                className="h-full rounded-full bg-gradient-to-r from-cyan-300 to-blue-400"
                style={{
                  width: `${
                    snapshot.totals.total
                      ? (snapshot.totals.done / snapshot.totals.total) * 100
                      : 0
                  }%`,
                }}
              />
            </div>
            <p className="mt-3 text-sm text-slate-200">
              {snapshot.totals.done} of {snapshot.totals.total} keywords completed.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
