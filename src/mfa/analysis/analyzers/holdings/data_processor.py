"""
Holdings data processor.

This module handles processing raw fund JSON data into clean,
structured holdings data for analysis.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List

from mfa.logging.logger import logger


@dataclass
class ProcessedFund:
    """Represents a processed fund with clean data."""
    name: str
    aum: str
    holdings: List['ProcessedHolding']


@dataclass 
class ProcessedHolding:
    """Represents a processed holding with normalized data."""
    company_name: str
    allocation_percentage: float
    rank: int


class HoldingsDataProcessor:
    """Processes raw fund JSON data into structured holdings."""
    
    def __init__(self, params: Dict[str, Any]):
        self.excluded_holdings = set(params.get("exclude_from_analysis", []))
    
    def process_fund_jsons(self, fund_jsons: List[Dict]) -> List[ProcessedFund]:
        """Process a list of fund JSON objects into structured data."""
        processed_funds = []
        
        for fund_json in fund_jsons:
            try:
                processed_fund = self._process_single_fund(fund_json)
                if processed_fund:
                    processed_funds.append(processed_fund)
            except Exception as e:
                logger.warning(f"Failed to process fund: {e}")
                continue
        
        logger.debug(f"Processed {len(processed_funds)} funds from {len(fund_jsons)} JSON files")
        return processed_funds
    
    def _process_single_fund(self, fund_json: Dict) -> ProcessedFund:
        """Process a single fund JSON into structured data."""
        data = fund_json.get("data", {})
        fund_info = data.get("fund_info", {})
        holdings = data.get("top_holdings", [])
        
        fund_name = fund_info.get("fund_name", "Unknown Fund")
        aum = fund_info.get("aum", "")
        
        processed_holdings = []
        for holding in holdings:
            processed_holding = self._process_single_holding(holding)
            if processed_holding and self._is_valid_holding(processed_holding):
                processed_holdings.append(processed_holding)
        
        return ProcessedFund(
            name=fund_name,
            aum=aum,
            holdings=processed_holdings
        )
    
    def _process_single_holding(self, holding: Dict) -> ProcessedHolding:
        """Process a single holding into structured data."""
        company_name = self._normalize_company_name(holding.get("company_name", ""))
        percentage = self._parse_percentage(holding.get("allocation_percentage", ""))
        rank = holding.get("rank", 0)
        
        return ProcessedHolding(
            company_name=company_name,
            allocation_percentage=percentage,
            rank=rank
        )
    
    def _is_valid_holding(self, holding: ProcessedHolding) -> bool:
        """Check if a holding should be included in analysis."""
        if not holding.company_name:
            return False
        return holding.company_name.upper() not in self.excluded_holdings
    
    def _normalize_company_name(self, name: str) -> str:
        """Normalize company name for consistent analysis."""
        if not name:
            return ""
        
        # Remove extra whitespace and normalize case
        normalized = re.sub(r'\s+', ' ', name.strip())
        return normalized.title()
    
    def _parse_percentage(self, percentage_str: str) -> float:
        """Parse percentage string to float value."""
        try:
            # Remove % sign and convert to float
            clean_str = str(percentage_str).replace('%', '').strip()
            return float(clean_str)
        except (ValueError, TypeError):
            return 0.0
