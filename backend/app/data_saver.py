import csv
import logging
import os
import threading
from datetime import datetime
from typing import Dict

from . import database, models
from .config import load_config
from .google_sheets import GoogleSheetsManager, SHEET_COLUMNS


logger = logging.getLogger(__name__)


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
STORAGE_DIR = os.path.join(PROJECT_ROOT, "storage")


class DataSaver:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.lock = threading.Lock()
        self.saved_count = 0
        self.duplicate_count = 0
        self.csv_path = os.path.join(STORAGE_DIR, f"results_{run_id}.csv")
        os.makedirs(STORAGE_DIR, exist_ok=True)
        self.sheets_manager = self._build_sheets_manager()

    def _build_sheets_manager(self):
        settings = load_config()
        if not settings.get("google_sheets_enabled"):
            return None

        credentials_candidates = [
            os.path.join(PROJECT_ROOT, "backend", "credentials", "service_account.json"),
            os.path.join(PROJECT_ROOT, "credentials", "service_account.json"),
            os.path.join(PROJECT_ROOT, "service_account.json"),
        ]
        credentials_path = next(
            (path for path in credentials_candidates if os.path.exists(path)),
            "",
        )
        if not credentials_path:
            logger.warning("Google Sheets enabled but credentials file was not found.")
            return None

        return GoogleSheetsManager(
            credentials_path=credentials_path,
            sheet_name=settings.get("google_sheets_sheet_name", "MapsScraperResults"),
        )

    def save_business(self, business: Dict) -> str:
        with self.lock:
            db = database.SessionLocal()
            try:
                normalized_url = business["google_maps_url"]
                place_id = business.get("place_id")

                existing = (
                    db.query(models.BusinessResult)
                    .filter(models.BusinessResult.google_maps_url == normalized_url)
                    .first()
                )
                if not existing and place_id:
                    existing = (
                        db.query(models.BusinessResult)
                        .filter(models.BusinessResult.place_id == place_id)
                        .first()
                    )

                if existing:
                    self.duplicate_count += 1
                    return "duplicate"

                record = models.BusinessResult(
                    keyword=business["keyword"],
                    name=business["name"],
                    rating=business.get("rating"),
                    address=business.get("address"),
                    phone=business.get("phone"),
                    website=business.get("website"),
                    category=business.get("category"),
                    opening_hours=business.get("opening_hours"),
                    google_maps_url=normalized_url,
                    place_id=place_id,
                    scraped_at=datetime.utcnow(),
                )
                db.add(record)
                db.commit()

                row = {
                    "keyword": business["keyword"],
                    "name": business["name"],
                    "rating": business.get("rating") or "",
                    "address": business.get("address") or "",
                    "phone": business.get("phone") or "",
                    "website": business.get("website") or "",
                    "category": business.get("category") or "",
                    "opening_hours": business.get("opening_hours") or "",
                    "google_maps_url": normalized_url,
                    "place_id": place_id or "",
                    "scraped_at": datetime.utcnow().isoformat(),
                }

                if load_config().get("auto_save", True):
                    self._append_to_csv(row)

                if self.sheets_manager and self.sheets_manager.is_connected:
                    self.sheets_manager.append_row(row)

                self.saved_count += 1
                return "saved"
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

    def _append_to_csv(self, row: Dict):
        file_exists = os.path.exists(self.csv_path)
        with open(self.csv_path, "a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=SHEET_COLUMNS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

    def get_stats(self):
        return {
            "run_id": self.run_id,
            "saved_count": self.saved_count,
            "duplicate_count": self.duplicate_count,
            "csv_path": self.csv_path,
            "google_sheets_connected": bool(
                self.sheets_manager and self.sheets_manager.is_connected
            ),
            "google_sheets_url": self.sheets_manager.get_sheet_url()
            if self.sheets_manager
            else None,
        }
