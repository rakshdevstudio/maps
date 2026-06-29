"""Retainer Opportunity Engine — Generates contextual retainer recommendations at 80% project completion."""
import json
from typing import List
from . import models


# Maps audit data to retainer opportunities
RETAINER_TYPES = {
    "maintenance": {
        "title": "Website Maintenance Retainer",
        "description": "Ongoing website health monitoring, security updates, performance optimization, and content updates.",
        "base_monthly_value": 500,
    },
    "seo": {
        "title": "SEO Growth Retainer",
        "description": "Monthly search engine optimization including keyword targeting, content strategy, backlink building, and ranking reports.",
        "base_monthly_value": 800,
    },
    "analytics": {
        "title": "Analytics & Intelligence Retainer",
        "description": "Advanced analytics setup, conversion tracking, A/B testing, and monthly performance intelligence reports.",
        "base_monthly_value": 600,
    },
    "growth": {
        "title": "Growth Marketing Retainer",
        "description": "Full-stack growth marketing including paid media management, funnel optimization, and lead generation campaigns.",
        "base_monthly_value": 1200,
    },
}


def _get_audit_leaks(audit: models.WebsiteAudit) -> list:
    try:
        return json.loads(audit.revenue_leaks) if audit.revenue_leaks else []
    except Exception:
        return []


def _get_audit_services(audit: models.WebsiteAudit) -> list:
    try:
        return json.loads(audit.nexora_services) if audit.nexora_services else []
    except Exception:
        return []


def generate_retainer_recommendations(project: models.Project, audit: models.WebsiteAudit, proposal: models.Proposal) -> List[dict]:
    """
    Generates retainer recommendations based on:
    - Website audit data (revenue leaks, services)
    - Proposal history (what was delivered)
    - Revenue potential scores
    """
    recommendations = []
    leaks = _get_audit_leaks(audit)
    services = _get_audit_services(audit)
    leaks_lower = " ".join(leaks).lower()
    services_lower = " ".join(services).lower()

    rev_potential = getattr(audit, 'revenue_potential_score', 50) or 50
    sales_readiness = getattr(audit, 'sales_readiness_score', 50) or 50

    # Maintenance — always recommend if project was a build
    rtype = RETAINER_TYPES["maintenance"]
    rationale = "After completing the initial project, ongoing maintenance ensures the investment continues generating returns. Without active monitoring, technical debt accumulates and performance degrades."
    recommendations.append({
        "type": "maintenance",
        "title": rtype["title"],
        "description": rtype["description"],
        "rationale": rationale,
        "monthly_value": rtype["base_monthly_value"],
    })

    # SEO — if audit found meta/ranking issues
    if any(k in leaks_lower for k in ["meta", "seo", "title", "description", "keyword"]) or not getattr(audit, 'has_meta_title', True):
        rtype = RETAINER_TYPES["seo"]
        rationale = f"Our audit identified SEO deficiencies that limit organic visibility. With a sales readiness score of {sales_readiness}/100, consistent SEO investment will compound organic lead acquisition over time."
        recommendations.append({
            "type": "seo",
            "title": rtype["title"],
            "description": rtype["description"],
            "rationale": rationale,
            "monthly_value": rtype["base_monthly_value"],
        })

    # Analytics — if no tracking was present
    if any(k in leaks_lower for k in ["analytics", "pixel", "tracking", "conversion"]) or not getattr(audit, 'has_google_analytics', True):
        rtype = RETAINER_TYPES["analytics"]
        rationale = "The initial project establishes tracking infrastructure, but ongoing analytics intelligence transforms raw data into actionable revenue insights. Without continuous analysis, optimization opportunities are missed."
        recommendations.append({
            "type": "analytics",
            "title": rtype["title"],
            "description": rtype["description"],
            "rationale": rationale,
            "monthly_value": rtype["base_monthly_value"],
        })

    # Growth — if revenue potential is high
    if rev_potential >= 40 or "growth" in services_lower or "retainer" in (audit.opportunity_type or "").lower():
        rtype = RETAINER_TYPES["growth"]
        rationale = f"With a revenue potential score of {rev_potential}/100, {project.client_name} has significant untapped growth capacity. A dedicated growth retainer maximizes the ROI of the infrastructure we have built."
        recommendations.append({
            "type": "growth",
            "title": rtype["title"],
            "description": rtype["description"],
            "rationale": rationale,
            "monthly_value": rtype["base_monthly_value"],
        })

    return recommendations
