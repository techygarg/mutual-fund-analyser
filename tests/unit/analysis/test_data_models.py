"""Unit tests for analysis data models and edge cases."""

from pathlib import Path

import pytest

from mfa.analysis.analyzer import (
    AnalysisResult,
    CompanyAnalysis,
    FundAnalysisResult,
    HoldingsData,
)


class TestAnalysisResult:
    """Test AnalysisResult data class."""

    def test_analysis_result_creation(self):
        """Test creating AnalysisResult with all fields."""
        result = AnalysisResult(
            category="largeCap",
            total_files=10,
            total_funds=10,
            unique_companies=150,
            output_file=Path("/tmp/largeCap.json"),
        )

        assert result.category == "largeCap"
        assert result.total_files == 10
        assert result.total_funds == 10
        assert result.unique_companies == 150
        assert result.output_file == Path("/tmp/largeCap.json")

    def test_average_companies_per_fund_normal(self):
        """Test average companies per fund calculation with normal values."""
        result = AnalysisResult(
            category="midCap",
            total_files=5,
            total_funds=5,
            unique_companies=100,
            output_file=Path("test.json"),
        )

        assert result.average_companies_per_fund == 20.0

    def test_average_companies_per_fund_partial_funds(self):
        """Test average calculation with fractional result."""
        result = AnalysisResult(
            category="smallCap",
            total_files=3,
            total_funds=3,
            unique_companies=10,
            output_file=Path("test.json"),
        )

        # 10 / 3 = 3.333...
        assert abs(result.average_companies_per_fund - 3.3333333333333335) < 1e-10

    def test_average_companies_per_fund_zero_funds(self):
        """Test average calculation with zero funds (edge case)."""
        result = AnalysisResult(
            category="empty",
            total_files=0,
            total_funds=0,
            unique_companies=0,
            output_file=Path("empty.json"),
        )

        assert result.average_companies_per_fund == 0.0

    def test_average_companies_per_fund_zero_companies(self):
        """Test average calculation with zero companies but funds exist."""
        result = AnalysisResult(
            category="nocompanies",
            total_files=5,
            total_funds=5,
            unique_companies=0,
            output_file=Path("test.json"),
        )

        assert result.average_companies_per_fund == 0.0


class TestFundAnalysisResult:
    """Test FundAnalysisResult data class."""

    def test_fund_analysis_result_creation(self):
        """Test creating FundAnalysisResult with all fields."""
        category_results = [
            AnalysisResult("largeCap", 5, 5, 50, Path("large.json")),
            AnalysisResult("midCap", 3, 3, 30, Path("mid.json")),
        ]

        result = FundAnalysisResult(
            categories_analyzed=2,
            total_categories=3,
            category_results=category_results,
            output_directory=Path("/tmp/analysis"),
        )

        assert result.categories_analyzed == 2
        assert result.total_categories == 3
        assert len(result.category_results) == 2
        assert result.output_directory == Path("/tmp/analysis")

    def test_success_rate_perfect(self):
        """Test success rate calculation with 100% success."""
        result = FundAnalysisResult(
            categories_analyzed=5,
            total_categories=5,
            category_results=[],
            output_directory=Path("output"),
        )

        assert result.success_rate == 100.0

    def test_success_rate_partial(self):
        """Test success rate calculation with partial success."""
        result = FundAnalysisResult(
            categories_analyzed=3,
            total_categories=4,
            category_results=[],
            output_directory=Path("output"),
        )

        assert result.success_rate == 75.0

    def test_success_rate_zero_success(self):
        """Test success rate calculation with zero success."""
        result = FundAnalysisResult(
            categories_analyzed=0,
            total_categories=5,
            category_results=[],
            output_directory=Path("output"),
        )

        assert result.success_rate == 0.0

    def test_success_rate_zero_total(self):
        """Test success rate calculation with zero total categories."""
        result = FundAnalysisResult(
            categories_analyzed=0,
            total_categories=0,
            category_results=[],
            output_directory=Path("output"),
        )

        assert result.success_rate == 0.0

    def test_success_rate_edge_case_more_analyzed_than_total(self):
        """Test success rate when analyzed > total (shouldn't happen, but handle gracefully)."""
        result = FundAnalysisResult(
            categories_analyzed=6,
            total_categories=5,
            category_results=[],
            output_directory=Path("output"),
        )

        # Should still calculate percentage
        assert result.success_rate == 120.0


