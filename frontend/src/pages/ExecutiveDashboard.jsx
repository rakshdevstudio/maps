import { useEffect, useState } from "react";
import { DollarSign, TrendingUp, AlertTriangle, Target, Briefcase, Activity, ShieldAlert, Sparkles } from "lucide-react";
import { getPipelineForecast, getProjectStats, getRevenueBriefing, getProjectRisks, getChiefOfStaffBrief } from "@/services/api";

export default function ExecutiveDashboard() {
  const [forecast, setForecast] = useState(null);
  const [projectStats, setProjectStats] = useState(null);
  const [revenueBrief, setRevenueBrief] = useState(null);
  const [risks, setRisks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [f, p, rev, r] = await Promise.all([
          getPipelineForecast(),
          getProjectStats(),
          getRevenueBriefing(),
          getProjectRisks()
        ]);
        setForecast(f);
        setProjectStats(p);
        setRevenueBrief(rev);
        setRisks(r || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center py-32 text-slate-500">Loading autonomous executive intelligence...</div>;
  }

  return (
    <div className="space-y-10">
      <div>
        <p className="text-xs uppercase tracking-[0.24em] text-indigo-400/70">Executive Intelligence</p>
        <h2 className="mt-2 text-3xl font-semibold text-white">Revenue Command Center</h2>
        <p className="mt-2 text-sm text-slate-400">Autonomous Pipeline & Delivery Analysis</p>
      </div>

      {revenueBrief && (
        <div className="rounded-2xl border border-indigo-500/20 bg-indigo-500/5 p-6">
          <div className="flex items-center gap-3 mb-6">
            <Sparkles className="h-5 w-5 text-indigo-400" />
            <h3 className="text-lg font-semibold text-white">AI Revenue Analysis</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm font-medium text-slate-400 mb-1">Risk Summary</p>
              <p className="text-slate-200">{revenueBrief.risk_summary}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-slate-400 mb-1">Blocked Deals</p>
              <p className="text-slate-200">{revenueBrief.blocked_summary}</p>
            </div>
          </div>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border border-white/10 bg-slate-900/50 p-6 shadow-lg">
          <div className="flex items-center gap-2 text-xs text-indigo-400 uppercase tracking-widest font-semibold mb-3">
            <DollarSign className="h-4 w-4" /> Pipeline
          </div>
          <p className="text-3xl font-bold text-white">{forecast?.pipeline_value || "$0"}</p>
        </div>

        <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-6 shadow-lg">
          <div className="flex items-center gap-2 text-xs text-emerald-400 uppercase tracking-widest font-semibold mb-3">
            <TrendingUp className="h-4 w-4" /> Likely Revenue
          </div>
          <p className="text-3xl font-bold text-emerald-400">{forecast?.likely_revenue || "$0"}</p>
        </div>

        <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/5 p-6 shadow-lg">
          <div className="flex items-center gap-2 text-xs text-cyan-400 uppercase tracking-widest font-semibold mb-3">
            <Briefcase className="h-4 w-4" /> In Delivery
          </div>
          <p className="text-3xl font-bold text-cyan-400">${projectStats?.revenue_in_delivery?.toLocaleString() || "0"}</p>
        </div>

        <div className="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-6 shadow-lg">
          <div className="flex items-center gap-2 text-xs text-rose-400 uppercase tracking-widest font-semibold mb-3">
            <ShieldAlert className="h-4 w-4" /> At Risk
          </div>
          <p className="text-3xl font-bold text-rose-400">{forecast?.at_risk_revenue || "$0"}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Pipeline Stage Breakdown */}
        {forecast?.stage_breakdown && Object.keys(forecast.stage_breakdown).length > 0 && (
          <div className="rounded-2xl border border-white/10 bg-slate-900/50 p-6">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-6">Pipeline by Stage</h3>
            <div className="space-y-4">
              {Object.entries(forecast.stage_breakdown).map(([stage, info]) => (
                <div key={stage} className="flex items-center gap-4">
                  <span className="w-36 text-sm text-slate-400 truncate">{stage}</span>
                  <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-indigo-500 to-cyan-500 rounded-full transition-all"
                      style={{ width: `${forecast.pipeline_value_raw > 0 ? (info.value / forecast.pipeline_value_raw) * 100 : 0}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-emerald-400 w-24 text-right">${Math.round(info.value).toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Project Delivery Risks */}
        <div className="rounded-2xl border border-white/10 bg-slate-900/50 p-6">
          <h3 className="text-sm font-semibold text-rose-400 uppercase tracking-wider mb-6">Delivery Risks</h3>
          {risks.length === 0 ? (
            <p className="text-slate-500 text-sm">No critical delivery risks detected.</p>
          ) : (
            <div className="space-y-4 max-h-80 overflow-y-auto pr-2">
              {risks.map(risk => (
                <div key={risk.id} className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-white font-medium">Project #{risk.project_id}</span>
                    <span className="text-[10px] bg-rose-500/20 text-rose-400 px-2 py-0.5 rounded-full uppercase tracking-wider font-bold">
                      {risk.risk_level}
                    </span>
                  </div>
                  <p className="text-sm text-slate-300">{risk.slipping_reason}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
