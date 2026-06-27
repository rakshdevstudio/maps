import sqlite3
import json
import os
import sys

from app.database import engine, SessionLocal
from app import models

DB_PATH = "maps_scraper.db"

def migrate():
    print("Starting safe migration for website_audits V2...")
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Backup existing data
    try:
        cursor.execute("SELECT * FROM website_audits")
        rows = cursor.fetchall()
        print(f"Backed up {len(rows)} records from website_audits.")
    except sqlite3.OperationalError:
        print("Table website_audits doesn't exist. Nothing to backup.")
        rows = []
        
    # 2. Drop table
    cursor.execute("DROP TABLE IF EXISTS website_audits")
    conn.commit()
    print("Dropped website_audits table.")
    
    # 3. Recreate table using SQLAlchemy schema
    print("Recreating table from new schema...")
    models.Base.metadata.create_all(bind=engine)
    
    # 4. Restore data with V2 defaults
    if rows:
        print("Restoring data...")
        for row in rows:
            data_dict = dict(row)
            # Add V2 fields
            data_dict["conversion_score"] = 0
            data_dict["lead_capture_present"] = False
            data_dict["conversion_screenshot_path"] = None
            data_dict["estimated_deal_size"] = None
            data_dict["sales_pitch_angle"] = None
            data_dict["business_impact"] = None
            data_dict["sales_readiness_score"] = 0
            data_dict["revenue_leaks"] = "[]"
            data_dict["nexora_services"] = "[]"
            
            columns = ", ".join(data_dict.keys())
            placeholders = ", ".join("?" * len(data_dict))
            values = tuple(data_dict.values())
            
            cursor.execute(f"INSERT INTO website_audits ({columns}) VALUES ({placeholders})", values)
        
        conn.commit()
        print("Data restored successfully.")
        
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
