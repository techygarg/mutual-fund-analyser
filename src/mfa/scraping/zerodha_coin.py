from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from mfa.logging.logger import logger
from mfa.models.schemas import ExtractedFundDocument, FundData, FundInfo, TopHolding
from mfa.scraping.core.playwright_scraper import PlaywrightScraper, PlaywrightSession


def _extract_by_label(text: str, label_patterns: List[str], value_pattern: str) -> str | None:
    pattern = re.compile(rf"(?:{'|'.join(label_patterns)}).*?({value_pattern})", re.IGNORECASE | re.DOTALL)
    m = pattern.search(text)
    return m.group(1).strip() if m else None


def _percent(text: str) -> str | None:
    m = re.search(r"\d{1,3}(?:\.\d+)?%", text)
    return m.group(0) if m else None


def _rupees(text: str) -> str | None:
    m = re.search(r"(?:₹|Rs\.?)[\s]*[\d,]+(?:\.\d+)?\s*(?:Cr\.|Cr|L|Lakh|Lakhs|Bn|Mn)?", text, re.IGNORECASE)
    return m.group(0) if m else None


def _extract_meta_fields(body_text: str) -> Dict[str, Any]:
    current_nav = _extract_by_label(body_text, ["NAV"], r"₹?\s?[\d,]+(?:\.\d+)?") or _rupees(body_text)
    expense_ratio = _extract_by_label(body_text, [r"expense\s*ratio"], r"\d{1,2}(?:\.\d+)?%") or _percent(body_text)
    aum = _extract_by_label(
        body_text,
        ["AUM", "assets? under management"],
        r"(?:₹|Rs\.?)[\s]*[\d,]+(?:\.\d+)?\s*(?:Cr\.|Cr|L|Lakh|Lakhs|Bn|Mn)?",
    ) or _rupees(body_text)
    fund_manager = _extract_by_label(body_text, [r"fund\s*manager", r"fund\s*managers"], r"[A-Za-z .,&-]{3,}")
    launch_date = _extract_by_label(
        body_text,
        [r"launch(?:ed)?\s*date", "inception"],
        r"\d{1,2}\s*[A-Za-z]{3,9}\s*\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
    )
    risk_level = _extract_by_label(body_text, ["risk"], r"(Very\s+High|High|Moderate|Low|Very\s+Low)")
    return {
        "current_nav": current_nav,
        "expense_ratio": expense_ratio,
        "aum": aum,
        "fund_manager": fund_manager,
        "launch_date": launch_date,
        "risk_level": risk_level,
    }


def _parse_top_holdings(page, base: PlaywrightScraper) -> List[Dict[str, Any]]:
    tbl = base.find_holdings_table(page)
    if tbl:
        res = base.parse_holdings_from_table(page, tbl)
        if res:
            return res
    res = base.parse_holdings_from_any_table(page)
    if res:
        return res
    # Fallback: parse from text within the Top holdings section (non-table layouts)
    try:
        section = page.get_by_role("heading", name=re.compile(r"^top\s+holdings$", re.I)).first
        container = section.locator(
            "xpath=ancestor::*[self::section or self::div][1]"
        )
    except Exception:
        container = page
    nodes = container.locator(r'text=/\b\d{1,2}(?:\.\d+)?%\b/').all()  # percent tokens within Top holdings
    seen: set[str] = set()
    items: List[Dict[str, Any]] = []
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
        name_text = re.sub(r"^(?:top\s+holdings|rank|weight|allocation)[:\s-]*", "", name_text, flags=re.I)
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
        if rank > 11:
            break
    return items



def _build_document(url: str, fund_name: Optional[str], meta: Dict[str, Any], holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
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
        source_url=url,
        provider="playwright",
        data=fd,
    )
    # Ensure JSON-serializable output (HttpUrl, datetime -> strings)
    return doc.model_dump(mode="json")


class ZerodhaCoinScraper(PlaywrightScraper):
    """Scraper for Zerodha Coin funds using Playwright."""

    def __init__(self, session: Optional[PlaywrightSession] = None, headless: bool = True, nav_timeout_ms: int = 30000) -> None:
        # Pass session through; base will create one if None and mark _own correctly
        super().__init__(session=session, headless=headless, nav_timeout_ms=nav_timeout_ms)

    def scrape(self, url: str) -> Dict[str, Any]:
        opened = False
        if self._own:
            self.session.open()
            opened = True
        try:
            page = self.goto(url)
            # Bring Top holdings into view and expand list
            try:
                page.get_by_text(re.compile(r"top\s+holdings", re.I)).first.scroll_into_view_if_needed(timeout=2000)
            except Exception:
                try:
                    page.get_by_text(re.compile(r"holdings", re.I)).first.scroll_into_view_if_needed(timeout=2000)
                except Exception:
                    pass
            self.click_holdings_tab(page)
            self.click_show_all(page)
            try:
                # Wait for either table rows or visible percent cells
                page.wait_for_selector("table tr", timeout=3500)
            except Exception:
                try:
                    page.wait_for_selector(r'text=/\d{1,2}(?:\.\d+)?%/', timeout=3500)
                except Exception:
                    pass
            body_text = self.get_body_text(page)
            fund_name = self.extract_heading(page)
            meta = _extract_meta_fields(body_text)
            holdings = _parse_top_holdings(page, self)
            if len(holdings) < 10:
                logger.warning("Holdings parsed less than 10 ({}): {}", len(holdings), fund_name or url)
            return _build_document(url, fund_name, meta, holdings)
        finally:
            if opened:
                self.session.close()

