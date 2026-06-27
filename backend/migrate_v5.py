import sqlite3
import json
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate_v5")

DB_PATH = os.path.join(os.path.dirname(__file__), "scraper.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Create proposals table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            proposal_number VARCHAR,
            version INTEGER DEFAULT 1,
            parent_proposal_id INTEGER,
            title VARCHAR,
            status VARCHAR DEFAULT 'draft',
            amount_min FLOAT,
            amount_max FLOAT,
            currency VARCHAR DEFAULT 'USD',
            package_name VARCHAR,
            proposal_data TEXT,
            close_probability INTEGER DEFAULT 0,
            public_token VARCHAR UNIQUE,
            proposal_pdf_path VARCHAR,
            sent_at DATETIME,
            viewed_at DATETIME,
            accepted_at DATETIME,
            rejected_at DATETIME,
            expires_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(lead_id) REFERENCES leads(id),
            FOREIGN KEY(parent_proposal_id) REFERENCES proposals(id)
        )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS ix_proposals_lead_id ON proposals(lead_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS ix_proposals_status ON proposals(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS ix_proposals_created_at ON proposals(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS ix_proposals_public_token ON proposals(public_token)')

        # Create proposal_templates table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS proposal_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR,
            category VARCHAR,
            description TEXT,
            deliverables TEXT,
            timeline VARCHAR,
            base_price FLOAT,
            is_active BOOLEAN DEFAULT 1
        )
        ''')

        # Create win_loss_reasons table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS win_loss_reasons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proposal_id INTEGER NOT NULL,
            outcome VARCHAR NOT NULL,
            reason_category VARCHAR NOT NULL,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(proposal_id) REFERENCES proposals(id)
        )
        ''')

        # Seed Default Packages (only if empty)
        cursor.execute("SELECT COUNT(*) FROM proposal_templates")
        if cursor.fetchone()[0] == 0:
            templates = [
                {
                    "name": "Website Modernization",
                    "category": "Development",
                    "description": "A complete overhaul of the existing website focusing on speed, mobile responsiveness, and modern design principles.",
                    "deliverables": ["Custom Design", "Mobile Optimization", "CMS Integration", "Speed Optimization", "Basic SEO"],
                    "timeline": "4-6 Weeks",
                    "base_price": 5000.0
                },
                {
                    "name": "SEO Growth",
                    "category": "Marketing",
                    "description": "Comprehensive search engine optimization to capture local and national organic traffic.",
                    "deliverables": ["Keyword Research", "On-page SEO", "Technical SEO Audit", "Content Strategy", "Link Building"],
                    "timeline": "3 Months (Retainer)",
                    "base_price": 2500.0
                },
                {
                    "name": "Analytics & Tracking Setup",
                    "category": "Data",
                    "description": "Implementation of advanced tracking systems to measure conversion events accurately.",
                    "deliverables": ["Google Tag Manager Setup", "GA4 Configuration", "Event Tracking", "Custom Dashboards", "Conversion Attribution"],
                    "timeline": "1-2 Weeks",
                    "base_price": 1500.0
                },
                {
                    "name": "Conversion Optimization",
                    "category": "Growth",
                    "description": "Data-driven improvements to increase the percentage of visitors who turn into leads or customers.",
                    "deliverables": ["A/B Testing", "Heatmap Analysis", "Funnel Optimization", "Copywriting Tweaks", "Lead Capture Setup"],
                    "timeline": "Ongoing",
                    "base_price": 3000.0
                },
                {
                    "name": "AI Automation",
                    "category": "Operations",
                    "description": "Streamlining business operations using AI-powered workflows and chatbots.",
                    "deliverables": ["AI Chatbot Integration", "CRM Automation", "Email Triage", "Lead Scoring Automation"],
                    "timeline": "3-5 Weeks",
                    "base_price": 7500.0
                },
                {
                    "name": "Custom Engagement",
                    "category": "Consulting",
                    "description": "A tailored scope of work defined after a deep discovery process.",
                    "deliverables": ["Discovery Workshop", "Architecture Design", "Custom Implementation"],
                    "timeline": "TBD",
                    "base_price": 10000.0
                }
            ]
            
            for t in templates:
                cursor.execute('''
                INSERT INTO proposal_templates (name, category, description, deliverables, timeline, base_price, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', (t["name"], t["category"], t["description"], json.dumps(t["deliverables"]), t["timeline"], t["base_price"]))

        conn.commit()
        logger.info("Phase 5 Migration completed successfully.")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
