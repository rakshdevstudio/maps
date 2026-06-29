import hashlib
import io
import csv
import os
from io import StringIO

from fastapi import Depends, FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from . import config, database, models, schemas
from .scraper_manager import scraper_manager
from .leads_router import router as leads_router
from .audits_router import router as audits_router
from .proposal_router import router as proposal_router
from .projects_router import router as projects_router
from .ai_router import router as ai_router

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Maps Scraper Dashboard")
app.include_router(leads_router)
app.include_router(audits_router)
app.include_router(proposal_router)
app.include_router(projects_router)
app.include_router(ai_router)

screenshots_dir = os.path.join(os.path.dirname(__file__), "..", "screenshots")
os.makedirs(screenshots_dir, exist_ok=True)
app.mount("/screenshots", StaticFiles(directory=screenshots_dir), name="screenshots")

project_files_dir = os.path.join(os.path.dirname(__file__), "..", "project-files")
os.makedirs(project_files_dir, exist_ok=True)
app.mount("/project-files", StaticFiles(directory=project_files_dir), name="project_files")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _serialize_keyword(keyword):
    return {
        "id": keyword.id,
        "text": keyword.text,
        "status": keyword.status,
        "updated_at": keyword.updated_at.isoformat() if keyword.updated_at else None,
    }


def _serialize_log(log):
    return {
        "id": log.id,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        "level": log.level,
        "message": log.message,
    }


def _serialize_business(item):
    return {
        "id": item.id,
        "keyword": item.keyword,
        "name": item.name,
        "rating": item.rating,
        "address": item.address,
        "phone": item.phone,
        "website": item.website,
        "category": item.category,
        "opening_hours": item.opening_hours,
        "google_maps_url": item.google_maps_url,
        "place_id": item.place_id,
        "scraped_at": item.scraped_at.isoformat() if item.scraped_at else None,
    }


def _normalize_keywords(lines):
    normalized = []
    seen = set()
    for line in lines:
        value = " ".join(str(line).split()).strip()
        if not value:
            continue
        if value.lower() in seen:
            continue
        seen.add(value.lower())
        normalized.append(value)
    return normalized


def _ingest_keywords(db: Session, keywords, mode: str):
    keywords = _normalize_keywords(keywords)
    if not keywords:
        raise HTTPException(status_code=400, detail="No valid keywords were provided")

    added = 0
    reset = 0

    if mode == "replace":
        db.query(models.Keyword).delete()
        db.bulk_insert_mappings(
            models.Keyword,
            [{"text": keyword, "status": models.KeywordStatus.PENDING.value} for keyword in keywords],
        )
        db.commit()
        return {
            "message": f"Replaced queue with {len(keywords)} keywords",
            "mode": mode,
            "added": len(keywords),
            "reset": 0,
            "total_in_file": len(keywords),
        }

    existing = {item.text: item for item in db.query(models.Keyword).all()}
    new_rows = []
    for keyword in keywords:
        if keyword in existing:
            if mode == "sync":
                existing[keyword].status = models.KeywordStatus.PENDING.value
                reset += 1
        else:
            new_rows.append({"text": keyword, "status": models.KeywordStatus.PENDING.value})

    if new_rows:
        db.bulk_insert_mappings(models.Keyword, new_rows)
        added = len(new_rows)
    db.commit()

    message = (
        f"Added {added} keywords"
        if mode == "add"
        else f"Synced keywords: added {added}, reset {reset}"
    )
    return {
        "message": message,
        "mode": mode,
        "added": added,
        "reset": reset,
        "total_in_file": len(keywords),
    }


