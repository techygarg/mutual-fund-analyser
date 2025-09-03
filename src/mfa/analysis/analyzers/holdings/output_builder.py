"""
Holdings output builder with dependency injection.

This module builds structured output for holdings analysis results using proper dependency injection.
"""

from __future__ import annotations

from typing import Any

from mfa.config.settings import ConfigProvider

from .aggregator import AggregatedData


class HoldingsOutputBuilder:
    """Builds structured output for holdings analysis."""

    def __init__(self, config_provider: ConfigProvider):
        """
        Initialize builder with dependency injection.

        Args:
            config_provider: Configuration provider instance
        """
        self.config_provider = config_provider

    def build_category_output(
        self, category: str, aggregated_data: AggregatedData
    ) -> dict[str, Any]:
        """
        Build the complete output structure for a category.

        Reads configuration directly from ConfigProvider instead of receiving params.

        Args:
            category: Category name (e.g., "largeCap")
            aggregated_data: Aggregated holdings data

        Returns:
            Complete analysis output dictionary
        """
        # Read configuration directly
        config = self.config_provider.get_config()
        holdings_config = config.analyses["holdings"]
        max_companies = holdings_config.params.max_companies_in_results or 100

        # Build fund references from aggregated data
        funds = [
            {"name": fund_info["name"], "aum": fund_info["aum"]}
            for fund_info in aggregated_data.funds_info.values()
        ]

        # Sort companies by fund count (descending) and weight
        sorted_companies = sorted(
            aggregated_data.companies.values(), key=lambda c: (-c.fund_count, -c.total_weight)
        )

        # Limit to max companies
        if max_companies > 0:
            sorted_companies = sorted_companies[:max_companies]

        # Build company output
        companies = []
        for company_data in sorted_companies:
            companies.append(
                {
                    "name": company_data.name,
                    "fund_count": company_data.fund_count,
                    "total_weight": round(company_data.total_weight, 2),
                    "average_weight": round(company_data.average_weight, 2),
                    "sample_funds": company_data.sample_funds,
                }
            )

        return {
            "category": category,
            "summary": {
                "total_funds": len(funds),
                "total_companies": len(aggregated_data.companies),
                "companies_in_results": len(companies),
            },
            "funds": funds,
            "companies": companies,
        }
