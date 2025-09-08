from __future__ import annotations

import re
from typing import Any

from loguru import logger

from mfa.config.settings import ConfigProvider


class PortfolioDataProcessor:
    """Transforms scraped fund JSONs into structures usable for portfolio math."""

    def __init__(self, config_provider: ConfigProvider):
        self.config_provider = config_provider

    def map_url_to_units(self, funds_cfg: list[dict[str, Any]]) -> dict[str, float]:
        url_to_units: dict[str, float] = {}
        for entry in funds_cfg:
            if isinstance(entry, dict):
                url = entry.get("url")
                units = entry.get("units")
                if url and units is not None:
                    try:
                        url_to_units[str(url)] = float(units)
                    except Exception:
                        pass  # Skip invalid entries
        return url_to_units

    def _parse_nav(self, nav_text: str | None) -> float:
        if not nav_text:
            return 0.0
        # Extract number from strings like "₹ 123.45" or "Rs. 123.45"
        m = re.search(r"[\d,.]+(?:\.\d+)?", nav_text)
        if not m:
            return 0.0
        return float(m.group(0).replace(",", ""))

    def _parse_percent(self, pct_text: str | None) -> float:
        if not pct_text:
            return 0.0
        m = re.search(r"\d{1,3}(?:\.\d+)?", pct_text)
        if not m:
            return 0.0
        return float(m.group(0)) / 100.0

    def process_fund_jsons(
        self, fund_documents: list[dict[str, Any]], url_to_units: dict[str, float]
    ) -> list[dict[str, Any]]:
        processed: list[dict[str, Any]] = []

        for doc in fund_documents:
            data = (doc or {}).get("data", {})
            fund_info = data.get("fund_info", {})
            holdings = data.get("top_holdings", [])
            url = (doc or {}).get("source_url")

            units = url_to_units.get(url, 0.0) if url else 0.0
            nav = self._parse_nav(fund_info.get("current_nav"))

            # Calculate fund value: units × NAV = actual portfolio value
            if nav > 0:
                fund_value = units * nav
                logger.debug(f"💰 Fund value: {units} units × ₹{nav} NAV = ₹{fund_value:,.2f}")
            else:
                # Fallback to units as nominal value if NAV unavailable
                fund_value = units
                logger.warning(f"⚠️ NAV not available for {url}, using units as value")

            processed_holdings: list[dict[str, Any]] = []
            for h in holdings:
                name = h.get("company_name")
                pct_text = h.get("allocation_percentage")
                fraction = self._parse_percent(pct_text)
                amount = fund_value * fraction
                if not name:
                    continue
                processed_holdings.append(
                    {
                        "company_name": str(name),
                        "fraction": fraction,
                        "amount": amount,
                    }
                )

            processed.append(
                {
                    "url": url,
                    "fund_name": fund_info.get("fund_name", ""),
                    "units": units,
                    "nav": nav,
                    "fund_value": fund_value,
                    "holdings": processed_holdings,
                }
            )

        return processed
