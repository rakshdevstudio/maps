from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict

from .database import get_db
from . import models, schemas
from .ai.orchestration.daily_briefing_engine import run_daily_orchestration

router = APIRouter(prefix="/ai", tags=["AI Workforce"])

@router.post("/orchestrate")
def trigger_ai_orchestration(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Manually trigger the daily AI orchestration engine."""
    background_tasks.add_task(run_daily_orchestration, db)
    return {"message": "AI Orchestration triggered in the background."}

@router.get("/chief-of-staff", response_model=schemas.AIExecutiveBriefItem)
def get_chief_of_staff_brief(db: Session = Depends(get_db)):
    """Get the latest executive brief."""
    brief = db.query(models.AIExecutiveBrief).order_by(models.AIExecutiveBrief.generated_at.desc()).first()
    return brief

@router.get("/sdr/daily", response_model=List[schemas.AIDailySdrRecommendationItem])
def get_daily_sdr_recs(db: Session = Depends(get_db)):
    """Get the latest daily SDR recommendations."""
    # Assuming we get the top 10 most recent
    recs = db.query(models.AIDailySdrRecommendation).order_by(models.AIDailySdrRecommendation.generated_at.desc()).limit(10).all()
    # Sort by score for display just in case
    return sorted(recs, key=lambda x: x.score, reverse=True)

@router.get("/revenue/briefing", response_model=schemas.AIRevenueBriefingItem)
def get_revenue_briefing(db: Session = Depends(get_db)):
    """Get the latest pipeline revenue briefing."""
    briefing = db.query(models.AIRevenueBriefing).order_by(models.AIRevenueBriefing.generated_at.desc()).first()
    return briefing

@router.get("/proposal-strategy/{lead_id}", response_model=schemas.AIProposalStrategyItem)
def get_proposal_strategy(lead_id: int, db: Session = Depends(get_db)):
    """Get the recommended proposal strategy for a specific lead."""
    strategy = db.query(models.AIProposalStrategy).filter(models.AIProposalStrategy.lead_id == lead_id).order_by(models.AIProposalStrategy.generated_at.desc()).first()
    return strategy

@router.get("/projects/risk", response_model=List[schemas.AIProjectRiskReportItem])
def get_project_risks(db: Session = Depends(get_db)):
    """Get the latest active project risk reports."""
    # Get distinct latest reports for each project
    subquery = db.query(
        models.AIProjectRiskReport.project_id,
        db.func.max(models.AIProjectRiskReport.generated_at).label("max_date")
    ).group_by(models.AIProjectRiskReport.project_id).subquery()
    
    risks = db.query(models.AIProjectRiskReport).join(
        subquery, 
        (models.AIProjectRiskReport.project_id == subquery.c.project_id) & 
        (models.AIProjectRiskReport.generated_at == subquery.c.max_date)
    ).all()
    
    return risks

@router.get("/account-growth/{project_id}", response_model=List[schemas.AIAccountGrowthOpportunityItem])
def get_account_growth_opps(project_id: int, db: Session = Depends(get_db)):
    """Get the account growth opportunities for a project."""
    opps = db.query(models.AIAccountGrowthOpportunity).filter(models.AIAccountGrowthOpportunity.project_id == project_id).order_by(models.AIAccountGrowthOpportunity.confidence_score.desc()).all()
    return opps

@router.get("/account-growth", response_model=List[schemas.AIAccountGrowthOpportunityItem])
def get_all_account_growth_opps(db: Session = Depends(get_db)):
    """Get all account growth opportunities across all projects."""
    opps = db.query(models.AIAccountGrowthOpportunity).order_by(models.AIAccountGrowthOpportunity.confidence_score.desc()).limit(20).all()
    return opps
