import logging
import os
import time
from typing import Dict, Optional

import gspread
from google.oauth2.service_account import Credentials


logger = logging.getLogger(__name__)


SHEET_COLUMNS = [
    "keyword",
    "name",
    "rating",
    "address",
    "phone",
    "website",
    "category",
    "opening_hours",
    "google_maps_url",
    "place_id",
    "scraped_at",
]


class GoogleSheetsManager:
    def __init__(self, credentials_path: str, sheet_name: str):
        self.credentials_path = credentials_path
        self.sheet_name = sheet_name
        self.client = None
        self.sheet = None
        self.worksheet = None
        self.is_connected = False
        self._connect()

    def _connect(self):
        if not self.credentials_path or not os.path.exists(self.credentials_path):
            logger.warning("Google Sheets credentials not found at %s", self.credentials_path)
            self.is_connected = False
            return

        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=scopes,
            )
            self.client = gspread.authorize(creds)

            try:
                self.sheet = self.client.open(self.sheet_name)
            except gspread.SpreadsheetNotFound:
                self.sheet = self.client.create(self.sheet_name)

            self.worksheet = self.sheet.sheet1
            self._ensure_headers()
            self.is_connected = True
            logger.info("Google Sheets connected: %s", self.sheet_name)
        except Exception as exc:
            logger.error("Failed to initialize Google Sheets: %s", exc)
            self.is_connected = False

    def _ensure_headers(self):
        if not self.worksheet:
            return
        try:
            headers = self.worksheet.row_values(1)
            if headers != SHEET_COLUMNS:
                if not headers or headers == [""]:
                    self.worksheet.update("A1:K1", [SHEET_COLUMNS])
        except Exception as exc:
            logger.warning("Could not verify Google Sheets headers: %s", exc)

    def append_row(self, row: Dict, retry_count: int = 3) -> bool:
        if not self.is_connected or not self.worksheet:
            return False

        values = [row.get(column, "") for column in SHEET_COLUMNS]
        for attempt in range(retry_count):
            try:
                self.worksheet.append_row(values, value_input_option="RAW")
                return True
            except Exception as exc:
                if attempt == retry_count - 1:
                    logger.error("Google Sheets append failed: %s", exc)
                    return False
                time.sleep(2**attempt)
        return False

    def get_sheet_url(self) -> Optional[str]:
        if self.sheet:
            return self.sheet.url
        return None
