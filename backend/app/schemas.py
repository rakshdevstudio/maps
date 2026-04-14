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
