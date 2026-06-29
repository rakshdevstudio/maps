import { useEffect, useState } from "react";
import { Sparkles, Target, AlertTriangle, TrendingUp, CheckCircle, Activity, Box, ArrowRight } from "lucide-react";
import { 
  getChiefOfStaffBrief, 
  getDailySdrRecommendations, 
  getProjectRisks, 
  getAccountGrowthOpportunities 
} from "@/services/api";
import LeadDetail from "@/components/LeadDetail";
import { useLeads } from "@/hooks/useLeads";

function AIBriefingCard({ brief }) {
  if (!brief) return null;
  return (
    <div className="rounded-2xl border border-indigo-500/30 bg-indigo-500/5 p-6 relative overflow-hidden">
      <div className="absolute top-0 right-0 p-32 bg-indigo-500/10 blur-[100px] rounded-full pointer-events-none" />
      <div className="flex items-center gap-3 mb-6 relative z-10">
        <div className="p-2 bg-indigo-500/20 rounded-lg">
          <Sparkles className="h-6 w-6 text-indigo-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Executive Briefing</h2>
          <p className="text-xs text-indigo-300">Autonomous AI Intelligence</p>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative z-10">
        <div className="space-y-6">
          <div>
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">What Happened</h3>
            <p className="text-slate-200">{brief.what_happened}</p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">What Matters</h3>
            <p className="text-slate-200">{brief.what_matters}</p>
          </div>
        </div>
        <div className="space-y-6">
          <div>
            <h3 className="text-sm font-semibold text-rose-400 uppercase tracking-wider mb-2">What Is Blocked</h3>
            <p className="text-slate-200">{brief.what_is_blocked}</p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-emerald-400 uppercase tracking-wider mb-2">Next Actions</h3>
            <p className="text-slate-200">{brief.what_should_happen_next}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Today() {
  const { fetchLeadDetails, updateLead } = useLeads();
  const [loading, setLoading] = useState(true);
  const [brief, setBrief] = useState(null);
  const [sdrRecs, setSdrRecs] = useState([]);
  const [risks, setRisks] = useState([]);
  const [growth, setGrowth] = useState([]);
  const [selectedLead, setSelectedLead] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [briefData, sdrData, riskData, growthData] = await Promise.all([
          getChiefOfStaffBrief(),
          getDailySdrRecommendations(),
          getProjectRisks(),
          getAccountGrowthOpportunities()
        ]);
        setBrief(briefData);
        setSdrRecs(sdrData || []);
        setRisks(riskData || []);
        setGrowth(growthData || []);
      } catch (e) {
        console.error("Failed to load AI intelligence", e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleLeadClick = async (leadId) => {
    const detail = await fetchLeadDetails(leadId);
    setSelectedLead(detail);
  };

  if (loading) {
    return <div className="flex items-center justify-center py-32 text-slate-500">Compiling AI Intelligence...</div>;
  }

  return (
    <div className="space-y-10">
      
      {/* 1. The Executive Brief */}
      <AIBriefingCard brief={brief} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* 2. Top Opportunities (SDR) */}
        <div className="space-y-4">
          <div className="flex items-center gap-3 mb-6">
            <Target className="h-5 w-5 text-emerald-400" />
            <h3 className="text-lg font-semibold text-white">Top Opportunities</h3>
          </div>
          {sdrRecs.length === 0 ? (
            <p className="text-slate-500 text-sm">No high-priority targets currently identified.</p>
          ) : (
            sdrRecs.map(rec => (
              <div 
                key={rec.id} 
                onClick={() => handleLeadClick(rec.lead_id)}
                className="cursor-pointer rounded-xl border border-white/10 bg-white/5 p-4 transition hover:bg-white/10"
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="flex items-center justify-center h-8 w-8 rounded-full bg-emerald-500/20 text-emerald-400 font-bold text-sm">
                      {rec.score}
                    </span>
                    <span className="text-white font-medium">Lead #{rec.lead_id}</span>
                  </div>
                  <span className="text-xs bg-emerald-500/10 text-emerald-400 px-2 py-1 rounded-full uppercase tracking-wider font-semibold">
                    Target
                  </span>
                </div>
                <p className="text-sm text-slate-300 mb-3">{rec.reason}</p>
                <div className="text-xs text-emerald-400 flex items-center gap-1 font-medium">
                  <ArrowRight className="h-3 w-3" /> {rec.recommended_action}
                </div>
              </div>
            ))
          )}
        </div>

        {/* 3. Operational Risks (Projects + Deals) */}
        <div className="space-y-4">
          <div className="flex items-center gap-3 mb-6">
            <AlertTriangle className="h-5 w-5 text-rose-400" />
            <h3 className="text-lg font-semibold text-white">Active Risks</h3>
          </div>
          {risks.length === 0 ? (
            <p className="text-slate-500 text-sm">No critical operational risks detected.</p>
          ) : (
            risks.map(risk => (
              <div key={risk.id} className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-white font-medium flex items-center gap-2">
                    <Box className="h-4 w-4 text-slate-400" /> Project #{risk.project_id}
                  </span>
                  <span className="text-[10px] bg-rose-500/20 text-rose-400 px-2 py-0.5 rounded-full uppercase tracking-wider font-bold">
                    {risk.risk_level}
                  </span>
                </div>
                <p className="text-sm text-slate-300 mb-2">{risk.slipping_reason}</p>
                <div className="text-xs text-rose-400 flex items-center gap-1 font-medium">
                  <ArrowRight className="h-3 w-3" /> {risk.priority_action}
                </div>
              </div>
            ))
          )}

          {/* 4. Account Growth */}
          <div className="flex items-center gap-3 mb-6 mt-10">
            <TrendingUp className="h-5 w-5 text-cyan-400" />
            <h3 className="text-lg font-semibold text-white">Growth Opportunities</h3>
          </div>
          {growth.length === 0 ? (
            <p className="text-slate-500 text-sm">No upsell opportunities currently detected.</p>
          ) : (
            growth.map(opp => (
              <div key={opp.id} className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-white font-medium">{opp.opportunity_type}</span>
                  <span className="text-xs text-cyan-400 font-bold">{opp.confidence_score}% Match</span>
                </div>
                <p className="text-sm text-slate-300 mb-2">{opp.rationale}</p>
                <p className="text-xs text-emerald-400 font-medium">{opp.expected_outcome}</p>
              </div>
            ))
          )}
        </div>
      </div>

      {selectedLead && (
        <LeadDetail
          lead={selectedLead}
          onClose={() => setSelectedLead(null)}
          onUpdate={(id, data) => updateLead(id, data)}
          logActivity={() => {}}
        />
      )}
    </div>
  );
}
