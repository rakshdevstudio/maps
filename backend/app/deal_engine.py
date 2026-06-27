"""
Deal Engine — Pure computation module for Phase 4.

All functions are pure: they take data in, return data out.
No database writes. No side effects. No state mutation.
"""
from datetime import datetime, timedelta


# ──────────────────────────────────────────────
# DEAL STAGE DEFINITIONS
# ──────────────────────────────────────────────

DEAL_STAGES = [
    "lead_found",
    "qualified",
    "contacted",
    "discovery_call",
    "meeting",
    "meeting_scheduled",
    "proposal_draft",
    "proposal_sent",
    "proposal_viewed",
    "negotiation",
    "closed_won",
    "closed_lost",
]

STAGE_PROBABILITIES = {
    "lead_found": 0.05,
    "qualified": 0.15,
    "contacted": 0.25,
    "discovery_call": 0.40,
    "meeting": 0.55,
    "meeting_scheduled": 0.55,
    "proposal_draft": 0.60,
    "proposal_sent": 0.70,
    "proposal_viewed": 0.75,
    "negotiation": 0.85,
    "closed_won": 1.00,
    "closed_lost": 0.00,
}

STAGE_LABELS = {
    "lead_found": "Lead Found",
    "qualified": "Qualified",
    "contacted": "Contacted",
    "discovery_call": "Discovery Call",
    "meeting": "Meeting",
    "meeting_scheduled": "Meeting Scheduled",
    "proposal_draft": "Proposal Draft",
    "proposal_sent": "Proposal Sent",
    "proposal_viewed": "Proposal Viewed",
    "negotiation": "Negotiation",
    "closed_won": "Closed Won",
    "closed_lost": "Closed Lost",
}


def stage_probability(stage: str) -> float:
    """Return the win probability for a given deal stage."""
    return STAGE_PROBABILITIES.get(stage, 0.05)


def stage_label(stage: str) -> str:
    """Return a human-readable label for a deal stage."""
    return STAGE_LABELS.get(stage, stage.replace("_", " ").title())


def stage_index(stage: str) -> int:
    """Return the ordinal position of a stage (0-indexed)."""
    try:
        return DEAL_STAGES.index(stage)
    except ValueError:
        return 0


def is_closed(stage: str) -> bool:
    """Check if a stage represents a terminal state."""
    return stage in ("closed_won", "closed_lost")


# ──────────────────────────────────────────────
# DEAL VALUE PARSING
# ──────────────────────────────────────────────

def parse_deal_value(val: str) -> float:
    """
    Parse deal value strings like "$1,500 - $3,000" into a midpoint float.
    Returns 0 if unparseable.
    """
    if not val:
        return 0.0
    import re
    nums = re.findall(r'\d+', val.replace(',', ''))
    if not nums:
        return 0.0
    if len(nums) >= 2:
        return (int(nums[0]) + int(nums[1])) / 2
    return float(nums[0])


# ──────────────────────────────────────────────
# DEAL HEALTH — DYNAMIC COMPUTATION
# ──────────────────────────────────────────────

def compute_days_since_contact(last_contact_date) -> int:
    """Compute days since last contact. Returns -1 if never contacted."""
    if not last_contact_date:
        return -1
    if isinstance(last_contact_date, str):
        try:
            last_contact_date = datetime.fromisoformat(last_contact_date)
        except (ValueError, TypeError):
            return -1
    delta = datetime.utcnow() - last_contact_date
    return max(0, delta.days)


def compute_contact_recency_score(days: int) -> int:
    """
    Score contact recency on 0-100 scale.
    0-7 days = 80-100 (Healthy)
    8-14 days = 50-79 (At Risk)
    15+ days = 0-49 (Critical)
    Never contacted = 30 (Warm)
    """
    if days < 0:
        return 30  # Never contacted
    if days <= 7:
        return 100 - (days * 3)  # 100 → 79
    if days <= 14:
        return 79 - ((days - 7) * 4)  # 79 → 51
    return max(0, 50 - ((days - 14) * 3))  # 50 → 0


