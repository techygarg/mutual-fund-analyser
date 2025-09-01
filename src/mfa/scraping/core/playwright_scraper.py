from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from loguru import logger
from playwright.sync_api import TimeoutError as PwTimeoutError
from playwright.sync_api import sync_playwright


class PlaywrightSession:
    def __init__(
        self,
        headless: bool = True,
        nav_timeout_ms: int = 30000,
        viewport: dict[str, int] | None = None,
    ) -> None:
        self._headless = headless
        self._timeout = nav_timeout_ms
        self._viewport = viewport or {"width": 1440, "height": 2200}
        self._p = None
        self._browser = None
        self._context = None
        self._page = None

    def open(self) -> None:
        if self._p is not None:
            return
        self._p = sync_playwright().start()
        self._browser = self._p.chromium.launch(headless=self._headless)
        self._context = self._browser.new_context(viewport=self._viewport)
        self._page = self._context.new_page()

    def goto(self, url: str):
        assert self._page is not None
        try:
            self._page.goto(url, timeout=self._timeout, wait_until="networkidle")
        except PwTimeoutError:
            self._page.wait_for_load_state("domcontentloaded", timeout=self._timeout)
        logger.debug("Navigated to {} (final URL: {})", url, self._page.url)
        return self._page

    def page(self):
        return self._page

    def close(self) -> None:
        try:
            if self._browser:
                self._browser.close()
        finally:
            if self._p:
                self._p.stop()
        self._p = None
        self._browser = None
        self._context = None
        self._page = None


