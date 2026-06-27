from datetime import datetime
from typing import List, Optional
import io
import csv

from fastapi import APIRouter, Depends, HTTPException, Query
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi.responses import StreamingResponse

from . import models, schemas, database, outreach_engine, deal_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("/promote", response_model=schemas.LeadItem)
def promote_to_lead(payload: schemas.LeadCreate, db: Session = Depends(database.get_db)):
    business = db.query(models.BusinessResult).filter(models.BusinessResult.id == payload.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
        
    existing = db.query(models.Lead).filter(models.Lead.business_id == payload.business_id).first()
    if existing:
        return schemas.LeadItem(
            id=existing.id,
            business_id=existing.business_id,
            status=existing.status,
            priority=existing.priority,
            notes=existing.notes,
            contact_name=existing.contact_name,
            last_contacted=existing.last_contacted.isoformat() if existing.last_contacted else None,
            next_followup=existing.next_followup.isoformat() if existing.next_followup else None,
            created_at=existing.created_at.isoformat(),
            updated_at=existing.updated_at.isoformat()
        )
        
    new_lead = models.Lead(business_id=payload.business_id)
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    
    # Auto-log activity
    activity = models.Activity(
        lead_id=new_lead.id,
        type="note",
        content="Promoted to pipeline"
    )
    db.add(activity)
    db.commit()
    
    return schemas.LeadItem(
        id=new_lead.id,
        business_id=new_lead.business_id,
        status=new_lead.status,
        priority=new_lead.priority,
        notes=new_lead.notes,
        contact_name=new_lead.contact_name,
        last_contacted=new_lead.last_contacted.isoformat() if new_lead.last_contacted else None,
        next_followup=new_lead.next_followup.isoformat() if new_lead.next_followup else None,
        created_at=new_lead.created_at.isoformat(),
        updated_at=new_lead.updated_at.isoformat()
    )


@router.get("", response_model=dict)
def list_leads(
    page: int = 1,
    limit: int = 50,
    status: Optional[str] = None,
    priority: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Lead).join(models.BusinessResult)
    
    if status:
        query = query.filter(models.Lead.status == status)
    if priority is not None:
        query = query.filter(models.Lead.priority == priority)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.BusinessResult.name.ilike(search_term)) |
            (models.BusinessResult.phone.ilike(search_term)) |
            (models.Lead.contact_name.ilike(search_term))
        )
        
    total = query.count()
    total_pages = max(1, (total + limit - 1) // limit)
    page = max(1, min(page, total_pages))
    
    results = (
        query.order_by(models.Lead.updated_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    
    # Manually attach business
    items = []
    for lead in results:
        data = schemas.LeadDetail(
            id=lead.id,
            business_id=lead.business_id,
            status=lead.status,
            priority=lead.priority,
            notes=lead.notes,
            contact_name=lead.contact_name,
            last_contacted=lead.last_contacted.isoformat() if lead.last_contacted else None,
            next_followup=lead.next_followup.isoformat() if lead.next_followup else None,
            created_at=lead.created_at.isoformat(),
            updated_at=lead.updated_at.isoformat(),
            business=schemas.BusinessItem(
                id=lead.business.id,
                keyword=lead.business.keyword,
                name=lead.business.name,
                rating=lead.business.rating,
                address=lead.business.address,
                phone=lead.business.phone,
                website=lead.business.website,
                category=lead.business.category,
                opening_hours=lead.business.opening_hours,
                google_maps_url=lead.business.google_maps_url,
                place_id=lead.business.place_id,
                scraped_at=lead.business.scraped_at.isoformat()
            )
        )
        items.append(data.dict())
        
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }


@router.get("/stats")
def get_lead_stats(db: Session = Depends(database.get_db)):
    total = db.query(models.Lead).count()
    new_leads = db.query(models.Lead).filter(models.Lead.status == "new").count()
    contacted = db.query(models.Lead).filter(models.Lead.status == "contacted").count()
    interested = db.query(models.Lead).filter(models.Lead.status == "interested").count()
    not_interested = db.query(models.Lead).filter(models.Lead.status == "not_interested").count()
    closed_won = db.query(models.Lead).filter(models.Lead.status == "closed_won").count()
    closed_lost = db.query(models.Lead).filter(models.Lead.status == "closed_lost").count()
    
    # Phase 3 specific stats
    high_opp = db.query(models.Lead).join(models.WebsiteAudit).filter(models.WebsiteAudit.opportunity_score >= 70).count()
    calls_due = db.query(models.Lead).filter(models.Lead.next_action == "Call").count()
    followups_due = db.query(models.Lead).filter(models.Lead.next_action == "Follow Up").count()
    avg_readiness = db.query(func.avg(models.WebsiteAudit.sales_readiness_score)).scalar() or 0
    
    # Revenue calc
    def parse_rev(val):
        if not val: return 0
        import re
        nums = re.findall(r'\d+', val.replace(',', ''))
        if not nums: return 0
        if len(nums) == 2: return (int(nums[0]) + int(nums[1])) / 2
        return int(nums[0])
    
    leads = db.query(models.Lead).all()
    pot_rev = sum(parse_rev(l.estimated_project_value) for l in leads if l.status not in ("closed_won", "closed_lost"))
    won_rev = sum(parse_rev(l.estimated_project_value) for l in leads if l.status == "closed_won")
    lost_rev = sum(parse_rev(l.estimated_project_value) for l in leads if l.status == "closed_lost")

    return {
        "new": new_leads,
        "contacted": contacted,
        "interested": interested,
        "not_interested": not_interested,
        "closed_won": closed_won,
        "closed_lost": closed_lost,
        "total_leads": total,
        "qualified_leads": total - closed_lost - not_interested,
        "high_opportunity_leads": high_opp,
        "calls_due_today": calls_due,
        "followups_due": followups_due,
        "potential_revenue": f"${int(pot_rev):,}",
        "won_revenue": f"${int(won_rev):,}",
        "lost_revenue": f"${int(lost_rev):,}",
        "average_readiness": int(avg_readiness),
        "deal_stages": deal_engine.DEAL_STAGES,
        "stage_labels": deal_engine.STAGE_LABELS,
    }


@router.get("/today")
def get_today_view(db: Session = Depends(database.get_db)):
    """Today View — the daily execution home screen. Pure reads, no writes."""
    from datetime import date
    
    today = date.today()
    all_leads = db.query(models.Lead).filter(
        models.Lead.deal_stage.notin_(["closed_won", "closed_lost"])
    ).all()
    
    overdue = []
    calls_due = []
    followups_due = []
    meetings_scheduled = []
    critical_deals = []
    
    for lead in all_leads:
        latest_audit = db.query(models.WebsiteAudit).filter(
            models.WebsiteAudit.lead_id == lead.id
        ).order_by(models.WebsiteAudit.id.desc()).first()
        
        health = deal_engine.compute_deal_health(lead, latest_audit)
        
        item = {
            "id": lead.id,
            "business_name": lead.business.name if lead.business else "Unknown",
            "business_phone": lead.business.phone if lead.business else None,
            "business_website": lead.business.website if lead.business else None,
            "deal_stage": lead.deal_stage or "lead_found",
            "deal_value": health["deal_value"],
            "deal_health_score": health["deal_health_score"],
            "deal_health_status": health["deal_health_status"],
            "days_since_contact": health["days_since_contact"],
            "next_action": lead.next_action,
            "next_action_date": lead.next_action_date.isoformat() if lead.next_action_date else None,
            "estimated_deal_size": latest_audit.estimated_deal_size if latest_audit else lead.estimated_project_value,
            "stage_label": health["stage_label"],
        }
        
        # Categorize
        if health["days_since_contact"] > 14:
            overdue.append(item)
        
        if lead.next_action == "Call":
            if not lead.next_action_date or lead.next_action_date.date() <= today:
                calls_due.append(item)
        
        if lead.next_action == "Follow Up":
            if not lead.next_action_date or lead.next_action_date.date() <= today:
                followups_due.append(item)
        
        if lead.next_action == "Meeting" or lead.deal_stage == "meeting_scheduled":
            meetings_scheduled.append(item)
        
        if health["deal_health_status"] == "Critical" and health["deal_value"] > 0:
            critical_deals.append(item)
    
    # Sort by urgency (health score ASC = worst first)
    overdue.sort(key=lambda x: x["deal_health_score"])
    calls_due.sort(key=lambda x: -x["deal_value"])
    followups_due.sort(key=lambda x: x["deal_health_score"])
    critical_deals.sort(key=lambda x: -x["deal_value"])
    
    return {
        "overdue": overdue,
        "calls_due": calls_due,
        "followups_due": followups_due,
        "meetings_scheduled": meetings_scheduled,
        "critical_deals": critical_deals,
        "summary": {
            "overdue_count": len(overdue),
            "calls_count": len(calls_due),
            "followups_count": len(followups_due),
            "meetings_count": len(meetings_scheduled),
            "critical_count": len(critical_deals),
        }
    }


@router.get("/command-center")
def get_command_center(
    db: Session = Depends(database.get_db),
    opportunity_type: str = Query(None),
    min_revenue_potential: int = Query(None),
    min_readiness: int = Query(None),
    next_action: str = Query(None)
):
    query = db.query(models.Lead).join(models.WebsiteAudit).filter(models.Lead.status.notin_(["closed_won", "closed_lost"]))
    
    if opportunity_type:
        query = query.filter(models.WebsiteAudit.opportunity_type == opportunity_type)
    if min_revenue_potential is not None:
        query = query.filter(models.WebsiteAudit.revenue_potential_score >= min_revenue_potential)
    if min_readiness is not None:
        query = query.filter(models.WebsiteAudit.sales_readiness_score >= min_readiness)
    if next_action:
        query = query.filter(models.Lead.next_action == next_action)
        
    leads = query.order_by(models.WebsiteAudit.opportunity_score.desc()).all()
    
    results = []
    for lead in leads:
        latest_audit = db.query(models.WebsiteAudit).filter(models.WebsiteAudit.lead_id == lead.id).order_by(models.WebsiteAudit.id.desc()).first()
        results.append({
            "id": lead.id,
            "business_id": lead.business_id,
            "status": lead.status,
            "priority": lead.priority,
            "notes": lead.notes,
            "contact_name": lead.contact_name,
            "last_contacted": lead.last_contacted.isoformat() if lead.last_contacted else None,
            "next_followup": lead.next_followup.isoformat() if lead.next_followup else None,
            "next_action": lead.next_action,
            "next_action_date": lead.next_action_date.isoformat() if lead.next_action_date else None,
            "proposal_status": lead.proposal_status,
            "created_at": lead.created_at.isoformat(),
            "updated_at": lead.updated_at.isoformat(),
            
            "business_name": lead.business.name,
            "business_website": lead.business.website,
            "audit_score": latest_audit.audit_score if latest_audit else None,
            "revenue_potential": latest_audit.revenue_potential_score if latest_audit else None,
            "sales_readiness": latest_audit.sales_readiness_score if latest_audit else None,
            "opportunity_type": latest_audit.opportunity_type if latest_audit else None,
            "deal_size": latest_audit.estimated_deal_size if latest_audit else None
        })
    return results


@router.get("/pipeline-revenue")
def get_pipeline_revenue(db: Session = Depends(database.get_db)):
    """Pipeline forecast using stage probabilities. Pure reads, no writes."""
    all_leads = db.query(models.Lead).all()
    leads_with_audits = []
    for lead in all_leads:
        audit = db.query(models.WebsiteAudit).filter(
            models.WebsiteAudit.lead_id == lead.id
        ).order_by(models.WebsiteAudit.id.desc()).first()
        leads_with_audits.append((lead, audit))
    
    return deal_engine.compute_pipeline_forecast(leads_with_audits)


@router.get("/pipeline/forecast")
def get_pipeline_forecast(db: Session = Depends(database.get_db)):
    """Alias for pipeline-revenue with full forecast data."""
    return get_pipeline_revenue(db)


@router.get("/{lead_id}", response_model=schemas.LeadDetail)
def get_lead(lead_id: int, db: Session = Depends(database.get_db)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    activities = db.query(models.Activity).filter(models.Activity.lead_id == lead_id).order_by(models.Activity.created_at.desc()).all()
    latest_audit_obj = db.query(models.WebsiteAudit).filter(models.WebsiteAudit.lead_id == lead_id).order_by(models.WebsiteAudit.audited_at.desc()).first()
    
    # Needs to import json or use json module in leads_router, so I will add import json at top of leads_router.py if not exists, actually I can just use it if I add it.
    import json
    
    latest_audit = None
    if latest_audit_obj:
        latest_audit = schemas.WebsiteAuditItem(
            id=latest_audit_obj.id,
            lead_id=latest_audit_obj.lead_id,
            url=latest_audit_obj.url,
            is_live=latest_audit_obj.is_live,
            has_ssl=latest_audit_obj.has_ssl,
            mobile_friendly=latest_audit_obj.mobile_friendly,
            page_load_ms=latest_audit_obj.page_load_ms,
            has_contact_form=latest_audit_obj.has_contact_form,
            has_whatsapp=latest_audit_obj.has_whatsapp,
            has_facebook_pixel=latest_audit_obj.has_facebook_pixel,
            has_google_analytics=latest_audit_obj.has_google_analytics,
            has_meta_title=latest_audit_obj.has_meta_title,
            has_meta_description=latest_audit_obj.has_meta_description,
            tech_stack=json.loads(latest_audit_obj.tech_stack) if latest_audit_obj.tech_stack else [],
            seo_title=latest_audit_obj.seo_title,
            seo_description=latest_audit_obj.seo_description,
            audit_score=latest_audit_obj.audit_score,
            opportunity_score=latest_audit_obj.opportunity_score,
            revenue_potential_score=latest_audit_obj.revenue_potential_score,
            opportunity_type=latest_audit_obj.opportunity_type,
            issues_found=json.loads(latest_audit_obj.issues_found) if latest_audit_obj.issues_found else [],
            recommendation=latest_audit_obj.recommendation,
            why_contact_summary=latest_audit_obj.why_contact_summary,
            screenshot_path=latest_audit_obj.screenshot_path,
            conversion_score=latest_audit_obj.conversion_score,
            lead_capture_present=latest_audit_obj.lead_capture_present,
            conversion_screenshot_path=latest_audit_obj.conversion_screenshot_path,
            estimated_deal_size=latest_audit_obj.estimated_deal_size,
            sales_pitch_angle=latest_audit_obj.sales_pitch_angle,
            business_impact=latest_audit_obj.business_impact,
            sales_readiness_score=latest_audit_obj.sales_readiness_score,
            revenue_leaks=json.loads(latest_audit_obj.revenue_leaks) if latest_audit_obj.revenue_leaks else [],
            nexora_services=json.loads(latest_audit_obj.nexora_services) if latest_audit_obj.nexora_services else [],
            audited_at=latest_audit_obj.audited_at.isoformat(),
            created_at=latest_audit_obj.created_at.isoformat(),
            updated_at=latest_audit_obj.updated_at.isoformat()
        )
    
    return schemas.LeadDetail(
        id=lead.id,
        business_id=lead.business_id,
        status=lead.status,
        priority=lead.priority,
        notes=lead.notes,
        contact_name=lead.contact_name,
        last_contacted=lead.last_contacted.isoformat() if lead.last_contacted else None,
        next_followup=lead.next_followup.isoformat() if lead.next_followup else None,
        created_at=lead.created_at.isoformat(),
        updated_at=lead.updated_at.isoformat(),
        business=schemas.BusinessItem(
            id=lead.business.id,
            keyword=lead.business.keyword,
            name=lead.business.name,
            rating=lead.business.rating,
            address=lead.business.address,
            phone=lead.business.phone,
            website=lead.business.website,
            category=lead.business.category,
            opening_hours=lead.business.opening_hours,
            google_maps_url=lead.business.google_maps_url,
            place_id=lead.business.place_id,
            scraped_at=lead.business.scraped_at.isoformat()
        ),
        activities=[schemas.ActivityItem(
            id=a.id,
            lead_id=a.lead_id,
            type=a.type,
            content=a.content,
            created_at=a.created_at.isoformat()
        ) for a in activities],
        latest_audit=latest_audit
    )


@router.patch("/{lead_id}")
def update_lead(lead_id: int, payload: schemas.LeadUpdate, db: Session = Depends(database.get_db)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    old_status = lead.status

    if payload.status is not None:
        lead.status = payload.status
    if payload.priority is not None:
        lead.priority = payload.priority
    if payload.notes is not None:
        lead.notes = payload.notes
    if payload.contact_name is not None:
        lead.contact_name = payload.contact_name
    if payload.last_contacted is not None:
        lead.last_contacted = datetime.fromisoformat(payload.last_contacted)
    if payload.next_followup is not None:
        lead.next_followup = datetime.fromisoformat(payload.next_followup)
        
    if payload.next_action is not None:
        lead.next_action = payload.next_action
    if payload.next_action_date is not None:
        lead.next_action_date = datetime.fromisoformat(payload.next_action_date)
    if payload.proposal_status is not None:
        lead.proposal_status = payload.proposal_status
    
    # Phase 4: Sales execution fields
    if payload.deal_stage is not None:
        old_stage = lead.deal_stage
        lead.deal_stage = payload.deal_stage
        if old_stage != payload.deal_stage:
            act = models.Activity(lead_id=lead.id, type="stage_change", content=f"Deal stage: {deal_engine.stage_label(old_stage or 'lead_found')} → {deal_engine.stage_label(payload.deal_stage)}")
            db.add(act)
            # Auto-assign next action based on stage
            stage_actions = {
                "qualified": "Call",
                "contacted": "Follow Up",
                "discovery_call": "Meeting",
                "meeting_scheduled": "Proposal",
                "proposal_sent": "Follow Up",
                "negotiation": "Follow Up",
            }
            if payload.deal_stage in stage_actions:
                lead.next_action = stage_actions[payload.deal_stage]
    if payload.call_attempts is not None:
        lead.call_attempts = payload.call_attempts
    if payload.emails_sent is not None:
        lead.emails_sent = payload.emails_sent
    if payload.meetings_completed is not None:
        lead.meetings_completed = payload.meetings_completed
    if payload.last_contact_date is not None:
        lead.last_contact_date = datetime.fromisoformat(payload.last_contact_date)
        
    # Phase 3: Auto-assign Next Action on Status change
    if old_status != lead.status:
        lead.last_action = lead.next_action
        lead.last_action_date = datetime.utcnow()
        if lead.status == "contacted":
            lead.next_action = "Follow Up"
        elif lead.status == "interested":
            lead.next_action = "Meeting"
        elif lead.status == "closed_won":
            lead.next_action = None
        elif lead.status == "closed_lost":
            lead.next_action = None
        
        # Log activity for status change
        act = models.Activity(lead_id=lead.id, type="status_change", content=f"Status changed from {old_status} to {lead.status}")
        db.add(act)

    db.commit()
    db.refresh(lead)
    
    # Just return basic representation since frontend refreshes
    return {
        "id": lead.id,
        "status": lead.status,
        "priority": lead.priority,
        "notes": lead.notes,
        "contact_name": lead.contact_name,
        "last_contacted": lead.last_contacted.isoformat() if lead.last_contacted else None,
        "next_followup": lead.next_followup.isoformat() if lead.next_followup else None,
        "next_action": lead.next_action,
        "next_action_date": lead.next_action_date.isoformat() if lead.next_action_date else None,
        "last_action": lead.last_action,
        "last_action_date": lead.last_action_date.isoformat() if lead.last_action_date else None,
        "proposal_status": lead.proposal_status,
        "estimated_project_value": lead.estimated_project_value
    }


@router.post("/{lead_id}/outreach", response_model=schemas.OutreachResponse)
@router.get("/{lead_id}/outreach", response_model=schemas.OutreachResponse)
def get_or_generate_outreach(lead_id: int, db: Session = Depends(database.get_db)):
    logger.info(f"Lead loaded: {lead_id}")
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    latest_audit = db.query(models.WebsiteAudit).filter(models.WebsiteAudit.lead_id == lead.id).order_by(models.WebsiteAudit.id.desc()).first()
    if not latest_audit:
        logger.warning(f"Lead {lead_id} missing WebsiteAudit")
        raise HTTPException(status_code=400, detail="Lead requires a Website Audit before outreach can be generated.")
    logger.info(f"Audit loaded: {latest_audit.id}")
        
    # Apply requested fallback defaults if missing
    import json
    if not latest_audit.revenue_leaks or latest_audit.revenue_leaks == "[]":
        latest_audit.revenue_leaks = json.dumps(["generic audit finding"])
    if not latest_audit.nexora_services or latest_audit.nexora_services == "[]":
        latest_audit.nexora_services = json.dumps(["Website Optimization"])
    if not latest_audit.opportunity_type:
        latest_audit.opportunity_type = "Website Improvement"
        
    # Check if active outreach already exists
    active_messages = db.query(models.OutreachMessage).filter(
        models.OutreachMessage.lead_id == lead.id,
        models.OutreachMessage.is_active == True
    ).all()
    
    def format_msg(msg):
        if not msg:
            return None
        return {
            "id": msg.id,
            "lead_id": msg.lead_id,
            "type": msg.type,
            "content": msg.content,
            "version": msg.version,
            "is_active": msg.is_active,
            "source_revenue_leaks": msg.source_revenue_leaks,
            "source_opportunity_type": msg.source_opportunity_type,
            "source_nexora_services": msg.source_nexora_services,
            "source_sales_readiness": msg.source_sales_readiness,
            "created_at": msg.created_at.isoformat() if msg.created_at else None
        }
    
    if active_messages:
        result = {"cold_email": None, "whatsapp": None, "linkedin": None, "call_script": None}
        for msg in active_messages:
            result[msg.type] = format_msg(msg)
        return result
        
    # Generate new outreach
    logger.info("Outreach generation started")
    generated = outreach_engine.generate_outreach(lead, latest_audit)
    logger.info("Outreach generation completed")
    
    saved_messages = {}
    for msg_type, content in generated.items():
        msg = models.OutreachMessage(
            lead_id=lead.id,
            type=msg_type,
            content=content,
            version=1,
            is_active=True,
            source_revenue_leaks=latest_audit.revenue_leaks,
            source_opportunity_type=latest_audit.opportunity_type,
            source_nexora_services=latest_audit.nexora_services,
            source_sales_readiness=latest_audit.sales_readiness_score
        )
        db.add(msg)
        saved_messages[msg_type] = msg
        
    # Log activity
    act = models.Activity(lead_id=lead.id, type="outreach_generated", content="AI Outreach Intelligence Generated")
    db.add(act)
    
    db.commit()
    for msg in saved_messages.values():
        db.refresh(msg)
        
    logger.info("Outreach saved")
    
    formatted_response = {}
    for msg_type, msg in saved_messages.items():
        formatted_response[msg_type] = format_msg(msg)
        
    return formatted_response


@router.delete("/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(database.get_db)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    db.delete(lead)
    db.commit()
    return {"message": "Lead deleted"}


@router.post("/{lead_id}/activities", response_model=schemas.ActivityItem)
def add_activity(lead_id: int, payload: schemas.ActivityCreate, db: Session = Depends(database.get_db)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    activity = models.Activity(
        lead_id=lead_id,
        type=payload.type,
        content=payload.content
    )
    db.add(activity)
    
    if payload.type == "status_change":
        # Usually content might contain the new status
        pass
        
    db.commit()
    db.refresh(activity)
    
    return schemas.ActivityItem(
        id=activity.id,
        lead_id=activity.lead_id,
        type=activity.type,
        content=activity.content,
        created_at=activity.created_at.isoformat()
    )


@router.get("/{lead_id}/activities", response_model=List[schemas.ActivityItem])
def list_activities(lead_id: int, db: Session = Depends(database.get_db)):
    activities = db.query(models.Activity).filter(models.Activity.lead_id == lead_id).order_by(models.Activity.created_at.desc()).all()
    return [schemas.ActivityItem(
        id=a.id,
        lead_id=a.lead_id,
        type=a.type,
        content=a.content,
        created_at=a.created_at.isoformat()
    ) for a in activities]
