import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from .database import Base


class JobStatus(str, enum.Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"


class KeywordStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"
    THROTTLED = "throttled"


class ProposalStatus(str, enum.Enum):
    NOT_CREATED = "not_created"
    DRAFTED = "drafted"
    SENT = "sent"
    WON = "won"
    LOST = "lost"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default=JobStatus.IDLE.value)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    total_keywords = Column(Integer, default=0)
    completed_keywords = Column(Integer, default=0)
    current_keyword = Column(String, nullable=True)


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, unique=True, index=True)
    status = Column(String, default=KeywordStatus.PENDING.value)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BusinessResult(Base):
    __tablename__ = "business_results"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, index=True)
    name = Column(String)
    rating = Column(Float, nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(Text, nullable=True)
    category = Column(String, nullable=True)
    opening_hours = Column(Text, nullable=True)
    google_maps_url = Column(Text, unique=True, nullable=False)
    place_id = Column(String, unique=True, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow, index=True)


class LogEntry(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String, default="INFO")
    message = Column(Text)


class UploadHistory(Base):
    __tablename__ = "upload_history"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    upload_time = Column(DateTime, default=datetime.utcnow)
    file_hash = Column(String, index=True)
    file_size_bytes = Column(Integer)
    keywords_count = Column(Integer)
    mode = Column(String)


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business_results.id"), nullable=False, index=True)
    status = Column(String, default="new", index=True)
    priority = Column(Integer, default=0, index=True)
    notes = Column(Text, nullable=True)
    contact_name = Column(String, nullable=True)
    last_contacted = Column(DateTime, nullable=True)
    next_followup = Column(DateTime, nullable=True)
    
    # Phase 3 Features
    next_action = Column(String, nullable=True)
    next_action_date = Column(DateTime, nullable=True)
    last_action = Column(String, nullable=True)
    last_action_date = Column(DateTime, nullable=True)
    estimated_project_value = Column(String, nullable=True)
    proposal_status = Column(String, default=ProposalStatus.NOT_CREATED.value)
    
    # Phase 4: Sales Execution
    call_attempts = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    meetings_completed = Column(Integer, default=0)
    last_contact_date = Column(DateTime, nullable=True)
    deal_stage = Column(String, default="lead_found")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business = relationship("BusinessResult")
    activities = relationship("Activity", back_populates="lead", cascade="all, delete-orphan")
    audits = relationship("WebsiteAudit", back_populates="lead", cascade="all, delete-orphan")
    outreach_messages = relationship("OutreachMessage", back_populates="lead", cascade="all, delete-orphan")
    proposals = relationship("Proposal", back_populates="lead", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="lead", cascade="all, delete-orphan")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    type = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="activities")


class WebsiteAudit(Base):
    __tablename__ = "website_audits"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    url = Column(String, nullable=False)
    is_live = Column(Boolean, default=False)
    has_ssl = Column(Boolean, default=False)
    mobile_friendly = Column(Boolean, default=False)
    page_load_ms = Column(Integer, nullable=True)
    has_contact_form = Column(Boolean, default=False)
    has_whatsapp = Column(Boolean, default=False)
    has_facebook_pixel = Column(Boolean, default=False)
    has_google_analytics = Column(Boolean, default=False)
    has_meta_title = Column(Boolean, default=False)
    has_meta_description = Column(Boolean, default=False)
    
    tech_stack = Column(Text, nullable=True) # JSON encoded string array
    seo_title = Column(Text, nullable=True)
    seo_description = Column(Text, nullable=True)
    
    audit_score = Column(Integer, default=0)
    opportunity_score = Column(Integer, default=0)
    revenue_potential_score = Column(Integer, default=0)
    opportunity_type = Column(String, nullable=True)
    
    issues_found = Column(Text, nullable=True) # JSON encoded string array
    recommendation = Column(Text, nullable=True)
    why_contact_summary = Column(Text, nullable=True)
    
    screenshot_path = Column(String, nullable=True)
    
    # V2 Features
    conversion_score = Column(Integer, default=0)
    lead_capture_present = Column(Boolean, default=False)
    conversion_screenshot_path = Column(String, nullable=True)
    estimated_deal_size = Column(String, nullable=True)
    sales_pitch_angle = Column(Text, nullable=True)
    business_impact = Column(Text, nullable=True)
    sales_readiness_score = Column(Integer, default=0)
    revenue_leaks = Column(Text, nullable=True)
    nexora_services = Column(Text, nullable=True)
    
    audited_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lead = relationship("Lead", back_populates="audits")


class OutreachMessage(Base):
    __tablename__ = "outreach_messages"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    type = Column(String, nullable=False) # 'cold_email', 'whatsapp', 'linkedin', 'call_script'
    content = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    
    # Traceability
    source_revenue_leaks = Column(Text, nullable=True)
    source_opportunity_type = Column(String, nullable=True)
    source_nexora_services = Column(Text, nullable=True)
    source_sales_readiness = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    lead = relationship("Lead", back_populates="outreach_messages")


