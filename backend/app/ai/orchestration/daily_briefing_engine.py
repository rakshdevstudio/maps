"""Daily Briefing Engine — Autonomous Orchestrator."""
from sqlalchemy.orm import Session
from ..workers.sdr_worker import run_sdr_worker
from ..workers.revenue_analyst_worker import run_revenue_analyst_worker
from ..workers.proposal_strategist_worker import run_proposal_strategist_worker
from ..workers.project_manager_worker import run_project_manager_worker
from ..workers.account_manager_worker import run_account_manager_worker
from ..workers.chief_of_staff_worker import run_chief_of_staff_worker

def run_daily_orchestration(db: Session):
    """
    Triggers the entire autonomous workforce in logical sequence.
    """
    print("--- STARTING AI WORKFORCE ORCHESTRATION ---")
    
    # 1. Clear previous day's ephemeral recommendations to keep tables lean, or just let them pile up.
    # For Phase 7, we'll let them pile up as an immutable log, and just query the latest.
    # Actually, SDR and Risks might need cleanup so we don't have dupes. We handled some cleanup inside the workers.

    # 2. Run independent analysis workers
    run_sdr_worker(db)
    run_revenue_analyst_worker(db)
    run_proposal_strategist_worker(db)
    run_project_manager_worker(db)
    run_account_manager_worker(db)
    
    # 3. Run the Chief of Staff (must run last to aggregate all above)
    run_chief_of_staff_worker(db)
    
    print("--- AI WORKFORCE ORCHESTRATION COMPLETE ---")
    return {"status": "success", "message": "Autonomous workforce execution complete."}
