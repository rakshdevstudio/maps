import { useEffect, useState } from "react";
import { getChiefOfStaffBrief, getDailySdrRecommendations, getPipelineForecast, getProjectRisks } from "@/services/api";

export default function FounderMode() {
  const [loading, setLoading] = useState(true);
  const [brief, setBrief] = useState(null);
  const [sdrRecs, setSdrRecs] = useState([]);
  const [forecast, setForecast] = useState(null);
  const [risks, setRisks] = useState([]);

  useEffect(() => {
    const load = async () => {
      try {
        const [b, s, f, r] = await Promise.all([
          getChiefOfStaffBrief(),
          getDailySdrRecommendations(),
          getPipelineForecast(),
          getProjectRisks()
        ]);
        setBrief(b);
        setSdrRecs(s || []);
        setForecast(f);
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
    return (
      <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-slate-950 text-white">
        <div className="h-12 w-12 rounded-full border-t-2 border-indigo-500 animate-spin mb-4" />
        <p className="text-slate-400 font-mono tracking-widest text-sm uppercase">Loading Founder Intelligence...</p>
      </div>
    );
  }

  // Calculate highest impact action
  const topSdr = sdrRecs.length > 0 ? sdrRecs[0] : null;
  const criticalRisk = risks.find(r => r.risk_level === 'critical');
  let biggestImpact = "Continue standard operations.";
  if (criticalRisk) {
    biggestImpact = `Intervene on Project #${criticalRisk.project_id}: ${criticalRisk.slipping_reason}`;
  } else if (topSdr) {
    biggestImpact = `Close the gap on Lead #${topSdr.lead_id} (Score: ${topSdr.score}). Action: ${topSdr.recommended_action}`;
  }

  return (
    <div className="min-h-screen bg-slate-950 px-8 py-12 flex items-center justify-center">
      <div className="max-w-4xl w-full space-y-12">
        
        <div className="text-center mb-16">
          <p className="text-xs uppercase tracking-[0.3em] text-indigo-500 mb-4 font-bold">Nexora OS // Founder Cockpit</p>
          <h1 className="text-5xl font-extrabold text-white tracking-tight">Pure Decision Support.</h1>
        </div>

        <div className="grid gap-8">
          
          {/* Question 1 */}
          <div className="group">
            <h2 className="text-lg font-bold text-slate-500 mb-2 transition group-hover:text-emerald-500">1. What revenue is most likely to close?</h2>
            <p className="text-3xl font-medium text-white">
              {forecast?.likely_revenue || "$0"} in high-probability pipeline.
            </p>
          </div>

          {/* Question 2 */}
          <div className="group">
            <h2 className="text-lg font-bold text-slate-500 mb-2 transition group-hover:text-rose-500">2. What is at risk?</h2>
            <p className="text-3xl font-medium text-white">
              {brief?.what_is_blocked || "No critical risks detected."}
            </p>
          </div>

          {/* Question 3 */}
          <div className="group">
            <h2 className="text-lg font-bold text-slate-500 mb-2 transition group-hover:text-cyan-500">3. What should I do today?</h2>
            <p className="text-3xl font-medium text-white">
              {brief?.what_should_happen_next || "Follow standard follow-up sequences."}
            </p>
          </div>

          {/* Question 4 */}
          <div className="group">
            <h2 className="text-lg font-bold text-slate-500 mb-2 transition group-hover:text-amber-500">4. Where is the biggest opportunity?</h2>
            <p className="text-3xl font-medium text-white">
              {topSdr ? `Lead #${topSdr.lead_id}: ${topSdr.reason}` : "No major outliers in pipeline currently."}
            </p>
          </div>

          {/* Question 5 */}
          <div className="group">
            <h2 className="text-lg font-bold text-slate-500 mb-2 transition group-hover:text-indigo-500">5. What will make the biggest impact?</h2>
            <p className="text-3xl font-medium text-white">
              {biggestImpact}
            </p>
          </div>

        </div>
      </div>
    </div>
  );
}
