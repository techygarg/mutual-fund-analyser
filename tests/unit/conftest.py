"""Shared test fixtures for unit tests."""

import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml

from mfa.config.settings import ConfigProvider


@pytest.fixture
def unit_test_config() -> Generator[dict[str, Any], None, None]:
    """Load unit test configuration."""
    config_path = Path(__file__).parent / "test_config.yaml"
    with open(config_path) as f:
        yield yaml.safe_load(f)


@pytest.fixture
def mock_config_provider(unit_test_config: dict[str, Any]) -> Generator[ConfigProvider, None, None]:
    """Mock ConfigProvider with unit test configuration."""
    with patch.object(ConfigProvider, "_config", unit_test_config):
        with patch.object(ConfigProvider, "_instance", None):
            yield ConfigProvider.get_instance()


@pytest.fixture
def temp_directory() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_fund_data() -> dict[str, Any]:
    """Sample fund data for testing."""
    return {
        "schema_version": "1.0",
        "extraction_timestamp": "2024-01-15T10:30:00",
        "source_url": "https://coin.zerodha.com/mf/fund/sample",
        "provider": "zerodha_coin",
        "data": {
            "fund_info": {
                "fund_name": "HDFC Top 100 Fund Direct Growth",
                "current_nav": "₹850.45",
                "cagr": "12.5%",
                "expense_ratio": "0.45%",
                "aum": "₹15,000 Cr",
                "fund_manager": "John Doe",
                "launch_date": "2010-01-01",
                "risk_level": "Moderate",
            },
            "top_holdings": [
                {
                    "rank": 1,
                    "company_name": "Reliance Industries Ltd",
                    "allocation_percentage": "8.50%",
                },
                {
                    "rank": 2,
                    "company_name": "Tata Consultancy Services Ltd",
                    "allocation_percentage": "6.25%",
                },
                {"rank": 3, "company_name": "HDFC Bank Ltd", "allocation_percentage": "5.80%"},
                {"rank": 4, "company_name": "Infosys Limited", "allocation_percentage": "4.90%"},
                {
                    "rank": 5,
                    "company_name": "CASH",  # Should be excluded
                    "allocation_percentage": "2.10%",
                },
            ],
        },
    }


@pytest.fixture
def sample_fund_data_minimal() -> dict[str, Any]:
    """Minimal fund data for edge case testing."""
    return {
        "data": {
            "fund_info": {"fund_name": "Simple Fund", "aum": "₹100 Cr"},
            "top_holdings": [
                {"rank": 1, "company_name": "Apple Inc", "allocation_percentage": "10.0%"}
            ],
        }
    }


@pytest.fixture
def sample_fund_data_empty() -> dict[str, Any]:
    """Empty fund data for error handling testing."""
    return {"data": {"fund_info": {}, "top_holdings": []}}


@pytest.fixture
def sample_fund_data_malformed() -> dict[str, Any]:
    """Malformed fund data for error handling testing."""
    return {
        "data": {
            "fund_info": {
                "fund_name": "Malformed Fund"
                # Missing other fields
            },
            "top_holdings": [
                {
                    "rank": 1,
                    "company_name": "Test Company",
                    "allocation_percentage": "invalid%",  # Invalid percentage
                },
                {
                    "rank": 2,
                    # Missing company_name
                    "allocation_percentage": "5.0%",
                },
            ],
        }
    }


@pytest.fixture
def multiple_funds_data() -> list[dict[str, Any]]:
    """Multiple fund data for aggregation testing."""
    return [
        {
            "data": {
                "fund_info": {"fund_name": "Large Cap Fund A", "aum": "₹5,000 Cr"},
                "top_holdings": [
                    {
                        "rank": 1,
                        "company_name": "Reliance Industries Ltd",
                        "allocation_percentage": "8.0%",
                    },
                    {"rank": 2, "company_name": "TCS Ltd", "allocation_percentage": "6.0%"},
                    {"rank": 3, "company_name": "HDFC Bank Ltd", "allocation_percentage": "5.0%"},
                ],
            }
        },
        {
            "data": {
                "fund_info": {"fund_name": "Large Cap Fund B", "aum": "₹3,000 Cr"},
                "top_holdings": [
                    {
                        "rank": 1,
                        "company_name": "Reliance Industries Ltd",
                        "allocation_percentage": "7.5%",
                    },  # Same company
                    {"rank": 2, "company_name": "Infosys Limited", "allocation_percentage": "6.5%"},
                    {"rank": 3, "company_name": "ICICI Bank Ltd", "allocation_percentage": "4.5%"},
                ],
            }
        },
        {
            "data": {
                "fund_info": {"fund_name": "Mid Cap Fund A", "aum": "₹1,500 Cr"},
                "top_holdings": [
                    {
                        "rank": 1,
                        "company_name": "Bajaj Finance Ltd",
                        "allocation_percentage": "9.0%",
                    },
                    {
                        "rank": 2,
                        "company_name": "Asian Paints Ltd",
                        "allocation_percentage": "7.0%",
                    },
                    {
                        "rank": 3,
                        "company_name": "Reliance Industries Ltd",
                        "allocation_percentage": "3.5%",
                    },  # Common across all
                ],
            }
        },
    ]


@pytest.fixture
def company_name_normalization_cases() -> list[tuple[str, str]]:
    """Test cases for company name normalization."""
    return [
        # (input, expected_output)
        ("Reliance Industries Ltd", "Reliance Industries"),
        ("Tata Consultancy Services Pvt. Ltd.", "Tata Consultancy Services"),
        ("HDFC Bank Limited", "HDFC Bank"),
        ("  Extra   Spaces  Corp  ", "Extra Spaces Corp"),
        ("Company & Associates Ltd", "Company & Associates"),
        ("Tech Corp Private Limited", "Tech Corp"),
        ("Simple Name", "Simple Name"),
        ("  .,:;-  Messy Corp  .,:;-  ", "Messy Corp"),
        ("", ""),  # Empty string
    ]


@pytest.fixture
def percentage_parsing_cases() -> list[tuple[str, float]]:
    """Test cases for percentage parsing."""
    return [
        # (input, expected_output)
        ("8.50%", 8.50),
        ("12.345%", 12.345),
        ("0.1%", 0.1),
        ("100%", 100.0),
        ("5%", 5.0),
        ("invalid%", 0.0),
        ("", 0.0),
        ("no percent", 0.0),
        ("123.45% extra text", 123.45),
        ("₹ 8.50%", 8.50),  # With currency symbol
    ]
