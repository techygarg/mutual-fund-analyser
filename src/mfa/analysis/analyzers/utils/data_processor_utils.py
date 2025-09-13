"""
Common utilities for data processors.

This module contains shared data processing utilities that are used across
different analysis types to ensure consistency and eliminate code duplication.
"""

from __future__ import annotations

import re


class DataProcessorUtils:
    """Common utilities for data processing across analyses."""

    # Precompiled regex patterns (module-level) for performance
    _SUFFIX_PATTERNS = [
        re.compile(r"\s+Limited\s*$", re.IGNORECASE),
        re.compile(r"\s+Ltd\.?\s*$", re.IGNORECASE),
        re.compile(r"\s+Pvt\.?\s*$", re.IGNORECASE),
        re.compile(r"\s+Private\s+Limited\s*$", re.IGNORECASE),
        re.compile(r"\s+Pvt\.?\s+Ltd\.?\s*$", re.IGNORECASE),
        re.compile(r"\s+Inc\.?\s*$", re.IGNORECASE),
        re.compile(r"\s+Corporation\s*$", re.IGNORECASE),
        re.compile(r"\s+Corp\.?\s*$", re.IGNORECASE),
        re.compile(r"\s+Company\s*$", re.IGNORECASE),
        re.compile(r"\s+Co\.?\s*$", re.IGNORECASE),
    ]

    _TRAILING_DOTS_SPACES_PATTERN = re.compile(r"[\.\s]+$")
    _PERCENT_WS_PATTERN = re.compile(r"[%\s]")

    @staticmethod
    def normalize_company_name(company_name: str) -> str:
        """
        Normalize company name by removing common suffixes and standardizing format.

        This helps avoid duplicate companies due to slight name variations.

        Args:
            company_name: Raw company name from fund data

        Returns:
            Normalized company name
        """
        if not company_name:
            return company_name

        # Remove leading/trailing whitespace
        normalized = company_name.strip()

        # Apply suffix removal using precompiled patterns
        for pattern in DataProcessorUtils._SUFFIX_PATTERNS:
            normalized = pattern.sub("", normalized)

        # Clean up any remaining trailing dots or spaces (precompiled)
        normalized = DataProcessorUtils._TRAILING_DOTS_SPACES_PATTERN.sub("", normalized)

        # Ensure we don't return empty string
        if not normalized.strip():
            return company_name

        return normalized.strip()

    @staticmethod
    def parse_percentage(percentage_str: str | None) -> float:
        """
        Parse percentage string to float value.

        Handles various percentage formats consistently across analyses.

        Args:
            percentage_str: Percentage string (e.g., "5.25%", "5.25")

        Returns:
            Float percentage value (5.25 for "5.25%")
        """
        if not percentage_str:
            return 0.0

        try:
            # Remove % sign and any whitespace
            clean_str = DataProcessorUtils._PERCENT_WS_PATTERN.sub("", str(percentage_str))
            return float(clean_str)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def parse_percentage_as_decimal(percentage_str: str | None) -> float:
        """
        Parse percentage string to decimal value (for portfolio calculations).

        Args:
            percentage_str: Percentage string (e.g., "5.25%")

        Returns:
            Decimal value (0.0525 for "5.25%")
        """
        if not percentage_str:
            return 0.0

        try:
            # Extract numeric part
            match = re.search(r"\d{1,3}(?:\.\d+)?", str(percentage_str))
            if not match:
                return 0.0
            return float(match.group(0)) / 100.0
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def parse_currency(currency_str: str | None) -> float:
        """
        Parse currency values from text.

        Handles various currency formats like "₹ 123.45", "Rs. 123.45", etc.

        Args:
            currency_str: Currency string to parse

        Returns:
            Float currency value
        """
        if not currency_str:
            return 0.0

        try:
            # Extract number from strings like "₹ 123.45" or "Rs. 123.45"
            match = re.search(r"[\d,.]+(?:\.\d+)?", str(currency_str))
            if not match:
                return 0.0
            return float(match.group(0).replace(",", ""))
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def is_excluded_holding(company_name: str, excluded_holdings: set[str]) -> bool:
        """
        Check if a company should be excluded from analysis.

        Args:
            company_name: Company name to check
            excluded_holdings: Set of excluded holding names

        Returns:
            True if company should be excluded
        """
        if not company_name or not excluded_holdings:
            return False

        company_upper = company_name.upper()
        return any(excluded.upper() in company_upper for excluded in excluded_holdings)
