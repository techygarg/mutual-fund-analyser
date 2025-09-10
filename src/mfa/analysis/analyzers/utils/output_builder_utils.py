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
