import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

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
    new_keywords = Column(Integer)
    mode = Column(String)
