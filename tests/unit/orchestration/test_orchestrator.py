"""Unit tests for AnalysisOrchestrator with dependency injection."""

from unittest.mock import Mock, patch
import pytest

from mfa.orchestration.analysis_orchestrator import AnalysisOrchestrator
from mfa.config.settings import ConfigProvider
from mfa.analysis.factories import AnalyzerFactory, ScrapingCoordinatorFactory
from mfa.analysis.analyzers.holdings import HoldingsAnalyzer
from mfa.analysis.scraping.category_coordinator import CategoryScrapingCoordinator
from mfa.core.exceptions import OrchestrationError


class TestAnalysisOrchestrator:
    """Test AnalysisOrchestrator with dependency injection."""

    @pytest.fixture
    def mock_config_provider(self) -> Mock:
        """Mock ConfigProvider for testing."""
        config_provider = Mock(spec=ConfigProvider)

        # Mock config with enabled analysis
        mock_config = Mock()
        mock_config.analyses = {
            "holdings": Mock(
                enabled=True,
                type="fund-holdings"
            )
        }
        mock_config.get_enabled_analyses.return_value = mock_config.analyses

        # Add paths to prevent mock object directory creation
        mock_config.paths = Mock()
        mock_config.paths.output_dir = "/tmp/test_output"
        mock_config.paths.analysis_dir = "/tmp/test_analysis"

        config_provider.get_config.return_value = mock_config
        return config_provider

    def test_orchestrator_initialization(self, mock_config_provider: Mock):
        """Test orchestrator initializes correctly with dependency injection."""
        orchestrator = AnalysisOrchestrator(mock_config_provider)

        assert orchestrator.config_provider is mock_config_provider

    def test_run_analysis_with_specific_type(self, mock_config_provider: Mock):
        """Test running analysis with specific analysis type."""
        orchestrator = AnalysisOrchestrator(mock_config_provider)

        with patch.object(orchestrator, '_run_single_analysis') as mock_run:
            mock_run.return_value = None

            # Run specific analysis
            orchestrator.run_analysis(analysis_type="holdings")

            # Verify single analysis was called
            mock_run.assert_called_once_with("holdings", mock_config_provider.get_config().analyses["holdings"], None)

    def test_run_analysis_with_all_enabled(self, mock_config_provider: Mock):
        """Test running all enabled analyses."""
        orchestrator = AnalysisOrchestrator(mock_config_provider)

        with patch.object(orchestrator, '_run_single_analysis') as mock_run:
            mock_run.return_value = None

            # Run all enabled analyses
            orchestrator.run_analysis()

            # Verify single analysis was called for holdings
            mock_run.assert_called_once()

    def test_run_analysis_unknown_type_raises_error(self, mock_config_provider: Mock):
        """Test running unknown analysis type raises error."""
        orchestrator = AnalysisOrchestrator(mock_config_provider)

        with pytest.raises(OrchestrationError, match="Analysis 'unknown' not found"):
            orchestrator.run_analysis(analysis_type="unknown")

    def test_run_analysis_no_enabled_analyses(self, mock_config_provider: Mock):
        """Test handling when no analyses are enabled."""
        # Configure no enabled analyses
        mock_config = mock_config_provider.get_config.return_value
        mock_config.get_enabled_analyses.return_value = {}

        orchestrator = AnalysisOrchestrator(mock_config_provider)

        # Should not crash, just log warning
        orchestrator.run_analysis()  # Should complete without error

    def test_single_analysis_execution_flow(self, mock_config_provider: Mock):
        """Test the complete flow of single analysis execution."""
        orchestrator = AnalysisOrchestrator(mock_config_provider)

        # Mock analysis config
        mock_analysis_config = Mock()
        mock_analysis_config.type = "fund-holdings"

        # Mock analyzer
        mock_analyzer = Mock()
        mock_requirements = Mock()
        mock_requirements.strategy.value = "categories"
        mock_requirements.urls = ["https://example.com"]
        mock_analyzer.get_data_requirements.return_value = mock_requirements

        mock_result = Mock()
        mock_result.analysis_type = "fund-holdings"
        mock_result.date = "20240903"
        mock_result.output_paths = ["/path/to/output1.json", "/path/to/output2.json"]  # Add output_paths
        mock_result.summary = {"total_funds": 3, "total_companies": 10}
        mock_analyzer.analyze.return_value = mock_result

        with patch.object(AnalyzerFactory, 'create_analyzer', return_value=mock_analyzer) as mock_create_analyzer:
            with patch.object(orchestrator, '_scrape_and_save_data') as mock_scrape:
                mock_scrape.return_value = {"file_paths": {"test": ["/path/to/file.json"]}}

                # Execute single analysis
                result = orchestrator._run_single_analysis("holdings", mock_analysis_config, "20240903")

                # Verify the flow
                mock_create_analyzer.assert_called_once_with("fund-holdings", mock_config_provider)
                mock_analyzer.get_data_requirements.assert_called_once()
                mock_scrape.assert_called_once_with(mock_requirements, "20240903")
                mock_analyzer.analyze.assert_called_once_with({"file_paths": {"test": ["/path/to/file.json"]}}, "20240903")

    def test_scrape_and_save_data_flow(self, mock_config_provider: Mock):
        """Test the scrape and save data flow."""
        orchestrator = AnalysisOrchestrator(mock_config_provider)

        mock_requirements = Mock()
        mock_requirements.strategy.value = "categories"

        mock_coordinator = Mock()
        mock_coordinator.scrape_for_requirement.return_value = {"file_paths": {"test": ["/test/file.json"]}}

        with patch.object(ScrapingCoordinatorFactory, 'create_coordinator', return_value=mock_coordinator) as mock_create_coordinator:
            result = orchestrator._scrape_and_save_data(mock_requirements, "20240903")

            mock_create_coordinator.assert_called_once_with("categories", mock_config_provider)
            mock_coordinator.scrape_for_requirement.assert_called_once_with(mock_requirements)
            assert result == {"file_paths": {"test": ["/test/file.json"]}}

    def test_error_handling_in_analysis_execution(self, mock_config_provider: Mock):
        """Test error handling during analysis execution."""
        orchestrator = AnalysisOrchestrator(mock_config_provider)

        mock_analysis_config = Mock()
        mock_analysis_config.type = "fund-holdings"

        # Mock analyzer to raise an exception
        mock_analyzer = Mock()
        mock_analyzer.get_data_requirements.side_effect = Exception("Test error")

        with patch.object(AnalyzerFactory, 'create_analyzer', return_value=mock_analyzer):
            # Should raise OrchestrationError wrapping the original error
            with pytest.raises(OrchestrationError, match="Unexpected error during analysis 'holdings'"):
                orchestrator._run_single_analysis("holdings", mock_analysis_config, "20240903")

    def test_list_available_analyses(self, mock_config_provider: Mock):
        """Test listing available analysis types."""
        orchestrator = AnalysisOrchestrator(mock_config_provider)

        with patch.object(AnalyzerFactory, 'get_available_types', return_value=["fund-holdings", "portfolio"]) as mock_get_types:
            result = orchestrator.list_available_analyses()

            mock_get_types.assert_called_once()
            assert result == ["fund-holdings", "portfolio"]

    def test_get_analysis_status(self, mock_config_provider: Mock):
        """Test getting analysis status information."""
        orchestrator = AnalysisOrchestrator(mock_config_provider)

        mock_config = mock_config_provider.get_config.return_value
        mock_config.analyses = {
            "holdings": Mock(enabled=True, type="fund-holdings")
        }

        status = orchestrator.get_analysis_status()

        assert "holdings" in status
        assert status["holdings"]["enabled"] is True
        assert status["holdings"]["type"] == "fund-holdings"
