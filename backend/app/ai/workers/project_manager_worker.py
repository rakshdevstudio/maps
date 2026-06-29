"""AI Project Manager Worker — Analyzes active projects for delivery risks."""
from sqlalchemy.orm import Session
from datetime import datetime
from ... import models
from ..engines.risk_engine import detect_project_risk


def run_project_manager_worker(db: Session):
    """
    Analyzes all active projects and generates risk reports.
    Persists to AIProjectRiskReport.
    """
    now = datetime.utcnow()
    projects = db.query(models.Project).filter(models.Project.status == "active").all()
    
    generated = 0
    for proj in projects:
        risk = detect_project_risk(proj)
        if risk["level"] == "low":
            continue
            
        # Analyze why it's slipping
        tasks = db.query(models.Task).filter(models.Task.project_id == proj.id).all()
        milestones = db.query(models.Milestone).filter(models.Milestone.project_id == proj.id).all()
        
        overdue_tasks = [t for t in tasks if t.due_date and t.due_date < now and t.status != "completed"]
        blocked_milestones = [m for m in milestones if m.due_date and m.due_date < now and m.status != "completed"]
        
        overdue_tasks_summary = f"{len(overdue_tasks)} tasks overdue." if overdue_tasks else None
        blocked_milestones_summary = f"{len(blocked_milestones)} milestones blocked." if blocked_milestones else None
        
        report = models.AIProjectRiskReport(
            project_id=proj.id,
            risk_level=risk["level"],
            slipping_reason=risk["reason"],
            overdue_tasks_summary=overdue_tasks_summary,
            blocked_milestones_summary=blocked_milestones_summary,
            priority_action=risk["action"]
        )
        db.add(report)
        generated += 1
        
    db.commit()
    print(f"AI Project Manager: Generated {generated} project risk reports.")
