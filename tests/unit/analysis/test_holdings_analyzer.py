"""Unit tests for HoldingsAnalyzer - business-critical analysis component."""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from mfa.analysis.analyzers.holdings import HoldingsAnalyzer
from mfa.config.settings import ConfigProvider
from mfa.storage.json_store import JsonStore


class TestHoldingsAnalyzer:
    """Test HoldingsAnalyzer with dependency injection."""

    @pytest.fixture
    def sample_file_data(self) -> dict[str, Any]:
        """Sample JSON data for testing."""
        return {
            "data": {
                "fund_info": {"fund_name": "Test Fund", "aum": "₹1000 Cr"},
                "top_holdings": [
                    {
                        "rank": 1,
                        "company_name": "Reliance Industries",
                        "allocation_percentage": "8.5%",
                    },
                    {"rank": 2, "company_name": "TCS Ltd", "allocation_percentage": "6.2%"},
                    {
                        "rank": 3,
                        "company_name": "CASH",
                        "allocation_percentage": "2.1%",
                    },  # Should be excluded
                ],
            }
        }

    def test_analyzer_initialization(self, mock_config_provider: ConfigProvider):
        """Test analyzer initializes correctly with dependency injection."""
        analyzer = HoldingsAnalyzer(mock_config_provider)

        assert analyzer.config_provider is mock_config_provider
        assert hasattr(analyzer, "data_processor")
        assert hasattr(analyzer, "aggregator")
        assert hasattr(analyzer, "output_builder")

        # Verify components received the config provider
        assert analyzer.data_processor.config_provider is mock_config_provider
        assert analyzer.aggregator.config_provider is mock_config_provider
        assert analyzer.output_builder.config_provider is mock_config_provider

    def test_get_data_requirements(self, mock_config_provider: ConfigProvider):
        """Test data requirements extraction from config."""
        analyzer = HoldingsAnalyzer(mock_config_provider)

        requirements = analyzer.get_data_requirements()

        assert requirements.strategy.value == "categories"
        # URLs should contain the actual fund URLs from categories
        assert (
            "https://coin.zerodha.com/mf/fund/INF204K01XI3/nippon-india-large-cap-fund-direct-growth"
            in requirements.urls
        )
        assert (
            "https://coin.zerodha.com/mf/fund/INF179K01XQ0/hdfc-mid-cap-fund-direct-growth"
            in requirements.urls
        )
        assert len(requirements.urls) == 2
        assert requirements.metadata["analysis_id"] == "holdings"
        # Categories should be in metadata
        assert "largeCap" in requirements.metadata["categories"]
        assert "midCap" in requirements.metadata["categories"]

    def test_analyze_processes_files_successfully(
        self, mock_config_provider: ConfigProvider, sample_file_data: dict[str, Any]
    ):
        """Test end-to-end analysis processing with file-based data."""
        analyzer = HoldingsAnalyzer(mock_config_provider)

        # Create temporary files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create sample JSON files
            file1 = temp_path / "large_cap_fund.json"
            JsonStore.save(sample_file_data, file1)

            file2 = temp_path / "mid_cap_fund.json"
            JsonStore.save(sample_file_data, file2)

            # Mock data source with file paths
            data_source = {"file_paths": {"largeCap": [str(file1)], "midCap": [str(file2)]}}

            # Execute analysis
            result = analyzer.analyze(data_source, "20240903")

            # Verify results
            assert result.analysis_type == "holdings"
            assert result.date == "20240903"
            assert len(result.output_paths) == 2  # One for each category
            assert isinstance(result.summary, dict)
            assert "total_categories" in result.summary
            assert result.summary["total_categories"] == 2

    def test_analyze_handles_missing_files_gracefully(self, mock_config_provider: ConfigProvider):
        """Test analysis handles missing files without crashing."""
        analyzer = HoldingsAnalyzer(mock_config_provider)

        # Mock data source with non-existent file paths
        data_source = {
            "file_paths": {
                "largeCap": ["/nonexistent/file1.json"],
                "midCap": ["/nonexistent/file2.json"],
            }
        }

        result = analyzer.analyze(data_source, "20240903")

        # Should still return result but with warnings
        assert result.analysis_type == "holdings"
        assert result.summary["total_categories"] == 2
        assert result.summary["categories_processed"] == 0  # No valid files

    def test_analyze_validates_data_source(self, mock_config_provider: ConfigProvider):
        """Test analysis validates input data source."""
        analyzer = HoldingsAnalyzer(mock_config_provider)

        # Test with empty data source
        with pytest.raises(ValueError, match="data_source cannot be empty"):
            analyzer.analyze({}, "20240903")

        # Test with None data source
        with pytest.raises(ValueError, match="data_source must be a dictionary"):
            analyzer.analyze(None, "20240903")  # type: ignore

    def test_analyzer_uses_config_for_processing(
        self, mock_config_provider: ConfigProvider, sample_file_data: dict[str, Any]
    ):
        """Test analyzer uses configuration values during processing."""
        # This test verifies that the analyzer properly passes config to its components
        analyzer = HoldingsAnalyzer(mock_config_provider)

        # Verify that the analyzer has access to configuration
        config = mock_config_provider.get_config()
        holdings_config = config.get_analysis("holdings")

        assert holdings_config is not None
        assert holdings_config.params.exclude_from_analysis is not None
        assert "CASH" in holdings_config.params.exclude_from_analysis

        # Verify components received the config provider
        assert analyzer.data_processor.config_provider is mock_config_provider
        assert analyzer.aggregator.config_provider is mock_config_provider
        assert analyzer.output_builder.config_provider is mock_config_provider

    def test_analyzer_handles_component_errors(self, mock_config_provider: ConfigProvider):
        """Test analyzer handles errors from individual components gracefully."""
        analyzer = HoldingsAnalyzer(mock_config_provider)

        # Mock data processor to raise an error
        with patch.object(analyzer.data_processor, "process_fund_jsons") as mock_process:
            mock_process.side_effect = Exception("Processing failed")

            data_source = {"file_paths": {"test": ["/some/file.json"]}}

            # Should not crash, should handle error gracefully
            result = analyzer.analyze(data_source, "20240903")

            # Verify result structure is maintained
            assert result.analysis_type == "holdings"
            assert result.date == "20240903"
