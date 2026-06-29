"""AI SDR Worker — Finds highest value opportunities."""
from sqlalchemy.orm import Session
from ... import models
from ..engines.opportunity_scoring_v2 import calculate_master_score, generate_opportunity_reason


def run_sdr_worker(db: Session):
    """
    Analyzes all leads and generates top recommendations.
    Persists to AIDailySdrRecommendation.
    """
    # 1. Clear previous recommendations (we only keep the daily snapshot, or keep history. Let's keep history but the frontend fetches latest. Actually, best practice is to clear today's or just insert new ones.)
    # We will just insert new ones. The frontend will query the latest 10 based on generated_at date.
    
    leads = db.query(models.Lead).filter(models.Lead.status != "rejected", models.Lead.deal_stage != "closed_won").all()
    
    scored_leads = []
    for lead in leads:
        audit = db.query(models.WebsiteAudit).filter(models.WebsiteAudit.lead_id == lead.id).order_by(models.WebsiteAudit.created_at.desc()).first()
        proposal = db.query(models.Proposal).filter(models.Proposal.lead_id == lead.id).order_by(models.Proposal.created_at.desc()).first()
        
        score = calculate_master_score(lead, audit, proposal)
        reason = generate_opportunity_reason(lead, score, audit)
        
        # Determine action
        if proposal and proposal.status == "sent":
            action = "Follow up on pending proposal."
        elif audit:
            action = "Generate and send proposal based on audit findings."
        else:
            action = "Run website audit and draft initial outreach."
            
        scored_leads.append({
            "lead_id": lead.id,
            "score": score,
            "reason": reason,
            "action": action
        })
        
    # Sort by score descending
    scored_leads.sort(key=lambda x: x["score"], reverse=True)
    
    # Save top 10 recommendations
    for sl in scored_leads[:10]:
        rec = models.AIDailySdrRecommendation(
            lead_id=sl["lead_id"],
            score=sl["score"],
            reason=sl["reason"],
            recommended_action=sl["action"]
        )
        db.add(rec)
    
    db.commit()
    print(f"AI SDR: Generated top {min(10, len(scored_leads))} opportunity recommendations.")
