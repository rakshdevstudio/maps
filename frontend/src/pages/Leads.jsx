import { Search } from "lucide-react";
import { useEffect, useState } from "react";

import LeadDetail from "@/components/LeadDetail";
import { useLeads } from "@/hooks/useLeads";

function priorityText(priority) {
  if (priority === 3) return "★★★ High";
  if (priority === 2) return "★★ Medium";
  if (priority === 1) return "★ Low";
  return "--";
}

function statusBadge(status) {
  const styles = {
    new: "bg-blue-500/10 text-blue-300 border-blue-500/20",
    contacted: "bg-amber-500/10 text-amber-300 border-amber-500/20",
    interested: "bg-purple-500/10 text-purple-300 border-purple-500/20",
    not_interested: "bg-slate-500/10 text-slate-300 border-slate-500/20",
    closed_won: "bg-emerald-500/10 text-emerald-300 border-emerald-500/20",
    closed_lost: "bg-rose-500/10 text-rose-300 border-rose-500/20",
  };
  const labels = {
    new: "New",
    contacted: "Contacted",
    interested: "Interested",
    not_interested: "Not Interested",
    closed_won: "Closed Won",
    closed_lost: "Closed Lost",
  };
  return (
    <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles[status]}`}>
      {labels[status]}
    </span>
  );
}

export default function Leads() {
  const { leads, stats, pagination, loading, fetchLeads, fetchStats, updateLead, fetchLeadDetails, logActivity } = useLeads();
  const [activeTab, setActiveTab] = useState("");
  const [search, setSearch] = useState("");
  const [priority, setPriority] = useState("");
  const [page, setPage] = useState(1);
  const [selectedLead, setSelectedLead] = useState(null);
  
  useEffect(() => {
    fetchLeads(page, 50, activeTab, priority || null, search);
    fetchStats();
  }, [fetchLeads, fetchStats, page, activeTab, priority, search]);

  const handleRowClick = async (leadId) => {
    const detail = await fetchLeadDetails(leadId);
    setSelectedLead(detail);
  };
  
  const handleUpdate = async (leadId, data) => {
    const updated = await updateLead(leadId, data);
    if (selectedLead && selectedLead.id === leadId) {
      setSelectedLead({ ...selectedLead, ...updated });
    }
  };

  const handleLogActivity = async (leadId, type, content) => {
    const activity = await logActivity(leadId, type, content);
    if (selectedLead && selectedLead.id === leadId) {
      setSelectedLead({
        ...selectedLead,
        activities: [activity, ...(selectedLead.activities || [])]
      });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-[0.24em] text-cyan-300/70">Pipeline</p>
        <h2 className="mt-2 text-3xl font-semibold text-white">Lead Management</h2>
        <p className="mt-3 max-w-3xl text-sm text-slate-400">
          Track and close the businesses you discovered.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <button onClick={() => { setActiveTab(""); setPage(1); }} className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${activeTab === "" ? "bg-white/10 text-white" : "text-slate-400 hover:bg-white/5"}`}>All Leads</button>
        <button onClick={() => { setActiveTab("new"); setPage(1); }} className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${activeTab === "new" ? "bg-blue-500/20 text-blue-200" : "text-slate-400 hover:bg-white/5"}`}>New ({stats.new || 0})</button>
        <button onClick={() => { setActiveTab("contacted"); setPage(1); }} className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${activeTab === "contacted" ? "bg-amber-500/20 text-amber-200" : "text-slate-400 hover:bg-white/5"}`}>Contacted ({stats.contacted || 0})</button>
        <button onClick={() => { setActiveTab("interested"); setPage(1); }} className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${activeTab === "interested" ? "bg-purple-500/20 text-purple-200" : "text-slate-400 hover:bg-white/5"}`}>Interested ({stats.interested || 0})</button>
        <button onClick={() => { setActiveTab("closed_won"); setPage(1); }} className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${activeTab === "closed_won" ? "bg-emerald-500/20 text-emerald-200" : "text-slate-400 hover:bg-white/5"}`}>Closed ({stats.closed_won || 0})</button>
      </div>

      <div className="rounded-3xl border border-white/10 bg-slate-950/60 shadow-[0_12px_40px_rgba(15,23,42,0.35)]">
        <div className="flex flex-col gap-4 border-b border-white/10 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-1 items-center gap-4">
            <label className="relative w-full max-w-sm">
              <Search className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-slate-500" />
              <input
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                placeholder="Search leads..."
                className="w-full rounded-2xl border border-white/10 bg-slate-950/90 py-3 pl-9 pr-3 text-sm text-white outline-none placeholder:text-slate-500"
              />
            </label>
            <select
              value={priority}
              onChange={(e) => { setPriority(e.target.value); setPage(1); }}
              className="rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-sm text-white outline-none"
            >
              <option value="">All Priorities</option>
              <option value="3">★★★ High</option>
              <option value="2">★★ Medium</option>
              <option value="1">★ Low</option>
              <option value="0">None</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-white/10 bg-slate-950/95 text-xs uppercase tracking-[0.18em] text-slate-500">
              <tr>
                <th className="px-6 py-4">Priority</th>
                <th className="px-6 py-4">Name</th>
                <th className="px-6 py-4">Phone</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Notes</th>
                <th className="px-6 py-4">Next Followup</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead) => (
                <tr 
                  key={lead.id} 
                  onClick={() => handleRowClick(lead.id)}
                  className="cursor-pointer border-b border-white/5 transition hover:bg-white/5"
                >
                  <td className="px-6 py-4 text-amber-400">{priorityText(lead.priority)}</td>
                  <td className="max-w-[14rem] px-6 py-4 font-medium text-slate-100">{lead.business.name}</td>
                  <td className="px-6 py-4 text-slate-300">{lead.business.phone || "--"}</td>
                  <td className="px-6 py-4">{statusBadge(lead.status)}</td>
                  <td className="max-w-[15rem] truncate px-6 py-4 text-slate-400">{lead.notes || "--"}</td>
                  <td className="px-6 py-4 text-cyan-200">
                    {lead.next_followup ? new Date(lead.next_followup).toLocaleDateString() : "--"}
                  </td>
                </tr>
              ))}
              {!loading && leads.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-10 text-center text-slate-500">
                    No leads found. Promote businesses from the Dashboard to get started.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between border-t border-white/10 px-6 py-4 text-sm text-slate-400">
          <span>Page {pagination.page} of {pagination.total_pages}</span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={pagination.page <= 1}
              className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 transition hover:bg-white/10 disabled:opacity-40"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((current) => Math.min(pagination.total_pages, current + 1))}
              disabled={pagination.page >= pagination.total_pages}
              className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 transition hover:bg-white/10 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </div>
      
      {selectedLead && (
        <LeadDetail 
          lead={selectedLead} 
          onClose={() => setSelectedLead(null)}
          onUpdate={handleUpdate}
          logActivity={handleLogActivity}
        />
      )}
    </div>
  );
}
