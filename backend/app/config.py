import json
import os
import threading
from copy import deepcopy


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
CONFIG_DIR = os.path.join(PROJECT_ROOT, "backend")
CONFIG_FILE = os.path.join(CONFIG_DIR, "control.json")
LOCK = threading.RLock()


def get_default_config():
    return {
        "max_results_per_keyword": 20,
        "delay_between_requests_ms": 1500,
        "parallel_workers": 1,
        "proxy_url": "",
        "headless": True,
        "auto_save": True,
        "google_sheets_enabled": False,
        "google_sheets_sheet_name": "MapsScraperResults",
        "api_endpoint": "http://localhost:8000",
        "max_retries": 3,
        "page_timeout_ms": 45000,
        "browser_executable_path": "",
        "scroll_depth_limit": 12,
        "stop_on_duplicate_results": True,
        "duplicate_stop_threshold": 5,
        "adaptive_delay_enabled": True,
        "adaptive_delay_max_ms": 8000,
    }


def _ensure_config_file():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as handle:
            json.dump(get_default_config(), handle, indent=2)


def load_config():
    with LOCK:
        _ensure_config_file()
        defaults = get_default_config()
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as handle:
                user_config = json.load(handle)
        except (OSError, json.JSONDecodeError):
            user_config = {}
        merged = deepcopy(defaults)
        merged.update(user_config or {})
        return merged


def save_config(settings):
    with LOCK:
        current = load_config()
        current.update(settings)
        with open(CONFIG_FILE, "w", encoding="utf-8") as handle:
            json.dump(current, handle, indent=2)
        return current


def update_config(key, value):
    return save_config({key: value})


def get_value(key, default=None):
    return load_config().get(key, default)
