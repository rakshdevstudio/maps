import asyncio
import logging
import os
import random
import shutil
from urllib.parse import urlparse


logger = logging.getLogger(__name__)


def _parse_proxy(proxy_url: str):
    if not proxy_url:
        return None
    parsed = urlparse(proxy_url)
    if not parsed.scheme or not parsed.hostname:
        return None
    proxy = {"server": f"{parsed.scheme}://{parsed.hostname}"}
    if parsed.port:
        proxy["server"] = f"{proxy['server']}:{parsed.port}"
    if parsed.username:
        proxy["username"] = parsed.username
    if parsed.password:
        proxy["password"] = parsed.password
    return proxy


class AsyncBrowserPool:
    def __init__(self):
        self._lock = asyncio.Lock()
        self.playwright = None
        self.browser = None
        self._launch_signature = None
        self._launch_target = None

    async def get_context(self, settings: dict):
        await self.ensure_browser(settings)
        viewport = random.choice(
            [
                {"width": 1280, "height": 900},
                {"width": 1366, "height": 768},
                {"width": 1440, "height": 900},
            ]
        )
        context = await self.browser.new_context(
            viewport=viewport,
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="Asia/Kolkata",
            ignore_https_errors=True,
        )
        page = await context.new_page()
        return context, page

    async def ensure_browser(self, settings: dict):
        signature = (
            settings.get("headless"),
            settings.get("proxy_url"),
            settings.get("browser_executable_path"),
        )
        async with self._lock:
            if self.browser and self._launch_signature == signature:
                return

            await self.shutdown()
            from playwright.async_api import async_playwright

            self.playwright = await async_playwright().start()
            self.browser, self._launch_target = await self._launch_browser(settings)
            self._launch_signature = signature
            logger.info("Browser ready using target: %s", self._launch_target)

    async def _launch_browser(self, settings: dict):
        browser_type = self.playwright.chromium
        headless = settings.get("headless", True)
        proxy = _parse_proxy(settings.get("proxy_url", ""))

        launch_args = {
            "headless": headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-renderer-backgrounding",
                "--disable-features=IsolateOrigins,site-per-process,AutomationControlled",
                "--no-sandbox",
            ],
        }
        if proxy:
            launch_args["proxy"] = proxy

        attempted = []

        async def try_launch(label, **kwargs):
            attempted.append(label)
            try:
                browser = await browser_type.launch(**launch_args, **kwargs)
                return browser, label
            except Exception as exc:
                logger.warning("Browser launch attempt '%s' failed: %s", label, exc)
                return None, None

        configured_path = settings.get("browser_executable_path", "").strip()
        if configured_path:
            browser, label = await try_launch(
                f"configured:{configured_path}",
                executable_path=configured_path,
            )
            if browser:
                return browser, label

        browser, label = await try_launch("playwright-bundled")
        if browser:
            return browser, label

        executable_candidates = [
            shutil.which("google-chrome"),
            shutil.which("chromium"),
            shutil.which("chromium-browser"),
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ]
        for executable_path in executable_candidates:
            if not executable_path or not os.path.exists(executable_path):
                continue
            browser, label = await try_launch(
                f"system:{executable_path}",
                executable_path=executable_path,
            )
            if browser:
                return browser, label

        raise RuntimeError(
            "Could not launch Chromium. Tried: " + ", ".join(attempted or ["none"])
        )

    async def restart(self, settings: dict):
        await self.shutdown()
        await self.ensure_browser(settings)

    async def release_context(self, context, page):
        try:
            if page and not page.is_closed():
                await page.close()
        except Exception:
            pass
        try:
            if context:
                await context.close()
        except Exception:
            pass

    async def shutdown(self):
        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
            self.browser = None
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception:
                pass
            self.playwright = None
        self._launch_signature = None
        self._launch_target = None


browser_pool = AsyncBrowserPool()
