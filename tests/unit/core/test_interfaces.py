"""Unit tests for analysis interfaces and core data structures."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from mfa.analysis.interfaces import (
    AnalysisResult,
    BaseAnalyzer,
    DataRequirement,
    IAnalyzer,
    IDataStore,
    IScrapingCoordinator,
    ScrapingStrategy,
)
from mfa.config.settings import ConfigProvider


class TestScrapingStrategy:
    """Test ScrapingStrategy enum."""

    def test_scraping_strategy_values(self):
        """Test ScrapingStrategy enum has expected values."""
        assert ScrapingStrategy.CATEGORIES.value == "categories"
        assert ScrapingStrategy.TARGETED_FUNDS.value == "targeted_funds"
        assert ScrapingStrategy.API_SCRAPING.value == "api_scraping"

    def test_scraping_strategy_from_string(self):
        """Test creating ScrapingStrategy from string values."""
        assert ScrapingStrategy("categories") == ScrapingStrategy.CATEGORIES
        assert ScrapingStrategy("targeted_funds") == ScrapingStrategy.TARGETED_FUNDS
        assert ScrapingStrategy("api_scraping") == ScrapingStrategy.API_SCRAPING

    def test_scraping_strategy_invalid_value(self):
        """Test invalid scraping strategy value raises error."""
        with pytest.raises(ValueError):
            ScrapingStrategy("invalid_strategy")


class TestDataRequirement:
    """Test DataRequirement dataclass."""

    def test_data_requirement_creation(self):
        """Test creating DataRequirement with all fields."""
        requirement = DataRequirement(
            strategy=ScrapingStrategy.CATEGORIES,
            urls=["https://example.com/fund1", "https://example.com/fund2"],
            metadata={"analysis_id": "holdings", "categories": {"largeCap": ["url1"]}},
        )

        assert requirement.strategy == ScrapingStrategy.CATEGORIES
        assert len(requirement.urls) == 2
        assert requirement.metadata["analysis_id"] == "holdings"

    def test_data_requirement_empty_urls(self):
        """Test DataRequirement with empty URLs list."""
        requirement = DataRequirement(
            strategy=ScrapingStrategy.TARGETED_FUNDS, urls=[], metadata={}
        )

        assert requirement.urls == []
        assert requirement.metadata == {}

    def test_data_requirement_complex_metadata(self):
        """Test DataRequirement with complex metadata."""
        metadata = {
            "analysis_id": "portfolio",
            "funds": [
                {"url": "https://example.com/fund1", "units": 100},
                {"url": "https://example.com/fund2", "units": 200},
            ],
            "config": {"max_holdings": 10},
        }

        requirement = DataRequirement(
            strategy=ScrapingStrategy.API_SCRAPING,
            urls=["https://example.com/fund1"],
            metadata=metadata,
        )

        assert requirement.metadata["analysis_id"] == "portfolio"
        assert len(requirement.metadata["funds"]) == 2
        assert requirement.metadata["config"]["max_holdings"] == 10


class TestAnalysisResult:
    """Test AnalysisResult dataclass."""

    def test_analysis_result_creation(self):
        """Test creating AnalysisResult with all fields."""
        paths = [Path("/output/result1.json"), Path("/output/result2.json")]
        summary = {"total_funds": 10, "total_companies": 50}

        result = AnalysisResult(
            analysis_type="holdings", date="20240915", output_paths=paths, summary=summary
        )

        assert result.analysis_type == "holdings"
        assert result.date == "20240915"
        assert len(result.output_paths) == 2
        assert result.summary["total_funds"] == 10

    def test_analysis_result_empty_paths(self):
        """Test AnalysisResult with empty output paths."""
        result = AnalysisResult(
            analysis_type="portfolio", date="20240915", output_paths=[], summary={}
        )

        assert result.output_paths == []
        assert result.summary == {}

    def test_analysis_result_path_objects(self):
        """Test AnalysisResult maintains Path objects."""
        paths = [Path("/test/path.json")]
        result = AnalysisResult(
            analysis_type="test", date="20240915", output_paths=paths, summary={}
        )

        assert isinstance(result.output_paths[0], Path)
        assert str(result.output_paths[0]) == "/test/path.json"


class TestBaseAnalyzer:
    """Test BaseAnalyzer implementation."""

    class TestAnalyzer(BaseAnalyzer):
        """Concrete test analyzer for testing BaseAnalyzer."""

        def get_data_requirements(self) -> DataRequirement:
            return DataRequirement(
                strategy=ScrapingStrategy.CATEGORIES,
                urls=["https://test.com"],
                metadata={"test": True},
            )

        def analyze(self, data_source: dict[str, Any], date: str) -> AnalysisResult:
            return AnalysisResult(
                analysis_type=self.analysis_type, date=date, output_paths=[], summary={}
            )

    @pytest.fixture
    def mock_config_provider(self):
        """Mock config provider for testing."""
        return Mock(spec=ConfigProvider)

    def test_base_analyzer_initialization(self, mock_config_provider):
        """Test BaseAnalyzer initialization."""
        analyzer = self.TestAnalyzer(mock_config_provider, "test_analyzer")

        assert analyzer.config_provider == mock_config_provider
        assert analyzer.analysis_type == "test_analyzer"

    def test_base_analyzer_analysis_type_property(self, mock_config_provider):
        """Test analysis_type property."""
        analyzer = self.TestAnalyzer(mock_config_provider, "holdings")

        assert analyzer.analysis_type == "holdings"

    def test_validate_data_source_valid_dict(self, mock_config_provider):
        """Test _validate_data_source with valid dictionary."""
        analyzer = self.TestAnalyzer(mock_config_provider, "test")
        data_source = {"file_paths": {"category": ["/path/to/file.json"]}}

        # Should not raise exception
        analyzer._validate_data_source(data_source)

    def test_validate_data_source_empty_dict(self, mock_config_provider):
        """Test _validate_data_source with empty dictionary."""
        analyzer = self.TestAnalyzer(mock_config_provider, "test")

        with pytest.raises(ValueError, match="data_source cannot be empty"):
            analyzer._validate_data_source({})

    def test_validate_data_source_none(self, mock_config_provider):
        """Test _validate_data_source with None."""
        analyzer = self.TestAnalyzer(mock_config_provider, "test")

        with pytest.raises(ValueError, match="data_source must be a dictionary"):
            analyzer._validate_data_source(None)

    def test_validate_data_source_invalid_type(self, mock_config_provider):
        """Test _validate_data_source with invalid type."""
        analyzer = self.TestAnalyzer(mock_config_provider, "test")

        with pytest.raises(ValueError, match="data_source must be a dictionary"):
            analyzer._validate_data_source("invalid")

    def test_create_result_method(self, mock_config_provider):
        """Test _create_result method."""
        analyzer = self.TestAnalyzer(mock_config_provider, "test_analyzer")

        output_paths = ["/output/file1.json", "/output/file2.json"]
        summary = {"total_items": 5, "processed": 3}
        date = "20240915"

        result = analyzer._create_result(output_paths, summary, date)

        assert isinstance(result, AnalysisResult)
        assert result.analysis_type == "test_analyzer"
        assert result.date == "20240915"
        assert len(result.output_paths) == 2
        assert all(isinstance(path, Path) for path in result.output_paths)
        assert result.summary == summary

    def test_create_result_with_path_objects(self, mock_config_provider):
        """Test _create_result with Path objects."""
        analyzer = self.TestAnalyzer(mock_config_provider, "test")

        output_paths = [Path("/output/file1.json")]
        result = analyzer._create_result(output_paths, {}, "20240915")

        assert len(result.output_paths) == 1
        assert isinstance(result.output_paths[0], Path)

    def test_analyzer_interface_compliance(self, mock_config_provider):
        """Test that TestAnalyzer properly implements IAnalyzer interface."""
        analyzer = self.TestAnalyzer(mock_config_provider, "test")

        # Test interface methods
        requirements = analyzer.get_data_requirements()
        assert isinstance(requirements, DataRequirement)

        result = analyzer.analyze({"test": "data"}, "20240915")
        assert isinstance(result, AnalysisResult)

        assert hasattr(analyzer, "analysis_type")
        assert isinstance(analyzer.analysis_type, str)


class TestIAnalyzerInterface:
    """Test IAnalyzer interface contract."""

    def test_ianalyzer_is_abstract(self):
        """Test that IAnalyzer cannot be instantiated directly."""
        with pytest.raises(TypeError):
            IAnalyzer()  # type: ignore

    def test_ianalyzer_has_required_methods(self):
        """Test that IAnalyzer defines required abstract methods."""
        required_methods = ["get_data_requirements", "analyze"]

        for method_name in required_methods:
            assert hasattr(IAnalyzer, method_name)
            method = getattr(IAnalyzer, method_name)
            assert getattr(method, "__isabstractmethod__", False)

    def test_ianalyzer_has_analysis_type_property(self):
        """Test that IAnalyzer defines analysis_type property."""
        assert hasattr(IAnalyzer, "analysis_type")


class TestIScrapingCoordinatorInterface:
    """Test IScrapingCoordinator interface contract."""

    def test_iscraping_coordinator_is_abstract(self):
        """Test that IScrapingCoordinator cannot be instantiated directly."""
        with pytest.raises(TypeError):
            IScrapingCoordinator()  # type: ignore

    def test_iscraping_coordinator_has_required_methods(self):
        """Test that IScrapingCoordinator defines required abstract methods."""
        assert hasattr(IScrapingCoordinator, "scrape_for_requirement")
        method = getattr(IScrapingCoordinator, "scrape_for_requirement")
        assert getattr(method, "__isabstractmethod__", False)


class TestIDataStoreInterface:
    """Test IDataStore interface contract."""

    def test_idata_store_is_abstract(self):
        """Test that IDataStore cannot be instantiated directly."""
        with pytest.raises(TypeError):
            IDataStore()  # type: ignore

    def test_idata_store_has_required_methods(self):
        """Test that IDataStore defines required abstract methods."""
        required_methods = ["save_analysis_result", "load_scraped_data"]

        for method_name in required_methods:
            assert hasattr(IDataStore, method_name)
            method = getattr(IDataStore, method_name)
            assert getattr(method, "__isabstractmethod__", False)


class TestInterfaceIntegration:
    """Integration tests for interface interactions."""

    def test_data_requirement_in_analyzer_workflow(self):
        """Test DataRequirement works in analyzer workflow."""
        # Simulate typical workflow
        requirement = DataRequirement(
            strategy=ScrapingStrategy.CATEGORIES,
            urls=["https://example.com/fund1"],
            metadata={"analysis_id": "holdings", "categories": {"largeCap": ["url1"]}},
        )

        # Verify requirement can be used in coordination
        assert requirement.strategy == ScrapingStrategy.CATEGORIES
        assert "analysis_id" in requirement.metadata
        assert len(requirement.urls) == 1

    def test_analysis_result_in_workflow(self):
        """Test AnalysisResult works in complete workflow."""
        # Simulate analysis completion
        result = AnalysisResult(
            analysis_type="holdings",
            date="20240915",
            output_paths=[Path("/output/holdings.json")],
            summary={"total_funds": 10, "categories_processed": 2},
        )

        # Verify result structure
        assert result.analysis_type == "holdings"
        assert len(result.output_paths) == 1
        assert result.summary["total_funds"] == 10

        # Verify paths are Path objects
        assert isinstance(result.output_paths[0], Path)
        assert result.output_paths[0].name == "holdings.json"
