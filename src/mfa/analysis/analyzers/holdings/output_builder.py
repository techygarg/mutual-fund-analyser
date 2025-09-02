"""
Holdings analysis output builder.

This module builds the final output structure for holdings analysis,
including rankings and common holdings identification.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .aggregator import AggregatedData
from .data_processor import ProcessedFund


class HoldingsOutputBuilder:
    """Builds structured output for holdings analysis."""
    
    def __init__(self, params: Dict[str, Any]):
        self.max_companies = params.get("max_companies_in_results", 100)
    
    def build_category_output(self, category: str, aggregated_data: AggregatedData, 
                            processed_funds: List[ProcessedFund]) -> Dict[str, Any]:
        """Build the complete output structure for a category."""
        
        # Build fund references
        funds = [
            {"name": fund.name, "aum": fund.aum}
            for fund in processed_funds
        ]
        
        # Sort companies by different criteria
        companies_by_fund_count = self._sort_by_fund_count(aggregated_data.companies)
        companies_by_total_weight = self._sort_by_total_weight(aggregated_data.companies)
        common_in_all_funds = self._find_common_companies(aggregated_data.companies, len(processed_funds))
        
        return {
            "category": category,
            "total_files": len(processed_funds),
            "total_funds": len(aggregated_data.funds),
            "unique_companies": len(aggregated_data.companies),
            "funds": funds,
            "top_by_fund_count": companies_by_fund_count[:self.max_companies],
            "top_by_total_weight": companies_by_total_weight[:self.max_companies],
            "common_in_all_funds": common_in_all_funds
        }
    
    def _sort_by_fund_count(self, companies: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Sort companies by fund count (most popular first)."""
        sorted_companies = sorted(
            companies.values(),
            key=lambda x: (-x.fund_count, -x.total_weight, x.name)
        )
        
        return [
            {
                "company": company.name,
                "fund_count": company.fund_count,
                "total_weight": round(company.total_weight, 2),
                "avg_weight": round(company.avg_weight, 2),
                "sample_funds": company.sample_funds
            }
            for company in sorted_companies
        ]
    
    def _sort_by_total_weight(self, companies: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Sort companies by total weight (highest allocation first)."""
        sorted_companies = sorted(
            companies.values(),
            key=lambda x: (-x.total_weight, -x.fund_count, x.name)
        )
        
        return [
            {
                "company": company.name,
                "fund_count": company.fund_count,
                "total_weight": round(company.total_weight, 2),
                "avg_weight": round(company.avg_weight, 2),
                "sample_funds": company.sample_funds
            }
            for company in sorted_companies
        ]
    
    def _find_common_companies(self, companies: Dict[str, Any], total_funds: int) -> List[Dict[str, Any]]:
        """Find companies that appear in all funds."""
        common_companies = [
            company for company in companies.values()
            if company.fund_count == total_funds
        ]
        
        # Sort by total weight
        common_companies.sort(key=lambda x: (-x.total_weight, x.name))
        
        return [
            {
                "company": company.name,
                "fund_count": company.fund_count,
                "total_weight": round(company.total_weight, 2),
                "avg_weight": round(company.avg_weight, 2)
            }
            for company in common_companies
        ]
