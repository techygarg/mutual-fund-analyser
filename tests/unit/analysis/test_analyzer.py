"""Unit tests for FundAnalyzer - core business logic testing."""

import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import pytest

from mfa.analysis.analyzer import (
    AnalysisError,
    AnalysisResult,
    CompanyAnalysis,
    FundAnalysisResult,
    FundAnalyzer,
    HoldingsData,
)
from mfa.config.settings import ConfigProvider
from mfa.storage.json_store import JsonStore


class TestDataClasses:
    """Test data classes and their properties."""

    def test_analysis_result_average_companies_per_fund_normal(self):
        """Test average companies per fund calculation."""
        result = AnalysisResult(
            category="largeCap",
            total_files=5,
            total_funds=5,
            unique_companies=50,
            output_file=Path("test.json"),
        )
        assert result.average_companies_per_fund == 10.0

    def test_analysis_result_average_companies_per_fund_zero_funds(self):
        """Test average calculation with zero funds."""
        result = AnalysisResult(
            category="largeCap",
            total_files=0,
            total_funds=0,
            unique_companies=0,
            output_file=Path("test.json"),
        )
        assert result.average_companies_per_fund == 0.0

    def test_fund_analysis_result_success_rate_normal(self):
        """Test success rate calculation."""
        result = FundAnalysisResult(
            categories_analyzed=8,
            total_categories=10,
            category_results=[],
            output_directory=Path("output"),
        )
        assert result.success_rate == 80.0

    def test_fund_analysis_result_success_rate_zero_total(self):
        """Test success rate with zero total categories."""
        result = FundAnalysisResult(
            categories_analyzed=0,
            total_categories=0,
            category_results=[],
            output_directory=Path("output"),
        )
        assert result.success_rate == 0.0

    def test_holdings_data_properties(self):
        """Test HoldingsData calculated properties."""
        holdings_data = HoldingsData(
            company_to_funds={"Company A": {"Fund 1", "Fund 2"}, "Company B": {"Fund 1"}},
            company_total_weights={"Company A": 15.5, "Company B": 8.0},
            company_examples={},
            funds_info={"Fund 1": "₹1000 Cr", "Fund 2": "₹500 Cr"},
            processed_files_count=2,
            skipped_files_count=0,
        )

        assert holdings_data.total_funds == 2
        assert holdings_data.unique_companies_count == 2


