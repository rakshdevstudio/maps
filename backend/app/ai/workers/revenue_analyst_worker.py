"""AI Revenue Analyst Worker — Analyzes pipeline health and forecasts revenue."""
from sqlalchemy.orm import Session
from ... import models
from ..engines.risk_engine import detect_lead_risk, detect_proposal_risk


def run_revenue_analyst_worker(db: Session):
    """
    Calculates pipeline health, risk, and likely closures.
    Persists to AIRevenueBriefing.
    """
    leads = db.query(models.Lead).filter(models.Lead.status != "rejected", models.Lead.deal_stage != "closed_won").all()
    proposals = db.query(models.Proposal).filter(models.Proposal.status.in_(["drafted", "sent"])).all()
    
    pipeline_total = sum((p.amount_min or 0) for p in proposals)
    likely_to_close = sum((p.amount_min or 0) * ((p.close_probability or 0) / 100.0) for p in proposals)
    
    # Analyze Risk
    high_risk_deals = 0
    blocked_deals = 0
    
    for lead in leads:
        last_activity = db.query(models.Activity).filter(models.Activity.lead_id == lead.id).order_by(models.Activity.created_at.desc()).first()
        risk = detect_lead_risk(lead, last_activity)
        if risk["level"] == "critical":
            blocked_deals += 1
        elif risk["level"] == "high":
            high_risk_deals += 1
            
    for prop in proposals:
        risk = detect_proposal_risk(prop)
        if risk["level"] == "critical":
            blocked_deals += 1
        elif risk["level"] == "high":
            high_risk_deals += 1

    # Generate Summaries
    risk_summary = "Pipeline is healthy."
    if high_risk_deals > 0:
        risk_summary = f"{high_risk_deals} deals are currently showing high risk of stalling."
        
    blocked_summary = "No immediate blockers detected."
    if blocked_deals > 0:
        blocked_summary = f"{blocked_deals} critical deals are currently blocked and require executive intervention."
        
    briefing = models.AIRevenueBriefing(
        pipeline_total=pipeline_total,
        likely_to_close=likely_to_close,
        risk_summary=risk_summary,
        blocked_summary=blocked_summary
    )
    db.add(briefing)
    db.commit()
    print("AI Revenue Analyst: Generated pipeline briefing.")