class PlaywrightScraper:
    """Base scraper providing Playwright session and common helpers.

    Extend this class and implement `scrape(url)` to return a dict compatible
    with ExtractedFundDocument. Use provided helpers for navigation and parsing.
    """

    HOLDINGS_TAB_PATTERNS = [r"^holdings$", r"^top\s+holdings$", r"portfolio"]
    SHOW_ALL_LABELS = [r"show all", r"view all", r"see all"]
    HOLDINGS_HEADER_KEYWORDS = ["holding", "company", "name"]

    def __init__(
        self,
        session: PlaywrightSession | None = None,
        *,
        headless: bool = True,
        nav_timeout_ms: int = 30000,
    ) -> None:
        self.session = session or PlaywrightSession(
            headless=headless, nav_timeout_ms=nav_timeout_ms
        )
        self._own = session is None

    def scrape(self, url: str) -> dict[str, Any]:  # pragma: no cover - abstract by convention
        raise NotImplementedError

    def scrape_many(self, urls: Iterable[str]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        opened = False
        if self._own:
            self.session.open()
            opened = True
        try:
            for url in urls:
                try:
                    results.append(self.scrape(url))
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Failed to scrape {}: {}", url, exc)
        finally:
            if opened:
                self.session.close()
        return results

    # ---- helpers ----
    def goto(self, url: str):
        # Lazy-open session if needed to avoid assertion errors
        try:
            pg = self.session.page()
        except Exception:
            pg = None
        if pg is None:
            self.session.open()
        return self.session.goto(url)

    def get_body_text(self, page) -> str:
        return re.sub(r"[\t\r\f]+", " ", page.inner_text("body"))

    def click_holdings_tab(self, page) -> None:
        for pattern in self.HOLDINGS_TAB_PATTERNS:
            # role-based tab
            try:
                page.get_by_role("tab", name=re.compile(pattern, re.I)).click(timeout=1800)
                page.wait_for_timeout(200)
                return
            except Exception:
                pass
            # anchor or button with text
            try:
                page.locator(f"a:has-text('{pattern}')").first.click(timeout=1800)
                page.wait_for_timeout(200)
                return
            except Exception:
                pass
            try:
                page.locator(f"button:has-text('{pattern}')").first.click(timeout=1800)
                page.wait_for_timeout(200)
                return
            except Exception:
                pass
            # generic text click
            try:
                page.get_by_text(re.compile(pattern, re.I)).first.click(timeout=1800)
                page.wait_for_timeout(200)
                return
            except Exception:
                pass

    def click_show_all(self, page) -> None:
        for label in self.SHOW_ALL_LABELS:
            # button with accessible name
            try:
                page.get_by_role("button", name=re.compile(label, re.I)).click(timeout=1200)
                page.wait_for_timeout(250)
                return
            except Exception:
                pass
            # explicit button/anchor contains
            try:
                page.locator(f"button:has-text('{label}')").first.click(timeout=1200)
                page.wait_for_timeout(250)
                return
            except Exception:
                pass
            try:
                page.locator(f"a:has-text('{label}')").first.click(timeout=1200)
                page.wait_for_timeout(250)
                return
            except Exception:
                pass
            # generic text click
            try:
                page.get_by_text(re.compile(label, re.I)).first.click(timeout=1200)
                page.wait_for_timeout(250)
                return
            except Exception:
                pass

    def ensure_top_holdings_visible(self, page) -> None:
        try:
            page.get_by_text(
                re.compile(r"(top\s+)?holdings", re.I)
            ).first.scroll_into_view_if_needed(timeout=2000)
        except Exception:
            try:
                page.get_by_role(
                    "heading", name=re.compile(r"holdings", re.I)
                ).first.scroll_into_view_if_needed(timeout=2000)
            except Exception:
                pass

    def scroll_page(self, page, steps: int = 5, dy: int = 900) -> None:
        for _ in range(max(1, steps)):
            try:
                page.mouse.wheel(0, dy)
                page.wait_for_timeout(200)
            except Exception:
                break

    def extract_heading(self, page) -> str | None:
        try:
            return page.locator("h1").first.inner_text(timeout=1500).strip()
        except Exception:
            try:
                return page.get_by_role("heading").first.inner_text(timeout=1500).strip()
            except Exception:
                return None

    def find_holdings_table(self, page):
        try:
            heading = page.get_by_role("heading", name=re.compile(r"^top\s+holdings$", re.I)).first
            h = heading.element_handle(timeout=1000)
            if h:
                tbl = h.query_selector("xpath=following::table[1]")
                # Validate header looks like holdings table
                if tbl:
                    try:
                        ths = tbl.query_selector_all("th") or []
                        header_text = " ".join([(t.inner_text() or "").lower() for t in ths])
                        if any(k in header_text for k in self.HOLDINGS_HEADER_KEYWORDS):
                            return tbl
                    except Exception:
                        return tbl
        except Exception:
            pass
        # Try by text container
        try:
            container = (
                page.locator("section, div")
                .filter(has_text=re.compile(r"^top\\s+holdings$", re.I))
                .first
            )
            h = container.element_handle(timeout=1000)
            if h:
                t = h.query_selector("table")
                if t:
                    try:
                        ths = t.query_selector_all("th") or []
                        header_text = " ".join([(th.inner_text() or "").lower() for th in ths])
                        if any(k in header_text for k in self.HOLDINGS_HEADER_KEYWORDS):
                            return t
                    except Exception:
                        return t
        except Exception:
            pass
        return None

    def parse_holdings_from_table(self, page, tbl) -> list[dict[str, Any]]:
        if not tbl:
            return []
        res: list[dict[str, Any]] = []
        # Get rows within this table robustly for both Locator and ElementHandle
        rows: list[Any] = []
        try:
            rows = tbl.locator("tr").all()  # Locator path
        except Exception:
            try:
                rows = tbl.query_selector_all("tr")  # ElementHandle path
            except Exception:
                rows = []
        rank = 1
        # Skip header row if present
        start_index = 1 if len(rows) > 0 else 0
        for r in rows[start_index:80]:
            # Get cell locators/handles
            cells: list[Any] = []
            try:
                cells = r.locator("td").all()
            except Exception:
                try:
                    cells = r.query_selector_all("td")
                except Exception:
                    cells = []
            if len(cells) < 2:
                continue
            # Extract name
            try:
                name = cells[0].inner_text().strip()
            except Exception:
                try:
                    name = (cells[0].text_content() or "").strip()
                except Exception:
                    name = ""
            # Extract percent allocation (prefer last cell)
            row_text = ""
            try:
                row_text = r.inner_text()
            except Exception:
                try:
                    row_text = r.text_content() or ""
                except Exception:
                    row_text = ""
            try:
                last_text = cells[-1].inner_text()
            except Exception:
                try:
                    last_text = cells[-1].text_content() or ""
                except Exception:
                    last_text = ""
            alloc = self._percent(last_text) or self._percent(row_text)
            if name and alloc:
                res.append({"rank": rank, "company_name": name, "allocation_percentage": alloc})
                rank += 1
            if rank > 11:
                break
        return res

    def parse_holdings_from_any_table(self, page) -> list[dict[str, Any]]:
        # Look for the first few tables near the Top holdings section, then parse
        try:
            containers = [
                page.get_by_role("heading", name=re.compile(r"^top\\s+holdings$", re.I)).first,
                page.locator("section, div")
                .filter(has_text=re.compile(r"^top\\s+holdings$", re.I))
                .first,
            ]
            for cont in containers:
                try:
                    h = cont.element_handle(timeout=800)
                except Exception:
                    h = None
                if h:
                    cand = h.query_selector("xpath=following::table[1]")
                    if cand:
                        # Validate by header
                        try:
                            ths = cand.query_selector_all("th") or []
                            header_text = " ".join([(t.inner_text() or "").lower() for t in ths])
                            if not any(k in header_text for k in self.HOLDINGS_HEADER_KEYWORDS):
                                cand = None
                        except Exception:
                            pass
                        if cand:
                            parsed = self.parse_holdings_from_table(page, cand)
                            if parsed:
                                return parsed
        except Exception:
            pass
        # Fallback: try all tables on page
        try:
            tables = page.locator("table").all()
            for tbl in tables[:8]:
                # Validate header
                try:
                    header = tbl.locator("th").all()
                    header_text = " ".join([(th.inner_text() or "").lower() for th in header])
                except Exception:
                    header_text = ""
                if any(k in header_text for k in self.HOLDINGS_HEADER_KEYWORDS):
                    parsed = self.parse_holdings_from_table(page, tbl)
                    if parsed:
                        return parsed
        except Exception:
            pass
        return []

    @staticmethod
    def _percent(text: str) -> str | None:
        m = re.search(r"\d{1,3}(?:\.\d+)?%", text)
        return m.group(0) if m else None
