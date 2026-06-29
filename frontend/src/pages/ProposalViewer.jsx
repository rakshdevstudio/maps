import { useState, useEffect } from "react";
import { toast } from "sonner";
import { CheckCircle, AlertTriangle, TrendingUp, ShieldAlert, FileSignature } from "lucide-react";

export default function ProposalViewer({ token }) {
  const [proposal, setProposal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeSection, setActiveSection] = useState("executive");

  useEffect(() => {
    const fetchProposal = async () => {
      try {
        const response = await fetch(`http://localhost:8000/proposals/public/${token}`);
        if (!response.ok) throw new Error("Proposal not found or expired");
        const data = await response.json();
        
        // Parse the proposal_data string to JSON if needed
        if (typeof data.proposal_data === "string") {
          data.proposal_data = JSON.parse(data.proposal_data);
        }
        setProposal(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchProposal();

    // Time tracking ping every 10 seconds
    const interval = setInterval(() => {
      fetch(`http://localhost:8000/proposals/public/${token}/track`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ time_spent: 10 }),
      }).catch(console.error);
    }, 10000);

    return () => clearInterval(interval);
  }, [token]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#050816] text-white">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-cyan-400"></div>
          <p className="text-slate-400">Loading Business Case...</p>
        </div>
      </div>
    );
  }

  if (error || !proposal) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#050816] text-white">
        <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-8 text-center max-w-md">
          <AlertTriangle className="mx-auto mb-4 h-12 w-12 text-rose-500" />
          <h2 className="mb-2 text-xl font-bold text-white">Access Denied</h2>
          <p className="text-rose-200">{error}</p>
        </div>
      </div>
    );
  }

  const { proposal_data: pd } = proposal;
  const metrics = pd.metrics || {};
  const findings = pd.audit_findings_detailed || [];

  const handleAccept = async () => {
    try {
      const response = await fetch(`http://localhost:8000/proposals/${proposal.id}/accept`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason_category: "Client Accepted via Portal", notes: "Accepted directly by the client on the Digital Proposal Portal." })
      });
      if (!response.ok) throw new Error("Failed to accept proposal");
      toast.success("Proposal Accepted! We will be in touch shortly.");
      setProposal({ ...proposal, status: "accepted" });
    } catch (err) {
      toast.error(err.message);
    }
  };

  return (
    <div className="min-h-screen bg-[#050816] text-slate-300 font-sans">
      {/* Premium Header */}
      <header className="sticky top-0 z-50 border-b border-white/5 bg-[#0a0f25]/80 backdrop-blur-md px-6 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white tracking-wider">NEXORA</h1>
            <p className="text-xs text-cyan-400">INTELLIGENCE REIMAGINED</p>
          </div>
          <div className="flex items-center gap-6">
            <div className="hidden text-right md:block">
              <p className="text-sm font-medium text-white">{proposal.title}</p>
              <p className="text-xs text-slate-500">Prepared by Nexora Growth Engineering</p>
            </div>
            {proposal.status === "accepted" ? (
              <span className="rounded-full bg-emerald-500/20 px-4 py-2 text-sm font-medium text-emerald-400 border border-emerald-500/30">
                Accepted
              </span>
            ) : (
              <button 
                onClick={handleAccept}
                className="rounded-lg bg-cyan-500 px-6 py-2 text-sm font-bold text-[#050816] transition hover:bg-cyan-400"
              >
                Accept Proposal
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-12 md:px-6">
        
        {/* Module 1 & 2: Executive Summary & Market Reality */}
        <section className="mb-20">
          <div className="mb-12">
            <h2 className="mb-4 text-sm font-bold tracking-widest text-cyan-500 uppercase">Executive Overview</h2>
            <h1 className="text-4xl font-bold text-white leading-tight md:text-5xl">
              Revenue Growth Strategy <br/>
              <span className="text-slate-500">for {proposal.title.split('for ')[1]}</span>
            </h1>
          </div>
          
          <div className="grid gap-12 lg:grid-cols-2">
            <div className="space-y-8">
              <div className="rounded-2xl border border-white/5 bg-white/5 p-8">
                <h3 className="mb-4 text-xl font-bold text-white">Current Digital Situation</h3>
                <p className="text-lg leading-relaxed text-slate-400">
                  {pd.current_situation}
                </p>
                <p className="mt-4 text-lg leading-relaxed text-slate-400">
                  {pd.executive_summary}
                </p>
              </div>
            </div>
            
            <div className="space-y-8">
              <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/5 p-8">
                <h3 className="mb-4 flex items-center gap-3 text-xl font-bold text-white">
                  <TrendingUp className="text-cyan-400" />
                  Competitive Positioning
                </h3>
                <p className="text-lg leading-relaxed text-slate-300">
                  {pd.market_positioning}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Module 5: Visual Revenue Dashboard */}
        <section className="mb-20">
          <h2 className="mb-8 text-2xl font-bold text-white">Executive Metrics Dashboard</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { label: "Revenue Potential", val: metrics.revenue_potential, color: "text-indigo-400" },
              { label: "Sales Readiness", val: metrics.sales_readiness, color: "text-sky-400" },
              { label: "Conversion Score", val: metrics.conversion_score, color: "text-emerald-400" },
              { label: "Audit Score", val: metrics.audit_score, color: "text-amber-400" }
            ].map((m, i) => (
              <div key={i} className="rounded-xl border border-white/5 bg-white/5 p-6 transition hover:bg-white/10">
                <p className="text-sm font-medium text-slate-500 uppercase tracking-wider">{m.label}</p>
                <p className={`mt-2 text-3xl font-bold ${m.color}`}>{m.val}/100</p>
              </div>
            ))}
          </div>
        </section>

        {/* Module 6: Website Intelligence Annotations */}
        {pd.screenshots?.homepage && pd.screenshots?.conversion && (
          <section className="mb-20">
            <h2 className="mb-8 text-2xl font-bold text-white">Website Intelligence Review</h2>
            <div className="grid gap-8 lg:grid-cols-2">
              
              <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
                <h3 className="mb-4 text-lg font-bold text-slate-300 text-center">Homepage Rendering</h3>
                <div className="overflow-hidden rounded-lg border border-white/10">
                  <img src={`http://localhost:8000${pd.screenshots.homepage}`} alt="Homepage" className="w-full object-cover" />
                </div>
              </div>
              
              <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
                <h3 className="mb-4 text-lg font-bold text-slate-300 text-center">Conversion Path</h3>
                <div className="overflow-hidden rounded-lg border border-white/10">
                  <img src={`http://localhost:8000${pd.screenshots.conversion}`} alt="Conversion" className="w-full object-cover" />
                </div>
              </div>

            </div>
          </section>
        )}

        {/* Module 4 & 8: Revenue Leak Analysis & Cost of Inaction */}
        <section className="mb-20">
          <div className="grid gap-12 lg:grid-cols-3">
            
            <div className="lg:col-span-2 space-y-6">
              <h2 className="mb-2 text-2xl font-bold text-white">Revenue Leak Analysis</h2>
              <p className="mb-6 text-slate-400">Technical friction directly translating to lost business opportunities.</p>
              
              {findings.map((f, i) => (
                <div key={i} className="rounded-xl border border-white/5 bg-[#0a0f25] p-6 shadow-lg">
                  <div className="mb-4 flex items-start justify-between">
                    <div>
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Problem Identified</span>
                      <h4 className="text-lg font-bold text-white mt-1">{f.leak}</h4>
                    </div>
                    <span className={`rounded-full px-3 py-1 text-xs font-bold ${f.risk_level === 'Critical' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'}`}>
                      {f.risk_level} Risk
                    </span>
                  </div>
                  
                  <div className="mb-4">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Business Impact</span>
                    <p className="text-slate-300 mt-1">{f.business_impact}</p>
                  </div>
                  
                  <div className="rounded-lg bg-cyan-500/10 p-4 border border-cyan-500/20">
                    <span className="text-xs font-bold uppercase tracking-wider text-cyan-500">Recommended Fix</span>
                    <p className="text-cyan-300 mt-1 font-medium">{f.action}</p>
                  </div>
                </div>
              ))}
            </div>
            
            {/* Cost of Inaction */}
            <div className="space-y-6">
              <div className="rounded-2xl border border-rose-500/30 bg-rose-500/5 p-8 sticky top-24">
                <ShieldAlert className="mb-4 h-10 w-10 text-rose-500" />
                <h3 className="mb-4 text-xl font-bold text-white">Cost of Inaction</h3>
                <p className="mb-6 text-rose-200">
                  Every month without an optimized system represents permanently unrecoverable revenue.
                </p>
                <div className="space-y-4">
                  {[
                    { t: "Customer Loss", d: "High-intent visitors abandoning the funnel." },
                    { t: "Visibility Loss", d: "Organic ranking decay over time." },
                    { t: "Conversion Loss", d: "Friction preventing interested prospects from converting." }
                  ].map((item, idx) => (
                    <div key={idx} className="border-l-2 border-rose-500/50 pl-4">
                      <h4 className="font-bold text-rose-400">{item.t}</h4>
                      <p className="text-sm text-rose-200/70">{item.d}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
          </div>
        </section>

        {/* Module 5: Solution Blueprint */}
        <section className="mb-20 rounded-3xl border border-white/5 bg-gradient-to-b from-white/5 to-transparent p-10 md:p-16">
          <h2 className="mb-4 text-sm font-bold tracking-widest text-cyan-500 uppercase">Solution Blueprint</h2>
          <h3 className="mb-12 text-3xl font-bold text-white">{pd.package_name}</h3>
          
          <div className="grid gap-12 md:grid-cols-2">
            <div>
              <h4 className="mb-6 text-xl font-bold text-white">Deliverables & Implementation</h4>
              <ul className="space-y-4">
                {pd.deliverables.map((d, i) => (
                  <li key={i} className="flex items-start gap-3 text-slate-300">
                    <CheckCircle className="mt-0.5 h-5 w-5 shrink-0 text-cyan-400" />
                    <span>{d}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="mb-6 text-xl font-bold text-white">Expected Outcomes</h4>
              <ul className="space-y-4">
                {pd.expected_outcomes.map((o, i) => (
                  <li key={i} className="flex items-start gap-3 text-slate-300">
                    <TrendingUp className="mt-0.5 h-5 w-5 shrink-0 text-emerald-400" />
                    <span>{o}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* Module 7: ROI Roadmap */}
        <section className="mb-20">
          <h2 className="mb-10 text-2xl font-bold text-white text-center">Execution Roadmap</h2>
          <div className="grid gap-4 md:grid-cols-4 relative">
            {/* Connecting line */}
            <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-white/10 hidden md:block -translate-y-1/2 z-0"></div>
            
            {[
              { phase: "Phase 1", title: "Audit & Strategy", desc: "Technical deep dive." },
              { phase: "Phase 2", title: "Implementation", desc: "Deploying infrastructure." },
              { phase: "Phase 3", title: "Optimization", desc: "Performance tuning." },
              { phase: "Phase 4", title: "Scaling", desc: "Analytics & measurement." },
            ].map((step, i) => (
              <div key={i} className="relative z-10 rounded-xl border border-cyan-500/20 bg-[#050816] p-6 text-center shadow-2xl">
                <div className="mx-auto mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-cyan-500/20 font-bold text-cyan-400 border border-cyan-500/50">
                  {i+1}
                </div>
                <h4 className="mb-1 font-bold text-white">{step.title}</h4>
                <p className="text-sm text-slate-400">{step.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Module 6: Investment & ROI */}
        <section className="mb-20 max-w-4xl mx-auto text-center">
          <h2 className="mb-8 text-2xl font-bold text-white">Investment Profile</h2>
          <div className="overflow-hidden rounded-3xl border border-white/10 bg-white/5">
            <div className="bg-[#0a0f25] p-12">
              <p className="mb-4 text-sm font-bold tracking-widest text-slate-400 uppercase">Total Project Investment</p>
              <div className="flex items-baseline justify-center gap-2">
                <span className="text-5xl font-bold text-white">${pd.investment?.setup_fee?.toLocaleString() || 0}</span>
                {pd.investment?.monthly_retainer > 0 && (
                  <span className="text-xl text-slate-400">+ ${pd.investment.monthly_retainer.toLocaleString()}/mo</span>
                )}
              </div>
              <p className="mt-6 text-slate-400">Project Duration: {pd.timeline}</p>
            </div>
            <div className="p-12 text-left">
              <h4 className="mb-4 font-bold text-white">Modeled ROI Profile</h4>
              <p className="text-slate-400 leading-relaxed">
                This investment is strategically modeled to return capital through increased lead volume, higher conversion rates, and optimized customer acquisition costs by actively plugging the revenue leaks identified in our audit.
              </p>
            </div>
          </div>
        </section>

        {/* Module 9: Acceptance */}
        <section className="mx-auto max-w-2xl text-center pb-20">
          <FileSignature className="mx-auto mb-6 h-16 w-16 text-cyan-500 opacity-80" />
          <h2 className="mb-6 text-3xl font-bold text-white">Ready To Get Started?</h2>
          <p className="mb-10 text-lg text-slate-400">
            Click below to formally accept this proposal. We will schedule a Kickoff Call within 48 hours to begin execution.
          </p>
          {proposal.status === "accepted" ? (
            <div className="inline-flex items-center gap-3 rounded-xl bg-emerald-500/20 px-8 py-4 text-lg font-bold text-emerald-400 border border-emerald-500/30">
              <CheckCircle className="h-6 w-6" /> Proposal Accepted
            </div>
          ) : (
            <button 
              onClick={handleAccept}
              className="rounded-xl bg-cyan-500 px-12 py-4 text-lg font-bold text-[#050816] transition hover:bg-cyan-400 hover:scale-105 active:scale-95 shadow-[0_0_40px_rgba(34,211,238,0.3)]"
            >
              Accept & Sign Proposal
            </button>
          )}
        </section>

      </main>
    </div>
  );
}
