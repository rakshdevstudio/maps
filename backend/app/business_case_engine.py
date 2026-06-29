import re
from typing import Dict, Optional

# Business logic translations
LEAK_TRANSLATIONS: Dict[str, str] = {
    "google analytics": "The business currently has no visibility into customer behavior, making marketing investment decisions effectively blind.",
    "facebook pixel": "The business is unable to retarget interested visitors, causing potential customers to leave permanently after a single visit.",
    "ssl": "Security warnings are actively deterring potential customers from engaging with the business.",
    "mobile": "A poor mobile experience is alienating over 60% of modern internet traffic, driving high-intent visitors directly to competitors.",
    "contact form": "The lack of clear conversion mechanisms prevents interested prospects from easily becoming paying customers.",
    "speed": "Slow loading times are causing severe visitor abandonment, directly resulting in lost revenue opportunities.",
    "meta title": "Poor search engine visibility prevents the business from capturing high-intent local demand.",
    "meta description": "Inadequate search presentation fails to compel prospects to click, lowering overall acquisition rates.",
    "conversion": "Friction in the conversion funnel is causing qualified leads to drop off before completing an inquiry."
}

def translate_leak(leak: str) -> str:
    """Translates a technical revenue leak into an executive business consequence."""
    leak_lower = leak.lower()
    
    for key, narrative in LEAK_TRANSLATIONS.items():
        if key in leak_lower:
            return narrative
            
    # Generic fallback that still uses business language
    return f"The current digital infrastructure surrounding '{leak}' is suboptimal, resulting in friction that prevents potential customers from converting into revenue."

def get_market_positioning(opportunity_type: str) -> str:
    """Generates a competitive positioning narrative based on opportunity type."""
    if not opportunity_type:
        opportunity_type = "Growth Opportunity"
        
    opp_lower = opportunity_type.lower()
    if "transformation" in opp_lower or "overhaul" in opp_lower:
        return "Businesses investing in modern visibility, analytics, and conversion systems continue to widen the digital gap. Delayed action on a complete infrastructure upgrade exponentially increases customer acquisition costs over time."
    elif "retainer" in opp_lower or "growth" in opp_lower:
        return "Local market dominance requires consistent, predictable growth systems. Competitors who maintain active search and conversion strategies are currently capturing the market share that should belong to you."
    else:
        return "In today's digital-first economy, the speed and efficiency of customer acquisition define market leaders. Upgrading your digital infrastructure is not just about aesthetics—it is a critical revenue defense strategy."
