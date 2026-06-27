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
