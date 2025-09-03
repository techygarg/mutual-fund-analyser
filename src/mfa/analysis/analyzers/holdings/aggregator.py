"""
Holdings aggregator with simplified interface.

This module aggregates holdings data across multiple funds.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List

from .data_processor import ProcessedFund


@dataclass
class CompanyData:
    """Aggregated data for a single company."""
    name: str
    fund_count: int
    total_weight: float
    average_weight: float
    sample_funds: List[str]


@dataclass
class AggregatedData:
    """Complete aggregated holdings data."""
    companies: Dict[str, CompanyData]
    funds_info: Dict[str, Dict[str, Any]]


class HoldingsAggregator:
    """Aggregates holdings data across multiple funds."""
    
    def __init__(self):
        """Initialize aggregator - parameters passed per call."""
        pass
    
    def aggregate_holdings(self, processed_funds: List[ProcessedFund], params: Any = None) -> AggregatedData:
        """
        Aggregate holdings data across all processed funds.
        
        Args:
            processed_funds: List of processed fund data
            params: Analysis parameters (for max_sample_funds_per_company)
        
        Returns:
            AggregatedData with company information
        """
        max_samples = getattr(params, 'max_sample_funds_per_company', 5) if params else 5
        
        company_to_funds = defaultdict(set)
        company_total_weights = defaultdict(float)
        company_examples = defaultdict(list)
        funds_info = {}
        
        # Process each fund
        for fund in processed_funds:
            fund_key = fund.name
            funds_info[fund_key] = {
                "name": fund.name,
                "aum": fund.aum,
                "holdings_count": len(fund.holdings)
            }
            
            # Process holdings in this fund
            for holding in fund.holdings:
                company_name = holding.company_name
                
                # Track which funds hold this company
                company_to_funds[company_name].add(fund_key)
                
                # Sum up total weights across all funds
                company_total_weights[company_name] += holding.allocation_percentage
                
                # Collect sample fund names (limited)
                if len(company_examples[company_name]) < max_samples:
                    company_examples[company_name].append(fund_key)
        
        # Build final company data
        companies = {}
        for company_name in company_to_funds:
            fund_count = len(company_to_funds[company_name])
            total_weight = company_total_weights[company_name]
            average_weight = total_weight / fund_count if fund_count > 0 else 0
            
            companies[company_name] = CompanyData(
                name=company_name,
                fund_count=fund_count,
                total_weight=total_weight,
                average_weight=average_weight,
                sample_funds=company_examples[company_name]
            )
        
        return AggregatedData(
            companies=companies,
            funds_info=funds_info
        )