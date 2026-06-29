"""Projects Router — Phase 6A Project Delivery Operating System."""
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from . import database, models, schemas
from .project_health_engine import recalculate_project
from .retainer_engine import generate_retainer_recommendations

router = APIRouter(prefix="/projects", tags=["projects"])


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Serializers ──────────────────────────────────────────────────────

def _serialize_project(p: models.Project) -> dict:
    return {
        "id": p.id,
        "lead_id": p.lead_id,
        "proposal_id": p.proposal_id,
        "project_name": p.project_name,
        "client_name": p.client_name,
        "project_value": p.project_value,
        "status": p.status,
        "health_status": p.health_status,
        "completion_percentage": p.completion_percentage,
        "start_date": p.start_date.isoformat() if p.start_date else None,
        "target_completion_date": p.target_completion_date.isoformat() if p.target_completion_date else None,
        "actual_completion_date": p.actual_completion_date.isoformat() if p.actual_completion_date else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


def _serialize_milestone(m: models.Milestone) -> dict:
    return {
        "id": m.id,
        "project_id": m.project_id,
        "title": m.title,
        "description": m.description,
        "status": m.status,
        "completion_percentage": m.completion_percentage,
        "due_date": m.due_date.isoformat() if m.due_date else None,
        "sort_order": m.sort_order,
        "created_at": m.created_at.isoformat() if m.created_at else None,
        "updated_at": m.updated_at.isoformat() if m.updated_at else None,
        "tasks": [_serialize_task(t) for t in (m.tasks or [])],
    }


def _serialize_task(t: models.Task) -> dict:
    return {
        "id": t.id,
        "project_id": t.project_id,
        "milestone_id": t.milestone_id,
        "title": t.title,
        "description": t.description,
        "priority": t.priority,
        "status": t.status,
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _serialize_file(f: models.ProjectFile) -> dict:
    return {
        "id": f.id,
        "project_id": f.project_id,
        "milestone_id": f.milestone_id,
        "task_id": f.task_id,
        "filename": f.filename,
        "filepath": f.filepath,
        "file_type": f.file_type,
        "file_size": f.file_size,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


def _serialize_event(e: models.ProjectEvent) -> dict:
    return {
        "id": e.id,
        "project_id": e.project_id,
        "event_type": e.event_type,
        "description": e.description,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


def _serialize_retainer(r: models.RetainerRecommendation) -> dict:
    return {
        "id": r.id,
        "project_id": r.project_id,
        "type": r.type,
        "title": r.title,
        "description": r.description,
        "rationale": r.rationale,
        "monthly_value": r.monthly_value,
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _log_event(db: Session, project_id: int, event_type: str, description: str):
    ev = models.ProjectEvent(project_id=project_id, event_type=event_type, description=description)
    db.add(ev)


# ── Project CRUD ─────────────────────────────────────────────────────

@router.get("")
def list_projects(
    status: Optional[str] = None,
    health: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Project)
    if status:
        q = q.filter(models.Project.status == status)
    if health:
        q = q.filter(models.Project.health_status == health)
    if search:
        q = q.filter(models.Project.project_name.ilike(f"%{search}%"))

    projects = q.order_by(
        # Critical first, then at_risk, then healthy
        models.Project.health_status.desc(),
        models.Project.project_value.desc(),
        models.Project.created_at.desc(),
    ).all()
    return [_serialize_project(p) for p in projects]


@router.get("/stats")
def delivery_stats(db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    active = [p for p in projects if p.status == "active"]
    at_risk = [p for p in active if p.health_status == "at_risk"]
    critical = [p for p in active if p.health_status == "critical"]
    completed = [p for p in projects if p.status == "completed"]
    revenue_in_delivery = sum(p.project_value for p in active)

    retainer_count = db.query(models.RetainerRecommendation).filter(
        models.RetainerRecommendation.status == "pending"
    ).count()

    # Upcoming deadlines: milestones due in the next 14 days
    from datetime import timedelta
    deadline_cutoff = datetime.utcnow() + timedelta(days=14)
    upcoming = db.query(models.Milestone).join(models.Project).filter(
        models.Project.status == "active",
        models.Milestone.status != "completed",
        models.Milestone.due_date != None,
        models.Milestone.due_date <= deadline_cutoff,
    ).order_by(models.Milestone.due_date).limit(10).all()

    upcoming_list = []
    for ms in upcoming:
        proj = db.query(models.Project).filter(models.Project.id == ms.project_id).first()
        upcoming_list.append({
            "milestone": ms.title,
            "project": proj.project_name if proj else "Unknown",
            "due_date": ms.due_date.isoformat() if ms.due_date else None,
        })

    return {
        "active_projects": len(active),
        "projects_at_risk": len(at_risk),
        "projects_critical": len(critical),
        "projects_completed": len(completed),
        "revenue_in_delivery": revenue_in_delivery,
        "retainer_opportunities": retainer_count,
        "upcoming_deadlines": upcoming_list,
    }


@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    proj = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "Project not found")

    milestones = db.query(models.Milestone).filter(models.Milestone.project_id == project_id).order_by(models.Milestone.sort_order).all()
    events = db.query(models.ProjectEvent).filter(models.ProjectEvent.project_id == project_id).order_by(models.ProjectEvent.created_at.desc()).limit(50).all()
    files = db.query(models.ProjectFile).filter(models.ProjectFile.project_id == project_id).all()
    retainers = db.query(models.RetainerRecommendation).filter(models.RetainerRecommendation.project_id == project_id).all()

    data = _serialize_project(proj)
    data["milestones"] = [_serialize_milestone(m) for m in milestones]
    data["events"] = [_serialize_event(e) for e in events]
    data["files"] = [_serialize_file(f) for f in files]
    data["retainer_recommendations"] = [_serialize_retainer(r) for r in retainers]
    return data


@router.patch("/{project_id}")
def update_project(project_id: int, req: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    proj = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "Project not found")

    if req.project_name is not None:
        proj.project_name = req.project_name
    if req.status is not None:
        old_status = proj.status
        proj.status = req.status
        _log_event(db, proj.id, "status_changed", f"Status changed from {old_status} to {req.status}")
        if req.status == "completed":
            proj.actual_completion_date = datetime.utcnow()
            proj.completion_percentage = 100
    if req.target_completion_date is not None:
        proj.target_completion_date = datetime.fromisoformat(req.target_completion_date)

    db.commit()
    db.refresh(proj)
    return _serialize_project(proj)


# ── Milestones ───────────────────────────────────────────────────────

@router.get("/{project_id}/milestones")
def list_milestones(project_id: int, db: Session = Depends(get_db)):
    milestones = db.query(models.Milestone).filter(
        models.Milestone.project_id == project_id
    ).order_by(models.Milestone.sort_order).all()
    return [_serialize_milestone(m) for m in milestones]


@router.patch("/{project_id}/milestones/{milestone_id}")
def update_milestone(project_id: int, milestone_id: int, req: schemas.MilestoneUpdate, db: Session = Depends(get_db)):
    ms = db.query(models.Milestone).filter(
        models.Milestone.id == milestone_id,
        models.Milestone.project_id == project_id,
    ).first()
    if not ms:
        raise HTTPException(404, "Milestone not found")

    if req.title is not None:
        ms.title = req.title
    if req.description is not None:
        ms.description = req.description
    if req.status is not None:
        old = ms.status
        ms.status = req.status
        _log_event(db, project_id, "milestone_updated", f"Milestone '{ms.title}' changed from {old} to {req.status}")
        if req.status == "completed":
            ms.completion_percentage = 100
            _log_event(db, project_id, "milestone_completed", f"Milestone '{ms.title}' completed")
    if req.due_date is not None:
        ms.due_date = datetime.fromisoformat(req.due_date)

    proj = db.query(models.Project).filter(models.Project.id == project_id).first()
    if proj:
        recalculate_project(proj, db)
        _check_retainer_trigger(proj, db)

    db.commit()
    db.refresh(ms)
    return _serialize_milestone(ms)


# ── Tasks ────────────────────────────────────────────────────────────

@router.get("/{project_id}/tasks")
def list_tasks(
    project_id: int,
    milestone_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Task).filter(models.Task.project_id == project_id)
    if milestone_id:
        q = q.filter(models.Task.milestone_id == milestone_id)
    if status:
        q = q.filter(models.Task.status == status)
    tasks = q.order_by(models.Task.created_at.desc()).all()
    return [_serialize_task(t) for t in tasks]


@router.post("/{project_id}/tasks")
def create_task(project_id: int, req: schemas.TaskCreate, db: Session = Depends(get_db)):
    proj = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "Project not found")

    task = models.Task(
        project_id=project_id,
        milestone_id=req.milestone_id,
        title=req.title,
        description=req.description,
        priority=req.priority,
        status=req.status,
        due_date=datetime.fromisoformat(req.due_date) if req.due_date else None,
    )
    db.add(task)
    _log_event(db, project_id, "task_created", f"Task '{req.title}' created")

    db.flush()
    recalculate_project(proj, db)
    db.commit()
    db.refresh(task)
    return _serialize_task(task)


@router.patch("/{project_id}/tasks/{task_id}")
def update_task(project_id: int, task_id: int, req: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.project_id == project_id,
    ).first()
    if not task:
        raise HTTPException(404, "Task not found")

    if req.milestone_id is not None:
        task.milestone_id = req.milestone_id
    if req.title is not None:
        task.title = req.title
    if req.description is not None:
        task.description = req.description
    if req.priority is not None:
        task.priority = req.priority
    if req.status is not None:
        old = task.status
        task.status = req.status
        if req.status == "completed" and old != "completed":
            _log_event(db, project_id, "task_completed", f"Task '{task.title}' completed")
        elif old != req.status:
            _log_event(db, project_id, "task_updated", f"Task '{task.title}' moved to {req.status}")
    if req.due_date is not None:
        task.due_date = datetime.fromisoformat(req.due_date)

    proj = db.query(models.Project).filter(models.Project.id == project_id).first()
    if proj:
        recalculate_project(proj, db)
        _check_retainer_trigger(proj, db)

    db.commit()
    db.refresh(task)
    return _serialize_task(task)


@router.delete("/{project_id}/tasks/{task_id}")
def delete_task(project_id: int, task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.project_id == project_id,
    ).first()
    if not task:
        raise HTTPException(404, "Task not found")

    _log_event(db, project_id, "task_deleted", f"Task '{task.title}' deleted")
    db.delete(task)

    proj = db.query(models.Project).filter(models.Project.id == project_id).first()
    if proj:
        recalculate_project(proj, db)

    db.commit()
    return {"status": "deleted"}


# ── Files ────────────────────────────────────────────────────────────

PROJECT_FILES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "project-files")
os.makedirs(PROJECT_FILES_DIR, exist_ok=True)


@router.get("/{project_id}/files")
def list_files(project_id: int, db: Session = Depends(get_db)):
    files = db.query(models.ProjectFile).filter(models.ProjectFile.project_id == project_id).all()
    return [_serialize_file(f) for f in files]


@router.post("/{project_id}/files")
async def upload_file(
    project_id: int,
    file: UploadFile = File(...),
    milestone_id: Optional[int] = None,
    task_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    proj = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "Project not found")

    # Save file to disk
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_name = f"{uuid.uuid4().hex}{ext}"
    project_dir = os.path.join(PROJECT_FILES_DIR, str(project_id))
    os.makedirs(project_dir, exist_ok=True)
    file_path = os.path.join(project_dir, unique_name)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    pf = models.ProjectFile(
        project_id=project_id,
        milestone_id=milestone_id,
        task_id=task_id,
        filename=file.filename or unique_name,
        filepath=file_path,
        file_type=ext.lstrip(".").lower() if ext else "unknown",
        file_size=len(contents),
    )
    db.add(pf)
    _log_event(db, project_id, "file_uploaded", f"File '{file.filename}' uploaded")
    db.commit()
    db.refresh(pf)
    return _serialize_file(pf)


@router.get("/files/{file_id}/download")
def download_file(file_id: int, db: Session = Depends(get_db)):
    pf = db.query(models.ProjectFile).filter(models.ProjectFile.id == file_id).first()
    if not pf or not os.path.exists(pf.filepath):
        raise HTTPException(404, "File not found")
    return FileResponse(pf.filepath, filename=pf.filename)


@router.delete("/files/{file_id}")
def delete_file(file_id: int, db: Session = Depends(get_db)):
    pf = db.query(models.ProjectFile).filter(models.ProjectFile.id == file_id).first()
    if not pf:
        raise HTTPException(404, "File not found")

    if os.path.exists(pf.filepath):
        os.remove(pf.filepath)

    _log_event(db, pf.project_id, "file_deleted", f"File '{pf.filename}' deleted")
    db.delete(pf)
    db.commit()
    return {"status": "deleted"}


# ── Timeline ─────────────────────────────────────────────────────────

@router.get("/{project_id}/timeline")
def get_timeline(project_id: int, db: Session = Depends(get_db)):
    events = db.query(models.ProjectEvent).filter(
        models.ProjectEvent.project_id == project_id
    ).order_by(models.ProjectEvent.created_at.desc()).limit(100).all()
    return [_serialize_event(e) for e in events]


# ── Lifecycle ────────────────────────────────────────────────────────

@router.get("/{project_id}/lifecycle")
def get_lifecycle(project_id: int, db: Session = Depends(get_db)):
    proj = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "Project not found")

    lead = db.query(models.Lead).filter(models.Lead.id == proj.lead_id).first()
    proposal = db.query(models.Proposal).filter(models.Proposal.id == proj.proposal_id).first()
    audit = db.query(models.WebsiteAudit).filter(
        models.WebsiteAudit.lead_id == proj.lead_id
    ).order_by(models.WebsiteAudit.created_at.desc()).first()
    outreach = db.query(models.OutreachMessage).filter(
        models.OutreachMessage.lead_id == proj.lead_id
    ).first()

    stages = []
    if lead:
        biz = lead.business
        stages.append({"stage": "Lead Discovered", "date": lead.created_at.isoformat() if lead.created_at else None, "detail": biz.name if biz else "Unknown"})
    if audit:
        stages.append({"stage": "Website Audited", "date": audit.created_at.isoformat() if audit.created_at else None, "detail": f"Score: {audit.audit_score}"})
    if outreach:
        stages.append({"stage": "Outreach Sent", "date": outreach.created_at.isoformat() if outreach.created_at else None, "detail": outreach.type})
    if proposal:
        stages.append({"stage": "Proposal Created", "date": proposal.created_at.isoformat() if proposal.created_at else None, "detail": proposal.title})
        if proposal.accepted_at:
            stages.append({"stage": "Deal Won", "date": proposal.accepted_at.isoformat(), "detail": f"${proposal.amount_min:,.0f}" if proposal.amount_min else ""})
    stages.append({"stage": "Project Started", "date": proj.created_at.isoformat() if proj.created_at else None, "detail": proj.project_name})
    if proj.status == "completed":
        stages.append({"stage": "Project Delivered", "date": proj.actual_completion_date.isoformat() if proj.actual_completion_date else None, "detail": "100% Complete"})

    retainers = db.query(models.RetainerRecommendation).filter(models.RetainerRecommendation.project_id == project_id).all()
    if retainers:
        stages.append({"stage": "Retainer Opportunities", "date": retainers[0].created_at.isoformat() if retainers[0].created_at else None, "detail": f"{len(retainers)} recommendations"})

    return {"project": _serialize_project(proj), "lifecycle": stages}


# ── Retainer Trigger ─────────────────────────────────────────────────

def _check_retainer_trigger(project: models.Project, db: Session):
    """Generate retainer recommendations when project hits 80% completion."""
    if project.completion_percentage < 80:
        return

    existing = db.query(models.RetainerRecommendation).filter(
        models.RetainerRecommendation.project_id == project.id
    ).count()
    if existing > 0:
        return  # Already generated

    audit = db.query(models.WebsiteAudit).filter(
        models.WebsiteAudit.lead_id == project.lead_id
    ).order_by(models.WebsiteAudit.created_at.desc()).first()
    proposal = db.query(models.Proposal).filter(
        models.Proposal.id == project.proposal_id
    ).first()

    if not audit or not proposal:
        return

    recs = generate_retainer_recommendations(project, audit, proposal)
    for rec in recs:
        rr = models.RetainerRecommendation(
            project_id=project.id,
            type=rec["type"],
            title=rec["title"],
            description=rec["description"],
            rationale=rec["rationale"],
            monthly_value=rec["monthly_value"],
        )
        db.add(rr)

    _log_event(db, project.id, "retainer_generated", f"{len(recs)} retainer recommendations generated")
