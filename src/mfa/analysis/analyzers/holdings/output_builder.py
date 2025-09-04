"""
Holdings output builder with dependency injection.

This module builds structured output for holdings analysis results using proper dependency injection.
"""

from __future__ import annotations

from typing import Any

from mfa.config.settings import ConfigProvider

from .aggregator import AggregatedData, CompanyData


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

        Matches the previous working structure that the dashboard expects.

        Args:
            category: Category name (e.g., "largeCap")
            aggregated_data: Aggregated holdings data

        Returns:
            Complete analysis output dictionary in the expected format
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

        # Convert company data to the expected format (dashboard compatible)
        def format_company(company_data: CompanyData) -> dict[str, Any]:
            return {
                "name": company_data.name,
                "company": company_data.name,  # Dashboard expects 'company' field
                "fund_count": company_data.fund_count,
                "total_weight": round(company_data.total_weight, 2),
                "avg_weight": round(company_data.average_weight, 3),  # Note: avg_weight, not average_weight
                "sample_funds": company_data.sample_funds,
            }

        # Sort companies by fund count (descending), then by total weight (descending)
        companies_by_fund_count = sorted(
            aggregated_data.companies.values(), 
            key=lambda c: (-c.fund_count, -c.total_weight)
        )

        # Sort companies by total weight (descending), then by fund count (descending)
        companies_by_total_weight = sorted(
            aggregated_data.companies.values(), 
            key=lambda c: (-c.total_weight, -c.fund_count)
        )

        # Find companies that appear in ALL funds
        total_funds = len(funds)
        companies_in_all_funds = [
            company for company in aggregated_data.companies.values()
            if company.fund_count == total_funds
        ]
        # Sort common companies by total weight (descending)
        companies_in_all_funds.sort(key=lambda c: -c.total_weight)

        # Apply max_companies limit to each category
        if max_companies > 0:
            companies_by_fund_count = companies_by_fund_count[:max_companies]
            companies_by_total_weight = companies_by_total_weight[:max_companies]
            companies_in_all_funds = companies_in_all_funds[:max_companies]

        # Build the output structure matching the previous format
        return {
            "total_files": len(funds),  # Dashboard expects this field
            "total_funds": len(funds),
            "funds": funds,
            "unique_companies": len(aggregated_data.companies),
            "top_by_fund_count": [format_company(c) for c in companies_by_fund_count],
            "top_by_total_weight": [format_company(c) for c in companies_by_total_weight],
            "common_in_all_funds": [format_company(c) for c in companies_in_all_funds],
        }
