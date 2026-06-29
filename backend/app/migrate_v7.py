"""Phase 7 Migration: Autonomous AI Workforce tables."""
import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "..", "maps_scraper.db")

TABLES = [
    """
    CREATE TABLE IF NOT EXISTS ai_daily_sdr_recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER NOT NULL REFERENCES leads(id),
        score INTEGER NOT NULL,
        reason TEXT NOT NULL,
        recommended_action TEXT NOT NULL,
        generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_revenue_briefings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pipeline_total REAL DEFAULT 0,
        likely_to_close REAL DEFAULT 0,
        risk_summary TEXT NOT NULL,
        blocked_summary TEXT NOT NULL,
        generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_proposal_strategy (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER NOT NULL REFERENCES leads(id),
        recommended_package TEXT NOT NULL,
        recommended_investment REAL NOT NULL,
        recommended_angle TEXT NOT NULL,
        positioning TEXT NOT NULL,
        generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_project_risk_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL REFERENCES projects(id),
        risk_level TEXT NOT NULL,
        slipping_reason TEXT,
        overdue_tasks_summary TEXT,
        blocked_milestones_summary TEXT,
        priority_action TEXT NOT NULL,
        generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_account_growth_opportunities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL REFERENCES projects(id),
        opportunity_type TEXT NOT NULL,
        rationale TEXT NOT NULL,
        expected_outcome TEXT NOT NULL,
        confidence_score INTEGER NOT NULL,
        generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_executive_briefs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        what_happened TEXT NOT NULL,
        what_matters TEXT NOT NULL,
        what_is_blocked TEXT NOT NULL,
        what_should_happen_next TEXT NOT NULL,
        what_deserves_attention TEXT NOT NULL,
        generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
]

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_ai_sdr_lead_id ON ai_daily_sdr_recommendations(lead_id)",
    "CREATE INDEX IF NOT EXISTS idx_ai_sdr_generated_at ON ai_daily_sdr_recommendations(generated_at)",
    "CREATE INDEX IF NOT EXISTS idx_ai_revenue_generated_at ON ai_revenue_briefings(generated_at)",
    "CREATE INDEX IF NOT EXISTS idx_ai_prop_strat_lead_id ON ai_proposal_strategy(lead_id)",
    "CREATE INDEX IF NOT EXISTS idx_ai_proj_risk_project_id ON ai_project_risk_reports(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_ai_proj_risk_generated_at ON ai_project_risk_reports(generated_at)",
    "CREATE INDEX IF NOT EXISTS idx_ai_account_growth_project_id ON ai_account_growth_opportunities(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_ai_account_growth_generated_at ON ai_account_growth_opportunities(generated_at)",
    "CREATE INDEX IF NOT EXISTS idx_ai_exec_brief_generated_at ON ai_executive_briefs(generated_at)",
]


def run_migration():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    for table_sql in TABLES:
        cursor.execute(table_sql)
        
    for index_sql in INDEXES:
        cursor.execute(index_sql)
    
    conn.commit()
    conn.close()
    print("Phase 7 migration complete. All AI tables created.")


if __name__ == "__main__":
    run_migration()
