import { useEffect, useState } from "react";
import { Clock, Phone, MessageSquare, CalendarCheck, AlertTriangle, ExternalLink, ArrowRight } from "lucide-react";
import { getTodayView, getPipelineForecast } from "@/services/api";
import LeadDetail from "@/components/LeadDetail";
import { useLeads } from "@/hooks/useLeads";

const HEALTH_COLORS = {
  Healthy: "emerald",
  Warm: "amber",
  "At Risk": "orange",
  Critical: "rose",
};

function HealthBadge({ status }) {
  const color = HEALTH_COLORS[status] || "slate";
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border border-${color}-500/30 bg-${color}-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-${color}-400`}>
      <span className={`h-1.5 w-1.5 rounded-full bg-${color}-400`} />
      {status}
    </span>
  );
}

function TodayCard({ item, onClick }) {
  return (
    <div
      onClick={() => onClick(item.id)}
      className="group cursor-pointer rounded-2xl border border-white/10 bg-white/[0.02] p-4 transition hover:border-white/20 hover:bg-white/[0.04]"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-white truncate">{item.business_name}</h4>
          <p className="mt-1 text-xs text-slate-500">{item.stage_label}</p>
        </div>
        <div className="ml-3 flex flex-col items-end gap-1.5">
          {item.estimated_deal_size && (
            <span className="text-sm font-bold text-emerald-400">{item.estimated_deal_size}</span>
          )}
          <HealthBadge status={item.deal_health_status} />
        </div>
      </div>
      <div className="mt-3 flex items-center gap-4 text-xs text-slate-500">
        {item.days_since_contact >= 0 && (
          <span className={item.days_since_contact > 14 ? "text-rose-400 font-semibold" : ""}>
            {item.days_since_contact}d since contact
          </span>
        )}
        {item.next_action && (
          <span className="flex items-center gap-1 text-amber-400">
            <ArrowRight className="h-3 w-3" /> {item.next_action}
          </span>
        )}
        {item.business_phone && (
          <a href={`tel:${item.business_phone}`} onClick={e => e.stopPropagation()} className="hover:text-cyan-300">
            {item.business_phone}
          </a>
        )}
      </div>
    </div>
  );
}

function Section({ icon: Icon, title, count, color, children }) {
  if (!children || (Array.isArray(children) && children.length === 0)) return null;
  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <div className={`rounded-xl bg-${color}-500/10 p-2.5 border border-${color}-500/20`}>
          <Icon className={`h-5 w-5 text-${color}-400`} />
        </div>
        <div>
          <h3 className="text-base font-semibold text-white">{title}</h3>
          <p className="text-xs text-slate-500">{count} item{count !== 1 ? "s" : ""}</p>
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {children}
      </div>
    </div>
  );
}

export default function Today() {
  const { fetchLeadDetails, updateLead, logActivity } = useLeads();
  const [data, setData] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [todayData, forecastData] = await Promise.all([
          getTodayView(),
          getPipelineForecast(),
        ]);
        setData(todayData);
        setForecast(forecastData);
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

  const handleUpdate = async (leadId, updates) => {
    await updateLead(leadId, updates);
    if (selectedLead?.id === leadId) {
      const detail = await fetchLeadDetails(leadId);
      setSelectedLead(detail);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center py-32 text-slate-500">Loading today's priorities...</div>;
  }

  const summary = data?.summary || {};
  const totalActions = (summary.overdue_count || 0) + (summary.calls_count || 0) + (summary.followups_count || 0) + (summary.meetings_count || 0);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <p className="text-xs uppercase tracking-[0.24em] text-amber-400/70">Sales Execution</p>
        <h2 className="mt-2 text-3xl font-semibold text-white">Today</h2>
        <p className="mt-2 text-sm text-slate-400">
          {totalActions > 0
            ? `${totalActions} action${totalActions !== 1 ? "s" : ""} require your attention.`
            : "All clear — no urgent actions today."}
        </p>
      </div>

      {/* Summary Bar */}
      {forecast && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider">Pipeline</p>
            <p className="mt-1.5 text-2xl font-bold text-white">{forecast.pipeline_value}</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
            <p className="text-xs text-emerald-500 uppercase tracking-wider">Likely Revenue</p>
            <p className="mt-1.5 text-2xl font-bold text-emerald-400">{forecast.likely_revenue}</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
            <p className="text-xs text-rose-500 uppercase tracking-wider">At Risk</p>
            <p className="mt-1.5 text-2xl font-bold text-rose-400">{forecast.at_risk_revenue}</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
            <p className="text-xs text-cyan-500 uppercase tracking-wider">Won Revenue</p>
            <p className="mt-1.5 text-2xl font-bold text-cyan-400">{forecast.won_revenue}</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
            <p className="text-xs text-indigo-500 uppercase tracking-wider">Win Rate</p>
            <p className="mt-1.5 text-2xl font-bold text-indigo-400">{forecast.win_rate}</p>
          </div>
        </div>
      )}

      {/* Action Sections */}
      <div className="space-y-10">
        <Section icon={AlertTriangle} title="Overdue Leads" count={data?.overdue?.length || 0} color="rose">
          {data?.overdue?.map(item => <TodayCard key={item.id} item={item} onClick={handleCardClick} />)}
        </Section>

        <Section icon={Phone} title="Calls Due Today" count={data?.calls_due?.length || 0} color="amber">
          {data?.calls_due?.map(item => <TodayCard key={item.id} item={item} onClick={handleCardClick} />)}
        </Section>

        <Section icon={MessageSquare} title="Follow-ups Due" count={data?.followups_due?.length || 0} color="blue">
          {data?.followups_due?.map(item => <TodayCard key={item.id} item={item} onClick={handleCardClick} />)}
        </Section>

        <Section icon={CalendarCheck} title="Meetings Scheduled" count={data?.meetings_scheduled?.length || 0} color="purple">
          {data?.meetings_scheduled?.map(item => <TodayCard key={item.id} item={item} onClick={handleCardClick} />)}
        </Section>

        <Section icon={Clock} title="Critical Deals" count={data?.critical_deals?.length || 0} color="orange">
          {data?.critical_deals?.map(item => <TodayCard key={item.id} item={item} onClick={handleCardClick} />)}
        </Section>
      </div>

      {totalActions === 0 && (
        <div className="flex flex-col items-center justify-center rounded-3xl border border-white/10 bg-white/[0.02] py-16 text-center">
          <div className="rounded-2xl bg-emerald-500/10 p-4">
            <CalendarCheck className="h-8 w-8 text-emerald-400" />
          </div>
          <p className="mt-4 text-lg font-medium text-white">You're all caught up.</p>
          <p className="mt-2 text-sm text-slate-500">No overdue contacts, no pending calls, no critical deals.</p>
        </div>
      )}

      {selectedLead && (
        <LeadDetail
          lead={selectedLead}
          onClose={() => setSelectedLead(null)}
          onUpdate={handleUpdate}
          logActivity={logActivity}
        />
      )}
    </div>
  );
}
