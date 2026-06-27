import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models, schemas, database, website_auditor, config

router = APIRouter(prefix="/audits", tags=["audits"])

def format_audit(audit: models.WebsiteAudit) -> schemas.WebsiteAuditItem:
    return schemas.WebsiteAuditItem(
        id=audit.id,
        lead_id=audit.lead_id,
        url=audit.url,
        is_live=audit.is_live,
        has_ssl=audit.has_ssl,
        mobile_friendly=audit.mobile_friendly,
        page_load_ms=audit.page_load_ms,
        has_contact_form=audit.has_contact_form,
        has_whatsapp=audit.has_whatsapp,
        has_facebook_pixel=audit.has_facebook_pixel,
        has_google_analytics=audit.has_google_analytics,
        has_meta_title=audit.has_meta_title,
        has_meta_description=audit.has_meta_description,
        tech_stack=json.loads(audit.tech_stack) if audit.tech_stack else [],
        seo_title=audit.seo_title,
        seo_description=audit.seo_description,
        audit_score=audit.audit_score,
        opportunity_score=audit.opportunity_score,
        revenue_potential_score=audit.revenue_potential_score,
        opportunity_type=audit.opportunity_type,
        issues_found=json.loads(audit.issues_found) if audit.issues_found else [],
        recommendation=audit.recommendation,
        why_contact_summary=audit.why_contact_summary,
        screenshot_path=audit.screenshot_path,
        conversion_score=audit.conversion_score,
        lead_capture_present=audit.lead_capture_present,
        conversion_screenshot_path=audit.conversion_screenshot_path,
        estimated_deal_size=audit.estimated_deal_size,
        sales_pitch_angle=audit.sales_pitch_angle,
        business_impact=audit.business_impact,
        sales_readiness_score=audit.sales_readiness_score,
        revenue_leaks=json.loads(audit.revenue_leaks) if audit.revenue_leaks else [],
        nexora_services=json.loads(audit.nexora_services) if audit.nexora_services else [],
        audited_at=audit.audited_at.isoformat(),
        created_at=audit.created_at.isoformat(),
        updated_at=audit.updated_at.isoformat()
    )

@router.post("/lead/{lead_id}", response_model=schemas.WebsiteAuditItem)
async def run_audit(lead_id: int, db: Session = Depends(database.get_db)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    if not lead.business.website:
        raise HTTPException(status_code=400, detail="Business does not have a website to audit.")
        
    settings = config.load_config()
    audit = await website_auditor.run_audit(lead, db, settings)
    
    activity = models.Activity(
        lead_id=lead.id,
        type="note",
        content=f"Ran Website Audit. Audit Score: {audit.audit_score}, Revenue Potential: {audit.revenue_potential_score}"
    )
    db.add(activity)
    db.commit()
    
    return format_audit(audit)

@router.get("/stats")
def get_audit_stats(db: Session = Depends(database.get_db)):
    total_audits = db.query(models.WebsiteAudit).count()
    healthy = db.query(models.WebsiteAudit).filter(models.WebsiteAudit.audit_score >= 70).count()
    critical = db.query(models.WebsiteAudit).filter(models.WebsiteAudit.audit_score < 40).count()
    
    avg_audit = db.query(func.avg(models.WebsiteAudit.audit_score)).scalar() or 0
    avg_opp = db.query(func.avg(models.WebsiteAudit.opportunity_score)).scalar() or 0
    avg_rev = db.query(func.avg(models.WebsiteAudit.revenue_potential_score)).scalar() or 0
    
    return {
        "total_audited": total_audits,
        "healthy_sites": healthy,
        "critical_sites": critical,
        "average_audit_score": int(avg_audit),
        "average_opportunity_score": int(avg_opp),
        "average_revenue_potential": int(avg_rev)
    }
