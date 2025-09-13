from __future__ import annotations

from typing import Any

from mfa.config.settings import ConfigProvider

from ..utils.aggregator_utils import AggregatorUtils


class PortfolioAggregator:
    """Aggregates per-company amounts across funds, with exclusions and scaling."""

    def __init__(self, config_provider: ConfigProvider):
        self.config_provider = config_provider

    def aggregate_portfolio(
        self, processed_funds: list[dict[str, Any]], params: Any
    ) -> dict[str, Any]:
        """Aggregate portfolio data across funds with exclusions."""
        # Build exclusion set using utility
        exclusion_set = AggregatorUtils.build_exclusion_set(params.exclude_from_analysis)

        company_to_amount: dict[str, float] = {}
        company_sources: dict[str, list[dict[str, Any]]] = {}

        total_value = 0.0
        for fund in processed_funds:
            total_value += float(fund.get("fund_value", 0.0))
            for h in fund.get("holdings", []):
                name = str(h.get("company_name", "")).strip()

                # Use utility for company exclusion check
                if AggregatorUtils.should_exclude_company(name, exclusion_set):
                    continue

                # Use utility for name normalization
                normalized_name = AggregatorUtils.normalize_company_name(name)
                if not normalized_name:
                    continue

                amt = float(h.get("amount", 0.0))

                # Aggregate amounts by normalized name
                company_to_amount[normalized_name] = (
                    company_to_amount.get(normalized_name, 0.0) + amt
                )

                # Track fund sources using utility
                AggregatorUtils.aggregate_company_sources(
                    company_sources, normalized_name, fund.get("fund_name", ""), amt
                )

        # Sort companies by amount desc
        sorted_items = sorted(company_to_amount.items(), key=lambda kv: kv[1], reverse=True)

        return {
            "total_value": total_value,
            "company_amounts": sorted_items,
            "company_sources": company_sources,
        }
