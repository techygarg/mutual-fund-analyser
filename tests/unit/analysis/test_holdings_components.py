"""Unit tests for individual holdings analysis components with dependency injection."""

from unittest.mock import Mock
from typing import Any, Dict

import pytest

from mfa.analysis.analyzers.holdings import (
    HoldingsDataProcessor,
    HoldingsAggregator,
    HoldingsOutputBuilder,
    ProcessedFund,
    ProcessedHolding,
    AggregatedData,
    CompanyData
)
from mfa.config.settings import ConfigProvider


class TestHoldingsDataProcessor:
    """Test HoldingsDataProcessor with dependency injection."""

    @pytest.fixture
    def mock_config_provider(self) -> Mock:
        """Mock ConfigProvider for testing."""
        config_provider = Mock(spec=ConfigProvider)

        mock_config = Mock()
        mock_config.analyses = {
            "holdings": Mock(
                params=Mock(
                    exclude_from_analysis=["CASH", "TREPS", "T-BILLS"],
                    max_sample_funds_per_company=3,
                    max_companies_in_results=5
                )
            )
        }

        # Add paths to prevent mock object directory creation
        mock_config.paths = Mock()
        mock_config.paths.output_dir = "/tmp/test_output"
        mock_config.paths.analysis_dir = "/tmp/test_analysis"

        config_provider.get_config.return_value = mock_config
        return config_provider

    @pytest.fixture
    def sample_fund_json(self) -> Dict[str, Any]:
        """Sample fund JSON data for testing."""
        return {
            "data": {
                "fund_info": {
                    "fund_name": "Test Fund",
                    "aum": "₹1000 Cr"
                },
                "top_holdings": [
                    {"rank": 1, "company_name": "Reliance Industries", "allocation_percentage": "8.5%"},
                    {"rank": 2, "company_name": "TCS Ltd", "allocation_percentage": "6.2%"},
                    {"rank": 3, "company_name": "CASH", "allocation_percentage": "2.1%"},  # Should be excluded
                    {"rank": 4, "company_name": "TREPS", "allocation_percentage": "1.5%"}  # Should be excluded
                ]
            }
        }

    def test_initialization_with_di(self, mock_config_provider: Mock):
        """Test DataProcessor initializes correctly with dependency injection."""
        processor = HoldingsDataProcessor(mock_config_provider)

        assert processor.config_provider is mock_config_provider

    def test_process_fund_jsons_excludes_configured_holdings(self, mock_config_provider: Mock, sample_fund_json: Dict[str, Any]):
        """Test processing excludes holdings based on configuration."""
        processor = HoldingsDataProcessor(mock_config_provider)

        result = processor.process_fund_jsons([sample_fund_json])

        assert len(result) == 1
        fund = result[0]
        assert fund.name == "Test Fund"

        # Should only include non-excluded holdings
        holdings = fund.holdings
        assert len(holdings) == 2  # CASH and TREPS excluded

        company_names = [h.company_name for h in holdings]
        assert "Reliance Industries" in company_names
        assert "TCS Ltd" in company_names
        assert "CASH" not in company_names
        assert "TREPS" not in company_names

    def test_process_fund_jsons_handles_empty_data(self, mock_config_provider: Mock):
        """Test processing handles empty fund data gracefully."""
        processor = HoldingsDataProcessor(mock_config_provider)

        result = processor.process_fund_jsons([])

        assert result == []

    def test_process_fund_jsons_handles_malformed_data(self, mock_config_provider: Mock):
        """Test processing handles malformed data gracefully."""
        processor = HoldingsDataProcessor(mock_config_provider)

        malformed_data = [{"data": {}}]  # Missing required fields

        # Should handle gracefully without crashing
        result = processor.process_fund_jsons(malformed_data)

        # Should return empty list or skip invalid data
        assert isinstance(result, list)


