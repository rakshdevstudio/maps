import json
from typing import Dict, Any
from .models import WebsiteAudit, Lead, ProposalTemplate
from .business_case_engine import translate_leak, get_market_positioning
from .revenue_impact_engine import analyze_revenue_impact

def build_proposal_story(audit: WebsiteAudit, lead: Lead, template: ProposalTemplate) -> Dict[str, Any]:
    """Orchestrates the entire proposal narrative into a rich JSON structure."""
    
    # Base Data Extraction
    revenue_leaks_str = getattr(audit, 'revenue_leaks', '[]') or '[]'
    try:
        revenue_leaks = json.loads(revenue_leaks_str)
    except Exception:
        revenue_leaks = [revenue_leaks_str]
        
    nexora_services_str = getattr(audit, 'nexora_services', '[]') or '[]'
    try:
        nexora_services = json.loads(nexora_services_str)
    except Exception:
        nexora_services = [nexora_services_str] * len(revenue_leaks)
        
    try:
        deliverables = json.loads(template.deliverables) if template.deliverables else []
    except Exception:
        deliverables = [template.deliverables] if template.deliverables else []
        
    primary_leak = revenue_leaks[0] if revenue_leaks else "generic optimization opportunities"
    
    # Story Engine Orchestration
    revenue_impact_data = analyze_revenue_impact(audit)
    market_positioning = get_market_positioning(audit.opportunity_type)
    
    # Build detailed findings
    audit_findings_detailed = []
    for i, leak in enumerate(revenue_leaks):
        business_consequence = translate_leak(leak)
        action = nexora_services[i] if i < len(nexora_services) else "General Optimization"
        risk_level = "Critical" if i == 0 else "Elevated"
        
        audit_findings_detailed.append({
            "leak": leak,
            "business_impact": business_consequence,
            "risk_level": risk_level,
            "action": action
        })
        
    # Constructing the comprehensive dictionary
    story_data = {
        # Story Module 1 & 2
        "current_situation": f"{lead.business.name} is a highly rated {getattr(lead.business, 'category', 'business')} ({getattr(lead.business, 'rating', 5)}*). However, the current digital infrastructure lacks key elements required to capture modern consumer demand.",
        "executive_summary": f"This proposal outlines a strategic partnership to eliminate critical revenue leaks at {lead.business.name}. Based on our technical audit, {lead.business.name} has a {getattr(audit, 'sales_readiness_score', 0)}/100 sales readiness score and is losing potential clients due to {primary_leak.lower()}.",
        
        # New Enriched Story Elements
        "market_positioning": market_positioning,
        "revenue_risk_level": revenue_impact_data["revenue_risk_level"],
        "revenue_opportunity_score": revenue_impact_data["revenue_opportunity_score"],
        "lost_revenue_narrative": revenue_impact_data["lost_revenue_narrative"],
        
        "metrics": {
            "revenue_potential": getattr(audit, 'revenue_potential_score', 0) or 0,
            "sales_readiness": getattr(audit, 'sales_readiness_score', 0) or 0,
            "opportunity_type": audit.opportunity_type or "Growth Opportunity",
            "audit_score": getattr(audit, 'opportunity_score', 0) or 0,
            "conversion_score": getattr(audit, 'conversion_score', 0) or 0
        },
        
        "screenshots": {
            "homepage": getattr(audit, 'screenshot_path', None),
            "conversion": getattr(audit, 'conversion_screenshot_path', None)
        },
        
        "audit_findings_detailed": audit_findings_detailed,
        "problems_found": [leak for leak in revenue_leaks],
        
        # Solution & Investment
        "package_name": template.name,
        "recommended_services": [action for action in nexora_services],
        "deliverables": deliverables,
        "timeline": template.timeline or "TBD",
        "investment": {
            "setup_fee": template.base_price,
            "monthly_retainer": 0
        },
        
        "expected_outcomes": [
            f"Plug the '{primary_leak}' revenue leak",
            f"Capitalize on the {audit.opportunity_type or 'Growth Opportunity'} identified in our audit",
            "Increase qualified lead capture rate",
            "Establish scalable digital infrastructure"
        ],
        "next_steps": "To proceed, please review the investment details and digitally sign this proposal. We will schedule a kickoff call within 48 hours of acceptance."
    }
    
    return story_data
