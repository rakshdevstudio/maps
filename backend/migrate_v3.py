import sqlite3
import os

DB_PATH = "maps_scraper.db"

def migrate_v3():
    print("Starting V3 Database Migration...")
    
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. ADD NEW COLUMNS TO LEADS
    columns_to_add = [
        ("next_action", "VARCHAR"),
        ("next_action_date", "DATETIME"),
        ("last_action", "VARCHAR"),
        ("last_action_date", "DATETIME"),
        ("estimated_project_value", "VARCHAR"),
        ("proposal_status", "VARCHAR DEFAULT 'not_created'")
    ]
    
    cursor.execute("PRAGMA table_info(leads)")
    existing_columns = {col[1] for col in cursor.fetchall()}
    
    for col_name, col_type in columns_to_add:
        if col_name not in existing_columns:
            try:
                print(f"Adding column {col_name} to leads...")
                cursor.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
        else:
            print(f"Column {col_name} already exists in leads.")
            
    # 2. CREATE OUTREACH_MESSAGES TABLE
    print("Creating outreach_messages table if not exists...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outreach_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            type VARCHAR NOT NULL,
            content TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            is_active BOOLEAN DEFAULT 1,
            source_revenue_leaks TEXT,
            source_opportunity_type VARCHAR,
            source_nexora_services TEXT,
            source_sales_readiness INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(lead_id) REFERENCES leads(id)
        )
    """)
    
    # 3. CREATE INDEXES
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_outreach_messages_id ON outreach_messages (id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_outreach_messages_lead_id ON outreach_messages (lead_id)")
    
    conn.commit()
    conn.close()
    
    print("V3 Migration Complete!")

if __name__ == "__main__":
    migrate_v3()
