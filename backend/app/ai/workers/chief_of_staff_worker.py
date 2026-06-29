"""AI Chief of Staff Worker — The Master Aggregator."""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ... import models


def run_chief_of_staff_worker(db: Session):
    """
    Reads outputs from all other AI workers and constructs the master daily executive brief.
    Persists to AIExecutiveBrief.
    """
    now = datetime.utcnow()
    twenty_four_hours_ago = now - timedelta(days=1)
    
    # 1. Gather Intelligence
    sdr_recs = db.query(models.AIDailySdrRecommendation).order_by(models.AIDailySdrRecommendation.score.desc()).limit(3).all()
    revenue = db.query(models.AIRevenueBriefing).order_by(models.AIRevenueBriefing.generated_at.desc()).first()
    risks = db.query(models.AIProjectRiskReport).order_by(models.AIProjectRiskReport.generated_at.desc()).all()
    growth = db.query(models.AIAccountGrowthOpportunity).order_by(models.AIAccountGrowthOpportunity.confidence_score.desc()).all()
    
    # 2. What Happened (Last 24 hours)
    new_leads = db.query(models.Lead).filter(models.Lead.created_at >= twenty_four_hours_ago).count()
    new_proposals = db.query(models.Proposal).filter(models.Proposal.created_at >= twenty_four_hours_ago).count()
    won_proposals = db.query(models.Proposal).filter(models.Proposal.accepted_at >= twenty_four_hours_ago).count()
    
    what_happened = f"In the last 24 hours, Nexora acquired {new_leads} new leads, generated {new_proposals} proposals, and won {won_proposals} deals."
    
    # 3. What Matters
    what_matters = f"Total pipeline sits at ${revenue.pipeline_total:,.2f}, with ${revenue.likely_to_close:,.2f} likely to close." if revenue else "Pipeline data unavailable."
    if sdr_recs:
        top_lead = sdr_recs[0].lead.business.name if sdr_recs[0].lead.business else "an unknown business"
        what_matters += f" Your top opportunity today is {top_lead} with a score of {sdr_recs[0].score}."
        
    # 4. What is Blocked
    critical_risks = [r for r in risks if r.risk_level == "critical"]
    if critical_risks:
        what_is_blocked = f"{len(critical_risks)} projects are in critical state and require immediate intervention. " + revenue.blocked_summary if revenue else ""
    elif revenue and "critical" in revenue.blocked_summary.lower():
        what_is_blocked = revenue.blocked_summary
    else:
        what_is_blocked = "No major blockers detected across sales or delivery pipelines."
        
    # 5. What Should Happen Next
    what_should_happen_next = []
    if sdr_recs:
        what_should_happen_next.append("Execute SDR recommended outreach for the top 3 high-intent leads.")
    if critical_risks:
        what_should_happen_next.append("Intervene on critical projects to unblock delivery.")
    if growth:
        what_should_happen_next.append(f"Pitch the {len(growth)} identified retainer opportunities to completed projects.")
        
    next_steps_str = " ".join(what_should_happen_next) if what_should_happen_next else "Continue standard operations."
    
    # 6. What Deserves Attention
    what_deserves_attention = "Growth Opportunities" if growth else "Pipeline Generation"
    if critical_risks:
        what_deserves_attention = "Delivery Crisis Management"
        
    brief = models.AIExecutiveBrief(
        what_happened=what_happened,
        what_matters=what_matters,
        what_is_blocked=what_is_blocked,
        what_should_happen_next=next_steps_str,
        what_deserves_attention=what_deserves_attention
    )
    
    db.add(brief)
    db.commit()
    print("AI Chief of Staff: Executive Brief generated.")
