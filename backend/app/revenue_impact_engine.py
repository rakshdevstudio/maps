from typing import Dict, Tuple, Optional
from .models import WebsiteAudit

def calculate_revenue_risk(sales_readiness: int, audit_score: int) -> str:
    """Calculates Revenue Risk based on the audit and readiness scores."""
    avg_score = (sales_readiness + audit_score) / 2 if audit_score > 0 else sales_readiness
    
    if avg_score < 30:
        return "Critical"
    elif avg_score < 50:
        return "High"
    elif avg_score < 75:
        return "Medium"
    else:
        return "Low"

def calculate_revenue_opportunity(sales_readiness: int) -> int:
    """Calculates Revenue Opportunity (0-100). Lower readiness means higher opportunity to improve."""
    opportunity = 100 - sales_readiness
    return max(0, min(100, opportunity))

def generate_lost_revenue_narrative(risk: str, opportunity: int, opportunity_type: str) -> str:
    """Generates a qualitative lost revenue narrative."""
    if risk in ["Critical", "High"]:
        return "Based on current website maturity and customer acquisition infrastructure, the business is likely missing substantial revenue from high-intent visitors who fail to convert due to digital friction."
    elif risk == "Medium":
        return "While some foundational elements exist, the business is leaking potential revenue through unoptimized conversion funnels and invisible customer behavior."
    else:
        return "The digital foundation is solid, but there is still untapped revenue potential that can be captured through advanced optimization and scaling strategies."

def analyze_revenue_impact(audit: WebsiteAudit) -> Dict:
    """Returns the full revenue impact dictionary."""
    sales_readiness = getattr(audit, 'sales_readiness_score', 50) or 50
    audit_score = getattr(audit, 'opportunity_score', 0) or 0
    opp_type = getattr(audit, 'opportunity_type', 'Growth Opportunity') or 'Growth Opportunity'
    
    risk = calculate_revenue_risk(sales_readiness, audit_score)
    opportunity = calculate_revenue_opportunity(sales_readiness)
    narrative = generate_lost_revenue_narrative(risk, opportunity, opp_type)
    
    return {
        "revenue_risk_level": risk,
        "revenue_opportunity_score": opportunity,
        "lost_revenue_narrative": narrative
    }