def compute_deal_health(lead, audit=None) -> dict:
    """
    Compute deal health dynamically. Pure function — no writes.

    Returns:
        {
            "deal_health_score": int (0-100),
            "deal_health_status": str ("Healthy" | "Warm" | "At Risk" | "Critical"),
            "days_since_contact": int,
            "contact_recency_score": int,
            "stage_probability": float,
            "weighted_value": float,
        }
    """
    stage = getattr(lead, 'deal_stage', None) or 'lead_found'
    last_contact = getattr(lead, 'last_contact_date', None)

    # Contact recency
    days = compute_days_since_contact(last_contact)
    recency_score = compute_contact_recency_score(days)

    # Stage progression score
    idx = stage_index(stage)
    stage_score = min(100, int((idx / max(len(DEAL_STAGES) - 2, 1)) * 100))

    # Sales readiness from audit
    readiness = 0
    rev_potential = 0
    if audit:
        readiness = getattr(audit, 'sales_readiness_score', 0) or 0
        rev_potential = getattr(audit, 'revenue_potential_score', 0) or 0

    # Weighted health score
    health_score = int(
        recency_score * 0.35 +
        stage_score * 0.30 +
        readiness * 0.20 +
        rev_potential * 0.15
    )
    health_score = max(0, min(100, health_score))

    # Determine status
    if is_closed(stage):
        status = "Closed Won" if stage == "closed_won" else "Closed Lost"
    elif health_score >= 70:
        status = "Healthy"
    elif health_score >= 50:
        status = "Warm"
    elif health_score >= 30:
        status = "At Risk"
    else:
        status = "Critical"

    # Weighted pipeline value
    prob = stage_probability(stage)
    deal_val = parse_deal_value(getattr(lead, 'estimated_project_value', None) or '')
    if not deal_val:
        deal_val = parse_deal_value(getattr(audit, 'estimated_deal_size', None) if audit else None or '')

    return {
        "deal_health_score": health_score,
        "deal_health_status": status,
        "days_since_contact": days,
        "contact_recency_score": recency_score,
        "stage_probability": prob,
        "stage_label": stage_label(stage),
        "weighted_value": round(deal_val * prob, 2),
        "deal_value": deal_val,
    }


# ──────────────────────────────────────────────
# PIPELINE FORECAST — DYNAMIC COMPUTATION
# ──────────────────────────────────────────────

def compute_pipeline_forecast(leads_with_audits: list) -> dict:
    """
    Compute full pipeline forecast from a list of (lead, audit) tuples.
    Uses stage probabilities — not arbitrary health weighting.

    Returns forecast dict with all values derived from actual data.
    """
    pipeline_value = 0.0
    weighted_pipeline = 0.0
    at_risk_revenue = 0.0
    won_revenue = 0.0
    lost_revenue = 0.0

    deals_total = 0
    deals_healthy = 0
    deals_warm = 0
    deals_at_risk = 0
    deals_critical = 0
    stage_breakdown = {}

    for lead, audit in leads_with_audits:
        health = compute_deal_health(lead, audit)
        stage = getattr(lead, 'deal_stage', None) or 'lead_found'
        deal_val = health["deal_value"]

        # Stage breakdown
        label = stage_label(stage)
        if label not in stage_breakdown:
            stage_breakdown[label] = {"count": 0, "value": 0, "weighted": 0}
        stage_breakdown[label]["count"] += 1
        stage_breakdown[label]["value"] += deal_val
        stage_breakdown[label]["weighted"] += health["weighted_value"]

        if stage == "closed_won":
            won_revenue += deal_val
            continue
        if stage == "closed_lost":
            lost_revenue += deal_val
            continue

        deals_total += 1
        pipeline_value += deal_val
        weighted_pipeline += health["weighted_value"]

        status = health["deal_health_status"]
        if status == "Healthy":
            deals_healthy += 1
        elif status == "Warm":
            deals_warm += 1
        elif status == "At Risk":
            at_risk_revenue += deal_val
            deals_at_risk += 1
        elif status == "Critical":
            at_risk_revenue += deal_val
            deals_critical += 1

    # Win rate
    closed_total = len([l for l, _ in leads_with_audits if getattr(l, 'deal_stage', '') in ('closed_won', 'closed_lost')])
    won_count = len([l for l, _ in leads_with_audits if getattr(l, 'deal_stage', '') == 'closed_won'])
    win_rate = round((won_count / closed_total * 100), 1) if closed_total > 0 else 0

    def fmt(v):
        return f"${int(v):,}"

    return {
        "pipeline_value": fmt(pipeline_value),
        "pipeline_value_raw": pipeline_value,
        "likely_revenue": fmt(weighted_pipeline),
        "likely_revenue_raw": weighted_pipeline,
        "at_risk_revenue": fmt(at_risk_revenue),
        "at_risk_revenue_raw": at_risk_revenue,
        "won_revenue": fmt(won_revenue),
        "won_revenue_raw": won_revenue,
        "lost_revenue": fmt(lost_revenue),
        "lost_revenue_raw": lost_revenue,
        "win_rate": f"{win_rate}%",
        "win_rate_raw": win_rate,
        "deals_total": deals_total,
        "deals_healthy": deals_healthy,
        "deals_warm": deals_warm,
        "deals_at_risk": deals_at_risk,
        "deals_critical": deals_critical,
        "stage_breakdown": stage_breakdown,
    }
