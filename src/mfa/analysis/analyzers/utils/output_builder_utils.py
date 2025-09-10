"""
Common utilities for output builders.

This module contains shared output building utilities that ensure consistent
formatting and structure across different analysis types.
"""

from __future__ import annotations

from typing import Any

from mfa.config.settings import ConfigProvider
from mfa.core.exceptions import ConfigurationError


class OutputBuilderUtils:
    """Common utilities for building analysis outputs."""

    @staticmethod
    def format_currency_value(value: float) -> int:
        """
        Format currency values consistently across analyses.

        Args:
            value: Currency value to format

        Returns:
            Rounded integer currency value
        """
        return int(round(value))

    @staticmethod
    def format_percentage(value: float, decimal_places: int = 2) -> float:
        """
        Format percentage values consistently.

        Args:
            value: Percentage value to format
            decimal_places: Number of decimal places

        Returns:
            Formatted percentage value
        """
        return round(value, decimal_places)

    @staticmethod
    def get_analysis_config_with_validation(
        config_provider: ConfigProvider, analysis_type: str
    ) -> Any:
        """
        Get analysis configuration with proper error handling.

        Args:
            config_provider: Configuration provider instance
            analysis_type: Type of analysis

        Returns:
            Analysis configuration

        Raises:
            ConfigurationError: If configuration is not found
        """
        config = config_provider.get_config()
        analysis_config = config.get_analysis(analysis_type)

        if analysis_config is None:
            raise ConfigurationError(
                f"{analysis_type.title()} analysis configuration not found",
                {"analysis": analysis_type},
            )

        return analysis_config

    @staticmethod
    def build_fund_info_dict(
        fund_name: str, additional_info: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Build standardized fund info dictionary.

        Args:
            fund_name: Name of the fund
            additional_info: Optional additional fund information

        Returns:
            Standardized fund info dictionary
        """
        fund_info = {"fund_name": fund_name}

        if additional_info:
            fund_info.update(additional_info)

        return fund_info

    @staticmethod
    def sort_companies_by_weight(
        companies: list[dict[str, Any]], weight_key: str = "total_weight"
    ) -> list[dict[str, Any]]:
        """
        Sort companies by weight/amount in descending order.

        Args:
            companies: List of company dictionaries
            weight_key: Key to sort by

        Returns:
            Sorted list of companies
        """
        return sorted(companies, key=lambda x: x.get(weight_key, 0), reverse=True)

    @staticmethod
    def limit_results(items: list[Any], max_items: int | None) -> list[Any]:
        """
        Limit results to maximum number of items.

        Args:
            items: List of items to limit
            max_items: Maximum number of items (None for no limit)

        Returns:
            Limited list of items
        """
        if max_items is None or max_items <= 0:
            return items

        return items[:max_items]

    @staticmethod
    def extract_max_companies_config(holdings_config: Any, default: int = 100) -> int:
        """
        Extract and validate max companies configuration.

        Args:
            holdings_config: Holdings configuration object
            default: Default value if config is invalid

        Returns:
            Validated max companies value
        """
        max_companies_config = holdings_config.params.max_companies_in_results
        max_companies = max_companies_config if isinstance(max_companies_config, int) else default

        # Ensure non-negative
        if isinstance(max_companies, int) and max_companies < 0:
            max_companies = 0

        return max_companies

    @staticmethod
    def format_company_for_dashboard(
        company_name: str,
        fund_count: int,
        total_weight: float,
        average_weight: float,
        sample_funds: list[str],
    ) -> dict[str, Any]:
        """
        Format company data for dashboard compatibility.

        Args:
            company_name: Name of the company
            fund_count: Number of funds containing this company
            total_weight: Total weight across all funds
            average_weight: Average weight per fund
            sample_funds: Sample fund names

        Returns:
            Dashboard-compatible company dictionary
        """
        return {
            "name": company_name,
            "company": company_name,  # Dashboard expects 'company' field
            "fund_count": fund_count,
            "total_weight": round(total_weight, 2),
            "avg_weight": round(average_weight, 3),  # Note: avg_weight, not average_weight
            "sample_funds": sample_funds,
        }

    @staticmethod
    def format_fund_contribution(fund_name: str, contribution: float) -> dict[str, Any]:
        """
        Format fund contribution for output.

        Args:
            fund_name: Name of the fund
            contribution: Contribution amount

        Returns:
            Formatted fund contribution dictionary
        """
        return {
            "fund_name": fund_name,
            "contribution": OutputBuilderUtils.format_currency_value(contribution),
        }

    @staticmethod
    def sort_companies_by_criteria(companies: list[Any], sort_type: str) -> list[Any]:
        """
        Sort companies by different criteria.

        Args:
            companies: List of company objects with fund_count and total_weight
            sort_type: "fund_count", "total_weight", or "weight_then_count"

        Returns:
            Sorted list of companies
        """
        if sort_type == "fund_count":
            return sorted(companies, key=lambda c: (-c.fund_count, -c.total_weight))
        elif sort_type == "total_weight":
            return sorted(companies, key=lambda c: (-c.total_weight, -c.fund_count))
        elif sort_type == "weight_then_count":
            return sorted(companies, key=lambda c: -c.total_weight)
        else:
            raise ValueError(f"Unknown sort_type: {sort_type}")

    @staticmethod
    def extract_fund_references(aggregated_data: Any) -> list[dict[str, Any]]:
        """
        Extract fund references from aggregated data.

        Args:
            aggregated_data: Aggregated data with funds_info

        Returns:
            List of fund reference dictionaries
        """
        return [
            {"name": fund_info["name"], "aum": fund_info["aum"]}
            for fund_info in aggregated_data.funds_info.values()
        ]

    @staticmethod
    def find_companies_in_all_funds(companies: list[Any], total_fund_count: int) -> list[Any]:
        """
        Find companies that appear in all funds.

        Args:
            companies: List of company objects with fund_count
            total_fund_count: Total number of funds

        Returns:
            List of companies that appear in all funds, sorted by total_weight
        """
        companies_in_all = [c for c in companies if c.fund_count == total_fund_count]
        return sorted(companies_in_all, key=lambda c: -c.total_weight)
