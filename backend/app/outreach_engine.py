import json
from . import models

BANNED_PHRASES = [
    "we help businesses grow",
    "hope you're doing well",
    "hope you are doing well",
    "i came across your business",
]

def contains_banned_phrase(text: str) -> bool:
    lower_text = text.lower()
    for phrase in BANNED_PHRASES:
        if phrase in lower_text:
            return True
    return False

def generate_outreach(lead: models.Lead, audit: models.WebsiteAudit) -> dict:
    """Generates deterministic, highly-specific outreach based on actual audit data."""
    business = lead.business
    
    revenue_leaks = json.loads(audit.revenue_leaks) if audit.revenue_leaks else []
    issues_found = json.loads(audit.issues_found) if audit.issues_found else []
    nexora_services = json.loads(audit.nexora_services) if audit.nexora_services else []
    
    primary_leak = revenue_leaks[0] if revenue_leaks else "sub-optimal digital infrastructure"
    primary_issue = issues_found[0] if issues_found else "missing advanced analytics"
    primary_service = nexora_services[0] if nexora_services else "Digital Modernization"
    opportunity = audit.opportunity_type or "Growth Opportunity"
    
    # 1. Cold Email
    cold_email = (
        f"Subject: Fix {business.name}'s {opportunity.lower()}\n\n"
        f"Hi {lead.contact_name or 'Team'},\n\n"
        f"Your {business.category or 'business'} has a great {business.rating} star rating on Google, but your current website has a critical issue: {primary_issue}. "
        f"This directly causes a revenue leak because {primary_leak.lower()}.\n\n"
        f"We can implement our {primary_service} package to resolve this immediately, capturing the traffic you are currently losing.\n\n"
        f"Are you available for a brief call next week to discuss?"
    )
    
    # 2. WhatsApp
    whatsapp = (
        f"Hi {lead.contact_name or 'there'}! Noticed {business.name} is highly rated ({business.rating}★), "
        f"but your website is losing customers due to: {primary_issue}. "
        f"This is a clear {opportunity} we can fix with our {primary_service}. Let's chat!"
    )
    
    # 3. LinkedIn
    linkedin = (
        f"Hi {lead.contact_name or 'Team'}, amazing work building {business.name} to a {business.rating} star reputation. "
        f"I reviewed your digital presence and identified a significant revenue leak: {primary_leak}. "
        f"My team specializes in {primary_service} to plug this exact leak. "
        f"Open to connecting and sharing a brief audit report?"
    )
    
    # 4. Call Script
    call_script = (
        f"[OPENER] Hi, I'm calling about {business.name}. You guys have great reviews, but I found a critical issue on your website.\n"
        f"[PAIN POINT] Specifically, {primary_issue}, which means {primary_leak.lower()}.\n"
        f"[PITCH] We specialize in {opportunity}. We can roll out {primary_service} to fix this.\n"
        f"[CLOSE] Can we schedule 10 minutes to walk through the technical fix?"
    )
    
    # Validation against generic banned phrases
    messages = {
        "cold_email": cold_email,
        "whatsapp": whatsapp,
        "linkedin": linkedin,
        "call_script": call_script
    }
    
    for key, msg in messages.items():
        if contains_banned_phrase(msg):
            raise ValueError(f"Generated {key} contains banned generic phrase.")
            
    return messages
