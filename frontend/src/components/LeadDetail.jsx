import { X, RefreshCw, ExternalLink, Activity, Target, Copy, Zap, MessageSquare, PhoneCall, Mail, CheckCircle2, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { runAudit, getLeadOutreach, generateLeadOutreach, getProposalTemplates, generateProposal, getProposals, getProposalPdfUrl, sendProposal, acceptProposal, rejectProposal, getProposalStrategy } from "../services/api";

export default function LeadDetail({ lead, onClose, onUpdate, logActivity }) {
  const [notes, setNotes] = useState(lead.notes || "");
  const [status, setStatus] = useState(lead.status);
  const [priority, setPriority] = useState(lead.priority);
  const [contactName, setContactName] = useState(lead.contactName || "");
  const [dealStage, setDealStage] = useState(lead.deal_stage || "lead_found");
  const [saving, setSaving] = useState(false);
  
  const [activityType, setActivityType] = useState("note");
  const [activityContent, setActivityContent] = useState("");
  const [logging, setLogging] = useState(false);
  
  const [auditing, setAuditing] = useState(false);
  const [auditData, setAuditData] = useState(lead.latest_audit);
  
  const [outreachData, setOutreachData] = useState(null);
  const [loadingOutreach, setLoadingOutreach] = useState(false);
  const [activeOutreachTab, setActiveOutreachTab] = useState("cold_email");
  
  const [proposals, setProposals] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [generatingProposal, setGeneratingProposal] = useState(false);
  const [aiStrategy, setAiStrategy] = useState(null);
  
  const fetchLeadProposals = async () => {
    try {
      const data = await getProposals();
      setProposals(data.filter(p => p.lead_id === lead.id));
    } catch (e) {}
  };
  
  const fetchTemplates = async () => {
    try {
      const data = await getProposalTemplates();
      setTemplates(data);
    } catch (e) {}
  };

  useEffect(() => {
    setNotes(lead.notes || "");
    setStatus(lead.status);
    setPriority(lead.priority);
    setContactName(lead.contactName || "");
    setDealStage(lead.deal_stage || "lead_found");
    setAuditData(lead.latest_audit);
    setOutreachData(null);
    fetchLeadProposals();
    fetchTemplates();
    getProposalStrategy(lead.id).then(setAiStrategy).catch(() => {});
  }, [lead]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await onUpdate(lead.id, {
        notes,
        status,
        priority: Number(priority),
        contact_name: contactName,
        deal_stage: dealStage,
      });
    } finally {
      setSaving(false);
    }
  };

  const handleLogActivity = async () => {
    if (!activityContent.trim()) return;
    setLogging(true);
    try {
      await logActivity(lead.id, activityType, activityContent);
      setActivityContent("");
      // Need a way to refresh activities - this will be handled by parent re-fetching or optimistic UI
      toast.success("Activity logged");
    } finally {
      setLogging(false);
    }
  };

  const handleRunAudit = async () => {
    setAuditing(true);
    try {
      const result = await runAudit(lead.id);
      setAuditData(result);
      toast.success("Website audit complete");
    } catch (err) {
      // API interceptor handles toast
    } finally {
      setAuditing(false);
    }
  };

  const handleGenerateOutreach = async () => {
    if (!auditData) return;
    setLoadingOutreach(true);
    try {
      const result = await generateLeadOutreach(lead.id);
      setOutreachData(result);
      toast.success("Outreach Intelligence Generated");
    } catch (err) {
      // API error intercepted
    } finally {
      setLoadingOutreach(false);
    }
  };
  
  const handleGenerateProposal = async (templateId) => {
    setGeneratingProposal(true);
    try {
      await generateProposal(lead.id, { template_id: parseInt(templateId) });
      toast.success("Proposal Generated!");
      fetchLeadProposals();
      // Optimistically update deal stage UI
      setDealStage("proposal_draft");
    } catch (e) {
    } finally {
      setGeneratingProposal(false);
    }
  };
  
  const handleProposalAction = async (action, propId) => {
    try {
      if (action === "send") await sendProposal(propId);
      if (action === "accept") {
        const r = prompt("Win Reason?");
        if (!r) return;
        await acceptProposal(propId, { reason_category: r });
      }
      if (action === "reject") {
        const r = prompt("Loss Reason?");
        if (!r) return;
        await rejectProposal(propId, { reason_category: r });
      }
      fetchLeadProposals();
      toast.success("Proposal updated");
    } catch (e) {}
  };
  
  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard");
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md border-l border-white/10 bg-slate-950/95 shadow-2xl backdrop-blur-xl sm:w-[32rem]">
      <div className="flex h-full flex-col">
        <div className="flex items-center justify-between border-b border-white/10 px-6 py-5">
          <div>
            <h2 className="text-xl font-semibold text-white">{lead.business.name}</h2>
            <p className="mt-1 text-sm text-slate-400">
              {lead.business.category} • {lead.business.rating ? `${lead.business.rating} ★` : "No rating"}
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-2 text-slate-400 hover:bg-white/10 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-6">
          
            {/* Phase 3: Next Action Bar */}
            {lead.next_action && (
              <div className="rounded-3xl border border-amber-500/20 bg-gradient-to-r from-amber-500/10 to-orange-500/5 p-4 flex items-center justify-between shadow-lg">
                <div className="flex items-center gap-3">
                  <div className="rounded-full bg-amber-500/20 p-2">
                    <Zap className="h-5 w-5 text-amber-400" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-amber-500/80">Next Action</p>
                    <p className="text-lg font-bold text-amber-300">{lead.next_action}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500">Scheduled for</p>
                  <p className="text-sm font-medium text-slate-300">
                    {lead.next_action_date ? new Date(lead.next_action_date).toLocaleDateString() : "Immediate"}
                  </p>
                </div>
              </div>
            )}

            <div className="grid gap-4 rounded-3xl border border-white/10 bg-white/[0.02] p-5 sm:grid-cols-2">
              <div>
                <label className="text-xs uppercase tracking-[0.1em] text-slate-500">Status</label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white outline-none"
                >
                  <option value="new">New</option>
                  <option value="contacted">Contacted</option>
                  <option value="interested">Interested</option>
                  <option value="not_interested">Not Interested</option>
                  <option value="closed_won">Closed Won</option>
                  <option value="closed_lost">Closed Lost</option>
                </select>
              </div>
              <div>
                <label className="text-xs uppercase tracking-[0.1em] text-slate-500">Priority</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white outline-none"
                >
                  <option value={0}>None</option>
                  <option value={1}>Low</option>
                  <option value={2}>Medium</option>
                  <option value={3}>High</option>
                </select>
              </div>
            </div>

            {/* Phase 4: Deal Stage */}
            <div className="rounded-3xl border border-white/10 bg-white/[0.02] p-5">
              <label className="text-xs uppercase tracking-[0.1em] text-slate-500">Deal Stage</label>
              <select
                value={dealStage}
                onChange={(e) => setDealStage(e.target.value)}
                className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900 px-3 py-2.5 text-sm text-white outline-none"
              >
                <option value="lead_found">Lead Found (5%)</option>
                <option value="qualified">Qualified (15%)</option>
                <option value="contacted">Contacted (25%)</option>
                <option value="discovery_call">Discovery Call (40%)</option>
                <option value="meeting_scheduled">Meeting Scheduled (55%)</option>
                <option value="proposal_sent">Proposal Sent (70%)</option>
                <option value="negotiation">Negotiation (85%)</option>
                <option value="closed_won">Closed Won (100%)</option>
                <option value="closed_lost">Closed Lost (0%)</option>
              </select>
            </div>

            <div className="space-y-4 rounded-3xl border border-white/10 bg-white/[0.02] p-5">
              <h3 className="text-sm font-semibold text-slate-300">Business Details</h3>
              <div className="grid gap-3 text-sm">
                <div className="flex gap-2">
                  <span className="w-20 text-slate-500">Phone</span>
                  <span className="text-slate-200">{lead.business.phone || "--"}</span>
                </div>
                <div className="flex gap-2">
                  <span className="w-20 text-slate-500">Website</span>
                  <span className="text-cyan-300">
                    {lead.business.website ? (
                      <a href={lead.business.website} target="_blank" rel="noreferrer" className="underline">
                        {lead.business.website}
                      </a>
                    ) : (
                      "--"
                    )}
                  </span>
                </div>
                <div className="flex gap-2">
                  <span className="w-20 text-slate-500">Address</span>
                  <span className="text-slate-200">{lead.business.address || "--"}</span>
                </div>
                <div className="flex gap-2">
                  <span className="w-20 text-slate-500">Maps</span>
                  <span className="text-cyan-300">
                    <a href={lead.business.google_maps_url} target="_blank" rel="noreferrer" className="underline">
                      View on Google Maps
                    </a>
                  </span>
                </div>
              </div>
            </div>

            {/* Client Acquisition Intelligence Block */}
            <div className="space-y-4 rounded-3xl border border-white/10 bg-white/[0.02] p-5">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-300">Client Acquisition Intelligence</h3>
                <button
                  onClick={handleRunAudit}
                  disabled={auditing || !lead.business.website}
                  className="flex items-center gap-1.5 rounded-lg bg-indigo-500/10 px-3 py-1.5 text-xs font-medium text-indigo-400 transition hover:bg-indigo-500/20 disabled:opacity-40"
                >
                  <RefreshCw className={`h-3 w-3 ${auditing ? "animate-spin" : ""}`} />
                  {auditing ? "Auditing..." : auditData ? "Re-Audit" : "Run Deep Audit"}
                </button>
              </div>

              {!lead.business.website ? (
                <p className="text-xs text-slate-500">Business has no website to audit.</p>
              ) : !auditData && !auditing ? (
                <p className="text-xs text-slate-500">No audit data yet. Run an audit to generate intelligence.</p>
              ) : auditing && !auditData ? (
                <div className="flex flex-col items-center justify-center py-6">
                  <RefreshCw className="h-6 w-6 animate-spin text-indigo-400" />
                  <p className="mt-3 text-xs font-medium text-slate-400">Performing deep site crawl...</p>
                </div>
              ) : auditData ? (
                <div className="space-y-5 animate-in fade-in duration-300">
                  {/* Scores */}
                  <div className="grid grid-cols-4 gap-2">
                    <div className="rounded-xl border border-slate-500/20 bg-slate-500/5 p-2 text-center">
                      <div className="text-xl font-bold text-slate-400">{auditData.audit_score}</div>
                      <div className="mt-1 text-[9px] uppercase tracking-wider text-slate-500/70">Audit</div>
                    </div>
                    <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-2 text-center">
                      <div className="text-xl font-bold text-rose-400">{auditData.conversion_score}</div>
                      <div className="mt-1 text-[9px] uppercase tracking-wider text-rose-500/70">Conversion</div>
                    </div>
                    <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-2 text-center">
                      <div className="text-xl font-bold text-emerald-400">{auditData.sales_readiness_score}</div>
                      <div className="mt-1 text-[9px] uppercase tracking-wider text-emerald-500/70">Readiness</div>
                    </div>
                    <div className="rounded-xl border border-indigo-500/20 bg-indigo-500/10 p-2 text-center relative overflow-hidden">
                      <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500/10 to-transparent"></div>
                      <div className="relative text-xl font-bold text-indigo-400">{auditData.revenue_potential_score}</div>
                      <div className="relative mt-1 text-[9px] uppercase tracking-wider text-indigo-500/70">Rev Potential</div>
                    </div>
                  </div>

                  {/* Phase 3: AI Sales Brief */}
                  <div className="rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-500/10 to-teal-500/5 p-5 shadow-lg">
                    <div className="flex items-center justify-between text-sm font-semibold text-emerald-300">
                      <div className="flex items-center gap-2 uppercase tracking-widest text-xs">
                        <Target className="h-4 w-4" />
                        WHY THIS LEAD MATTERS
                      </div>
                      <span className="text-emerald-400 font-bold">{auditData.estimated_deal_size}</span>
                    </div>
                    <p className="mt-4 text-sm text-emerald-100/90 leading-relaxed font-medium">
                      "{auditData.sales_pitch_angle}"
                    </p>
                  </div>

                  {/* Pitch & Problems */}
                  <div className="space-y-4">
                    <div>
                      <span className="text-xs uppercase tracking-wider text-slate-500">Business Impact</span>
                      <div className="mt-1 text-sm font-medium text-rose-400">{auditData.business_impact}</div>
                    </div>
                    
                    <div>
                      <span className="text-xs uppercase tracking-wider text-slate-500">Revenue Leaks</span>
                      <ul className="mt-2 space-y-2">
                        {auditData.revenue_leaks?.map((leak, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-sm text-slate-300">
                            <span className="mt-1 flex h-1.5 w-1.5 shrink-0 rounded-full bg-rose-500"></span>
                            {leak}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <span className="text-xs uppercase tracking-wider text-slate-500">Nexora Service Mapping</span>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {auditData.nexora_services?.map((svc, idx) => (
                          <span key={idx} className="rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-400">
                            {svc}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Tech Stack */}
                  {auditData.tech_stack && auditData.tech_stack.length > 0 && (
                    <div className="border-t border-white/5 pt-4">
                      <span className="text-xs uppercase tracking-wider text-slate-500">Tech Stack Detected</span>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {auditData.tech_stack.map((tech, idx) => (
                          <span key={idx} className="rounded-md bg-white/5 px-2 py-1 text-[10px] font-medium text-slate-400">
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Screenshots */}
                  <div className="flex gap-4 border-t border-white/5 pt-4">
                    {auditData.screenshot_path && (
                      <a
                        href={`http://localhost:8000${auditData.screenshot_path}`}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 text-xs font-medium text-cyan-400 hover:text-cyan-300"
                      >
                        <ExternalLink className="h-3 w-3" />
                        Homepage Capture
                      </a>
                    )}
                    {auditData.conversion_screenshot_path && (
                      <a
                        href={`http://localhost:8000${auditData.conversion_screenshot_path}`}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 text-xs font-medium text-purple-400 hover:text-purple-300"
                      >
                        <ExternalLink className="h-3 w-3" />
                        Conversion Capture
                      </a>
                    )}
                  </div>

                  {/* Phase 3: Outreach Intelligence */}
                  <div className="pt-4 border-t border-white/10">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-slate-300">Outreach Intelligence</h4>
                      {!outreachData && (
                        <button
                          onClick={handleGenerateOutreach}
                          disabled={loadingOutreach}
                          className="flex items-center gap-1.5 rounded-lg bg-cyan-500/10 px-3 py-1.5 text-xs font-medium text-cyan-400 transition hover:bg-cyan-500/20 disabled:opacity-40"
                        >
                          {loadingOutreach ? <RefreshCw className="h-3 w-3 animate-spin" /> : <Zap className="h-3 w-3" />}
                          {loadingOutreach ? "Generating..." : "Generate Specific Outreach"}
                        </button>
                      )}
                    </div>
                    
                    {outreachData && (
                      <div className="mt-4 rounded-2xl border border-white/10 bg-slate-900/50 overflow-hidden">
                        <div className="flex border-b border-white/10 bg-slate-950/80">
                          <button onClick={() => setActiveOutreachTab("cold_email")} className={`flex-1 flex items-center justify-center gap-2 py-3 text-xs font-medium transition ${activeOutreachTab === "cold_email" ? "text-cyan-300 bg-white/5 border-b-2 border-cyan-400" : "text-slate-500 hover:text-slate-300"}`}><Mail className="h-3.5 w-3.5"/> Email</button>
                          <button onClick={() => setActiveOutreachTab("whatsapp")} className={`flex-1 flex items-center justify-center gap-2 py-3 text-xs font-medium transition ${activeOutreachTab === "whatsapp" ? "text-green-400 bg-white/5 border-b-2 border-green-500" : "text-slate-500 hover:text-slate-300"}`}><MessageSquare className="h-3.5 w-3.5"/> WhatsApp</button>
                          <button onClick={() => setActiveOutreachTab("linkedin")} className={`flex-1 flex items-center justify-center gap-2 py-3 text-xs font-medium transition ${activeOutreachTab === "linkedin" ? "text-blue-400 bg-white/5 border-b-2 border-blue-500" : "text-slate-500 hover:text-slate-300"}`}><Activity className="h-3.5 w-3.5"/> LinkedIn</button>
                          <button onClick={() => setActiveOutreachTab("call_script")} className={`flex-1 flex items-center justify-center gap-2 py-3 text-xs font-medium transition ${activeOutreachTab === "call_script" ? "text-amber-400 bg-white/5 border-b-2 border-amber-500" : "text-slate-500 hover:text-slate-300"}`}><PhoneCall className="h-3.5 w-3.5"/> Script</button>
                        </div>
                        <div className="p-4 relative group">
                          <button onClick={() => handleCopy(outreachData[activeOutreachTab]?.content)} className="absolute top-4 right-4 rounded-md bg-white/10 p-1.5 text-slate-400 opacity-0 transition group-hover:opacity-100 hover:bg-white/20 hover:text-white">
                            <Copy className="h-4 w-4" />
                          </button>
                          <pre className="whitespace-pre-wrap font-sans text-sm text-slate-300 leading-relaxed">
                            {outreachData[activeOutreachTab]?.content}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ) : null}
            </div>
            
            {/* Phase 7: AI Proposal Strategist */}
            {aiStrategy && (
              <div className="rounded-3xl border border-indigo-500/20 bg-gradient-to-br from-indigo-500/10 to-purple-500/5 p-5 shadow-lg relative overflow-hidden">
                <div className="absolute top-0 right-0 p-16 bg-indigo-500/10 blur-[50px] rounded-full pointer-events-none" />
                <div className="flex items-center gap-2 text-sm font-semibold text-indigo-300 mb-4 relative z-10">
                  <Sparkles className="h-4 w-4" />
                  AI PROPOSAL STRATEGIST
                </div>
                
                <div className="grid gap-4 relative z-10">
                  <div>
                    <span className="text-xs uppercase tracking-wider text-slate-500">Recommended Package</span>
                    <div className="mt-1 font-bold text-white text-lg">{aiStrategy.recommended_package}</div>
                  </div>
                  <div>
                    <span className="text-xs uppercase tracking-wider text-slate-500">Suggested Investment</span>
                    <div className="mt-1 font-bold text-emerald-400 text-lg">${aiStrategy.recommended_investment.toLocaleString()}</div>
                  </div>
                  <div className="pt-2 border-t border-white/10">
                    <span className="text-xs uppercase tracking-wider text-slate-500">Sales Angle</span>
                    <p className="mt-1 text-sm text-slate-300 leading-relaxed italic">"{aiStrategy.recommended_angle}"</p>
                  </div>
                </div>
              </div>
            )}

            {/* Phase 5: Proposal Engine */}
            <div className="space-y-4 rounded-3xl border border-white/10 bg-white/[0.02] p-5">
              <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <h3 className="text-sm font-semibold text-slate-300">Proposals & Quotes</h3>
              </div>
              
              <div className="flex gap-2">
                <select id="template-select" className="flex-1 rounded-lg bg-slate-900 border border-white/10 text-sm text-slate-300 px-3 outline-none py-2">
                  <option value="">Select Template...</option>
                  {templates.map(t => <option key={t.id} value={t.id}>{t.name} - ${t.base_price.toLocaleString()}</option>)}
                </select>
                <button 
                  onClick={() => {
                    const val = document.getElementById("template-select").value;
                    if(val) handleGenerateProposal(val);
                  }}
                  disabled={generatingProposal || !auditData}
                  className="rounded-lg bg-cyan-500/20 px-4 py-2 text-sm font-medium text-cyan-400 hover:bg-cyan-500/30 disabled:opacity-50 transition"
                >
                  {generatingProposal ? "Generating..." : "Generate"}
                </button>
              </div>
              
              <div className="space-y-3 mt-4">
                {proposals.map(prop => (
                  <div key={prop.id} className="rounded-xl border border-white/10 bg-slate-900/50 p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="text-sm font-semibold text-white">{prop.title}</div>
                        <div className="text-xs text-slate-500 mt-1">{prop.proposal_number} • Version {prop.version}</div>
                        <div className="text-xs text-slate-400 mt-1">Value: ${prop.amount_min.toLocaleString()} | Prob: {prop.close_probability}%</div>
                      </div>
                      <span className={`px-2 py-1 text-[10px] font-bold uppercase rounded-md 
                        ${prop.status === 'draft' ? 'bg-slate-500/20 text-slate-400' :
                          prop.status === 'accepted' ? 'bg-emerald-500/20 text-emerald-400' :
                          prop.status === 'rejected' ? 'bg-red-500/20 text-red-400' :
                          'bg-blue-500/20 text-blue-400'}`}>
                        {prop.status}
                      </span>
                    </div>
                    
                    <div className="mt-4 flex flex-wrap gap-2 pt-3 border-t border-white/5">
                      <a href={getProposalPdfUrl(prop.id)} target="_blank" rel="noreferrer" className="px-3 py-1.5 rounded bg-white/5 text-xs text-slate-300 hover:bg-white/10">View PDF</a>
                      {prop.status === 'draft' && <button onClick={() => handleProposalAction("send", prop.id)} className="px-3 py-1.5 rounded bg-blue-500/20 text-xs text-blue-400 hover:bg-blue-500/30">Mark Sent</button>}
                      {(prop.status === 'sent' || prop.status === 'viewed') && (
                        <>
                          <button onClick={() => handleProposalAction("accept", prop.id)} className="px-3 py-1.5 rounded bg-emerald-500/20 text-xs text-emerald-400 hover:bg-emerald-500/30">Accept</button>
                          <button onClick={() => handleProposalAction("reject", prop.id)} className="px-3 py-1.5 rounded bg-red-500/20 text-xs text-red-400 hover:bg-red-500/30">Reject</button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              <label className="text-sm font-semibold text-slate-300">Internal Notes</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Background context, decision makers..."
                className="h-32 w-full rounded-2xl border border-white/10 bg-slate-900 px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500"
              />
              <button
                onClick={handleSave}
                disabled={saving}
                className="w-full rounded-xl bg-cyan-500/90 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-cyan-400 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Details"}
              </button>
            </div>

            <div className="space-y-4 pt-4 border-t border-white/10">
              <h3 className="text-sm font-semibold text-slate-300">Deal Timeline</h3>
              
              <div className="flex flex-col gap-2 rounded-2xl border border-white/10 bg-slate-900/50 p-3">
                <select
                  value={activityType}
                  onChange={(e) => setActivityType(e.target.value)}
                  className="rounded-lg bg-transparent text-sm text-slate-300 outline-none"
                >
                  <option value="note">Note</option>
                  <option value="call">Call</option>
                  <option value="email">Email</option>
                  <option value="meeting">Meeting</option>
                </select>
                <textarea
                  value={activityContent}
                  onChange={(e) => setActivityContent(e.target.value)}
                  placeholder="What happened?"
                  className="min-h-[4rem] w-full resize-none rounded-lg bg-transparent text-sm text-white outline-none placeholder:text-slate-600"
                />
                <div className="flex justify-end">
                  <button
                    onClick={handleLogActivity}
                    disabled={logging || !activityContent.trim()}
                    className="rounded-lg bg-white/10 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-white/20 disabled:opacity-40"
                  >
                    Log Activity
                  </button>
                </div>
              </div>

              {/* Timeline */}
              <div className="relative ml-3 border-l-2 border-white/10 pl-6 space-y-0">
                {lead.activities?.map((activity, idx) => {
                  const iconMap = {
                    note: { icon: "📝", color: "slate" },
                    call: { icon: "📞", color: "amber" },
                    email: { icon: "✉️", color: "cyan" },
                    meeting: { icon: "🤝", color: "purple" },
                    status_change: { icon: "🔄", color: "blue" },
                    stage_change: { icon: "📊", color: "indigo" },
                    outreach_generated: { icon: "🚀", color: "emerald" },
                    audit_completed: { icon: "🔍", color: "violet" },
                  };
                  const info = iconMap[activity.type] || { icon: "•", color: "slate" };
                  return (
                    <div key={activity.id} className="relative pb-5">
                      <span className="absolute -left-[1.85rem] top-0 flex h-5 w-5 items-center justify-center rounded-full bg-slate-900 border border-white/10 text-[10px]">
                        {info.icon}
                      </span>
                      <div className="text-sm">
                        <div className="flex items-center justify-between">
                          <span className={`text-xs uppercase font-semibold text-${info.color}-400`}>{activity.type.replace("_", " ")}</span>
                          <span className="text-[10px] text-slate-600">{new Date(activity.created_at).toLocaleString()}</span>
                        </div>
                        <p className="mt-1 text-slate-300 whitespace-pre-wrap">{activity.content}</p>
                      </div>
                    </div>
                  );
                })}
                {(!lead.activities || lead.activities.length === 0) && (
                  <p className="text-sm text-slate-500 py-2">No activity yet.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
