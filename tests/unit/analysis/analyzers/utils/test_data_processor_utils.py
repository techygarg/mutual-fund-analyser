"""Unit tests for data processor utilities - core business logic only."""

import pytest

from mfa.analysis.analyzers.utils.data_processor_utils import DataProcessorUtils


class TestDataProcessorUtils:
    """Test DataProcessorUtils for essential data processing functionality."""

    class TestNormalizeCompanyName:
        """Test basic company name normalization."""

        def test_normalize_company_name_basic_cases(self):
            """Test basic company name normalization cases."""
            # Test core business cases
            assert (
                DataProcessorUtils.normalize_company_name("Reliance Industries Limited")
                == "Reliance Industries"
            )
            assert DataProcessorUtils.normalize_company_name("TCS Ltd") == "TCS"
            assert DataProcessorUtils.normalize_company_name("HDFC Bank Limited") == "HDFC Bank"

        def test_normalize_company_name_unchanged(self):
            """Test cases where company name should remain unchanged."""
            # Names without suffixes should stay the same
            assert DataProcessorUtils.normalize_company_name("Reliance") == "Reliance"
            assert DataProcessorUtils.normalize_company_name("TCS") == "TCS"
            assert DataProcessorUtils.normalize_company_name("HDFC Bank") == "HDFC Bank"

    class TestParsePercentageAsDecimal:
        """Test percentage parsing functionality."""

        def test_parse_percentage_basic_cases(self):
            """Test basic percentage parsing."""
            assert DataProcessorUtils.parse_percentage_as_decimal("10%") == 0.10
            assert DataProcessorUtils.parse_percentage_as_decimal("5.5%") == 0.055
            assert DataProcessorUtils.parse_percentage_as_decimal("100%") == 1.0

        def test_parse_percentage_edge_cases(self):
            """Test percentage parsing edge cases."""
            assert DataProcessorUtils.parse_percentage_as_decimal("0%") == 0.0
            assert DataProcessorUtils.parse_percentage_as_decimal("") == 0.0
            assert DataProcessorUtils.parse_percentage_as_decimal("invalid") == 0.0

    class TestParseCurrency:
        """Test currency parsing functionality."""

        def test_parse_currency_basic_cases(self):
            """Test basic currency parsing."""
            assert DataProcessorUtils.parse_currency("₹1000") == 1000.0
            assert DataProcessorUtils.parse_currency("₹1,500") == 1500.0
            assert DataProcessorUtils.parse_currency("₹10,000.50") == 10000.5

        def test_parse_currency_edge_cases(self):
            """Test currency parsing edge cases."""
            assert DataProcessorUtils.parse_currency("₹0") == 0.0
            assert DataProcessorUtils.parse_currency("") == 0.0
            assert DataProcessorUtils.parse_currency("invalid") == 0.0
