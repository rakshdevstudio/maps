import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import ProposalTemplate
import json

def seed_templates():
    db = SessionLocal()
    
    if db.query(ProposalTemplate).count() == 0:
        templates = [
            ProposalTemplate(
                name="Revenue Recovery Sprint",
                category="Website Optimization",
                description="Fast-track optimization to plug critical revenue leaks.",
                deliverables=json.dumps(["Conversion Rate Optimization", "Speed Optimization", "Technical SEO Fixes", "Analytics Setup"]),
                timeline="2 Weeks",
                base_price=2500.0,
                is_active=True
            ),
            ProposalTemplate(
                name="Digital Transformation Engine",
                category="Full Stack Build",
                description="End-to-end digital presence overhaul.",
                deliverables=json.dumps(["Custom Website Redesign", "CRM Integration", "Automated Lead Nurturing", "SEO Strategy", "1 Year Support"]),
                timeline="6 Weeks",
                base_price=10000.0,
                is_active=True
            ),
            ProposalTemplate(
                name="Local Dominance Retainer",
                category="Ongoing Growth",
                description="Monthly growth partner for local service businesses.",
                deliverables=json.dumps(["Local SEO Management", "Google Business Profile Optimization", "Review Generation System", "Monthly Reporting"]),
                timeline="6 Month Retainer",
                base_price=1500.0,
                is_active=True
            )
        ]
        db.add_all(templates)
        db.commit()
        print("Seeded templates.")
    else:
        print("Templates already exist.")
        
if __name__ == "__main__":
    seed_templates()
