"""Phase 6A Migration: Project Delivery Operating System tables."""
import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "..", "maps_scraper.db")

TABLES = [
    """
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER NOT NULL REFERENCES leads(id),
        proposal_id INTEGER NOT NULL REFERENCES proposals(id),
        project_name TEXT NOT NULL,
        client_name TEXT NOT NULL,
        project_value REAL DEFAULT 0,
        status TEXT DEFAULT 'active',
        health_status TEXT DEFAULT 'healthy',
        completion_percentage INTEGER DEFAULT 0,
        start_date DATETIME,
        target_completion_date DATETIME,
        actual_completion_date DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS milestones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL REFERENCES projects(id),
        title TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'pending',
        completion_percentage INTEGER DEFAULT 0,
        due_date DATETIME,
        sort_order INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL REFERENCES projects(id),
        milestone_id INTEGER REFERENCES milestones(id),
        title TEXT NOT NULL,
        description TEXT,
        priority TEXT DEFAULT 'medium',
        status TEXT DEFAULT 'backlog',
        due_date DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS project_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL REFERENCES projects(id),
        milestone_id INTEGER REFERENCES milestones(id),
        task_id INTEGER REFERENCES tasks(id),
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        file_type TEXT,
        file_size INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS project_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL REFERENCES projects(id),
        event_type TEXT NOT NULL,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS retainer_recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL REFERENCES projects(id),
        type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        rationale TEXT,
        monthly_value REAL DEFAULT 0,
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
]

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_projects_lead_id ON projects(lead_id)",
    "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
    "CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_milestones_project_id ON milestones(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_milestone_id ON tasks(milestone_id)",
    "CREATE INDEX IF NOT EXISTS idx_project_files_project_id ON project_files(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_project_events_project_id ON project_events(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_project_events_created_at ON project_events(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_retainer_recs_project_id ON retainer_recommendations(project_id)",
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
    print("Phase 6A migration complete. All tables created.")


if __name__ == "__main__":
    run_migration()
