import json
import uuid
import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models, schemas, database, deal_engine
from .proposal_engine import generate_proposal_data, calculate_close_probability
from .proposal_pdf import generate_proposal_pdf
from .negotiation_engine import generate_negotiation_guidance

router = APIRouter(prefix="/proposals", tags=["proposals"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _serialize_proposal(prop: models.Proposal) -> dict:
    return {
        "id": prop.id,
        "lead_id": prop.lead_id,
        "proposal_number": prop.proposal_number,
        "version": prop.version,
        "parent_proposal_id": prop.parent_proposal_id,
        "title": prop.title,
        "status": prop.status,
        "amount_min": prop.amount_min,
        "amount_max": prop.amount_max,
        "currency": prop.currency,
        "package_name": prop.package_name,
        "proposal_data": prop.proposal_data,
        "close_probability": prop.close_probability,
        "public_token": prop.public_token,
        "proposal_pdf_path": prop.proposal_pdf_path,
        "sent_at": prop.sent_at.isoformat() if prop.sent_at else None,
        "viewed_at": prop.viewed_at.isoformat() if prop.viewed_at else None,
        "accepted_at": prop.accepted_at.isoformat() if prop.accepted_at else None,
        "rejected_at": prop.rejected_at.isoformat() if prop.rejected_at else None,
        "expires_at": prop.expires_at.isoformat() if prop.expires_at else None,
        "created_at": prop.created_at.isoformat() if prop.created_at else None,
        "updated_at": prop.updated_at.isoformat() if prop.updated_at else None,
    }

@router.get("/templates", response_model=List[schemas.ProposalTemplateItem])
def get_templates(db: Session = Depends(get_db)):
    return db.query(models.ProposalTemplate).filter(models.ProposalTemplate.is_active == True).all()

@router.post("/generate/{lead_id}")
def generate_proposal(lead_id: int, req: schemas.ProposalGenerateRequest, db: Session = Depends(get_db)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    audit = db.query(models.WebsiteAudit).filter(models.WebsiteAudit.lead_id == lead_id).order_by(models.WebsiteAudit.created_at.desc()).first()
    if not audit:
        raise HTTPException(status_code=400, detail="Cannot generate proposal without an audit")
        
    template = db.query(models.ProposalTemplate).filter(models.ProposalTemplate.id == req.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    # Check for existing
    existing = db.query(models.Proposal).filter(models.Proposal.lead_id == lead_id).order_by(models.Proposal.version.desc()).first()
    
    version = existing.version + 1 if existing else 1
    parent_id = existing.id if existing else None
    
    proposal_data = generate_proposal_data(lead, audit, template)
    probability = calculate_close_probability(lead, audit, "proposal_draft")
    
    amount = template.base_price
    if "Retainer" in template.timeline:
        amount += (template.base_price * 0.2 * 12) # Annualized
        
    prop = models.Proposal(
        lead_id=lead_id,
        proposal_number=f"PRP-{lead_id}-{version}",
        version=version,
        parent_proposal_id=parent_id,
        title=f"{template.name} for {lead.business.name if lead.business else 'Client'}",
        status="draft",
        amount_min=amount,
        amount_max=amount * 1.5,
        package_name=template.name,
        proposal_data=json.dumps(proposal_data),
        close_probability=probability,
        public_token=str(uuid.uuid4()),
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    db.add(prop)
    
    # Auto-advance deal stage
    lead.deal_stage = "proposal_draft"
    db.add(models.Activity(lead_id=lead_id, type="proposal_generated", content=f"Generated Proposal V{version}: {template.name}"))
    
    db.commit()
    db.refresh(prop)
    return _serialize_proposal(prop)

@router.get("", response_model=List[schemas.ProposalItem])
def list_proposals(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Proposal)
    if status:
        q = q.filter(models.Proposal.status == status)
    # Sort highest revenue first by default
    proposals = q.order_by(models.Proposal.amount_min.desc()).all()
    return [_serialize_proposal(p) for p in proposals]

@router.get("/stats", response_model=schemas.ProposalStatsResponse)
def get_stats(db: Session = Depends(get_db)):
    drafted = db.query(models.Proposal).filter(models.Proposal.status == "draft").count()
    sent = db.query(models.Proposal).filter(models.Proposal.status == "sent").count()
    viewed = db.query(models.Proposal).filter(models.Proposal.status == "viewed").count()
    won = db.query(models.Proposal).filter(models.Proposal.status == "accepted").count()
    lost = db.query(models.Proposal).filter(models.Proposal.status == "rejected").count()
    
    total_closed = won + lost
    acceptance_rate = (won / total_closed * 100) if total_closed > 0 else 0.0
    
    avg_deal = db.query(func.avg(models.Proposal.amount_min)).filter(models.Proposal.status == "accepted").scalar() or 0.0
    won_rev = db.query(func.sum(models.Proposal.amount_min)).filter(models.Proposal.status == "accepted").scalar() or 0.0
    
    pipeline_q = db.query(models.Proposal).filter(models.Proposal.status.in_(["draft", "sent", "viewed", "negotiation"])).all()
    pipe_rev = sum(p.amount_min or 0 for p in pipeline_q)
    likely_rev = sum((p.amount_min or 0) * (p.close_probability / 100.0) for p in pipeline_q)
    
    return {
        "drafted": drafted,
        "sent": sent,
        "viewed": viewed,
        "acceptance_rate": acceptance_rate,
        "average_deal_size": float(avg_deal),
        "forecasted_revenue": float(won_rev + likely_rev),
        "likely_revenue": float(likely_rev),
        "pipeline_revenue": float(pipe_rev)
    }

@router.get("/{proposal_id}", response_model=schemas.ProposalDetail)
def get_proposal(proposal_id: int, db: Session = Depends(get_db)):
    prop = db.query(models.Proposal).filter(models.Proposal.id == proposal_id).first()
    if not prop:
        raise HTTPException(404, "Proposal not found")
    data = _serialize_proposal(prop)
    
    lead = db.query(models.Lead).filter(models.Lead.id == prop.lead_id).first()
    if lead:
        data["lead"] = {
            "id": lead.id,
            "business_id": lead.business_id,
            "status": lead.status,
            "priority": lead.priority,
            "deal_stage": lead.deal_stage,
            "created_at": lead.created_at.isoformat() if lead.created_at else "",
            "updated_at": lead.updated_at.isoformat() if lead.updated_at else ""
        }
    
    win_losses = db.query(models.WinLossReason).filter(models.WinLossReason.proposal_id == prop.id).all()
    data["win_loss"] = [{
        "id": wl.id,
        "proposal_id": wl.proposal_id,
        "outcome": wl.outcome,
        "reason_category": wl.reason_category,
        "notes": wl.notes,
        "created_at": wl.created_at.isoformat()
    } for wl in win_losses]
    
    return data

@router.post("/{proposal_id}/send")
def send_proposal(proposal_id: int, db: Session = Depends(get_db)):
    prop = db.query(models.Proposal).filter(models.Proposal.id == proposal_id).first()
    if not prop:
        raise HTTPException(404)
        
    prop.status = "sent"
    prop.sent_at = datetime.utcnow()
    
    lead = db.query(models.Lead).filter(models.Lead.id == prop.lead_id).first()
    if lead:
        lead.deal_stage = "proposal_sent"
        audit = db.query(models.WebsiteAudit).filter(models.WebsiteAudit.lead_id == prop.lead_id).order_by(models.WebsiteAudit.created_at.desc()).first()
        prop.close_probability = calculate_close_probability(lead, audit, "proposal_sent")
        db.add(models.Activity(lead_id=lead.id, type="proposal_sent", content=f"Sent Proposal V{prop.version}"))
        
    db.commit()
    db.refresh(prop)
    return _serialize_proposal(prop)

@router.post("/{proposal_id}/accept")
def accept_proposal(proposal_id: int, req: schemas.WinLossReasonCreate, db: Session = Depends(get_db)):
    prop = db.query(models.Proposal).filter(models.Proposal.id == proposal_id).first()
    if not prop:
        raise HTTPException(404)
        
    prop.status = "accepted"
    prop.accepted_at = datetime.utcnow()
    prop.close_probability = 100
    
    lead = db.query(models.Lead).filter(models.Lead.id == prop.lead_id).first()
    if lead:
        lead.deal_stage = "closed_won"
        db.add(models.Activity(lead_id=lead.id, type="proposal_accepted", content=f"Proposal V{prop.version} Accepted!"))
        
    wl = models.WinLossReason(
        proposal_id=prop.id,
        outcome="won",
        reason_category=req.reason_category,
        notes=req.notes
    )
    db.add(wl)
    db.commit()
    db.refresh(prop)
    return _serialize_proposal(prop)

@router.post("/{proposal_id}/reject")
def reject_proposal(proposal_id: int, req: schemas.WinLossReasonCreate, db: Session = Depends(get_db)):
    prop = db.query(models.Proposal).filter(models.Proposal.id == proposal_id).first()
    if not prop:
        raise HTTPException(404)
        
    prop.status = "rejected"
    prop.rejected_at = datetime.utcnow()
    prop.close_probability = 0
    
    lead = db.query(models.Lead).filter(models.Lead.id == prop.lead_id).first()
    if lead:
        lead.deal_stage = "closed_lost"
        db.add(models.Activity(lead_id=lead.id, type="proposal_rejected", content=f"Proposal V{prop.version} Rejected."))
        
    wl = models.WinLossReason(
        proposal_id=prop.id,
        outcome="lost",
        reason_category=req.reason_category,
        notes=req.notes
    )
    db.add(wl)
    db.commit()
    db.refresh(prop)
    return _serialize_proposal(prop)

@router.get("/{proposal_id}/pdf")
def download_pdf(proposal_id: int, db: Session = Depends(get_db)):
    prop = db.query(models.Proposal).filter(models.Proposal.id == proposal_id).first()
    if not prop:
        raise HTTPException(404)
        
    if prop.proposal_pdf_path and os.path.exists(prop.proposal_pdf_path):
        return FileResponse(prop.proposal_pdf_path, media_type='application/pdf', filename=f"Proposal_{prop.proposal_number}.pdf")
        
    # Generate on the fly
    lead = db.query(models.Lead).filter(models.Lead.id == prop.lead_id).first()
    b_name = lead.business.name if lead and lead.business else "Client"
    pdf_path = generate_proposal_pdf(prop.id, prop.proposal_data, b_name)
    
    prop.proposal_pdf_path = pdf_path
    db.commit()
    
    return FileResponse(pdf_path, media_type='application/pdf', filename=f"Proposal_{prop.proposal_number}.pdf")

@router.get("/{proposal_id}/negotiation", response_model=List[schemas.NegotiationGuidance])
def get_negotiation(proposal_id: int, db: Session = Depends(get_db)):
    prop = db.query(models.Proposal).filter(models.Proposal.id == proposal_id).first()
    if not prop:
        raise HTTPException(404)
        
    audit = db.query(models.WebsiteAudit).filter(models.WebsiteAudit.lead_id == prop.lead_id).order_by(models.WebsiteAudit.created_at.desc()).first()
    if not audit:
        return []
        
    return generate_negotiation_guidance(prop, audit)

@router.get("/public/{token}")
def public_proposal(token: str, db: Session = Depends(get_db)):
    prop = db.query(models.Proposal).filter(models.Proposal.public_token == token).first()
    if not prop:
        raise HTTPException(404, "Invalid token")
        
    if prop.status == "sent":
        prop.status = "viewed"
        prop.viewed_at = datetime.utcnow()
        lead = db.query(models.Lead).filter(models.Lead.id == prop.lead_id).first()
        if lead:
            lead.deal_stage = "proposal_viewed"
            audit = db.query(models.WebsiteAudit).filter(models.WebsiteAudit.lead_id == prop.lead_id).order_by(models.WebsiteAudit.created_at.desc()).first()
            prop.close_probability = calculate_close_probability(lead, audit, "proposal_viewed")
        db.commit()
        
    return _serialize_proposal(prop)
