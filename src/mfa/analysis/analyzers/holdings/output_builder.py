"""
Holdings output builder with dependency injection.

This module builds structured output for holdings analysis results using proper dependency injection.
"""

from __future__ import annotations

from typing import Any

from mfa.config.settings import ConfigProvider

from ..utils.output_builder_utils import OutputBuilderUtils
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
        # Get configuration and limits
        max_companies = self._get_max_companies_config()

        # Extract fund references
        funds = self._extract_fund_references(aggregated_data)

        # Sort companies by different criteria
        sorted_companies = self._sort_companies_by_criteria(aggregated_data, funds)

        # Apply result limits
        limited_companies = self._apply_result_limits(sorted_companies, max_companies)

        # Build final output structure
        return self._build_output_structure(funds, aggregated_data, limited_companies)

    def _get_max_companies_config(self) -> int:
        """Get and validate max companies configuration."""
        holdings_config = OutputBuilderUtils.get_analysis_config_with_validation(
            self.config_provider, "holdings"
        )
        return OutputBuilderUtils.extract_max_companies_config(holdings_config)

    def _extract_fund_references(self, aggregated_data: AggregatedData) -> list[dict[str, Any]]:
        """Extract fund references from aggregated data."""
        return OutputBuilderUtils.extract_fund_references(aggregated_data)

    def _sort_companies_by_criteria(
        self, aggregated_data: AggregatedData, funds: list[dict[str, Any]]
    ) -> dict[str, list]:
        """Sort companies by different criteria for various output sections."""
        company_values = list(aggregated_data.companies.values())

        return {
            "by_fund_count": OutputBuilderUtils.sort_companies_by_criteria(
                company_values, "fund_count"
            ),
            "by_total_weight": OutputBuilderUtils.sort_companies_by_criteria(
                company_values, "total_weight"
            ),
            "common_in_all": OutputBuilderUtils.find_companies_in_all_funds(
                company_values, len(funds)
            ),
        }

    def _apply_result_limits(
        self, sorted_companies: dict[str, list], max_companies: int
    ) -> dict[str, list]:
        """Apply max companies limit to each category."""
        return {
            key: OutputBuilderUtils.limit_results(companies, max_companies)
            for key, companies in sorted_companies.items()
        }

    def _build_output_structure(
        self,
        funds: list[dict[str, Any]],
        aggregated_data: AggregatedData,
        limited_companies: dict[str, list],
    ) -> dict[str, Any]:
        """Build the final output structure matching dashboard format."""
        return {
            "total_files": len(funds),  # Dashboard expects this field
            "total_funds": len(funds),
            "funds": funds,
            "unique_companies": len(aggregated_data.companies),
            "top_by_fund_count": [
                self._format_company_for_output(c) for c in limited_companies["by_fund_count"]
            ],
            "top_by_total_weight": [
                self._format_company_for_output(c) for c in limited_companies["by_total_weight"]
            ],
            "common_in_all_funds": [
                self._format_company_for_output(c) for c in limited_companies["common_in_all"]
            ],
        }

    def _format_company_for_output(self, company_data: CompanyData) -> dict[str, Any]:
        """Format company data for dashboard compatibility."""
        return OutputBuilderUtils.format_company_for_dashboard(
            company_data.name,
            company_data.fund_count,
            company_data.total_weight,
            company_data.average_weight,
            company_data.sample_funds,
        )