class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    proposal_number = Column(String, nullable=True)
    version = Column(Integer, default=1)
    parent_proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=True)
    
    title = Column(String, nullable=True)
    status = Column(String, default="draft", index=True)
    
    amount_min = Column(Float, nullable=True)
    amount_max = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    package_name = Column(String, nullable=True)
    
    proposal_data = Column(Text, nullable=True) # JSON
    close_probability = Column(Integer, default=0)
    public_token = Column(String, unique=True, index=True)
    proposal_pdf_path = Column(String, nullable=True)
    
    sent_at = Column(DateTime, nullable=True)
    viewed_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Analytics
    view_count = Column(Integer, default=0)
    first_viewed_at = Column(DateTime, nullable=True)
    last_viewed_at = Column(DateTime, nullable=True)
    time_spent = Column(Integer, default=0) # Total seconds
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lead = relationship("Lead", back_populates="proposals")


class ProposalTemplate(Base):
    __tablename__ = "proposal_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    category = Column(String)
    description = Column(Text)
    deliverables = Column(Text) # JSON
    timeline = Column(String)
    base_price = Column(Float)
    is_active = Column(Boolean, default=True)


class WinLossReason(Base):
    __tablename__ = "win_loss_reasons"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False)
    outcome = Column(String, nullable=False) # won or lost
    reason_category = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    proposal = relationship("Proposal")


# ── Phase 6A: Project Delivery Operating System ──────────────────────

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False, index=True)
    project_name = Column(String, nullable=False)
    client_name = Column(String, nullable=False)
    project_value = Column(Float, default=0)
    status = Column(String, default="active", index=True)  # active, on_hold, completed, cancelled
    health_status = Column(String, default="healthy")  # healthy, at_risk, critical
    completion_percentage = Column(Integer, default=0)
    start_date = Column(DateTime, default=datetime.utcnow)
    target_completion_date = Column(DateTime, nullable=True)
    actual_completion_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lead = relationship("Lead", back_populates="projects")
    proposal = relationship("Proposal")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan", order_by="Milestone.sort_order")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    events = relationship("ProjectEvent", back_populates="project", cascade="all, delete-orphan", order_by="ProjectEvent.created_at.desc()")
    retainer_recommendations = relationship("RetainerRecommendation", back_populates="project", cascade="all, delete-orphan")


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, in_progress, completed
    completion_percentage = Column(Integer, default=0)
    due_date = Column(DateTime, nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="milestones")
    tasks = relationship("Task", back_populates="milestone", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String, default="medium")  # low, medium, high, critical
    status = Column(String, default="backlog")  # backlog, todo, in_progress, review, completed
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="tasks")
    milestone = relationship("Milestone", back_populates="tasks")


class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    file_size = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="files")


class ProjectEvent(Base):
    __tablename__ = "project_events"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    project = relationship("Project", back_populates="events")


class RetainerRecommendation(Base):
    __tablename__ = "retainer_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    type = Column(String, nullable=False)  # maintenance, seo, analytics, growth
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)
    monthly_value = Column(Float, default=0)
    status = Column(String, default="pending")  # pending, presented, accepted, declined
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="retainer_recommendations")


# ── Phase 7: Autonomous AI Workforce ─────────────────────────────────

class AIDailySdrRecommendation(Base):
    __tablename__ = "ai_daily_sdr_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)

    lead = relationship("Lead")


class AIRevenueBriefing(Base):
    __tablename__ = "ai_revenue_briefings"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_total = Column(Float, default=0)
    likely_to_close = Column(Float, default=0)
    risk_summary = Column(Text, nullable=False)
    blocked_summary = Column(Text, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)


class AIProposalStrategy(Base):
    __tablename__ = "ai_proposal_strategy"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    recommended_package = Column(String, nullable=False)
    recommended_investment = Column(Float, nullable=False)
    recommended_angle = Column(Text, nullable=False)
    positioning = Column(Text, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead")


class AIProjectRiskReport(Base):
    __tablename__ = "ai_project_risk_reports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    risk_level = Column(String, nullable=False)  # low, medium, high, critical
    slipping_reason = Column(Text, nullable=True)
    overdue_tasks_summary = Column(Text, nullable=True)
    blocked_milestones_summary = Column(Text, nullable=True)
    priority_action = Column(Text, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)

    project = relationship("Project")


class AIAccountGrowthOpportunity(Base):
    __tablename__ = "ai_account_growth_opportunities"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    opportunity_type = Column(String, nullable=False)
    rationale = Column(Text, nullable=False)
    expected_outcome = Column(Text, nullable=False)
    confidence_score = Column(Integer, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)

    project = relationship("Project")


class AIExecutiveBrief(Base):
    __tablename__ = "ai_executive_briefs"

    id = Column(Integer, primary_key=True, index=True)
    what_happened = Column(Text, nullable=False)
    what_matters = Column(Text, nullable=False)
    what_is_blocked = Column(Text, nullable=False)
    what_should_happen_next = Column(Text, nullable=False)
    what_deserves_attention = Column(Text, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
