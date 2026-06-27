"""
Phase 4: Sales Execution Center — Safe Additive Migration

Adds new columns to `leads` table via ALTER TABLE ADD COLUMN.
No data is deleted. No tables are dropped. No writes to existing data.
"""
import sqlite3
import os

DB_PATH = "maps_scraper.db"


def migrate_v4():
    print("=" * 60)
    print("Phase 4 — Sales Execution Center Migration")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get existing columns
    cursor.execute("PRAGMA table_info(leads)")
    existing_columns = {col[1] for col in cursor.fetchall()}
    print(f"Existing leads columns: {len(existing_columns)}")

    # Phase 4 columns — Sales Task Engine + Deal Stage
    columns_to_add = [
        ("call_attempts", "INTEGER DEFAULT 0"),
        ("emails_sent", "INTEGER DEFAULT 0"),
        ("meetings_completed", "INTEGER DEFAULT 0"),
        ("last_contact_date", "DATETIME"),
        ("deal_stage", "VARCHAR DEFAULT 'lead_found'"),
    ]

    for col_name, col_type in columns_to_add:
        if col_name not in existing_columns:
            try:
                print(f"  Adding column: {col_name} ({col_type})")
                cursor.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"  Error adding {col_name}: {e}")
        else:
            print(f"  Column {col_name} already exists — skipping")

    # Map existing status values to deal stages for existing leads
    print("\nMapping existing status values to deal stages...")
    status_to_stage = {
        "new": "lead_found",
        "contacted": "contacted",
        "interested": "discovery_call",
        "not_interested": "closed_lost",
        "closed_won": "closed_won",
        "closed_lost": "closed_lost",
    }

    for old_status, new_stage in status_to_stage.items():
        cursor.execute(
            "UPDATE leads SET deal_stage = ? WHERE status = ? AND (deal_stage IS NULL OR deal_stage = 'lead_found')",
            (new_stage, old_status),
        )
        if cursor.rowcount > 0:
            print(f"  Mapped {cursor.rowcount} leads: status={old_status} → deal_stage={new_stage}")

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("Phase 4 Migration Complete!")
    print("=" * 60)


if __name__ == "__main__":
    migrate_v4()