class TestFundAnalyzer:
    """Test FundAnalyzer business logic methods."""

    def test_get_analysis_settings(self, mock_config_provider: ConfigProvider):
        """Test analysis settings extraction from config."""
        analyzer = FundAnalyzer()
        settings = analyzer._get_analysis_settings()

        assert settings["max_companies"] == 10  # From test config
        assert settings["max_samples"] == 3  # From test config
        assert "TREPS" in settings["excluded_holdings"]
        assert "CASH" in settings["excluded_holdings"]

    def test_normalize_company_name_standard_cases(self, company_name_normalization_cases):
        """Test company name normalization with standard cases."""
        analyzer = FundAnalyzer()

        for input_name, expected_output in company_name_normalization_cases:
            result = analyzer._normalize_company_name(input_name)
            assert result == expected_output, (
                f"Input: '{input_name}' -> Expected: '{expected_output}', Got: '{result}'"
            )

    def test_parse_percentage_standard_cases(self, percentage_parsing_cases):
        """Test percentage parsing with various input formats."""
        analyzer = FundAnalyzer()

        for input_percentage, expected_output in percentage_parsing_cases:
            result = analyzer._parse_percentage(input_percentage)
            assert result == expected_output, (
                f"Input: '{input_percentage}' -> Expected: {expected_output}, Got: {result}"
            )

    def test_is_valid_company_normal_company(self, mock_config_provider: ConfigProvider):
        """Test company validation for normal companies."""
        analyzer = FundAnalyzer()

        assert analyzer._is_valid_company("Apple Inc") is True
        assert analyzer._is_valid_company("Microsoft Corp") is True

    def test_is_valid_company_excluded_companies(self, mock_config_provider: ConfigProvider):
        """Test company validation for excluded companies."""
        analyzer = FundAnalyzer()

        assert analyzer._is_valid_company("CASH") is False
        assert analyzer._is_valid_company("TREPS") is False
        assert analyzer._is_valid_company("T-BILLS") is False
        assert analyzer._is_valid_company("cash") is False  # Case insensitive

    def test_is_valid_company_empty_name(self, mock_config_provider: ConfigProvider):
        """Test company validation for empty names."""
        analyzer = FundAnalyzer()

        assert analyzer._is_valid_company("") is False
        # Note: whitespace-only strings are handled by normalization, not empty check
        assert analyzer._is_valid_company("   ") is True  # Will be normalized to empty later

    def test_extract_fund_info_complete_data(self, sample_fund_data: dict[str, Any]):
        """Test fund info extraction with complete data."""
        analyzer = FundAnalyzer()
        json_file = Path("test_fund.json")

        result = analyzer._extract_fund_info(sample_fund_data, json_file)

        assert result["name"] == "HDFC Top 100 Fund Direct Growth"
        assert result["aum"] == "₹15,000 Cr"

    def test_extract_fund_info_minimal_data(self, sample_fund_data_minimal: dict[str, Any]):
        """Test fund info extraction with minimal data."""
        analyzer = FundAnalyzer()
        json_file = Path("simple_fund.json")

        result = analyzer._extract_fund_info(sample_fund_data_minimal, json_file)

        assert result["name"] == "Simple Fund"
        assert result["aum"] == "₹100 Cr"

    def test_extract_fund_info_missing_data(self, sample_fund_data_empty: dict[str, Any]):
        """Test fund info extraction with missing data."""
        analyzer = FundAnalyzer()
        json_file = Path("empty_fund.json")

        result = analyzer._extract_fund_info(sample_fund_data_empty, json_file)

        assert result["name"] == "empty_fund"  # Falls back to filename
        assert result["aum"] == ""  # Empty string for missing AUM

    def test_update_fund_registry_new_fund(self, mock_config_provider: ConfigProvider):
        """Test updating fund registry with new fund."""
        analyzer = FundAnalyzer()

        holdings_data = HoldingsData(
            company_to_funds=defaultdict(set),
            company_total_weights=defaultdict(float),
            company_examples=defaultdict(list),
            funds_info={},
            processed_files_count=0,
            skipped_files_count=0,
        )

        fund_info = {"name": "Test Fund", "aum": "₹1000 Cr"}
        analyzer._update_fund_registry(fund_info, holdings_data)

        assert "Test Fund" in holdings_data.funds_info
        assert holdings_data.funds_info["Test Fund"] == "₹1000 Cr"

    def test_update_fund_registry_duplicate_fund(self, mock_config_provider: ConfigProvider):
        """Test updating fund registry with duplicate fund (should not overwrite)."""
        analyzer = FundAnalyzer()

        holdings_data = HoldingsData(
            company_to_funds=defaultdict(set),
            company_total_weights=defaultdict(float),
            company_examples=defaultdict(list),
            funds_info={"Test Fund": "₹1000 Cr"},
            processed_files_count=0,
            skipped_files_count=0,
        )

        fund_info = {"name": "Test Fund", "aum": "₹2000 Cr"}  # Different AUM
        analyzer._update_fund_registry(fund_info, holdings_data)

        # Should not overwrite
        assert holdings_data.funds_info["Test Fund"] == "₹1000 Cr"

    def test_update_company_data_new_company(self, mock_config_provider: ConfigProvider):
        """Test updating company data with new company."""
        analyzer = FundAnalyzer()

        holdings_data = HoldingsData(
            company_to_funds=defaultdict(set),
            company_total_weights=defaultdict(float),
            company_examples=defaultdict(list),
            funds_info={},
            processed_files_count=0,
            skipped_files_count=0,
        )

        analyzer._update_company_data("Apple Inc", "Tech Fund", 8.5, holdings_data)

        assert "Tech Fund" in holdings_data.company_to_funds["Apple Inc"]
        assert holdings_data.company_total_weights["Apple Inc"] == 8.5
        assert "Tech Fund" in holdings_data.company_examples["Apple Inc"]

    def test_update_company_data_existing_company(self, mock_config_provider: ConfigProvider):
        """Test updating company data with existing company from different fund."""
        analyzer = FundAnalyzer()

        holdings_data = HoldingsData(
            company_to_funds=defaultdict(set),
            company_total_weights=defaultdict(float),
            company_examples=defaultdict(list),
            funds_info={},
            processed_files_count=0,
            skipped_files_count=0,
        )

        # Add first fund
        analyzer._update_company_data("Apple Inc", "Tech Fund A", 8.5, holdings_data)
        # Add second fund
        analyzer._update_company_data("Apple Inc", "Tech Fund B", 6.0, holdings_data)

        assert len(holdings_data.company_to_funds["Apple Inc"]) == 2
        assert "Tech Fund A" in holdings_data.company_to_funds["Apple Inc"]
        assert "Tech Fund B" in holdings_data.company_to_funds["Apple Inc"]
        assert holdings_data.company_total_weights["Apple Inc"] == 14.5  # 8.5 + 6.0

    def test_update_company_data_max_samples_limit(self, mock_config_provider: ConfigProvider):
        """Test that company examples respect max samples limit."""
        analyzer = FundAnalyzer()

        holdings_data = HoldingsData(
            company_to_funds=defaultdict(set),
            company_total_weights=defaultdict(float),
            company_examples=defaultdict(list),
            funds_info={},
            processed_files_count=0,
            skipped_files_count=0,
        )

        # Add more funds than max_samples (3 in test config)
        for i in range(5):
            analyzer._update_company_data("Popular Company", f"Fund {i}", 5.0, holdings_data)

        # Should only keep first 3 (max_samples from config)
        assert len(holdings_data.company_examples["Popular Company"]) == 3

    def test_process_fund_holdings_valid_holdings(self, mock_config_provider: ConfigProvider):
        """Test processing fund holdings with valid data."""
        analyzer = FundAnalyzer()

        holdings_data = HoldingsData(
            company_to_funds=defaultdict(set),
            company_total_weights=defaultdict(float),
            company_examples=defaultdict(list),
            funds_info={},
            processed_files_count=0,
            skipped_files_count=0,
        )

        holdings = [
            {"company_name": "Apple Inc", "allocation_percentage": "8.5%"},
            {"company_name": "Microsoft Corp", "allocation_percentage": "6.0%"},
            {"company_name": "CASH", "allocation_percentage": "2.0%"},  # Should be excluded
        ]

        analyzer._process_fund_holdings(holdings, "Tech Fund", holdings_data)

        # Should only process valid companies (not CASH)
        assert len(holdings_data.company_to_funds) == 2
        assert "Apple Inc" in holdings_data.company_to_funds
        assert "Microsoft Corp" in holdings_data.company_to_funds
        assert "CASH" not in holdings_data.company_to_funds

    def test_build_companies_by_fund_count(self, mock_config_provider: ConfigProvider):
        """Test building companies list sorted by fund count."""
        analyzer = FundAnalyzer()

        holdings_data = HoldingsData(
            company_to_funds={
                "Popular Company": {"Fund A", "Fund B", "Fund C"},  # 3 funds
                "Moderate Company": {"Fund A", "Fund B"},  # 2 funds
                "Rare Company": {"Fund A"},  # 1 fund
            },
            company_total_weights={
                "Popular Company": 24.0,  # 8.0 avg per fund
                "Moderate Company": 15.0,  # 7.5 avg per fund
                "Rare Company": 5.0,  # 5.0 avg per fund
            },
            company_examples={
                "Popular Company": ["Fund A", "Fund B", "Fund C"],
                "Moderate Company": ["Fund A", "Fund B"],
                "Rare Company": ["Fund A"],
            },
            funds_info={},
            processed_files_count=0,
            skipped_files_count=0,
        )

        result = analyzer._build_companies_by_fund_count(holdings_data)

        # Should be sorted by fund_count (desc), then total_weight (desc)
        assert len(result) == 3
        assert result[0].name == "Popular Company"
        assert result[0].fund_count == 3
        assert result[0].total_weight == 24.0
        assert result[0].avg_weight == 8.0

        assert result[1].name == "Moderate Company"
        assert result[1].fund_count == 2

        assert result[2].name == "Rare Company"
        assert result[2].fund_count == 1

    def test_build_companies_by_total_weight(self, mock_config_provider: ConfigProvider):
        """Test building companies list sorted by total weight."""
        analyzer = FundAnalyzer()

        holdings_data = HoldingsData(
            company_to_funds={
                "Heavy Weight": {"Fund A"},  # 1 fund, high weight
                "Medium Weight": {"Fund A", "Fund B"},  # 2 funds, medium total
                "Light Weight": {"Fund A", "Fund B", "Fund C"},  # 3 funds, low total
            },
            company_total_weights={
                "Heavy Weight": 25.0,  # Highest total weight
                "Medium Weight": 18.0,  # Medium total weight
                "Light Weight": 12.0,  # Lowest total weight
            },
            company_examples={
                "Heavy Weight": ["Fund A"],
                "Medium Weight": ["Fund A", "Fund B"],
                "Light Weight": ["Fund A", "Fund B", "Fund C"],
            },
            funds_info={},
            processed_files_count=0,
            skipped_files_count=0,
        )

        result = analyzer._build_companies_by_total_weight(holdings_data)

        # Should be sorted by total_weight (desc), then fund_count (desc)
        assert len(result) == 3
        assert result[0].name == "Heavy Weight"
        assert result[0].total_weight == 25.0

        assert result[1].name == "Medium Weight"
        assert result[1].total_weight == 18.0

        assert result[2].name == "Light Weight"
        assert result[2].total_weight == 12.0

    def test_find_companies_in_all_funds_with_common_companies(
        self, mock_config_provider: ConfigProvider
    ):
        """Test finding companies that appear in all funds."""
        analyzer = FundAnalyzer()

        holdings_data = HoldingsData(
            company_to_funds={
                "Universal Company": {"Fund A", "Fund B", "Fund C"},  # In all 3 funds
                "Popular Company": {"Fund A", "Fund B"},  # In 2 funds
                "Rare Company": {"Fund A"},  # In 1 fund
            },
            company_total_weights={
                "Universal Company": 30.0,
                "Popular Company": 20.0,
                "Rare Company": 10.0,
            },
            company_examples={},
            funds_info={"Fund A": "", "Fund B": "", "Fund C": ""},  # 3 total funds
            processed_files_count=0,
            skipped_files_count=0,
        )

        result = analyzer._find_companies_in_all_funds(holdings_data)

        assert len(result) == 1
        assert result[0].name == "Universal Company"
        assert result[0].fund_count == 3

    def test_find_companies_in_all_funds_no_common_companies(
        self, mock_config_provider: ConfigProvider
    ):
        """Test finding companies when none appear in all funds."""
        analyzer = FundAnalyzer()

        holdings_data = HoldingsData(
            company_to_funds={
                "Company A": {"Fund A", "Fund B"},  # Missing Fund C
                "Company B": {"Fund A", "Fund C"},  # Missing Fund B
                "Company C": {"Fund B", "Fund C"},  # Missing Fund A
            },
            company_total_weights={
                "Company A": 20.0,
                "Company B": 15.0,
                "Company C": 18.0,
            },
            company_examples={},
            funds_info={"Fund A": "", "Fund B": "", "Fund C": ""},  # 3 total funds
            processed_files_count=0,
            skipped_files_count=0,
        )

        result = analyzer._find_companies_in_all_funds(holdings_data)

        assert len(result) == 0

    def test_find_companies_in_all_funds_zero_funds(self, mock_config_provider: ConfigProvider):
        """Test finding companies when there are zero funds."""
        analyzer = FundAnalyzer()

        holdings_data = HoldingsData(
            company_to_funds={},
            company_total_weights={},
            company_examples={},
            funds_info={},  # 0 total funds
            processed_files_count=0,
            skipped_files_count=0,
        )

        result = analyzer._find_companies_in_all_funds(holdings_data)

        assert len(result) == 0

    def test_build_funds_list(self, mock_config_provider: ConfigProvider):
        """Test building sorted funds list."""
        analyzer = FundAnalyzer()

        funds_info = {
            "Z Fund": "₹1000 Cr",
            "A Fund": "₹2000 Cr",
            "M Fund": "₹1500 Cr",
        }

        result = analyzer._build_funds_list(funds_info)

        # Should be sorted alphabetically
        assert len(result) == 3
        assert result[0]["name"] == "A Fund"
        assert result[0]["aum"] == "₹2000 Cr"
        assert result[1]["name"] == "M Fund"
        assert result[2]["name"] == "Z Fund"


