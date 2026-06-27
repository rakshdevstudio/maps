from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class KeywordBulkRequest(BaseModel):
    keywords_text: str = ""
    mode: Literal["add", "replace", "sync"] = "add"


class SettingsPayload(BaseModel):
    max_results_per_keyword: int = Field(default=20, ge=1, le=200)
    delay_between_requests_ms: int = Field(default=1500, ge=0, le=60000)
    parallel_workers: int = Field(default=1, ge=1, le=10)
    proxy_url: str = ""
    headless: bool = True
    auto_save: bool = True
    google_sheets_enabled: bool = False
    google_sheets_sheet_name: str = "MapsScraperResults"
    api_endpoint: str = "http://localhost:8000"
    max_retries: int = Field(default=3, ge=1, le=10)
    page_timeout_ms: int = Field(default=45000, ge=5000, le=180000)
    browser_executable_path: str = ""
    scroll_depth_limit: int = Field(default=12, ge=1, le=100)
    stop_on_duplicate_results: bool = True
    duplicate_stop_threshold: int = Field(default=5, ge=1, le=50)
    adaptive_delay_enabled: bool = True
    adaptive_delay_max_ms: int = Field(default=8000, ge=500, le=120000)


class KeywordItem(BaseModel):
    id: int
    text: str
    status: str
    updated_at: str


class LogItem(BaseModel):
    id: int
    timestamp: str
    level: str
    message: str


class BusinessItem(BaseModel):
    id: int
    keyword: str
    name: str
    rating: Optional[float]
    address: Optional[str]
    phone: Optional[str]
    website: Optional[str]
    category: Optional[str]
    opening_hours: Optional[str]
    google_maps_url: str
    place_id: Optional[str]
    scraped_at: str


class DashboardSnapshot(BaseModel):
    status: str
    current_keyword: Optional[str]
    active_workers: int
    totals: dict
    logs: List[LogItem]
    keywords: List[KeywordItem]
    keyword_progress: List[dict] = []


class ActivityItem(BaseModel):
    id: int
    lead_id: int
    type: str
    content: Optional[str]
    created_at: str

    class Config:
        orm_mode = True


class LeadItem(BaseModel):
    id: int
    business_id: int
    status: str
    priority: int
    notes: Optional[str]
    contact_name: Optional[str]
    last_contacted: Optional[str]
    next_followup: Optional[str]
    
    # Phase 3
    next_action: Optional[str] = None
    next_action_date: Optional[str] = None
    last_action: Optional[str] = None
    last_action_date: Optional[str] = None
    estimated_project_value: Optional[str] = None
    proposal_status: Optional[str] = None
    
    # Phase 4: Sales Execution
    call_attempts: int = 0
    emails_sent: int = 0
    meetings_completed: int = 0
    last_contact_date: Optional[str] = None
    deal_stage: str = "lead_found"
    
    created_at: str
    updated_at: str

    class Config:
        orm_mode = True


class WebsiteAuditItem(BaseModel):
    id: int
    lead_id: int
    url: str
    is_live: bool
    has_ssl: bool
    mobile_friendly: bool
    page_load_ms: Optional[int]
    has_contact_form: bool
    has_whatsapp: bool
    has_facebook_pixel: bool
    has_google_analytics: bool
    has_meta_title: bool
    has_meta_description: bool
    
    tech_stack: List[str] = []
    seo_title: Optional[str]
    seo_description: Optional[str]
    
    audit_score: int
    opportunity_score: int
    revenue_potential_score: int
    opportunity_type: Optional[str]
    
    issues_found: List[str] = []
    recommendation: Optional[str]
    why_contact_summary: Optional[str]
    
    screenshot_path: Optional[str]
    
    # V2 Features
    conversion_score: int
    lead_capture_present: bool
    conversion_screenshot_path: Optional[str]
    estimated_deal_size: Optional[str]
    sales_pitch_angle: Optional[str]
    business_impact: Optional[str]
    sales_readiness_score: int
    revenue_leaks: List[str] = []
    nexora_services: List[str] = []
    
    audited_at: str
    created_at: str
    updated_at: str

    class Config:
        orm_mode = True


class LeadDetail(LeadItem):
    business: BusinessItem
    activities: List[ActivityItem] = []
    latest_audit: Optional[WebsiteAuditItem] = None


class LeadCreate(BaseModel):
    business_id: int


class LeadUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[int] = None
    notes: Optional[str] = None
    contact_name: Optional[str] = None
    last_contacted: Optional[str] = None
    next_followup: Optional[str] = None
    
    # Phase 3
    next_action: Optional[str] = None
    next_action_date: Optional[str] = None
    proposal_status: Optional[str] = None
    
    # Phase 4
    deal_stage: Optional[str] = None
    call_attempts: Optional[int] = None
    emails_sent: Optional[int] = None
    meetings_completed: Optional[int] = None
    last_contact_date: Optional[str] = None


class ActivityCreate(BaseModel):
    type: str
    content: Optional[str]


class OutreachMessageItem(BaseModel):
    id: int
    lead_id: int
    type: str
    content: str
    version: int
    is_active: bool
    source_revenue_leaks: Optional[str]
    source_opportunity_type: Optional[str]
    source_nexora_services: Optional[str]
    source_sales_readiness: Optional[int]
    created_at: str

    class Config:
        orm_mode = True


class OutreachResponse(BaseModel):
    cold_email: Optional[OutreachMessageItem]
    whatsapp: Optional[OutreachMessageItem]
    linkedin: Optional[OutreachMessageItem]
    call_script: Optional[OutreachMessageItem]


class PipelineRevenue(BaseModel):
    potential_revenue_val: float
    won_revenue_val: float
    lost_revenue_val: float
    potential_revenue_fmt: str
    won_revenue_fmt: str
    lost_revenue_fmt: str


class CommandCenterItem(LeadItem):
    business_name: str
    business_website: Optional[str]
    audit_score: Optional[int]
    revenue_potential: Optional[int]
    sales_readiness: Optional[int]
    opportunity_type: Optional[str]
    deal_size: Optional[str]


class DealHealthInfo(BaseModel):
    deal_health_score: int = 0
    deal_health_status: str = "Unknown"
    days_since_contact: int = -1
    contact_recency_score: int = 0
    stage_probability: float = 0.0
    stage_label: str = ""
    weighted_value: float = 0.0
    deal_value: float = 0.0


class TodayLeadItem(BaseModel):
    id: int
    business_name: str
    business_phone: Optional[str] = None
    business_website: Optional[str] = None
    deal_stage: str = "lead_found"
    deal_value: float = 0
    deal_health_score: int = 0
    deal_health_status: str = "Unknown"
    days_since_contact: int = -1
    next_action: Optional[str] = None
    next_action_date: Optional[str] = None
    estimated_deal_size: Optional[str] = None
    stage_label: str = ""


class TodayViewResponse(BaseModel):
    overdue: List[TodayLeadItem] = []
    calls_due: List[TodayLeadItem] = []
    followups_due: List[TodayLeadItem] = []
    meetings_scheduled: List[TodayLeadItem] = []
    critical_deals: List[TodayLeadItem] = []
    summary: dict = {}


class ProposalTemplateItem(BaseModel):
    id: int
    name: str
    category: str
    description: str
    deliverables: str
    timeline: str
    base_price: float
    is_active: bool

    class Config:
        orm_mode = True


class WinLossReasonItem(BaseModel):
    id: int
    proposal_id: int
    outcome: str
    reason_category: str
    notes: Optional[str]
    created_at: str

    class Config:
        orm_mode = True


class ProposalItem(BaseModel):
    id: int
    lead_id: int
    proposal_number: Optional[str]
    version: int
    parent_proposal_id: Optional[int]
    title: Optional[str]
    status: str
    amount_min: Optional[float]
    amount_max: Optional[float]
    currency: str
    package_name: Optional[str]
    proposal_data: Optional[str]
    close_probability: int
    public_token: Optional[str]
    proposal_pdf_path: Optional[str]
    sent_at: Optional[str]
    viewed_at: Optional[str]
    accepted_at: Optional[str]
    rejected_at: Optional[str]
    expires_at: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        orm_mode = True


class ProposalDetail(ProposalItem):
    lead: Optional[LeadItem] = None
    win_loss: Optional[List[WinLossReasonItem]] = []


class ProposalUpdate(BaseModel):
    status: Optional[str] = None


class ProposalGenerateRequest(BaseModel):
    template_id: int


class WinLossReasonCreate(BaseModel):
    reason_category: str
    notes: Optional[str] = None


class ProposalStatsResponse(BaseModel):
    drafted: int
    sent: int
    viewed: int
    acceptance_rate: float
    average_deal_size: float
    forecasted_revenue: float
    likely_revenue: float
    pipeline_revenue: float


class NegotiationGuidance(BaseModel):
    objection: str
    response: str