class TestHoldingsData:
    """Test HoldingsData data class."""

    def test_holdings_data_creation(self):
        """Test creating HoldingsData with all fields."""
        from collections import defaultdict

        holdings_data = HoldingsData(
            company_to_funds=defaultdict(set),
            company_total_weights=defaultdict(float),
            company_examples=defaultdict(list),
            funds_info={},
            processed_files_count=0,
            skipped_files_count=0,
        )

        assert isinstance(holdings_data.company_to_funds, defaultdict)
        assert isinstance(holdings_data.company_total_weights, defaultdict)
        assert isinstance(holdings_data.company_examples, defaultdict)
        assert holdings_data.funds_info == {}
        assert holdings_data.processed_files_count == 0
        assert holdings_data.skipped_files_count == 0

    def test_total_funds_empty(self):
        """Test total_funds property with empty funds_info."""
        from collections import defaultdict

        holdings_data = HoldingsData(
            company_to_funds=defaultdict(set),
            company_total_weights=defaultdict(float),
            company_examples=defaultdict(list),
            funds_info={},
            processed_files_count=0,
            skipped_files_count=0,
        )

        assert holdings_data.total_funds == 0

    def test_total_funds_multiple(self):
        """Test total_funds property with multiple funds."""
        from collections import defaultdict

        holdings_data = HoldingsData(
            company_to_funds=defaultdict(set),
            company_total_weights=defaultdict(float),
            company_examples=defaultdict(list),
            funds_info={"Fund A": "₹1000 Cr", "Fund B": "₹2000 Cr", "Fund C": "₹500 Cr"},
            processed_files_count=3,
            skipped_files_count=0,
        )

        assert holdings_data.total_funds == 3

    def test_unique_companies_count_empty(self):
        """Test unique_companies_count property with no companies."""
        from collections import defaultdict

        holdings_data = HoldingsData(
            company_to_funds=defaultdict(set),
            company_total_weights=defaultdict(float),
            company_examples=defaultdict(list),
            funds_info={},
            processed_files_count=0,
            skipped_files_count=0,
        )

        assert holdings_data.unique_companies_count == 0

    def test_unique_companies_count_multiple(self):
        """Test unique_companies_count property with multiple companies."""
        from collections import defaultdict

        company_to_funds = defaultdict(set)
        company_to_funds["Apple Inc"] = {"Fund A", "Fund B"}
        company_to_funds["Microsoft Corp"] = {"Fund A"}
        company_to_funds["Google Inc"] = {"Fund C"}

        holdings_data = HoldingsData(
            company_to_funds=company_to_funds,
            company_total_weights=defaultdict(float),
            company_examples=defaultdict(list),
            funds_info={},
            processed_files_count=0,
            skipped_files_count=0,
        )

        assert holdings_data.unique_companies_count == 3


class TestCompanyAnalysis:
    """Test CompanyAnalysis data class."""

    def test_company_analysis_creation(self):
        """Test creating CompanyAnalysis with all fields."""
        company = CompanyAnalysis(
            name="Apple Inc",
            fund_count=5,
            total_weight=42.5,
            avg_weight=8.5,
            sample_funds=["Fund A", "Fund B", "Fund C"],
        )

        assert company.name == "Apple Inc"
        assert company.fund_count == 5
        assert company.total_weight == 42.5
        assert company.avg_weight == 8.5
        assert company.sample_funds == ["Fund A", "Fund B", "Fund C"]

    def test_company_analysis_empty_samples(self):
        """Test CompanyAnalysis with empty sample funds."""
        company = CompanyAnalysis(
            name="Rare Company", fund_count=1, total_weight=5.0, avg_weight=5.0, sample_funds=[]
        )

        assert company.sample_funds == []
        assert len(company.sample_funds) == 0

    def test_company_analysis_edge_values(self):
        """Test CompanyAnalysis with edge case values."""
        company = CompanyAnalysis(
            name="",  # Empty name
            fund_count=0,  # Zero count
            total_weight=0.0,  # Zero weight
            avg_weight=0.0,  # Zero average
            sample_funds=[],
        )

        assert company.name == ""
        assert company.fund_count == 0
        assert company.total_weight == 0.0
        assert company.avg_weight == 0.0
        assert company.sample_funds == []

    def test_company_analysis_large_values(self):
        """Test CompanyAnalysis with large values."""
        large_samples = [f"Fund {i}" for i in range(100)]

        company = CompanyAnalysis(
            name="Very Popular Company",
            fund_count=100,
            total_weight=999.999,
            avg_weight=9.999,
            sample_funds=large_samples,
        )

        assert company.fund_count == 100
        assert company.total_weight == 999.999
        assert len(company.sample_funds) == 100
