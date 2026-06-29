"""AI Account Manager Worker — Generates upsell opportunities for completed projects."""
from sqlalchemy.orm import Session
from ... import models
from ...retainer_engine import generate_retainer_recommendations


def run_account_manager_worker(db: Session):
    """
    Analyzes projects >= 80% completion and generates retainer recommendations.
    Persists to AIAccountGrowthOpportunity.
    """
    projects = db.query(models.Project).filter(models.Project.completion_percentage >= 80).all()
    
    generated = 0
    for proj in projects:
        # Check if already generated today for this project
        # In a real system, you might only generate once, or clear and replace. We'll clear and replace.
        db.query(models.AIAccountGrowthOpportunity).filter(models.AIAccountGrowthOpportunity.project_id == proj.id).delete()
        
        audit = db.query(models.WebsiteAudit).filter(models.WebsiteAudit.lead_id == proj.lead_id).order_by(models.WebsiteAudit.created_at.desc()).first()
        proposal = db.query(models.Proposal).filter(models.Proposal.id == proj.proposal_id).first()
        
        if not audit or not proposal:
            continue
            
        recs = generate_retainer_recommendations(proj, audit, proposal)
        
        for rec in recs:
            confidence = 90 if rec["type"] == "maintenance" else (80 if rec["type"] == "seo" else 75)
            growth_opp = models.AIAccountGrowthOpportunity(
                project_id=proj.id,
                opportunity_type=rec["title"],
                rationale=rec["rationale"],
                expected_outcome=f"Generate ${rec['monthly_value']}/mo in recurring revenue.",
                confidence_score=confidence
            )
            db.add(growth_opp)
            generated += 1
            
    db.commit()
    print(f"AI Account Manager: Generated {generated} growth opportunities.")
