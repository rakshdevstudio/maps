import asyncio
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import func

from . import config, database, models
from .data_saver import DataSaver
from .scraper_engine import scraper_instance


logger = logging.getLogger(__name__)


class ScraperManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.scraper_task = None
            cls._instance.stop_event = asyncio.Event()
            cls._instance.pause_event = asyncio.Event()
            cls._instance.pause_event.set()
            cls._instance.claim_lock = asyncio.Lock()
            cls._instance.active_workers = 0
            cls._instance.current_keyword = None
            cls._instance.last_error = None
            cls._instance.started_at = None
            cls._instance.data_saver = None
            cls._instance.run_id = None
            cls._instance.keyword_started_at = {}
            cls._instance.keyword_saved_count = {}
        return cls._instance

    def _get_db(self):
        return database.SessionLocal()

    def _ensure_job(self, db):
        job = db.query(models.Job).filter(models.Job.id == 1).first()
        if not job:
            job = models.Job(id=1)
            db.add(job)
            db.commit()
            db.refresh(job)
        return job

    def log(self, message: str, level: str = "INFO"):
        level = level.upper()
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)

        db = self._get_db()
        try:
            db.add(models.LogEntry(level=level, message=message))
            db.commit()
        finally:
            db.close()

    def save_business(self, business):
        if not self.data_saver:
            raise RuntimeError("DataSaver is not initialized")
        return self.data_saver.save_business(business)

    def should_stop(self) -> bool:
        return self.stop_event.is_set()

    async def wait_if_paused(self):
        await self.pause_event.wait()

    async def start_scraper(self):
        if self.scraper_task and not self.scraper_task.done():
            return

        self.stop_event = asyncio.Event()
        self.pause_event = asyncio.Event()
        self.pause_event.set()
        self.active_workers = 0
        self.current_keyword = None
        self.last_error = None
        self.started_at = datetime.utcnow()
        self.run_id = self.started_at.strftime("%Y%m%d_%H%M%S")
        self.data_saver = DataSaver(self.run_id)
        self.keyword_started_at = {}
        self.keyword_saved_count = {}

        db = self._get_db()
        try:
            self._recover_processing_keywords(db)
            job = self._ensure_job(db)
            job.status = models.JobStatus.RUNNING.value
            job.start_time = self.started_at
            job.end_time = None
            job.current_keyword = None
            job.total_keywords = db.query(models.Keyword).count()
            job.completed_keywords = db.query(models.Keyword).filter(
                models.Keyword.status == models.KeywordStatus.DONE.value
            ).count()
            db.commit()
        finally:
            db.close()

        self.log("Starting scraper queue")
        self.scraper_task = asyncio.create_task(self._run())

    async def _run(self):
        settings = config.load_config()
        worker_count = max(1, settings.get("parallel_workers", 1))
        workers = [asyncio.create_task(self._worker(index)) for index in range(worker_count)]

        try:
            await asyncio.gather(*workers)
            final_status = (
                models.JobStatus.STOPPED.value
                if self.stop_event.is_set()
                else models.JobStatus.COMPLETED.value
            )
            self._update_job(final_status)
            self.log(f"Scraper queue finished with status={final_status}")
        except asyncio.CancelledError:
            self._update_job(models.JobStatus.STOPPED.value)
            self.log("Scraper queue cancelled", level="WARNING")
            raise
        except Exception as exc:
            self.last_error = str(exc)
            self._update_job(models.JobStatus.ERROR.value)
            self.log(f"Scraper queue crashed: {self.last_error}", level="ERROR")
        finally:
            self.active_workers = 0
            self.current_keyword = None

    async def _worker(self, worker_index: int):
        self.log(f"Worker {worker_index + 1} ready", level="DEBUG")
        while not self.stop_event.is_set():
            await self.wait_if_paused()
            claim = await self._claim_next_keyword()
            if not claim:
                return

            keyword_id, keyword_text = claim
            self.current_keyword = keyword_text
            self.active_workers += 1
            self.keyword_started_at[keyword_id] = datetime.utcnow()
            self.log(f"Worker {worker_index + 1} processing '{keyword_text}'")

            try:
                result = await scraper_instance.scrape_keyword(keyword_text, config.load_config(), self)
                await self._finish_keyword(keyword_id, keyword_text, result)
            except Exception as exc:
                await self._finish_keyword(
                    keyword_id,
                    keyword_text,
                    {"status": "failed", "error": str(exc), "saved": 0, "duplicates": 0},
                )
            finally:
                self.active_workers = max(0, self.active_workers - 1)
                self.current_keyword = None

    async def _claim_next_keyword(self) -> Optional[tuple]:
        async with self.claim_lock:
            db = self._get_db()
            try:
                keyword = (
                    db.query(models.Keyword)
                    .filter(models.Keyword.status == models.KeywordStatus.PENDING.value)
                    .order_by(models.Keyword.id.asc())
                    .first()
                )
                if not keyword:
                    return None

                keyword.status = models.KeywordStatus.PROCESSING.value
                db.commit()

                job = self._ensure_job(db)
                job.status = (
                    models.JobStatus.PAUSED.value
                    if not self.pause_event.is_set()
                    else models.JobStatus.RUNNING.value
                )
                job.current_keyword = keyword.text
                db.commit()
                return keyword.id, keyword.text
            finally:
                db.close()

    async def _finish_keyword(self, keyword_id: int, keyword_text: str, result: dict):
        db = self._get_db()
        try:
            keyword = db.query(models.Keyword).filter(models.Keyword.id == keyword_id).first()
            if not keyword:
                return

            status = result.get("status", "failed")
            self.keyword_saved_count[keyword_id] = int(result.get("saved", 0) or 0)
            if status == "done":
                keyword.status = models.KeywordStatus.DONE.value
                self.log(
                    f"Keyword complete '{keyword_text}' saved={result.get('saved', 0)} duplicates={result.get('duplicates', 0)}"
                )
            elif status == "pending":
                keyword.status = models.KeywordStatus.PENDING.value
                self.log(f"Keyword paused for resume '{keyword_text}'", level="WARNING")
            elif "throttle" in result.get("error", "").lower():
                keyword.status = models.KeywordStatus.THROTTLED.value
                self.log(f"Keyword throttled '{keyword_text}'", level="WARNING")
            else:
                keyword.status = models.KeywordStatus.FAILED.value
                self.last_error = result.get("error")
                self.log(
                    f"Keyword failed '{keyword_text}': {result.get('error', 'unknown error')}",
                    level="ERROR",
                )

            job = self._ensure_job(db)
            job.total_keywords = db.query(models.Keyword).count()
            job.completed_keywords = db.query(models.Keyword).filter(
                models.Keyword.status == models.KeywordStatus.DONE.value
            ).count()
            job.current_keyword = None
            if not self.stop_event.is_set() and self.pause_event.is_set():
                job.status = models.JobStatus.RUNNING.value
            elif not self.pause_event.is_set():
                job.status = models.JobStatus.PAUSED.value
            else:
                job.status = models.JobStatus.STOPPED.value
            db.commit()
        finally:
            db.close()

    async def pause_scraper(self):
        if not self.scraper_task or self.scraper_task.done():
            return
        self.pause_event.clear()
        self._update_job(models.JobStatus.PAUSED.value)
        self.log("Scraper paused")

    async def resume_scraper(self):
        if not self.scraper_task or self.scraper_task.done():
            await self.start_scraper()
            return
        self.pause_event.set()
        self._update_job(models.JobStatus.RUNNING.value)
        self.log("Scraper resumed")

    async def stop_scraper(self):
        self.stop_event.set()
        self.pause_event.set()
        self._update_job(models.JobStatus.STOPPED.value)
        self.log("Stop requested")
        if self.scraper_task and not self.scraper_task.done():
            await self.scraper_task

    def reset_runtime_state(self):
        # Reinitialize manager state without starting a new scrape run.
        self.scraper_task = None
        self.stop_event = asyncio.Event()
        self.pause_event = asyncio.Event()
        self.pause_event.set()
        self.active_workers = 0
        self.current_keyword = None
        self.last_error = None
        self.started_at = None
        self.data_saver = None
        self.run_id = None
        self.keyword_started_at = {}
        self.keyword_saved_count = {}
        self._update_job(models.JobStatus.IDLE.value)
        self.log("Queue manager reset")

    def _build_keyword_progress(self, db, limit: int = 200):
        rows = (
            db.query(models.Keyword)
            .order_by(models.Keyword.updated_at.desc(), models.Keyword.id.desc())
            .limit(limit)
            .all()
        )

        grouped_counts = {
            key: count
            for key, count in (
                db.query(models.BusinessResult.keyword, func.count(models.BusinessResult.id))
                .group_by(models.BusinessResult.keyword)
                .all()
            )
        }

        settings = config.load_config()
        max_results = max(1, int(settings.get("max_results_per_keyword", 20)))
        elapsed_minutes = 0.0
        if self.started_at:
            elapsed_minutes = max(
                (datetime.utcnow() - self.started_at).total_seconds() / 60,
                0.0,
            )

        total_results = db.query(models.BusinessResult).count()
        speed_per_min = (total_results / elapsed_minutes) if elapsed_minutes > 0 else 0.0

        progress = []
        for row in rows:
            scraped_count = int(grouped_counts.get(row.text, 0) or 0)
            started_at = self.keyword_started_at.get(row.id)
            started_iso = started_at.isoformat() if started_at else None

            eta_seconds = None
            if row.status == models.KeywordStatus.PROCESSING.value and speed_per_min > 0:
                remaining = max(max_results - scraped_count, 0)
                eta_seconds = int((remaining / speed_per_min) * 60)

            progress.append(
                {
                    "id": row.id,
                    "keyword": row.text,
                    "status": row.status,
                    "businesses_scraped": scraped_count,
                    "progress_percent": min(int((scraped_count / max_results) * 100), 100),
                    "started_at": started_iso,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                    "estimated_completion_seconds": eta_seconds,
                }
            )

        return progress

    def _recover_processing_keywords(self, db):
        (
            db.query(models.Keyword)
            .filter(models.Keyword.status == models.KeywordStatus.PROCESSING.value)
            .update({"status": models.KeywordStatus.PENDING.value}, synchronize_session=False)
        )
        db.commit()

    def _update_job(self, status: str):
        db = self._get_db()
        try:
            job = self._ensure_job(db)
            job.status = status
            if status in {models.JobStatus.COMPLETED.value, models.JobStatus.STOPPED.value, models.JobStatus.ERROR.value}:
                job.end_time = datetime.utcnow()
            job.current_keyword = self.current_keyword
            job.total_keywords = db.query(models.Keyword).count()
            job.completed_keywords = db.query(models.Keyword).filter(
                models.Keyword.status == models.KeywordStatus.DONE.value
            ).count()
            db.commit()
        finally:
            db.close()

    def get_runtime_status(self):
        db = self._get_db()
        try:
            job = self._ensure_job(db)
            total_keywords = db.query(models.Keyword).count()
            done_keywords = (
                db.query(models.Keyword)
                .filter(models.Keyword.status == models.KeywordStatus.DONE.value)
                .count()
            )
            failed_keywords = (
                db.query(models.Keyword)
                .filter(models.Keyword.status == models.KeywordStatus.FAILED.value)
                .count()
            )
            total_results = db.query(models.BusinessResult).count()

            elapsed_minutes = 0.0
            if self.started_at:
                elapsed_minutes = max(
                    (datetime.utcnow() - self.started_at).total_seconds() / 60,
                    0.0,
                )
            speed_per_min = (total_results / elapsed_minutes) if elapsed_minutes > 0 else 0.0
            success_rate = (done_keywords / total_keywords * 100) if total_keywords else 0.0

            totals = {
                "total": total_keywords,
                "done": done_keywords,
                "pending": db.query(models.Keyword)
                .filter(models.Keyword.status == models.KeywordStatus.PENDING.value)
                .count(),
                "processing": db.query(models.Keyword)
                .filter(models.Keyword.status == models.KeywordStatus.PROCESSING.value)
                .count(),
                "failed": failed_keywords,
                "skipped": db.query(models.Keyword)
                .filter(models.Keyword.status == models.KeywordStatus.SKIPPED.value)
                .count(),
                "throttled": db.query(models.Keyword)
                .filter(models.Keyword.status == models.KeywordStatus.THROTTLED.value)
                .count(),
                "results": total_results,
                "results_per_min": round(speed_per_min, 2),
                "success_rate": round(success_rate, 2),
            }
            return {
                "status": job.status,
                "current_keyword": self.current_keyword or job.current_keyword,
                "active_workers": self.active_workers,
                "run_id": self.run_id,
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "last_error": self.last_error,
                "totals": totals,
                "keyword_progress": self._build_keyword_progress(db),
                "data_saver": self.data_saver.get_stats() if self.data_saver else None,
            }
        finally:
            db.close()


scraper_manager = ScraperManager()
