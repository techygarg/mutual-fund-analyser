from __future__ import annotations

import re
from typing import Any

from mfa.config.settings import ConfigProvider

# Precompiled regex patterns (module-level) for performance - same as holdings data_processor
_SUFFIX_PATTERNS = [
    re.compile(r"\s+Limited\s*$", re.IGNORECASE),
    re.compile(r"\s+Ltd\.?\s*$", re.IGNORECASE),
    re.compile(r"\s+Pvt\.?\s*$", re.IGNORECASE),
    re.compile(r"\s+Private\s+Limited\s*$", re.IGNORECASE),
    re.compile(r"\s+Pvt\.?\s+Ltd\.?\s*$", re.IGNORECASE),
    re.compile(r"\s+Inc\.?\s*$", re.IGNORECASE),
    re.compile(r"\s+Corporation\s*$", re.IGNORECASE),
    re.compile(r"\s+Corp\.?\s*$", re.IGNORECASE),
    re.compile(r"\s+Company\s*$", re.IGNORECASE),
    re.compile(r"\s+Co\.?\s*$", re.IGNORECASE),
]

_TRAILING_DOTS_SPACES_PATTERN = re.compile(r"[\.\s]+$")


class PortfolioAggregator:
    """Aggregates per-company amounts across funds, with exclusions and scaling."""

    def __init__(self, config_provider: ConfigProvider):
        self.config_provider = config_provider

    def _normalize_name(self, name: str) -> str:
        """
        Normalize company name by removing common suffixes and standardizing format.

        This uses the same logic as the holdings data_processor for consistency.
        """
        if not name:
            return name

        # Remove leading/trailing whitespace
        normalized = name.strip()

        # Apply suffix removal using precompiled patterns
        for pattern in _SUFFIX_PATTERNS:
            normalized = pattern.sub("", normalized)

        # Clean up any remaining trailing dots or spaces (precompiled)
        normalized = _TRAILING_DOTS_SPACES_PATTERN.sub("", normalized)

        # Ensure we don't return empty string
        if not normalized.strip():
            return name

        return normalized.strip()

    def aggregate_portfolio(
        self, processed_funds: list[dict[str, Any]], params: Any
    ) -> dict[str, Any]:
        exclude = set(params.exclude_from_analysis or [])
        exclude_norm = {self._normalize_name(x) for x in exclude}

        company_to_amount: dict[str, float] = {}
        company_sources: dict[str, list[dict[str, Any]]] = {}

        total_value = 0.0
        for fund in processed_funds:
            total_value += float(fund.get("fund_value", 0.0))
            for h in fund.get("holdings", []):
                name = str(h.get("company_name", "")).strip()
                normalized_name = self._normalize_name(name)
                if not name or normalized_name in exclude_norm:
                    continue
                amt = float(h.get("amount", 0.0))
                # Use normalized name as key for proper consolidation
                company_to_amount[normalized_name] = (
                    company_to_amount.get(normalized_name, 0.0) + amt
                )
                company_sources.setdefault(normalized_name, []).append(
                    {
                        "fund_name": fund.get("fund_name", ""),
                        "contribution": amt,
                    }
                )

        # Use actual portfolio value (no scaling to target_investment)
        # Portfolio value = sum of (units × NAV) for all funds

        # Sort companies by amount desc
        sorted_items = sorted(company_to_amount.items(), key=lambda kv: kv[1], reverse=True)

        return {
            "total_value": total_value,
            "company_amounts": sorted_items,
            "company_sources": company_sources,
        }
