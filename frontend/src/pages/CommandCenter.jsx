import { Search, SortDesc, Filter, ExternalLink } from "lucide-react";
import { useEffect, useState } from "react";
import LeadDetail from "@/components/LeadDetail";
import { getCommandCenter, getPipelineRevenue } from "@/services/api";
import { useLeads } from "@/hooks/useLeads";

function priorityText(priority) {
  if (priority === 3) return "High";
  if (priority === 2) return "Medium";
  if (priority === 1) return "Low";
  return "--";
}

export default function CommandCenter() {
  const { fetchLeadDetails, updateLead, logActivity } = useLeads();
  const [leads, setLeads] = useState([]);
  const [revenue, setRevenue] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const [filters, setFilters] = useState({
    opportunity_type: "",
    min_revenue_potential: "",
    min_readiness: "",
    next_action: ""
  });
  
  const [selectedLead, setSelectedLead] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const activeFilters = {};
      if (filters.opportunity_type) activeFilters.opportunity_type = filters.opportunity_type;
      if (filters.min_revenue_potential) activeFilters.min_revenue_potential = parseInt(filters.min_revenue_potential, 10);
      if (filters.min_readiness) activeFilters.min_readiness = parseInt(filters.min_readiness, 10);
      if (filters.next_action) activeFilters.next_action = filters.next_action;
      
      const data = await getCommandCenter(activeFilters);
      setLeads(data);
      const revData = await getPipelineRevenue();
      setRevenue(revData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filters]);

  const handleRowClick = async (leadId) => {
    const detail = await fetchLeadDetails(leadId);
    setSelectedLead(detail);
  };
  
  const handleUpdate = async (leadId, data) => {
    const updated = await updateLead(leadId, data);
    if (selectedLead && selectedLead.id === leadId) {
      setSelectedLead({ ...selectedLead, ...updated });
    }
    fetchData();
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
        <p className="text-xs uppercase tracking-[0.24em] text-emerald-400/70">Revenue Operations</p>
        <h2 className="mt-2 text-3xl font-semibold text-white">Lead Command Center</h2>
        <p className="mt-3 max-w-3xl text-sm text-slate-400">
          Prioritized pipeline of high-opportunity leads sorted by revenue potential and sales readiness.
        </p>
      </div>
      
      {revenue && (
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-5 shadow-lg">
            <p className="text-sm text-emerald-400 font-medium">Pipeline Revenue</p>
            <p className="mt-2 text-3xl font-bold text-white">{revenue.potential_revenue_fmt}</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-5 shadow-lg">
            <p className="text-sm text-cyan-400 font-medium">Won Revenue</p>
            <p className="mt-2 text-3xl font-bold text-white">{revenue.won_revenue_fmt}</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-5 shadow-lg">
            <p className="text-sm text-rose-400 font-medium">Lost Revenue</p>
            <p className="mt-2 text-3xl font-bold text-white">{revenue.lost_revenue_fmt}</p>
          </div>
        </div>
      )}

      <div className="rounded-3xl border border-white/10 bg-slate-950/60 shadow-[0_12px_40px_rgba(15,23,42,0.35)]">
        <div className="flex flex-col gap-4 border-b border-white/10 px-6 py-5 lg:flex-row lg:items-center">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-400" />
            <span className="text-sm text-slate-400">Filters:</span>
          </div>
          <select
            value={filters.opportunity_type}
            onChange={(e) => setFilters({...filters, opportunity_type: e.target.value})}
            className="rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-2 text-sm text-white outline-none"
          >
            <option value="">All Opportunity Types</option>
            <option value="Full Build Opportunity">Full Build Opportunity</option>
            <option value="Conversion & Automation">Conversion & Automation</option>
            <option value="Tracking & Analytics">Tracking & Analytics</option>
            <option value="SEO & Modernization">SEO & Modernization</option>
            <option value="Growth Retainer">Growth Retainer</option>
          </select>
          <select
            value={filters.next_action}
            onChange={(e) => setFilters({...filters, next_action: e.target.value})}
            className="rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-2 text-sm text-white outline-none"
          >
            <option value="">All Next Actions</option>
            <option value="Call">Call</option>
            <option value="Email">Email</option>
            <option value="Follow Up">Follow Up</option>
            <option value="Meeting">Meeting</option>
            <option value="Proposal">Proposal</option>
          </select>
          <select
            value={filters.min_readiness}
            onChange={(e) => setFilters({...filters, min_readiness: e.target.value})}
            className="rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-2 text-sm text-white outline-none"
          >
            <option value="">Min Sales Readiness</option>
            <option value="90">90+</option>
            <option value="75">75+</option>
            <option value="50">50+</option>
          </select>
          <button 
            onClick={() => setFilters({opportunity_type: "", min_revenue_potential: "", min_readiness: "", next_action: ""})}
            className="ml-auto text-sm text-slate-400 hover:text-white"
          >
            Clear Filters
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-white/10 bg-slate-950/95 text-xs uppercase tracking-[0.18em] text-slate-500">
              <tr>
                <th className="px-6 py-4">Business</th>
                <th className="px-6 py-4">Opp. Type</th>
                <th className="px-6 py-4">Rev. Potential</th>
                <th className="px-6 py-4">Readiness</th>
                <th className="px-6 py-4">Next Action</th>
                <th className="px-6 py-4">Action Date</th>
                <th className="px-6 py-4">Deal Size</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead) => (
                <tr 
                  key={lead.id} 
                  onClick={() => handleRowClick(lead.id)}
                  className="cursor-pointer border-b border-white/5 transition hover:bg-white/5"
                >
                  <td className="px-6 py-4">
                    <div className="font-medium text-slate-100">{lead.business_name}</div>
                    {lead.business_website && (
                      <a 
                        href={lead.business_website} 
                        target="_blank" 
                        rel="noreferrer"
                        onClick={e => e.stopPropagation()}
                        className="mt-1 flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
                      >
                        Visit <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {lead.opportunity_type ? (
                      <span className="rounded-md bg-purple-500/10 px-2 py-1 text-xs text-purple-300 border border-purple-500/20">
                        {lead.opportunity_type}
                      </span>
                    ) : "--"}
                  </td>
                  <td className="px-6 py-4">
                    {lead.revenue_potential !== null ? (
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-16 overflow-hidden rounded-full bg-white/10">
                          <div 
                            className="h-full bg-emerald-400"
                            style={{ width: `${lead.revenue_potential}%` }}
                          />
                        </div>
                        <span className="text-emerald-400">{lead.revenue_potential}</span>
                      </div>
                    ) : "--"}
                  </td>
                  <td className="px-6 py-4">
                    {lead.sales_readiness !== null ? (
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-16 overflow-hidden rounded-full bg-white/10">
                          <div 
                            className="h-full bg-cyan-400"
                            style={{ width: `${lead.sales_readiness}%` }}
                          />
                        </div>
                        <span className="text-cyan-400">{lead.sales_readiness}</span>
                      </div>
                    ) : "--"}
                  </td>
                  <td className="px-6 py-4 font-medium text-amber-300">{lead.next_action || "None"}</td>
                  <td className="px-6 py-4 text-slate-400">
                    {lead.next_action_date ? new Date(lead.next_action_date).toLocaleDateString() : "--"}
                  </td>
                  <td className="px-6 py-4 font-medium text-emerald-300">{lead.deal_size || "--"}</td>
                </tr>
              ))}
              {!loading && leads.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-10 text-center text-slate-500">
                    No leads found matching criteria.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
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