class TestHoldingsAggregator:
    """Test HoldingsAggregator with dependency injection."""

    @pytest.fixture
    def mock_config_provider(self) -> Mock:
        """Mock ConfigProvider for testing."""
        config_provider = Mock(spec=ConfigProvider)

        mock_config = Mock()
        mock_config.analyses = {
            "holdings": Mock(
                params=Mock(
                    max_sample_funds_per_company=3
                )
            )
        }

        config_provider.get_config.return_value = mock_config
        return config_provider

    @pytest.fixture
    def sample_processed_funds(self) -> list:
        """Sample processed funds for testing."""
        return [
            ProcessedFund(
                name="Fund A",
                aum="₹1000 Cr",
                holdings=[
                    ProcessedHolding("Company X", 5.0, 1),
                    ProcessedHolding("Company Y", 3.0, 2),
                ]
            ),
            ProcessedFund(
                name="Fund B",
                aum="₹2000 Cr",
                holdings=[
                    ProcessedHolding("Company X", 4.0, 1),
                    ProcessedHolding("Company Z", 6.0, 2),
                ]
            )
        ]

    def test_initialization_with_di(self, mock_config_provider: Mock):
        """Test Aggregator initializes correctly with dependency injection."""
        aggregator = HoldingsAggregator(mock_config_provider)

        assert aggregator.config_provider is mock_config_provider

    def test_aggregate_holdings_combines_data_correctly(self, mock_config_provider: Mock, sample_processed_funds: list):
        """Test aggregation combines holdings data across funds."""
        aggregator = HoldingsAggregator(mock_config_provider)

        result = aggregator.aggregate_holdings(sample_processed_funds)

        assert isinstance(result, AggregatedData)

        # Check Company X appears in both funds
        assert "Company X" in result.companies
        company_x = result.companies["Company X"]
        assert company_x.fund_count == 2  # Appears in both funds
        assert company_x.total_weight == 9.0  # 5.0 + 4.0
        assert company_x.average_weight == 4.5  # 9.0 / 2

        # Check Company Y appears in only one fund
        assert "Company Y" in result.companies
        company_y = result.companies["Company Y"]
        assert company_y.fund_count == 1
        assert company_y.total_weight == 3.0

        # Check sample funds are limited by config
        assert len(company_x.sample_funds) <= 3  # max_sample_funds_per_company

    def test_aggregate_holdings_handles_empty_input(self, mock_config_provider: Mock):
        """Test aggregation handles empty input gracefully."""
        aggregator = HoldingsAggregator(mock_config_provider)

        result = aggregator.aggregate_holdings([])

        assert isinstance(result, AggregatedData)
        assert result.companies == {}
        assert result.funds_info == {}

    def test_aggregate_holdings_uses_config_limits(self, mock_config_provider: Mock):
        """Test aggregation respects configuration limits."""
        # Configure small limit
        mock_config = mock_config_provider.get_config.return_value
        mock_config.analyses["holdings"].params.max_sample_funds_per_company = 1

        aggregator = HoldingsAggregator(mock_config_provider)

        # Create funds with many overlapping holdings
        funds = []
        for i in range(5):  # 5 funds
            holdings = [ProcessedHolding("Company X", 1.0, j) for j in range(3)]  # 3 holdings each
            funds.append(ProcessedFund(f"Fund {i}", "₹100 Cr", holdings))

        result = aggregator.aggregate_holdings(funds)

        # Should limit samples per company
        company_x = result.companies["Company X"]
        assert len(company_x.sample_funds) <= 1  # Limited by config


class TestHoldingsOutputBuilder:
    """Test HoldingsOutputBuilder with dependency injection."""

    @pytest.fixture
    def mock_config_provider(self) -> Mock:
        """Mock ConfigProvider for testing."""
        config_provider = Mock(spec=ConfigProvider)

        mock_config = Mock()
        mock_config.analyses = {
            "holdings": Mock(
                params=Mock(
                    max_companies_in_results=5
                )
            )
        }

        config_provider.get_config.return_value = mock_config
        return config_provider

    @pytest.fixture
    def sample_aggregated_data(self) -> AggregatedData:
        """Sample aggregated data for testing."""
        companies = {
            "Company A": CompanyData("Company A", 3, 15.0, 5.0, ["Fund1", "Fund2", "Fund3"]),
            "Company B": CompanyData("Company B", 2, 8.0, 4.0, ["Fund1", "Fund2"]),
            "Company C": CompanyData("Company C", 1, 3.0, 3.0, ["Fund3"]),
        }

        funds_info = {
            "Fund1": {"name": "Fund 1", "aum": "₹1000 Cr"},
            "Fund2": {"name": "Fund 2", "aum": "₹2000 Cr"},
            "Fund3": {"name": "Fund 3", "aum": "₹1500 Cr"},
        }

        return AggregatedData(companies, funds_info)

    def test_initialization_with_di(self, mock_config_provider: Mock):
        """Test OutputBuilder initializes correctly with dependency injection."""
        builder = HoldingsOutputBuilder(mock_config_provider)

        assert builder.config_provider is mock_config_provider

    def test_build_category_output_structures_data_correctly(self, mock_config_provider: Mock, sample_aggregated_data: AggregatedData):
        """Test output building creates correct data structure."""
        builder = HoldingsOutputBuilder(mock_config_provider)

        result = builder.build_category_output("largeCap", sample_aggregated_data)

        # Verify structure
        assert isinstance(result, dict)
        assert "funds" in result
        assert "companies" in result
        assert "summary" in result
        assert "category" in result

        # Verify funds data
        assert len(result["funds"]) == 3
        assert result["funds"][0]["name"] == "Fund 1"

        # Verify companies are sorted by fund count
        assert len(result["companies"]) == 3  # All companies included
        assert result["companies"][0]["name"] == "Company A"  # Most funds (3)
        assert result["companies"][1]["name"] == "Company B"  # Second most (2)

    def test_build_category_output_respects_config_limits(self, mock_config_provider: Mock, sample_aggregated_data: AggregatedData):
        """Test output building respects configuration limits."""
        # Configure small limit
        mock_config = mock_config_provider.get_config.return_value
        mock_config.analyses["holdings"].params.max_companies_in_results = 2

        builder = HoldingsOutputBuilder(mock_config_provider)

        result = builder.build_category_output("largeCap", sample_aggregated_data)

        # Should limit number of companies
        assert len(result["companies"]) <= 2

    def test_build_category_output_includes_summary(self, mock_config_provider: Mock, sample_aggregated_data: AggregatedData):
        """Test output includes proper summary information."""
        builder = HoldingsOutputBuilder(mock_config_provider)

        result = builder.build_category_output("largeCap", sample_aggregated_data)

        assert "summary" in result
        summary = result["summary"]
        assert "total_companies" in summary
        assert "total_funds" in summary
        assert "companies_in_results" in summary
        assert summary["total_funds"] == 3
        assert summary["total_companies"] == 3
        assert result["category"] == "largeCap"
