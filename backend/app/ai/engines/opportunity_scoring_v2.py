"""Opportunity Scoring Engine V2 — The Master AI Score"""
from datetime import datetime
from ... import models


def calculate_master_score(lead: models.Lead, audit: models.WebsiteAudit = None, proposal: models.Proposal = None) -> int:
    """
    Calculates the master opportunity score (0-100) based on multiple deterministic vectors.
    """
    score = 0
    now = datetime.utcnow()

    # 1. Audit Factors (Max 40 points)
    if audit:
        # High revenue potential indicates they need help and have money (up to 15 pts)
        rev_pot = getattr(audit, 'revenue_potential_score', 0) or 0
        score += (rev_pot / 100.0) * 15

        # Sales readiness indicates they are primed to buy (up to 15 pts)
        sales_read = getattr(audit, 'sales_readiness_score', 0) or 0
        score += (sales_read / 100.0) * 15

        # Lower conversion score = higher need for us (up to 10 pts)
        conv_score = getattr(audit, 'conversion_score', 100) or 100
        score += ((100 - conv_score) / 100.0) * 10
    
    # 2. Business Quality (Max 15 points)
    if lead.business:
        # Rating penalty/bonus. We want good businesses to work with.
        rating = getattr(lead.business, 'rating', 0) or 0
        if rating >= 4.5:
            score += 15
        elif rating >= 4.0:
            score += 10
        elif rating >= 3.0:
            score += 5
    
    # 3. Pipeline Momentum (Max 30 points)
    if proposal:
        if proposal.status == "accepted":
            score += 30  # Already closed won
        elif proposal.status == "sent":
            score += 25  # Highest priority to follow up
        elif proposal.status == "drafted":
            score += 15
    elif lead.deal_stage == "contacted":
        score += 10
    elif lead.deal_stage == "qualified":
        score += 20
    elif lead.deal_stage == "negotiation":
        score += 25
    
    # 4. Recency Bonus (Max 15 points)
    # Give higher scores to leads interacted with recently
    last_touch = lead.updated_at
    if last_touch:
        days_ago = (now - last_touch).days
        if days_ago <= 1:
            score += 15
        elif days_ago <= 3:
            score += 10
        elif days_ago <= 7:
            score += 5
        elif days_ago > 30:
            score -= 10 # Penalty for very stale leads

    # Ensure bounds
    return max(0, min(100, int(score)))

def generate_opportunity_reason(lead: models.Lead, score: int, audit: models.WebsiteAudit = None) -> str:
    """Generate human readable reasoning for the score."""
    reasons = []
    
    if score >= 80:
        reasons.append("High intent opportunity.")
    elif score >= 60:
        reasons.append("Solid pipeline prospect.")
    
    if audit:
        rev_pot = getattr(audit, 'revenue_potential_score', 0) or 0
        sales_read = getattr(audit, 'sales_readiness_score', 0) or 0
        if rev_pot > 70:
            reasons.append(f"Massive revenue potential ({rev_pot}/100).")
        if sales_read > 70:
            reasons.append("Highly sales-ready infrastructure.")
            
    if lead.business and lead.business.rating and lead.business.rating >= 4.5:
        reasons.append("Strong business reputation.")
        
    if not reasons:
        reasons.append("Standard lead.")
        
    return " ".join(reasons)
