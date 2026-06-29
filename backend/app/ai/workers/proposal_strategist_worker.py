"""AI Proposal Strategist Worker — Optimizes proposal generation parameters."""
from sqlalchemy.orm import Session
from ... import models
import json

def run_proposal_strategist_worker(db: Session):
    """
    Analyzes leads with audits but no proposals, and recommends a package and angle.
    Persists to AIProposalStrategy.
    """
    # Find leads that have audits but no proposals (or proposals in draft status)
    leads = db.query(models.Lead).filter(models.Lead.status != "rejected").all()
    
    generated = 0
    for lead in leads:
        audit = db.query(models.WebsiteAudit).filter(models.WebsiteAudit.lead_id == lead.id).order_by(models.WebsiteAudit.created_at.desc()).first()
        if not audit:
            continue
            
        proposal = db.query(models.Proposal).filter(models.Proposal.lead_id == lead.id, models.Proposal.status != "lost").first()
        if proposal and proposal.status != "drafted":
            continue # Already handled
            
        # We need a strategy for this lead. Check if we already generated one recently
        existing = db.query(models.AIProposalStrategy).filter(models.AIProposalStrategy.lead_id == lead.id).first()
        if existing:
            # We already have a strategy. Only regenerate if audit is newer than strategy
            if audit.created_at < existing.generated_at:
                continue
            db.delete(existing)
            db.flush()

        # Generate strategy
        rev_pot = getattr(audit, 'revenue_potential_score', 0) or 0
        sales_read = getattr(audit, 'sales_readiness_score', 0) or 0
        
        try:
            leaks = json.loads(audit.revenue_leaks) if audit.revenue_leaks else []
        except:
            leaks = []
        leaks_str = " ".join(leaks).lower()

        # Determine Package & Investment
        if rev_pot > 70 and sales_read < 40:
            package = "Digital Transformation Accelerator"
            investment = 7500.0
            angle = "Focus heavily on the massive revenue potential being lost due to outdated infrastructure."
            positioning = "Strategic Partner"
        elif "conversion" in leaks_str or "analytics" in leaks_str:
            package = "Revenue Optimization Sprint"
            investment = 3500.0
            angle = "Focus on plugging existing traffic leaks to immediately increase ROI."
            positioning = "Performance Engineer"
        elif "seo" in leaks_str or "meta" in leaks_str:
            package = "Search Dominance Campaign"
            investment = 2500.0
            angle = "Focus on local market capture and ranking above direct competitors."
            positioning = "Growth Consultant"
        else:
            package = "Foundation Build"
            investment = 1500.0
            angle = "Focus on establishing professional credibility and baseline lead capture."
            positioning = "Technical Executor"

        strategy = models.AIProposalStrategy(
            lead_id=lead.id,
            recommended_package=package,
            recommended_investment=investment,
            recommended_angle=angle,
            positioning=positioning
        )
        db.add(strategy)
        generated += 1
        
    db.commit()
    print(f"AI Proposal Strategist: Generated {generated} proposal strategies.")
