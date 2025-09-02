"""
Holdings data aggregator.

This module aggregates holdings data across multiple funds to find
patterns, overlaps, and common investments.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List

from .data_processor import ProcessedFund


@dataclass
class AggregatedData:
    """Container for aggregated holdings data across funds."""
    companies: Dict[str, 'CompanyData']
    funds: Dict[str, str]  # fund_name -> aum


@dataclass
class CompanyData:
    """Aggregated data for a single company across funds."""
    name: str
    fund_count: int
    total_weight: float
    avg_weight: float
    sample_funds: List[str]


class HoldingsAggregator:
    """Aggregates holdings data across multiple funds."""
    
    def __init__(self, params: Dict[str, Any]):
        self.max_samples = params.get("max_sample_funds_per_company", 5)
    
    def aggregate_holdings(self, processed_funds: List[ProcessedFund]) -> AggregatedData:
        """Aggregate holdings data across all processed funds."""
        company_to_funds = defaultdict(set)
        company_total_weights = defaultdict(float)
        company_examples = defaultdict(list)
        funds_info = {}
        
        # Collect data from all funds
        for fund in processed_funds:
            funds_info[fund.name] = fund.aum
            
            for holding in fund.holdings:
                company_name = holding.company_name
                
                # Track which funds hold this company
                company_to_funds[company_name].add(fund.name)
                
                # Accumulate total weight across funds
                company_total_weights[company_name] += holding.allocation_percentage
                
                # Add to examples if not maxed out
                if len(company_examples[company_name]) < self.max_samples:
                    if fund.name not in company_examples[company_name]:
                        company_examples[company_name].append(fund.name)
        
        # Build aggregated company data
        companies = {}
        for company_name in company_to_funds:
            fund_count = len(company_to_funds[company_name])
            total_weight = company_total_weights[company_name]
            avg_weight = total_weight / fund_count if fund_count > 0 else 0
            
            companies[company_name] = CompanyData(
                name=company_name,
                fund_count=fund_count,
                total_weight=total_weight,
                avg_weight=avg_weight,
                sample_funds=company_examples[company_name]
            )
        
        return AggregatedData(
            companies=companies,
            funds=funds_info
        )
