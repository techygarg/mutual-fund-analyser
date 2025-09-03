"""
Holdings data processor with dependency injection.

This module handles processing raw fund JSON data into clean,
structured holdings data for analysis using proper dependency injection.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List

from mfa.config.settings import ConfigProvider
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

    def __init__(self, config_provider: ConfigProvider):
        """
        Initialize processor with dependency injection.

        Args:
            config_provider: Configuration provider instance
        """
        self.config_provider = config_provider

    def process_fund_jsons(self, fund_jsons: List[Dict[str, Any]]) -> List[ProcessedFund]:
        """
        Process a list of fund JSON objects into structured data.

        Reads configuration directly from ConfigProvider instead of receiving params.

        Args:
            fund_jsons: List of fund data dictionaries

        Returns:
            List of ProcessedFund objects
        """
        # Read configuration directly
        config = self.config_provider.get_config()
        holdings_config = config.analyses["holdings"]
        excluded_holdings = set(holdings_config.params.exclude_from_analysis or [])
        processed_funds = []
        
        for fund_json in fund_jsons:
            try:
                processed_fund = self._process_single_fund(fund_json, excluded_holdings)
                if processed_fund:
                    processed_funds.append(processed_fund)
            except Exception as e:
                logger.warning(f"Failed to process fund: {e}")
                continue
        
        logger.debug(f"Processed {len(processed_funds)} funds from {len(fund_jsons)} JSON files")
        return processed_funds
    
    def _process_single_fund(self, fund_json: Dict, excluded_holdings: set) -> ProcessedFund | None:
        """Process a single fund JSON into structured data."""
        try:
            # Extract fund info
            fund_data = fund_json.get("data", {})
            fund_info = fund_data.get("fund_info", {})
            top_holdings = fund_data.get("top_holdings", [])
            
            fund_name = fund_info.get("fund_name", "Unknown Fund")
            aum = fund_info.get("aum", "N/A")
            
            # Process holdings
            processed_holdings = []
            for holding_data in top_holdings:
                company_name = holding_data.get("company_name", "").strip()
                
                # Skip excluded holdings
                if self._is_excluded_holding(company_name, excluded_holdings):
                    continue
                
                # Parse allocation percentage
                allocation_str = holding_data.get("allocation_percentage", "0%")
                allocation_pct = self._parse_percentage(allocation_str)
                
                # Get rank
                rank = holding_data.get("rank", 0)
                
                if company_name and allocation_pct > 0:
                    processed_holdings.append(ProcessedHolding(
                        company_name=company_name,
                        allocation_percentage=allocation_pct,
                        rank=rank
                    ))
            
            if processed_holdings:
                return ProcessedFund(
                    name=fund_name,
                    aum=aum,
                    holdings=processed_holdings
                )
            
        except Exception as e:
            logger.warning(f"Error processing fund {fund_json.get('source_url', 'unknown')}: {e}")
        
        return None
    
    def _is_excluded_holding(self, company_name: str, excluded_holdings: set) -> bool:
        """Check if a holding should be excluded from analysis."""
        company_upper = company_name.upper()
        return any(excluded.upper() in company_upper for excluded in excluded_holdings)
    
    def _parse_percentage(self, percentage_str: str) -> float:
        """Parse percentage string to float value."""
        try:
            # Remove % sign and any whitespace
            clean_str = re.sub(r'[%\s]', '', percentage_str)
            return float(clean_str)
        except (ValueError, TypeError):
            return 0.0