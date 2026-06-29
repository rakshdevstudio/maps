import { useEffect, useState } from "react";
import { TrendingUp, AlertTriangle, Phone, DollarSign, Target, FolderKanban, AlertOctagon, CheckCircle2 } from "lucide-react";
import { getPipelineForecast, getTodayView, getProposalStats, getProjectStats } from "@/services/api";
import LeadDetail from "@/components/LeadDetail";
import { useLeads } from "@/hooks/useLeads";

export default function ExecutiveDashboard() {
  const { fetchLeadDetails, updateLead, logActivity } = useLeads();
  const [forecast, setForecast] = useState(null);
  const [today, setToday] = useState(null);
  const [proposalStats, setProposalStats] = useState(null);
  const [projectStats, setProjectStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [f, t, p, proj] = await Promise.all([getPipelineForecast(), getTodayView(), getProposalStats(), getProjectStats()]);
        setForecast(f);
        setToday(t);
        setProposalStats(p);
        setProjectStats(proj);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleCardClick = async (leadId) => {
    const detail = await fetchLeadDetails(leadId);
    setSelectedLead(detail);
  };

  if (loading) {
    return <div className="flex items-center justify-center py-32 text-slate-500">Loading executive intelligence...</div>;
  }

  // Merge and deduplicate all leads needing attention
  const attentionLeads = [];
  const seen = new Set();
  for (const item of [...(today?.overdue || []), ...(today?.critical_deals || [])]) {
    if (!seen.has(item.id)) {
      seen.add(item.id);
      attentionLeads.push(item);
    }
  }
  attentionLeads.sort((a, b) => b.deal_value - a.deal_value);

  // Leads closest to closing = highest stage index, not closed
  const contactToday = [];
  const contactSeen = new Set();
  for (const item of [...(today?.calls_due || []), ...(today?.followups_due || []), ...(today?.meetings_scheduled || [])]) {
    if (!contactSeen.has(item.id)) {
      contactSeen.add(item.id);
      contactToday.push(item);
    }
  }
  contactToday.sort((a, b) => b.deal_value - a.deal_value);

  const stageOrder = ["negotiation", "proposal_sent", "meeting_scheduled", "discovery_call", "contacted", "qualified"];
  const closestToClosing = [...(today?.calls_due || []), ...(today?.followups_due || []), ...(today?.meetings_scheduled || []), ...(today?.overdue || []), ...(today?.critical_deals || [])];
  const closestSeen = new Set();
  const closestDeals = [];
  for (const item of closestToClosing) {
    if (!closestSeen.has(item.id)) {
      closestSeen.add(item.id);
      closestDeals.push(item);
    }
  }
  closestDeals.sort((a, b) => {
    const aIdx = stageOrder.indexOf(a.deal_stage);
    const bIdx = stageOrder.indexOf(b.deal_stage);
    return aIdx - bIdx;
  });

  return (
    <div className="space-y-8">
      <div>
        <p className="text-xs uppercase tracking-[0.24em] text-indigo-400/70">Executive Intelligence</p>
        <h2 className="mt-2 text-3xl font-semibold text-white">Revenue Command Center</h2>
      </div>

      {/* Question 1: How much pipeline exists? */}
      {forecast && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-indigo-500/10 to-purple-500/5 p-6 shadow-lg">
            <div className="flex items-center gap-2 text-xs text-indigo-400 uppercase tracking-widest font-semibold">
              <DollarSign className="h-4 w-4" /> Pipeline Value
            </div>
            <p className="mt-3 text-4xl font-bold text-white">{forecast.pipeline_value}</p>
            <p className="mt-2 text-xs text-slate-500">{forecast.deals_total} active deal{forecast.deals_total !== 1 ? "s" : ""}</p>
          </div>

          {/* Question 2: How much is likely to close? */}
          <div className="rounded-3xl border border-emerald-500/20 bg-gradient-to-br from-emerald-500/10 to-teal-500/5 p-6 shadow-lg">
            <div className="flex items-center gap-2 text-xs text-emerald-400 uppercase tracking-widest font-semibold">
              <TrendingUp className="h-4 w-4" /> Likely Revenue
            </div>
            <p className="mt-3 text-4xl font-bold text-emerald-400">{forecast.likely_revenue}</p>
            <p className="mt-2 text-xs text-slate-500">Win rate: {forecast.win_rate}</p>
          </div>

          {/* Question 3: What is at risk? */}
          <div className="rounded-3xl border border-rose-500/20 bg-gradient-to-br from-rose-500/10 to-orange-500/5 p-6 shadow-lg">
            <div className="flex items-center gap-2 text-xs text-rose-400 uppercase tracking-widest font-semibold">
              <AlertTriangle className="h-4 w-4" /> At Risk
            </div>
            <p className="mt-3 text-4xl font-bold text-rose-400">{forecast.at_risk_revenue}</p>
            <p className="mt-2 text-xs text-slate-500">{forecast.deals_at_risk + forecast.deals_critical} deal{(forecast.deals_at_risk + forecast.deals_critical) !== 1 ? "s" : ""} need attention</p>
          </div>

          <div className="rounded-3xl border border-cyan-500/20 bg-gradient-to-br from-cyan-500/10 to-blue-500/5 p-6 shadow-lg">
            <div className="flex items-center gap-2 text-xs text-cyan-400 uppercase tracking-widest font-semibold">
              <Target className="h-4 w-4" /> Won Revenue
            </div>
            <p className="mt-3 text-4xl font-bold text-cyan-400">{forecast.won_revenue}</p>
            <p className="mt-2 text-xs text-slate-500">Closed deals</p>
          </div>
        </div>
      )}

      {/* Proposal Metrics */}
      {proposalStats && (
        <div className="mt-8 mb-8">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Proposal & Closing Metrics</h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-6 shadow-lg">
              <div className="text-xs text-slate-400 uppercase tracking-widest font-semibold">Draft / Sent / Viewed</div>
              <p className="mt-3 text-3xl font-bold text-white">{proposalStats.drafted} / {proposalStats.sent} / {proposalStats.viewed}</p>
              <p className="mt-2 text-xs text-slate-500">Proposal Funnel</p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-6 shadow-lg">
              <div className="text-xs text-slate-400 uppercase tracking-widest font-semibold">Acceptance Rate</div>
              <p className="mt-3 text-3xl font-bold text-emerald-400">{proposalStats.acceptance_rate.toFixed(1)}%</p>
              <p className="mt-2 text-xs text-slate-500">Win Rate on Sent Proposals</p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-6 shadow-lg">
              <div className="text-xs text-slate-400 uppercase tracking-widest font-semibold">Avg Deal Size</div>
              <p className="mt-3 text-3xl font-bold text-indigo-400">${proposalStats.average_deal_size.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})}</p>
              <p className="mt-2 text-xs text-slate-500">Won Deals Average</p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-6 shadow-lg">
              <div className="text-xs text-slate-400 uppercase tracking-widest font-semibold">Forecasted Revenue</div>
              <p className="mt-3 text-3xl font-bold text-cyan-400">${proposalStats.forecasted_revenue.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})}</p>
              <p className="mt-2 text-xs text-slate-500">Won + Likely Revenue</p>
            </div>
          </div>
        </div>
      )}

      {/* Stage Breakdown */}
      {forecast?.stage_breakdown && Object.keys(forecast.stage_breakdown).length > 0 && (
        <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-6">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Pipeline by Stage</h3>
          <div className="space-y-3">
            {Object.entries(forecast.stage_breakdown).map(([stage, info]) => (
              <div key={stage} className="flex items-center gap-4">
                <span className="w-36 text-sm text-slate-400 truncate">{stage}</span>
                <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 to-cyan-500 rounded-full transition-all"
                    style={{ width: `${forecast.pipeline_value_raw > 0 ? (info.value / forecast.pipeline_value_raw) * 100 : 0}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-slate-300 w-16 text-right">{info.count}</span>
                <span className="text-sm font-medium text-emerald-400 w-24 text-right">${Math.round(info.value).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Question 4: Who needs attention today? */}
        <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-6 space-y-4">
          <h3 className="text-sm font-semibold text-rose-400 uppercase tracking-wider">Needs Attention</h3>
          {attentionLeads.length === 0 ? (
            <p className="text-sm text-slate-500 py-4">No deals need urgent attention.</p>
          ) : (
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {attentionLeads.slice(0, 8).map(item => (
                <div
                  key={item.id}
                  onClick={() => handleCardClick(item.id)}
                  className="flex items-center justify-between rounded-2xl border border-white/5 bg-white/[0.02] p-3.5 cursor-pointer transition hover:border-rose-500/20 hover:bg-rose-500/5"
                >
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-white truncate">{item.business_name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {item.days_since_contact >= 0 ? `${item.days_since_contact}d since contact` : "Never contacted"} · {item.stage_label}
                    </p>
                  </div>
                  <div className="ml-3 text-right shrink-0">
                    <p className="text-sm font-bold text-emerald-400">{item.estimated_deal_size || "--"}</p>
                    <p className={`text-[10px] font-semibold uppercase ${item.deal_health_status === "Critical" ? "text-rose-400" : "text-orange-400"}`}>
                      {item.deal_health_status}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Question 5: What deals are closest to closing? / Who to contact today */}
        <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-6 space-y-4">
          <h3 className="text-sm font-semibold text-amber-400 uppercase tracking-wider">Contact Today</h3>
          {contactToday.length === 0 ? (
            <p className="text-sm text-slate-500 py-4">No calls or follow-ups scheduled today.</p>
          ) : (
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {contactToday.slice(0, 8).map(item => (
                <div
                  key={item.id}
                  onClick={() => handleCardClick(item.id)}
                  className="flex items-center justify-between rounded-2xl border border-white/5 bg-white/[0.02] p-3.5 cursor-pointer transition hover:border-amber-500/20 hover:bg-amber-500/5"
                >
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-white truncate">{item.business_name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{item.next_action} · {item.stage_label}</p>
                  </div>
                  <div className="ml-3 flex items-center gap-3 shrink-0">
                    {item.business_phone && (
                      <a href={`tel:${item.business_phone}`} onClick={e => e.stopPropagation()} className="rounded-lg bg-emerald-500/10 p-1.5 text-emerald-400 hover:bg-emerald-500/20">
                        <Phone className="h-3.5 w-3.5" />
                      </a>
                    )}
                    <span className="text-sm font-bold text-emerald-400">{item.estimated_deal_size || "--"}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        {/* Phase 6A: Delivery Intelligence Section */}
        {projectStats && (
          <div className="mt-8">
            <h2 className="text-xl font-bold text-white tracking-tight mb-4 flex items-center gap-2">
              <FolderKanban className="h-5 w-5 text-cyan-400" />
              Delivery Intelligence
            </h2>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-xl border border-white/10 bg-slate-900/50 p-6 shadow-xl backdrop-blur-3xl">
                <div className="flex items-center gap-4">
                  <div className="rounded-xl bg-cyan-400/10 p-3 ring-1 ring-cyan-400/20">
                    <FolderKanban className="h-6 w-6 text-cyan-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-400">Active Projects</p>
                    <p className="text-2xl font-bold text-white">{projectStats.active_projects}</p>
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-white/10 bg-slate-900/50 p-6 shadow-xl backdrop-blur-3xl">
                <div className="flex items-center gap-4">
                  <div className="rounded-xl bg-emerald-400/10 p-3 ring-1 ring-emerald-400/20">
                    <DollarSign className="h-6 w-6 text-emerald-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-400">Revenue in Delivery</p>
                    <p className="text-2xl font-bold text-white">${projectStats.revenue_in_delivery.toLocaleString()}</p>
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-red-500/20 bg-slate-900/50 p-6 shadow-xl backdrop-blur-3xl shadow-red-500/5">
                <div className="flex items-center gap-4">
                  <div className="rounded-xl bg-red-400/10 p-3 ring-1 ring-red-400/20">
                    <AlertOctagon className="h-6 w-6 text-red-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-400">Projects at Risk</p>
                    <p className="text-2xl font-bold text-red-400">{projectStats.projects_at_risk + projectStats.projects_critical}</p>
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-emerald-500/20 bg-slate-900/50 p-6 shadow-xl backdrop-blur-3xl shadow-emerald-500/5">
                <div className="flex items-center gap-4">
                  <div className="rounded-xl bg-emerald-400/10 p-3 ring-1 ring-emerald-400/20">
                    <Target className="h-6 w-6 text-emerald-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-400">Retainer Opportunities</p>
                    <p className="text-2xl font-bold text-emerald-400">{projectStats.retainer_opportunities}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {selectedLead && (
        <LeadDetail
          lead={selectedLead}
          onClose={() => setSelectedLead(null)}
          onUpdate={(id, data) => updateLead(id, data)}
          logActivity={logActivity}
        />
      )}
    </div>
  );
}
