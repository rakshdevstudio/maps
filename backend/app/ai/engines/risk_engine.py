"""Risk Detection Engine — Proactively detects business risks"""
from datetime import datetime
from ... import models


def detect_lead_risk(lead: models.Lead, last_activity: models.Activity = None) -> dict:
    """Analyzes a lead for stagnation and ghosting risks."""
    now = datetime.utcnow()
    risk = {"level": "low", "reason": None, "action": None}

    if not last_activity:
        days_stagnant = (now - lead.created_at).days if lead.created_at else 0
        if days_stagnant > 7 and lead.status != 'rejected':
            risk = {
                "level": "medium", 
                "reason": f"Uncontacted Opportunity. Sitting idle for {days_stagnant} days.",
                "action": "Initiate Outreach"
            }
        return risk

    days_since_activity = (now - last_activity.created_at).days if last_activity.created_at else 0

    if lead.deal_stage == "negotiation" and days_since_activity > 3:
        risk = {
            "level": "critical",
            "reason": f"Stalled Deal. Negotiation silent for {days_since_activity} days.",
            "action": "Urgent Followup Call"
        }
    elif lead.deal_stage == "qualified" and days_since_activity > 7:
        risk = {
            "level": "high",
            "reason": f"Stagnant Qualified Lead. No activity for {days_since_activity} days.",
            "action": "Send Value Asset"
        }
    elif days_since_activity > 14 and lead.status not in ["rejected", "closed_won"]:
        risk = {
            "level": "medium",
            "reason": f"Ignored Lead. Slipping away after {days_since_activity} days of silence.",
            "action": "Re-engagement Sequence"
        }

    return risk


def detect_proposal_risk(proposal: models.Proposal) -> dict:
    """Analyzes sent proposals for closing risks."""
    now = datetime.utcnow()
    risk = {"level": "low", "reason": None, "action": None}

    if proposal.status != "sent":
        return risk

    days_sent = (now - proposal.updated_at).days if proposal.updated_at else 0
    
    if days_sent > 7:
        risk = {
            "level": "critical",
            "reason": f"Proposal Stagnation. Sent {days_sent} days ago with no decision.",
            "action": "Offer Closing Incentive"
        }
    elif proposal.view_count > 5 and days_sent > 2:
        risk = {
            "level": "high",
            "reason": f"High friction. Proposal viewed {proposal.view_count} times but unsigned.",
            "action": "Schedule Objection Handling Call"
        }

    return risk


def detect_project_risk(project: models.Project) -> dict:
    """Analyzes active projects for delivery risks."""
    now = datetime.utcnow()
    risk = {"level": "low", "reason": None, "action": None}

    if project.status != "active":
        return risk

    if project.health_status == "critical":
        risk = {
            "level": "critical",
            "reason": "Project health is critical due to overdue tasks or missed milestones.",
            "action": "Executive Intervention Required"
        }
    elif project.health_status == "at_risk":
        risk = {
            "level": "high",
            "reason": "Project at risk of missing deadlines.",
            "action": "Realign Milestones"
        }
    
    if project.target_completion_date:
        days_left = (project.target_completion_date - now).days
        if days_left < 0 and project.completion_percentage < 100:
             risk = {
                "level": "critical",
                "reason": f"Overdue Project. Past target date by {abs(days_left)} days.",
                "action": "Emergency Delivery Sprint"
            }

    return risk
