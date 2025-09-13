"""
Holdings aggregator with dependency injection.

This module aggregates holdings data across multiple funds using proper dependency injection.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from mfa.config.settings import ConfigProvider

from ..utils.aggregator_utils import AggregatorUtils
from ..utils.output_builder_utils import OutputBuilderUtils
from .data_processor import ProcessedFund


@dataclass
class CompanyData:
    """Aggregated data for a single company."""

    name: str
    fund_count: int
    total_weight: float
    average_weight: float
    sample_funds: list[str]


@dataclass
class AggregatedData:
    """Complete aggregated holdings data."""

    companies: dict[str, CompanyData]
    funds_info: dict[str, dict[str, Any]]


class HoldingsAggregator:
    """Aggregates holdings data across multiple funds."""

    def __init__(self, config_provider: ConfigProvider):
        """
        Initialize aggregator with dependency injection.

        Args:
            config_provider: Configuration provider instance
        """
        self.config_provider = config_provider

    def aggregate_holdings(self, processed_funds: list[ProcessedFund]) -> AggregatedData:
        """
        Aggregate holdings data across all processed funds.

        Reads configuration directly from ConfigProvider instead of receiving params.

        Args:
            processed_funds: List of processed fund data

        Returns:
            AggregatedData with company information
        """
        # Read configuration using utility
        holdings_config = OutputBuilderUtils.get_analysis_config_with_validation(
            self.config_provider, "holdings"
        )

        max_samples_config = holdings_config.params.max_sample_funds_per_company
        max_samples = max_samples_config if isinstance(max_samples_config, int) else 5
        if isinstance(max_samples, int) and max_samples < 0:
            max_samples = 0

        company_to_funds: defaultdict[str, set] = defaultdict(set)
        company_total_weights: defaultdict[str, float] = defaultdict(float)
        company_examples: defaultdict[str, list] = defaultdict(list)
        funds_info = {}

        # Process each fund
        for fund in processed_funds:
            fund_key = fund.name
            funds_info[fund_key] = {
                "name": fund.name,
                "aum": fund.aum,
                "holdings_count": len(fund.holdings),
            }

            # Process holdings in this fund
            for holding in fund.holdings:
                company_name = holding.company_name
                weight = holding.allocation_percentage

                # Track fund associations
                company_to_funds[company_name].add(fund_key)
                company_total_weights[company_name] += weight

                # Limit sample funds using utility
                if len(company_examples[company_name]) < max_samples:
                    company_examples[company_name].append(fund_key)

        # Build company data
        companies = {}
        for company_name in company_to_funds:
            fund_count = len(company_to_funds[company_name])
            total_weight = company_total_weights[company_name]

            # Calculate average weight using utility
            average_weight = AggregatorUtils.calculate_average_weight(total_weight, fund_count)

            # Limit sample funds using utility
            sample_funds = AggregatorUtils.limit_sample_funds(
                company_examples[company_name], max_samples
            )

            companies[company_name] = CompanyData(
                name=company_name,
                fund_count=fund_count,
                total_weight=total_weight,
                average_weight=average_weight,
                sample_funds=sample_funds,
            )

        return AggregatedData(companies=companies, funds_info=funds_info)
