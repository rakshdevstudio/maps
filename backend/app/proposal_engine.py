import json
import uuid
from typing import Dict, Any
from . import models
from .deal_engine import compute_deal_health

def calculate_close_probability(lead: models.Lead, audit: models.WebsiteAudit, stage: str = "proposal_draft") -> int:
    """
    Close Probability Engine
    Inputs: Revenue Potential, Sales Readiness, Deal Health, Opportunity Score, Proposal Stage
    """
    health_info = compute_deal_health(lead, audit)
    base_health = health_info.get("deal_health_score", 50)
    
    # Audit metrics
    readiness = getattr(audit, 'sales_readiness_score', 0) or 0
    opp_score = getattr(audit, 'opportunity_score', 0) or 0
    rev_potential = getattr(audit, 'revenue_potential_score', 0) or 0
    
    # Stage boost
    stage_boosts = {
        "proposal_draft": 10,
        "proposal_sent": 20,
        "proposal_viewed": 30,
        "negotiation": 40,
        "closed_won": 100,
        "closed_lost": -100
    }
    stage_boost = stage_boosts.get(stage, 0)
    
    # Weighted calculation
    probability = (base_health * 0.3) + (readiness * 0.2) + (opp_score * 0.2) + (rev_potential * 0.1) + stage_boost
    
    # Clamp
    return max(1, min(99, int(probability))) if stage not in ("closed_won", "closed_lost") else (100 if stage == "closed_won" else 0)

def generate_proposal_data(lead: models.Lead, audit: models.WebsiteAudit, template: models.ProposalTemplate) -> Dict[str, Any]:
    """Generates the structured JSON data for a proposal based on real audit findings."""
    business = lead.business
    
    revenue_leaks = json.loads(audit.revenue_leaks) if audit.revenue_leaks and audit.revenue_leaks != "[]" else ["generic optimization opportunities"]
    issues_found = json.loads(audit.issues_found) if audit.issues_found and audit.issues_found != "[]" else ["various technical improvements"]
    nexora_services = json.loads(audit.nexora_services) if audit.nexora_services and audit.nexora_services != "[]" else [template.name]
    deliverables = json.loads(template.deliverables) if template.deliverables else []
    
    primary_leak = revenue_leaks[0]
    opportunity = audit.opportunity_type or "Growth Opportunity"
    readiness = getattr(audit, 'sales_readiness_score', 50)
    
    data = {
        "executive_summary": f"This proposal outlines a strategic partnership to eliminate critical revenue leaks at {business.name}. Based on our technical audit, {business.name} has a {readiness}/100 sales readiness score and is losing potential clients due to {primary_leak.lower()}.",
        "current_situation": f"{business.name} is a highly rated {business.category or 'business'} ({business.rating}★). However, the current digital infrastructure lacks key elements required to capture modern consumer demand.",
        "problems_found": issues_found,
        "recommended_services": nexora_services,
        "deliverables": deliverables,
        "timeline": template.timeline,
        "investment": {
            "setup_fee": template.base_price,
            "monthly_retainer": template.base_price * 0.2 if "Retainer" in template.timeline else 0
        },
        "expected_outcomes": [
            f"Plug the '{primary_leak.lower()}' revenue leak",
            f"Capitalize on the {opportunity} identified in our audit",
            "Increase qualified lead capture rate",
            "Establish scalable digital infrastructure"
        ],
        "next_steps": "To proceed, please review the investment details and digitally sign this proposal. We will schedule a kickoff call within 48 hours of acceptance."
    }
    
    return data
