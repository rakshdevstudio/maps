import { useState, useEffect } from "react";
import { formatDistanceToNow } from "date-fns";
import { getProposals, getProposalPdfUrl, sendProposal, acceptProposal, rejectProposal } from "@/services/api";
import { toast } from "sonner";
import { FiSend, FiCheck, FiX, FiDownload } from "react-icons/fi";

export default function Proposals() {
  const [proposals, setProposals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("all");

  const fetchProposals = async () => {
    setLoading(true);
    try {
      const data = await getProposals({ status: statusFilter === "all" ? "" : statusFilter });
      
      // Module 12: Deal Closing Command Center Sorting
      // Sort: Highest Value First, Then Highest Acceptance Probability
      data.sort((a, b) => {
        if (b.amount_min !== a.amount_min) {
          return b.amount_min - a.amount_min;
        }
        return b.close_probability - a.close_probability;
      });
      
      setProposals(data);
    } catch (err) {
      // Error handled by interceptor
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProposals();
  }, [statusFilter]);

  const handleSend = async (id) => {
    try {
      await sendProposal(id);
      toast.success("Proposal marked as sent!");
      fetchProposals();
    } catch (e) {}
  };

  const handleAccept = async (id) => {
    const reason = prompt("Why did we win this? (e.g., Price, Speed, Features)");
    if (!reason) return;
    try {
      await acceptProposal(id, { reason_category: reason, notes: "" });
      toast.success("Proposal marked as WON! 🎉");
      fetchProposals();
    } catch (e) {}
  };

  const handleReject = async (id) => {
    const reason = prompt("Why did we lose this? (e.g., Budget, Competition)");
    if (!reason) return;
    try {
      await rejectProposal(id, { reason_category: reason, notes: "" });
      toast.success("Proposal marked as lost.");
      fetchProposals();
    } catch (e) {}
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white tracking-tight">Proposals</h1>
        <select
          className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-white shadow-sm outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="all">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="sent">Sent</option>
          <option value="viewed">Viewed</option>
          <option value="negotiation">Negotiation</option>
          <option value="accepted">Won</option>
          <option value="rejected">Lost</option>
        </select>
      </div>

      <div className="rounded-xl border border-white/10 bg-slate-900/50 p-6 backdrop-blur-xl shadow-2xl">
        {loading ? (
          <div className="flex h-32 items-center justify-center text-slate-400">Loading proposals...</div>
        ) : proposals.length === 0 ? (
          <div className="flex h-32 items-center justify-center text-slate-400">No proposals found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-800/50 text-xs font-semibold uppercase text-slate-400">
                <tr>
                  <th className="px-4 py-3">Proposal</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Value</th>
                  <th className="px-4 py-3">Acceptance Prob.</th>
                  <th className="px-4 py-3">Proposal Health</th>
                  <th className="px-4 py-3">Days Open</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {proposals.map((prop) => (
                  <tr key={prop.id} className="hover:bg-white/5 transition-colors">
                    <td className="px-4 py-4">
                      <div className="font-medium text-white">{prop.title}</div>
                      <div className="text-xs text-slate-500">{prop.proposal_number} • V{prop.version}</div>
                    </td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize
                        ${prop.status === 'accepted' ? 'bg-emerald-500/10 text-emerald-400' :
                          prop.status === 'rejected' ? 'bg-red-500/10 text-red-400' :
                          prop.status === 'sent' || prop.status === 'viewed' ? 'bg-blue-500/10 text-blue-400' :
                          'bg-slate-500/10 text-slate-400'}`}>
                        {prop.status}
                      </span>
                    </td>
                    <td className="px-4 py-4 font-medium text-emerald-400">
                      ${prop.amount_min?.toLocaleString()}
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        <div className="bg-slate-800 rounded-full h-1.5 w-16">
                          <div className={`h-1.5 rounded-full ${prop.close_probability > 70 ? 'bg-emerald-500' : prop.close_probability > 40 ? 'bg-amber-500' : 'bg-red-500'}`} style={{ width: `${prop.close_probability}%` }}></div>
                        </div>
                        <span className="text-xs text-slate-400">{prop.close_probability}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="text-xs text-slate-300">Views: <span className="font-bold text-white">{prop.view_count || 0}</span></div>
                      <div className="text-xs text-slate-400">Last: {prop.last_viewed_at ? formatDistanceToNow(new Date(prop.last_viewed_at + 'Z'), { addSuffix: true }) : 'Never'}</div>
                    </td>
                    <td className="px-4 py-4 text-slate-400 text-xs">
                      {formatDistanceToNow(new Date(prop.created_at + 'Z'))}
                    </td>
                    <td className="px-4 py-4 text-right">
                      <div className="flex justify-end gap-2">
                        <a href={`/proposal/${prop.public_token}`} target="_blank" rel="noreferrer" title="Open Digital Portal" className="p-2 rounded hover:bg-cyan-500/20 text-cyan-400 transition font-bold text-xs uppercase tracking-wider flex items-center">
                          Portal
                        </a>
                        <a href={getProposalPdfUrl(prop.id)} target="_blank" rel="noreferrer" title="Download PDF" className="p-2 rounded hover:bg-slate-700 text-slate-400 hover:text-white transition">
                          <FiDownload />
                        </a>
                        {prop.status === 'draft' && (
                          <button onClick={() => handleSend(prop.id)} title="Mark Sent" className="p-2 rounded hover:bg-blue-500/20 text-blue-400 transition">
                            <FiSend />
                          </button>
                        )}
                        {(prop.status === 'sent' || prop.status === 'viewed' || prop.status === 'negotiation') && (
                          <>
                            <button onClick={() => handleAccept(prop.id)} title="Mark Won" className="p-2 rounded hover:bg-emerald-500/20 text-emerald-400 transition">
                              <FiCheck />
                            </button>
                            <button onClick={() => handleReject(prop.id)} title="Mark Lost" className="p-2 rounded hover:bg-red-500/20 text-red-400 transition">
                              <FiX />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
