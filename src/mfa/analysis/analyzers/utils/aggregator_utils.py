"""
Common utilities for aggregators.

This module contains shared aggregation utilities that ensure consistent
data aggregation patterns across different analysis types.
"""

from __future__ import annotations

from typing import Any

from .data_processor_utils import DataProcessorUtils


class AggregatorUtils:
    """Common utilities for data aggregation across analyses."""

    @staticmethod
    def normalize_company_name(name: str) -> str:
        """
        Normalize company name using consistent logic.

        This delegates to DataProcessorUtils to ensure all components
        use the same normalization approach.

        Args:
            name: Company name to normalize

        Returns:
            Normalized company name
        """
        return DataProcessorUtils.normalize_company_name(name)

    @staticmethod
    def build_exclusion_set(exclude_list: list[str] | None) -> set[str]:
        """
        Build normalized exclusion set from configuration.

        Args:
            exclude_list: List of company names to exclude

        Returns:
            Set of normalized exclusion names for efficient lookup
        """
        if not exclude_list:
            return set()

        return {AggregatorUtils.normalize_company_name(name) for name in exclude_list}

    @staticmethod
    def should_exclude_company(company_name: str, exclusion_set: set[str]) -> bool:
        """
        Check if company should be excluded from aggregation.

        Args:
            company_name: Company name to check
            exclusion_set: Set of normalized exclusion names

        Returns:
            True if company should be excluded
        """
        if not company_name or not exclusion_set:
            return False

        normalized_name = AggregatorUtils.normalize_company_name(company_name)
        return normalized_name in exclusion_set

    @staticmethod
    def calculate_average_weight(total_weight: float, fund_count: int) -> float:
        """
        Calculate average weight across funds.

        Args:
            total_weight: Total weight across all funds
            fund_count: Number of funds

        Returns:
            Average weight per fund
        """
        return total_weight / fund_count if fund_count > 0 else 0.0

    @staticmethod
    def limit_sample_funds(sample_funds: list[str], max_samples: int | None) -> list[str]:
        """
        Limit sample funds to maximum number.

        Args:
            sample_funds: List of sample fund names
            max_samples: Maximum number of samples (None for no limit)

        Returns:
            Limited list of sample funds
        """
        if max_samples is None or max_samples <= 0:
            return sample_funds

        return sample_funds[:max_samples]

    @staticmethod
    def aggregate_company_sources(
        company_sources: dict[str, list[dict[str, Any]]],
        company_name: str,
        fund_name: str,
        contribution: float,
    ) -> None:
        """
        Add fund contribution to company sources tracking.

        Args:
            company_sources: Dictionary tracking company fund sources
            company_name: Name of the company
            fund_name: Name of the contributing fund
            contribution: Amount/weight of contribution
        """
        company_sources.setdefault(company_name, []).append(
            {
                "fund_name": fund_name,
                "contribution": contribution,
            }
        )
