"""Project Health Engine — Computes project health automatically from task/milestone data."""
from datetime import datetime
from typing import List
from . import models


def compute_project_health(project: models.Project, milestones: List[models.Milestone], tasks: List[models.Task]) -> dict:
    """
    Computes project health_status and completion_percentage from actual task/milestone data.
    Never manually set — always computed.
    """
    now = datetime.utcnow()

    # ── Task Metrics ──
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == "completed"])
    overdue_tasks = len([t for t in tasks if t.due_date and t.due_date < now and t.status != "completed"])
    in_progress_tasks = len([t for t in tasks if t.status == "in_progress"])

    # ── Milestone Metrics ──
    total_milestones = len(milestones)
    completed_milestones = len([m for m in milestones if m.status == "completed"])
    missed_milestones = len([m for m in milestones if m.due_date and m.due_date < now and m.status != "completed"])

    # ── Completion Percentage ──
    if total_milestones > 0:
        # Weight milestones equally, each milestone's completion is based on its tasks
        milestone_completions = []
        for ms in milestones:
            ms_tasks = [t for t in tasks if t.milestone_id == ms.id]
            if ms_tasks:
                ms_completed = len([t for t in ms_tasks if t.status == "completed"])
                milestone_completions.append(int((ms_completed / len(ms_tasks)) * 100))
            elif ms.status == "completed":
                milestone_completions.append(100)
            else:
                milestone_completions.append(0)
        completion = int(sum(milestone_completions) / total_milestones) if milestone_completions else 0
    elif total_tasks > 0:
        completion = int((completed_tasks / total_tasks) * 100)
    else:
        completion = 0

    # ── Health Status ──
    health_score = 100

    # Overdue penalties
    if total_tasks > 0:
        overdue_ratio = overdue_tasks / total_tasks
        health_score -= overdue_ratio * 40

    # Missed milestones penalty
    if total_milestones > 0:
        missed_ratio = missed_milestones / total_milestones
        health_score -= missed_ratio * 30

    # Days remaining vs work remaining
    if project.target_completion_date:
        days_remaining = (project.target_completion_date - now).days
        work_remaining = 100 - completion
        if days_remaining <= 0 and completion < 100:
            health_score -= 30
        elif days_remaining > 0 and work_remaining > 0:
            velocity_needed = work_remaining / max(days_remaining, 1)
            if velocity_needed > 10:  # More than 10% per day needed
                health_score -= 20
            elif velocity_needed > 5:
                health_score -= 10

    health_score = max(0, min(100, health_score))

    if health_score >= 70:
        health_status = "healthy"
    elif health_score >= 40:
        health_status = "at_risk"
    else:
        health_status = "critical"

    return {
        "completion_percentage": completion,
        "health_status": health_status,
        "health_score": health_score,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "overdue_tasks": overdue_tasks,
        "in_progress_tasks": in_progress_tasks,
        "total_milestones": total_milestones,
        "completed_milestones": completed_milestones,
        "missed_milestones": missed_milestones,
    }


def update_milestone_completion(milestone: models.Milestone, tasks: List[models.Task]):
    """Recompute a single milestone's completion from its tasks."""
    ms_tasks = [t for t in tasks if t.milestone_id == milestone.id]
    if not ms_tasks:
        return
    completed = len([t for t in ms_tasks if t.status == "completed"])
    milestone.completion_percentage = int((completed / len(ms_tasks)) * 100)
    if milestone.completion_percentage == 100:
        milestone.status = "completed"
    elif completed > 0:
        milestone.status = "in_progress"


def recalculate_project(project: models.Project, db):
    """Full recalculation of project health and completion. Called after any task/milestone change."""
    milestones = db.query(models.Milestone).filter(models.Milestone.project_id == project.id).all()
    tasks = db.query(models.Task).filter(models.Task.project_id == project.id).all()

    # Update each milestone's completion
    for ms in milestones:
        update_milestone_completion(ms, tasks)

    # Compute project-level health
    health = compute_project_health(project, milestones, tasks)
    project.completion_percentage = health["completion_percentage"]
    project.health_status = health["health_status"]

    # Auto-complete project if all milestones done
    if health["total_milestones"] > 0 and health["completed_milestones"] == health["total_milestones"]:
        project.status = "completed"
        project.actual_completion_date = datetime.utcnow()
        project.completion_percentage = 100
