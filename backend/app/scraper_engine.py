import asyncio
import random
import re
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import quote

from .browser_pool import browser_pool


RATING_REGEX = re.compile(r"([0-9]+(?:\.[0-9]+)?)")
PLACE_ID_REGEX = re.compile(r"!1s([^!]+)!")


def _normalize_maps_url(url: str) -> str:
    if not url:
        return url
    return url.split("&authuser=")[0].split("?hl=")[0].rstrip("/")


def _extract_place_id(url: str) -> Optional[str]:
    if not url:
        return None
    match = PLACE_ID_REGEX.search(url)
    return match.group(1) if match else None


class ScraperEngine:
    def _classify_failure_reason(self, message: str) -> str:
        text = (message or "").lower()
        if "captcha" in text or "unusual traffic" in text:
            return "Blocked by Google"
        if "throttle" in text or "rate limit" in text or "too many requests" in text:
            return "Rate limited"
        if "no business urls" in text or "empty results" in text:
            return "No results found"
        if "timeout" in text:
            return "Timeout"
        return "Unknown scraping error"

    async def scrape_keyword(self, keyword: str, settings: dict, runtime) -> Dict:
        max_retries = settings.get("max_retries", 3)
        last_error = None
        current_delay_ms = int(settings.get("delay_between_requests_ms", 1500))
        adaptive_enabled = bool(settings.get("adaptive_delay_enabled", True))
        adaptive_max_ms = int(settings.get("adaptive_delay_max_ms", 8000))

        for attempt in range(1, max_retries + 1):
            if runtime.should_stop():
                return {"status": "pending", "saved": 0, "duplicates": 0}

            context = page = None
            try:
                runtime.log(f"[{keyword}] launch attempt {attempt}/{max_retries}")
                context, page = await browser_pool.get_context(settings)
                result = await self._run_keyword(
                    keyword,
                    settings,
                    runtime,
                    page,
                    context,
                    current_delay_ms,
                )
                result["attempts"] = attempt
                return result
            except Exception as exc:
                last_error = str(exc)
                reason = self._classify_failure_reason(last_error)
                runtime.log(
                    f"[{keyword}] attempt {attempt} failed: {reason} ({last_error})",
                    level="WARNING",
                )
                await browser_pool.restart(settings)
                if adaptive_enabled and reason in {"Blocked by Google", "Rate limited"}:
                    current_delay_ms = min(int(current_delay_ms * 1.5), adaptive_max_ms)
                    runtime.log(
                        f"[{keyword}] adaptive delay increased to {current_delay_ms}ms",
                        level="WARNING",
                    )
                await asyncio.sleep(min(3 * attempt, 8))
            finally:
                if context or page:
                    await browser_pool.release_context(context, page)

        return {
            "status": "failed",
            "saved": 0,
            "duplicates": 0,
            "error": self._classify_failure_reason(last_error or "Unknown scraping error"),
        }

    async def _run_keyword(self, keyword: str, settings: dict, runtime, page, context, delay_ms: int):
        timeout_ms = settings.get("page_timeout_ms", 45000)
        max_results = settings.get("max_results_per_keyword", 20)
        scroll_depth_limit = int(settings.get("scroll_depth_limit", 12))
        stop_on_duplicate = bool(settings.get("stop_on_duplicate_results", True))
        duplicate_stop_threshold = int(settings.get("duplicate_stop_threshold", 5))

        search_url = f"https://www.google.com/maps/search/{quote(keyword)}?hl=en"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=timeout_ms)
        await self._handle_consent(page)
        await self._wait_for_results_ready(page, timeout_ms)
        await self._assert_not_blocked(page)

        urls = await self._collect_result_urls(
            page=page,
            max_results=max_results,
            runtime=runtime,
            scroll_depth_limit=scroll_depth_limit,
        )
        if not urls and "/maps/place/" in page.url:
            urls = [_normalize_maps_url(page.url)]

        if not urls:
            raise RuntimeError("Empty results")

        saved = 0
        duplicates = 0
        duplicate_streak = 0

        for position, url in enumerate(urls[:max_results], start=1):
            await runtime.wait_if_paused()
            if runtime.should_stop():
                return {"status": "pending", "saved": saved, "duplicates": duplicates}

            detail_page = await context.new_page()
            try:
                business = await self._extract_business(
                    detail_page=detail_page,
                    url=url,
                    keyword=keyword,
                    timeout_ms=timeout_ms,
                )
                if not business:
                    runtime.log(
                        f"[{keyword}] skipped empty profile for result {position}",
                        level="WARNING",
                    )
                    continue

                outcome = runtime.save_business(business)
                if outcome == "saved":
                    saved += 1
                    duplicate_streak = 0
                    runtime.log(
                        f"[{keyword}] saved {business['name']}",
                        level="INFO",
                    )
                elif outcome == "duplicate":
                    duplicates += 1
                    duplicate_streak += 1
                    runtime.log(
                        f"[{keyword}] duplicate skipped {business['name']}",
                        level="DEBUG",
                    )
                    if stop_on_duplicate and duplicate_streak >= duplicate_stop_threshold:
                        runtime.log(
                            f"[{keyword}] duplicate threshold reached; stopping keyword early",
                            level="WARNING",
                        )
                        break
            finally:
                await detail_page.close()

            await asyncio.sleep(
                max(0, delay_ms / 1000) + random.uniform(0.25, 1.1)
            )

        return {"status": "done", "saved": saved, "duplicates": duplicates}

    async def _handle_consent(self, page):
        consent_selectors = [
            'button:has-text("Accept all")',
            'button[aria-label="Accept all"]',
            'button:has-text("I agree")',
        ]
        for selector in consent_selectors:
            try:
                locator = page.locator(selector)
                if await locator.count():
                    await locator.first.click(timeout=3000)
                    await page.wait_for_timeout(1000)
                    return
            except Exception:
                continue

    async def _wait_for_results_ready(self, page, timeout_ms: int):
        selectors = [
            'div[role="feed"]',
            'a[href*="/maps/place/"]',
            "h1.DUwDvf",
            "h1",
        ]
        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=timeout_ms // 2)
                return
            except Exception:
                continue
        raise RuntimeError("Google Maps results did not load")

    async def _assert_not_blocked(self, page):
        page_text = (await page.content()).lower()
        blocked_markers = [
            "unusual traffic",
            "sorry, but you have been sending automated queries",
            "captcha",
        ]
        if any(marker in page_text for marker in blocked_markers):
            raise RuntimeError("Google Maps throttled or blocked the scraper")

    async def _collect_result_urls(self, page, max_results: int, runtime, scroll_depth_limit: int) -> List[str]:
        seen = []
        stalled_rounds = 0
        previous_count = 0
        scroll_rounds = 0

        while len(seen) < max_results and stalled_rounds < 4 and scroll_rounds < max(1, scroll_depth_limit):
            urls = await page.locator('a[href*="/maps/place/"]').evaluate_all(
                """
                anchors => anchors
                  .map(anchor => anchor.href)
                  .filter(Boolean)
                """
            )
            cleaned = []
            for url in urls:
                normalized = _normalize_maps_url(url)
                if "/maps/place/" not in normalized:
                    continue
                if normalized not in cleaned:
                    cleaned.append(normalized)

            for url in cleaned:
                if url not in seen:
                    seen.append(url)

            if len(seen) == previous_count:
                stalled_rounds += 1
            else:
                stalled_rounds = 0
            previous_count = len(seen)

            if len(seen) >= max_results:
                break

            feed = page.locator('div[role="feed"]')
            if await feed.count():
                await feed.evaluate(
                    "(element) => { element.scrollTop = element.scrollHeight; }"
                )
                scroll_rounds += 1
                await page.wait_for_timeout(1500 + random.randint(200, 900))
                runtime.log(
                    f"Collected {len(seen)} URLs so far for active keyword (scroll {scroll_rounds}/{max(1, scroll_depth_limit)})",
                    level="DEBUG",
                )
            else:
                break

        return seen[:max_results]

    async def _extract_business(self, detail_page, url: str, keyword: str, timeout_ms: int):
        await detail_page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        await self._wait_for_results_ready(detail_page, timeout_ms)
        await detail_page.wait_for_timeout(1200)

        name = await self._get_first_text(
            detail_page,
            [
                "h1.DUwDvf",
                "h1",
            ],
        )
        if not name or name in {"Google Maps", "Maps"}:
            return None

        rating_text = await self._get_first_attribute(
            detail_page,
            [
                'div.F7nice span[role="img"]',
                'span[role="img"][aria-label*="stars"]',
                'div[role="img"][aria-label*="stars"]',
            ],
            "aria-label",
        )
        rating = None
        if rating_text:
            match = RATING_REGEX.search(rating_text)
            if match:
                rating = float(match.group(1))

        address = await self._extract_label_value(
            detail_page,
            selectors=[
                'button[data-item-id="address"]',
                'button[aria-label^="Address:"]',
            ],
            prefixes=["Address: "],
        )
        phone = await self._extract_label_value(
            detail_page,
            selectors=[
                'button[data-item-id^="phone"]',
                'button[aria-label^="Phone:"]',
            ],
            prefixes=["Phone: ", "Call "],
        )
        website = await self._get_first_attribute(
            detail_page,
            [
                'a[data-item-id="authority"]',
                'a[aria-label^="Website:"]',
            ],
            "href",
        )
        category = await self._get_first_text(
            detail_page,
            [
                'button[jsaction*="pane.rating.category"]',
                "button.DkEaL",
                "div.DkEaL",
            ],
        )
        opening_hours = await self._extract_opening_hours(detail_page)

        return {
            "keyword": keyword,
            "name": name,
            "rating": rating,
            "address": address,
            "phone": phone,
            "website": website,
            "category": category,
            "opening_hours": opening_hours,
            "google_maps_url": _normalize_maps_url(detail_page.url),
            "place_id": _extract_place_id(detail_page.url),
            "scraped_at": datetime.utcnow().isoformat(),
        }

    async def _get_first_text(self, page, selectors: List[str]) -> Optional[str]:
        for selector in selectors:
            try:
                locator = page.locator(selector)
                if not await locator.count():
                    continue
                text = (await locator.first.inner_text(timeout=2000)).strip()
                if text:
                    return " ".join(text.split())
            except Exception:
                continue
        return None

    async def _get_first_attribute(
        self, page, selectors: List[str], attribute: str
    ) -> Optional[str]:
        for selector in selectors:
            try:
                locator = page.locator(selector)
                if not await locator.count():
                    continue
                value = await locator.first.get_attribute(attribute, timeout=2000)
                if value:
                    return value.strip()
            except Exception:
                continue
        return None

    async def _extract_label_value(
        self, page, selectors: List[str], prefixes: List[str]
    ) -> Optional[str]:
        for selector in selectors:
            try:
                locator = page.locator(selector)
                if not await locator.count():
                    continue
                for attribute in ["aria-label", "data-tooltip", "title"]:
                    value = await locator.first.get_attribute(attribute)
                    if value:
                        cleaned = value.strip()
                        for prefix in prefixes:
                            if cleaned.startswith(prefix):
                                cleaned = cleaned[len(prefix) :]
                        if cleaned:
                            return " ".join(cleaned.split())

                text = (await locator.first.inner_text(timeout=2000)).strip()
                if text:
                    return " ".join(text.split())
            except Exception:
                continue
        return None

    async def _extract_opening_hours(self, page) -> Optional[str]:
        summary = await self._extract_label_value(
            page,
            selectors=[
                'button[data-item-id="oh"]',
                "div.OqCZI",
                "div.t39EBf",
                'div[aria-label*="Hours"]',
                'div[aria-label*="Open"]',
            ],
            prefixes=["Hours: "],
        )
        if summary:
            cleaned_summary = summary.replace("Suggest new hours", "").strip()
            if cleaned_summary:
                summary = cleaned_summary
        if summary and "Open" in summary:
            return summary

        try:
            rows = await page.locator("table.eK4R0e tr").all()
            values = []
            for row in rows:
                text = " ".join((await row.inner_text()).split())
                if text:
                    values.append(text)
            if values:
                return " | ".join(values)
        except Exception:
            pass

        return summary


scraper_instance = ScraperEngine()