class TestFundAnalyzerFileProcessing:
    """Test file processing methods with actual file operations."""

    def test_process_single_fund_file_valid_file(
        self,
        mock_config_provider: ConfigProvider,
        sample_fund_data: dict[str, Any],
        temp_directory: Path,
    ):
        """Test processing a valid fund file."""
        analyzer = FundAnalyzer()

        # Create test file
        test_file = temp_directory / "test_fund.json"
        JsonStore.save(sample_fund_data, test_file)

        holdings_data = HoldingsData(
            company_to_funds=defaultdict(set),
            company_total_weights=defaultdict(float),
            company_examples=defaultdict(list),
            funds_info={},
            processed_files_count=0,
            skipped_files_count=0,
        )

        analyzer._process_single_fund_file(test_file, holdings_data)

        # Verify processing results
        assert holdings_data.processed_files_count == 1
        assert holdings_data.skipped_files_count == 0
        assert "HDFC Top 100 Fund Direct Growth" in holdings_data.funds_info

        # Should have processed valid companies (excluding CASH)
        assert "Reliance Industries" in holdings_data.company_to_funds  # Normalized name
        assert "Tata Consultancy Services" in holdings_data.company_to_funds  # Normalized name
        assert "HDFC Bank" in holdings_data.company_to_funds  # Normalized name
        assert "Infosys" in holdings_data.company_to_funds  # Normalized name
        assert "CASH" not in holdings_data.company_to_funds  # Excluded

    def test_process_single_fund_file_invalid_file(
        self, mock_config_provider: ConfigProvider, temp_directory: Path
    ):
        """Test processing an invalid/non-existent file."""
        analyzer = FundAnalyzer()

        # Non-existent file
        invalid_file = temp_directory / "nonexistent.json"

        holdings_data = HoldingsData(
            company_to_funds=defaultdict(set),
            company_total_weights=defaultdict(float),
            company_examples=defaultdict(list),
            funds_info={},
            processed_files_count=0,
            skipped_files_count=0,
        )

        analyzer._process_single_fund_file(invalid_file, holdings_data)

        # Should skip invalid file
        assert holdings_data.processed_files_count == 0
        assert holdings_data.skipped_files_count == 1

    def test_build_analysis_output_complete(self, mock_config_provider: ConfigProvider):
        """Test building complete analysis output."""
        analyzer = FundAnalyzer()

        holdings_data = HoldingsData(
            company_to_funds={
                "Company A": {"Fund 1", "Fund 2"},
                "Company B": {"Fund 1"},
            },
            company_total_weights={
                "Company A": 16.0,
                "Company B": 8.0,
            },
            company_examples={
                "Company A": ["Fund 1", "Fund 2"],
                "Company B": ["Fund 1"],
            },
            funds_info={"Fund 1": "₹1000 Cr", "Fund 2": "₹500 Cr"},
            processed_files_count=2,
            skipped_files_count=0,
        )

        result = analyzer._build_analysis_output(holdings_data)

        # Verify output structure
        assert result["total_files"] == 2
        assert result["total_funds"] == 2
        assert result["unique_companies"] == 2
        assert len(result["funds"]) == 2
        assert len(result["top_by_fund_count"]) == 2
        assert len(result["top_by_total_weight"]) == 2
        assert isinstance(result["common_in_all_funds"], list)

        # Verify sorting
        assert result["top_by_fund_count"][0]["name"] == "Company A"  # More funds
        assert result["top_by_total_weight"][0]["name"] == "Company A"  # Higher weight
