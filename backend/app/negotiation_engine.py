import json
from typing import List, Dict
from . import models

def generate_negotiation_guidance(proposal: models.Proposal, audit: models.WebsiteAudit) -> List[Dict[str, str]]:
    business_name = proposal.lead.business.name if proposal.lead and proposal.lead.business else "the business"
    
    revenue_leaks = json.loads(audit.revenue_leaks) if audit and audit.revenue_leaks and audit.revenue_leaks != "[]" else ["missed digital opportunities"]
    primary_leak = revenue_leaks[0]
    
    opp_type = getattr(audit, 'opportunity_type', "growth opportunity") or "growth opportunity"
    deal_size = getattr(audit, 'estimated_deal_size', "significant new revenue") or "significant new revenue"
    readiness = getattr(audit, 'sales_readiness_score', 50)
    
    guidance = [
        {
            "objection": "Too Expensive",
            "response": f"I understand price is a concern. However, by not addressing the '{primary_leak.lower()}' leak, {business_name} is currently losing {deal_size} in potential revenue. This {opp_type} pays for itself quickly once we plug the leak."
        },
        {
            "objection": "Need Approval",
            "response": f"Of course. When you present this to the team, emphasize that this isn't an expense, but a fix for the '{primary_leak.lower()}' leak that is currently restricting growth. We have a clear {readiness}/100 opportunity here."
        },
        {
            "objection": "Already Have Vendor",
            "response": f"That's great you're investing in your digital presence. But did your current vendor mention the '{primary_leak.lower()}'? Our audit found specific gaps that they are missing, leaving {deal_size} on the table."
        },
        {
            "objection": "Need More Time / No Budget",
            "response": f"Timing is always tricky. But every month we delay, {business_name} continues to lose {deal_size} due to {primary_leak.lower()}. Can we start with the setup phase to immediately plug the bleeding?"
        }
    ]
    
    return guidance