def _extract_keywords_from_upload(filename: str, file_bytes: bytes):
    import pandas as pd

    lower_name = filename.lower()
    if lower_name.endswith(".csv"):
        dataframe = pd.read_csv(io.BytesIO(file_bytes))
        return dataframe.iloc[:, 0].tolist() if "keyword" not in dataframe.columns else dataframe["keyword"].tolist()
    if lower_name.endswith(".xlsx") or lower_name.endswith(".xls"):
        dataframe = pd.read_excel(io.BytesIO(file_bytes))
        return dataframe.iloc[:, 0].tolist() if "keyword" not in dataframe.columns else dataframe["keyword"].tolist()
    if lower_name.endswith(".txt"):
        return io.BytesIO(file_bytes).read().decode("utf-8").splitlines()
    raise HTTPException(status_code=400, detail="Supported formats: .csv, .xlsx, .xls, .txt")


@app.get("/")
def read_root():
    return {"message": "Maps Scraper API is running"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@app.get("/status")
def get_status():
    return scraper_manager.get_runtime_status()


@app.get("/metrics")
def get_metrics(response: Response):
    response.headers["Cache-Control"] = "no-store"
    return scraper_manager.get_runtime_status()["totals"]


@app.get("/dashboard/snapshot")
def get_dashboard_snapshot(db: Session = Depends(get_db)):
    runtime = scraper_manager.get_runtime_status()
    recent_logs = (
        db.query(models.LogEntry)
        .order_by(models.LogEntry.timestamp.desc())
        .limit(100)
        .all()
    )
    recent_keywords = (
        db.query(models.Keyword).order_by(models.Keyword.updated_at.desc()).limit(100).all()
    )
    return {
        **runtime,
        "logs": [_serialize_log(item) for item in reversed(recent_logs)],
        "keywords": [_serialize_keyword(item) for item in recent_keywords],
    }


@app.post("/control/{action}")
async def control_scraper(action: str):
    if action == "start":
        await scraper_manager.start_scraper()
    elif action == "pause":
        await scraper_manager.pause_scraper()
    elif action == "resume":
        await scraper_manager.resume_scraper()
    elif action == "stop":
        await scraper_manager.stop_scraper()
    else:
        raise HTTPException(status_code=400, detail="Invalid control action")
    return scraper_manager.get_runtime_status()


@app.post("/api/scrape")
async def api_scrape(request: schemas.KeywordBulkRequest | None = None, db: Session = Depends(get_db)):
    if request and request.keywords_text.strip():
        _ingest_keywords(db, request.keywords_text.splitlines(), request.mode)
    await scraper_manager.start_scraper()
    return scraper_manager.get_runtime_status()


@app.post("/admin/reset-all")
async def admin_reset_all(db: Session = Depends(get_db)):
    await scraper_manager.stop_scraper()

    cleared_keywords = db.query(models.Keyword).delete(synchronize_session=False)
    cleared_results = db.query(models.BusinessResult).delete(synchronize_session=False)
    (
        db.query(models.Keyword)
        .filter(models.Keyword.status != models.KeywordStatus.PENDING.value)
        .update({"status": models.KeywordStatus.PENDING.value}, synchronize_session=False)
    )
    db.commit()

    scraper_manager.reset_runtime_state()
    return {
        "message": "Stopped scraper, cleared queue and results, reset statuses, and restarted queue manager",
        "cleared_keywords": cleared_keywords,
        "cleared_results": cleared_results,
        "status": scraper_manager.get_runtime_status(),
    }


@app.get("/settings")
def get_settings():
    return config.load_config()


@app.put("/settings")
def update_settings(payload: schemas.SettingsPayload):
    return config.save_config(payload.model_dump())


@app.get("/config")
def config_alias_get():
    return get_settings()


@app.post("/config")
def config_alias_update(payload: dict):
    return config.save_config(payload)


@app.get("/keywords")
def get_keywords(
    response: Response,
    page: int = 1,
    limit: int = 100,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"
    page = max(page, 1)
    limit = max(1, min(limit, 500))

    query = db.query(models.Keyword)
    if status:
        query = query.filter(models.Keyword.status == status)

    total = query.count()
    items = (
        query.order_by(models.Keyword.updated_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "items": [_serialize_keyword(item) for item in items],
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": max(1, (total + limit - 1) // limit),
    }


@app.get("/keywords/progress")
def get_keywords_progress(
    page: int = 1,
    limit: int = 100,
    search: str = "",
    status: str | None = None,
):
    items = scraper_manager.get_runtime_status().get("keyword_progress", [])

    if search:
        search_lower = search.lower()
        items = [item for item in items if search_lower in item["keyword"].lower()]

    if status:
        items = [item for item in items if item["status"] == status]

    page = max(page, 1)
    limit = max(1, min(limit, 500))
    total = len(items)
    start = (page - 1) * limit
    end = start + limit

    return {
        "items": items[start:end],
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": max(1, (total + limit - 1) // limit),
    }


@app.post("/keywords/bulk")
def add_keywords_bulk(request: schemas.KeywordBulkRequest, db: Session = Depends(get_db)):
    result = _ingest_keywords(db, request.keywords_text.splitlines(), request.mode)
    return {
        **result,
        "total_keywords": db.query(models.Keyword).count(),
    }


@app.post("/keywords/upload")
async def upload_keywords(
    file: UploadFile = File(...),
    mode: str = Form("add"),
    db: Session = Depends(get_db),
):
    if mode not in {"add", "replace", "sync"}:
        raise HTTPException(status_code=400, detail="Mode must be add, replace, or sync")

    file_bytes = await file.read()
    file_hash = hashlib.md5(file_bytes).hexdigest()
    keywords = _extract_keywords_from_upload(file.filename or "upload", file_bytes)
    result = _ingest_keywords(db, keywords, mode)

    db.add(
        models.UploadHistory(
            filename=file.filename or "upload",
            file_hash=file_hash,
            file_size_bytes=len(file_bytes),
            keywords_count=result["total_in_file"],
            new_keywords=result["added"],
            mode=mode,
        )
    )
    db.commit()

    return {
        **result,
        "file_hash": file_hash,
        "total_keywords": db.query(models.Keyword).count(),
    }


@app.get("/keywords/upload-history")
def get_upload_history(limit: int = 10, db: Session = Depends(get_db)):
    items = (
        db.query(models.UploadHistory)
        .order_by(models.UploadHistory.upload_time.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": item.id,
            "filename": item.filename,
            "upload_time": item.upload_time.isoformat() if item.upload_time else None,
            "file_hash": item.file_hash,
            "file_size_bytes": item.file_size_bytes,
            "keywords_count": item.keywords_count,
            "new_keywords": item.new_keywords,
            "mode": item.mode,
        }
        for item in items
    ]


def _reset_keywords(db: Session, statuses):
    count = (
        db.query(models.Keyword)
        .filter(models.Keyword.status.in_(statuses))
        .update({"status": models.KeywordStatus.PENDING.value}, synchronize_session=False)
    )
    db.commit()
    return count


@app.post("/keywords/reset-failed")
def reset_failed_keywords(db: Session = Depends(get_db)):
    count = _reset_keywords(
        db,
        [models.KeywordStatus.FAILED.value, models.KeywordStatus.THROTTLED.value],
    )
    return {"message": f"Reset {count} failed keywords", "count": count}


@app.post("/keywords/reset-skipped")
def reset_skipped_keywords(db: Session = Depends(get_db)):
    count = _reset_keywords(db, [models.KeywordStatus.SKIPPED.value])
    return {"message": f"Reset {count} skipped keywords", "count": count}


@app.post("/keywords/reset-all")
def reset_all_keywords(db: Session = Depends(get_db)):
    count = _reset_keywords(
        db,
        [
            models.KeywordStatus.FAILED.value,
            models.KeywordStatus.PROCESSING.value,
            models.KeywordStatus.SKIPPED.value,
            models.KeywordStatus.THROTTLED.value,
        ],
    )
    return {"message": f"Reset {count} keywords to pending", "count": count}


@app.get("/logs")
def get_logs(limit: int = 100, db: Session = Depends(get_db)):
    items = (
        db.query(models.LogEntry)
        .order_by(models.LogEntry.timestamp.desc())
        .limit(min(max(limit, 1), 500))
        .all()
    )
    return [_serialize_log(item) for item in reversed(items)]


@app.get("/results")
def get_results(
    page: int = 1,
    limit: int = 100,
    search: str = "",
    keyword: str = "",
    category: str = "",
    min_rating: float | None = None,
    db: Session = Depends(get_db),
):
    page = max(page, 1)
    limit = max(1, min(limit, 500))

    query = db.query(models.BusinessResult)

    if keyword:
        query = query.filter(models.BusinessResult.keyword.ilike(f"%{keyword}%"))
    if category:
        query = query.filter(models.BusinessResult.category.ilike(f"%{category}%"))
    if min_rating is not None:
        query = query.filter(models.BusinessResult.rating >= min_rating)
    if search:
        match = f"%{search}%"
        query = query.filter(
            (models.BusinessResult.name.ilike(match))
            | (models.BusinessResult.address.ilike(match))
            | (models.BusinessResult.phone.ilike(match))
            | (models.BusinessResult.website.ilike(match))
            | (models.BusinessResult.category.ilike(match))
            | (models.BusinessResult.keyword.ilike(match))
        )

    total = query.count()
    items = (
        query.order_by(models.BusinessResult.scraped_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return {
        "items": [_serialize_business(item) for item in items],
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": max(1, (total + limit - 1) // limit),
    }


@app.get("/results/export")
def export_results_csv(
    search: str = "",
    keyword: str = "",
    category: str = "",
    min_rating: float | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.BusinessResult)

    if keyword:
        query = query.filter(models.BusinessResult.keyword.ilike(f"%{keyword}%"))
    if category:
        query = query.filter(models.BusinessResult.category.ilike(f"%{category}%"))
    if min_rating is not None:
        query = query.filter(models.BusinessResult.rating >= min_rating)
    if search:
        match = f"%{search}%"
        query = query.filter(
            (models.BusinessResult.name.ilike(match))
            | (models.BusinessResult.address.ilike(match))
            | (models.BusinessResult.phone.ilike(match))
            | (models.BusinessResult.website.ilike(match))
            | (models.BusinessResult.category.ilike(match))
            | (models.BusinessResult.keyword.ilike(match))
        )

    items = query.order_by(models.BusinessResult.scraped_at.desc()).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "name",
            "rating",
            "address",
            "phone",
            "website",
            "category",
            "keyword",
            "google_maps_url",
            "place_id",
            "scraped_at",
        ]
    )

    for item in items:
        writer.writerow(
            [
                item.name or "",
                item.rating if item.rating is not None else "",
                item.address or "",
                item.phone or "",
                item.website or "",
                item.category or "",
                item.keyword or "",
                item.google_maps_url or "",
                item.place_id or "",
                item.scraped_at.isoformat() if item.scraped_at else "",
            ]
        )

    csv_data = output.getvalue()
    output.close()

    filename = "results_export.csv"
    if keyword:
        safe_keyword = "_".join(keyword.strip().split())[:40]
        filename = f"results_{safe_keyword}.csv"

    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=csv_data, media_type="text/csv", headers=headers)


@app.get("/results/stats")
def get_results_stats(db: Session = Depends(get_db)):
    total = db.query(models.BusinessResult).count()
    latest = (
        db.query(models.BusinessResult)
        .order_by(models.BusinessResult.scraped_at.desc())
        .first()
    )
    saver_stats = scraper_manager.data_saver.get_stats() if scraper_manager.data_saver else None
    return {
        "total_results": total,
        "latest_result_at": latest.scraped_at.isoformat() if latest else None,
        "data_saver": saver_stats,
    }
