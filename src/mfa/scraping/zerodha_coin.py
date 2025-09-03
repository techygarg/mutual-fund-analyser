from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from playwright.sync_api import Page
from pydantic import HttpUrl

from mfa.logging.logger import logger
from mfa.core.schemas import ExtractedFundDocument, FundData, FundInfo, TopHolding
from mfa.scraping.core.playwright_scraper import PlaywrightScraper, PlaywrightSession


def _extract_by_label(text: str, label_patterns: list[str], value_pattern: str) -> str | None:
    pattern = re.compile(
        rf"(?:{'|'.join(label_patterns)}).*?({value_pattern})", re.IGNORECASE | re.DOTALL
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else None


def _percent(text: str) -> str | None:
    m = re.search(r"\d{1,3}(?:\.\d+)?%", text)
    return m.group(0) if m else None


def _rupees(text: str) -> str | None:
    m = re.search(
        r"(?:₹|Rs\.?)[\s]*[\d,]+(?:\.\d+)?\s*(?:Cr\.|Cr|L|Lakh|Lakhs|Bn|Mn)?", text, re.IGNORECASE
    )
    return m.group(0) if m else None


def _extract_meta_fields(body_text: str) -> dict[str, Any]:
    current_nav = _extract_by_label(body_text, ["NAV"], r"₹?\s?[\d,]+(?:\.\d+)?") or _rupees(
        body_text
    )
    expense_ratio = _extract_by_label(
        body_text, [r"expense\s*ratio"], r"\d{1,2}(?:\.\d+)?%"
    ) or _percent(body_text)
    aum = _extract_by_label(
        body_text,
        ["AUM", "assets? under management"],
        r"(?:₹|Rs\.?)[\s]*[\d,]+(?:\.\d+)?\s*(?:Cr\.|Cr|L|Lakh|Lakhs|Bn|Mn)?",
    ) or _rupees(body_text)
    fund_manager = _extract_by_label(
        body_text, [r"fund\s*manager", r"fund\s*managers"], r"[A-Za-z .,&-]{3,}"
    )
    launch_date = _extract_by_label(
        body_text,
        [r"launch(?:ed)?\s*date", "inception"],
        r"\d{1,2}\s*[A-Za-z]{3,9}\s*\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
    )
    risk_level = _extract_by_label(
        body_text, ["risk"], r"(Very\s+High|High|Moderate|Low|Very\s+Low)"
    )
    return {
        "current_nav": current_nav,
        "expense_ratio": expense_ratio,
        "aum": aum,
        "fund_manager": fund_manager,
        "launch_date": launch_date,
        "risk_level": risk_level,
    }


def _parse_top_holdings(page: Page, base: PlaywrightScraper, max_holdings: int = 10) -> list[dict[str, Any]]:
    tbl = base.find_holdings_table(page)
    if tbl:
        res = base.parse_holdings_from_table(page, tbl, max_holdings)
        if res:
            return res
    res = base.parse_holdings_from_any_table(page, max_holdings)
    if res:
        return res
    # Fallback: parse from text within the Top holdings section (non-table layouts)
    try:
        section = page.get_by_role("heading", name=re.compile(r"^top\s+holdings$", re.I)).first
        container = section.locator("xpath=ancestor::*[self::section or self::div][1]")
    except Exception:
        container = page.locator("body")
    nodes = container.locator(
        r"text=/\b\d{1,2}(?:\.\d+)?%\b/"
    ).all()  # percent tokens within Top holdings
    seen: set[str] = set()
    items: list[dict[str, Any]] = []
    rank = 1
    # Simple sector/catch-all exclusions to avoid sector allocation tiles
    sector_like = re.compile(
        r"^(financials|industrials|materials|energy|utilities|health\s*care|consumer|it|information\s*technology|communication|treps|reverse\s*repo|cash|pharmaceuticals|staples)$",
        re.I,
    )
    for node in nodes:
        try:
            row = node.locator("xpath=ancestor::*[self::tr or self::li or self::div][1]")
            txt = row.inner_text()
        except Exception:
            try:
                txt = node.inner_text()
            except Exception:
                continue
        m_pct = re.search(r"\d{1,2}(?:\.\d+)?%", txt)
        if not m_pct:
            continue
        alloc = m_pct.group(0)
        # Remove percent chunk and noisy tokens to derive a name-ish string
        name_text = re.sub(r"\s*\d{1,2}(?:\.\d+)?%\s*", " ", txt)
        name_text = re.sub(
            r"^(?:top\s+holdings|rank|weight|allocation)[:\s-]*", "", name_text, flags=re.I
        )
        # Choose first sensible line as company name
        candidates = [
            ln.strip()
            for ln in re.split(r"[\n\r]+", name_text)
            if ln.strip() and "%" not in ln and len(ln.strip()) > 2
        ]
        if not candidates:
            continue
        name = candidates[0]
        # Normalize trivial prefixes like numbering
        name = re.sub(r"^\d+\.\s*", "", name).strip()
        if sector_like.match(name.strip(" .").lower()):
            continue
        if name.lower() in seen:
            continue
        seen.add(name.lower())
        items.append({"rank": rank, "company_name": name, "allocation_percentage": alloc})
        rank += 1
        if rank > max_holdings:
            break
    return items


def _build_document(
    url: str, fund_name: str | None, meta: dict[str, Any], holdings: list[dict[str, Any]]
) -> dict[str, Any]:
    fi = FundInfo(
        fund_name=fund_name or "",
        current_nav=meta.get("current_nav") or "",
        cagr="",
        expense_ratio=meta.get("expense_ratio") or "",
        aum=meta.get("aum") or "",
        fund_manager=meta.get("fund_manager") or "",
        launch_date=meta.get("launch_date") or "",
        risk_level=meta.get("risk_level") or "",
    )
    th = [
        TopHolding(
            rank=int(h.get("rank", i + 1)),
            company_name=h["company_name"],
            allocation_percentage=h["allocation_percentage"],
        )
        for i, h in enumerate(holdings)
    ]
    fd = FundData(fund_info=fi, top_holdings=th)
    doc = ExtractedFundDocument(
        extraction_timestamp=datetime.utcnow(),
        source_url=HttpUrl(url),
        provider="playwright",
        data=fd,
    )
    # Ensure JSON-serializable output (HttpUrl, datetime -> strings)
    return doc.model_dump(mode="json")


class ZerodhaCoinScraper(PlaywrightScraper):
    """Scraper for Zerodha Coin funds using Playwright."""

    def __init__(
        self,
        session: PlaywrightSession | None = None,
        headless: bool = True,
        nav_timeout_ms: int = 30000,
    ) -> None:
        # Pass session through; base will create one if None and mark _own correctly
        super().__init__(session=session, headless=headless, nav_timeout_ms=nav_timeout_ms)

    def scrape(self, url: str, max_holdings: int = 10, storage_config: dict | None = None) -> dict[str, Any]:
        """
        Scrape fund data from a URL with configurable holdings limit and smart storage.
        
        Args:
            url: Fund URL to scrape
            max_holdings: Maximum number of holdings to extract
            storage_config: Optional storage configuration containing:
                - should_save: bool - Whether to save to disk
                - base_dir: str - Base directory for storage
                - category: str - Fund category for organization
                - filename_prefix: str - Prefix for generated filenames
                
        Returns:
            dict: Scraped fund data document
        """
        logger.debug("🌐 Starting scrape for: {}", url)
        
        session_opened = self._open_session_if_needed()
        try:
            page = self._navigate_to_fund_page(url)
            self._prepare_holdings_section(page)
            fund_name, meta, holdings = self._extract_fund_data(page, max_holdings)
            self._log_extraction_results(fund_name, meta, holdings, max_holdings, url)
            
            document = self._build_and_optionally_save_document(url, fund_name, meta, holdings, storage_config)
            return document
            
        except Exception as e:
            self._log_scraping_error(url, e)
            raise
        finally:
            if session_opened:
                self._close_session()

    def _open_session_if_needed(self) -> bool:
        """Open browser session if this scraper owns it. Returns True if opened."""
        if self._own:
            self.session.open()
            return True
        return False

    def _navigate_to_fund_page(self, url: str) -> Page:
        """Navigate to the fund page and return the page object."""
        logger.debug("🗺️ Navigating to fund page...")
        return self.goto(url)

    def _prepare_holdings_section(self, page: Page) -> None:
        """Locate, scroll to, and expand the holdings section."""
        self._scroll_to_holdings_section(page)
        self._expand_holdings_view(page)
        self._wait_for_holdings_data(page)

    def _scroll_to_holdings_section(self, page: Page) -> None:
        """Scroll to the holdings section if found."""
        logger.debug("🔍 Looking for holdings section...")
        try:
            page.get_by_text(
                re.compile(r"top\s+holdings", re.I)
            ).first.scroll_into_view_if_needed(timeout=2000)
            logger.debug("✅ Found 'Top Holdings' section")
        except Exception:
            try:
                page.get_by_text(
                    re.compile(r"holdings", re.I)
                ).first.scroll_into_view_if_needed(timeout=2000)
                logger.debug("✅ Found 'Holdings' section (alternative)")
            except Exception:
                logger.debug("⚠️ Holdings section not found, continuing...")

    def _expand_holdings_view(self, page: Page) -> None:
        """Expand the holdings view by clicking relevant tabs and buttons."""
        logger.debug("🔄 Attempting to expand holdings view...")
        self.click_holdings_tab(page)
        self.click_show_all(page)

    def _wait_for_holdings_data(self, page: Page) -> None:
        """Wait for holdings data to load on the page."""
        logger.debug("⏳ Waiting for holdings data to load...")
        try:
            # Wait for either table rows or visible percent cells
            page.wait_for_selector("table tr", timeout=5000)
            logger.debug("✅ Holdings table found")
        except Exception:
            try:
                page.wait_for_selector(r"text=/\d{1,2}(?:\.\d+)?%/", timeout=3500)
                logger.debug("✅ Holdings percentages found (non-table format)")
            except Exception:
                logger.debug("⚠️ Holdings data not immediately visible, proceeding...")

    def _extract_fund_data(self, page: Page, max_holdings: int) -> tuple[str | None, dict[str, Any], list[dict[str, Any]]]:
        """Extract all fund data from the page. Returns (fund_name, metadata, holdings)."""
        logger.debug("📋 Extracting fund information...")
        
        # Extract basic fund information
        body_text = self.get_body_text(page)
        fund_name = self.extract_heading(page)
        
        if fund_name:
            logger.debug("🏦 Fund name: {}", fund_name)
        else:
            logger.debug("⚠️ Fund name not found")

        # Extract metadata (NAV, AUM, etc.)
        logger.debug("🔍 Extracting metadata (NAV, AUM, etc.)...")
        meta = _extract_meta_fields(body_text)

        # Extract holdings data
        logger.debug("📈 Parsing holdings data...")
        holdings = _parse_top_holdings(page, self, max_holdings)
        
        return fund_name, meta, holdings

    def _log_extraction_results(self, fund_name: str | None, meta: dict[str, Any], 
                              holdings: list[dict[str, Any]], max_holdings: int, url: str) -> None:
        """Log the results of data extraction with validation."""
        # Validate and report holdings extraction
        expected_min = min(max_holdings, 5)  # Expect at least 5 holdings, but not more than requested
        if len(holdings) < expected_min:
            logger.warning("⚠️  Low holdings count: {} (expected {}+ for max_holdings={})", 
                          len(holdings), expected_min, max_holdings)
            logger.warning("🏦 Fund: {}", fund_name or "Unknown")
            logger.warning("🔗 URL: {}", url)
            logger.info("💡 This might indicate incomplete data extraction")
        else:
            logger.debug("✅ Successfully extracted {} holdings (max_holdings={})", 
                        len(holdings), max_holdings)

        # Log key metadata if available
        if meta.get("aum"):
            logger.debug("💰 AUM: {}", meta["aum"])
        if meta.get("expense_ratio"):
            logger.debug("📊 Expense Ratio: {}", meta["expense_ratio"])

    def _build_and_optionally_save_document(
        self, 
        url: str, 
        fund_name: str | None, 
        meta: dict[str, Any], 
        holdings: list[dict[str, Any]], 
        storage_config: dict | None
    ) -> dict[str, Any]:
        """
        Build the final document and optionally save using JSONStore.
        
        This method now delegates storage responsibilities to JSONStore,
        following single responsibility principle.
        """
        logger.debug("🗺️ Building final document...")
        document = _build_document(url, fund_name, meta, holdings)
        
        # Use PathGenerator and JSONStore for smart storage if requested
        if storage_config and storage_config.get("should_save", False):
            from mfa.storage.json_store import JsonStore
            from mfa.storage.path_generator import PathGenerator
            from mfa.config.settings import ConfigProvider

            # Create path generator and generate path
            config_provider = ConfigProvider()  # Could be injected if needed
            path_gen = PathGenerator(config_provider)

            # Create analysis config dict for path generation
            analysis_config = {
                "type": storage_config.get("analysis_type", "default"),
                "path_template": storage_config.get("path_template")
            }

            file_path = path_gen.generate_scraped_data_path(
                url=url,
                category=storage_config["category"],
                analysis_config=analysis_config
            )

            JsonStore.save_with_path(data=document, file_path=file_path)
        
        return document

    def _log_scraping_error(self, url: str, error: Exception) -> None:
        """Log scraping errors with context."""
        logger.error("❌ Scraping failed for: {}", url)
        logger.error("🚨 Error details: {}", str(error))
        logger.debug("🔍 Full traceback:", exc_info=True)

    def _close_session(self) -> None:
        """Close the browser session."""
        logger.debug("🔒 Closing browser session")
        self.session.close()
