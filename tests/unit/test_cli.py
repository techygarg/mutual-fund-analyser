"""Unit tests for CLI command handling."""

from unittest.mock import Mock, patch

import pytest

from mfa.cli.analyze import main
from mfa.core.exceptions import OrchestrationError


class TestCLIAnalyze:
    """Test CLI analyze command."""

    @patch("sys.argv", ["analyze", "holdings"])
    def test_parse_args_default(self):
        """Test argument parsing with default values."""
        from mfa.cli.analyze import _parse_args

        args = _parse_args()

        assert args.analysis_type == "holdings"
        assert args.date is None
        assert args.list is False
        assert args.status is False

    @patch("sys.argv", ["analyze", "holdings"])
    def test_parse_args_with_analysis_type(self):
        """Test argument parsing with analysis type."""
        from mfa.cli.analyze import _parse_args

        args = _parse_args()

        assert args.analysis_type == "holdings"
        assert args.list is False

    @patch("sys.argv", ["analyze", "holdings", "--date", "20240903"])
    def test_parse_args_with_date(self):
        """Test argument parsing with date."""
        from mfa.cli.analyze import _parse_args

        args = _parse_args()

        assert args.analysis_type == "holdings"
        assert args.date == "20240903"

    @patch("sys.argv", ["analyze", "--list"])
    def test_parse_args_list_flag(self):
        """Test argument parsing with list flag."""
        from mfa.cli.analyze import _parse_args

        args = _parse_args()

        assert args.list is True
        assert args.analysis_type is None

    @patch("sys.argv", ["analyze", "--status"])
    def test_parse_args_status_flag(self):
        """Test argument parsing with status flag."""
        from mfa.cli.analyze import _parse_args

        args = _parse_args()

        assert args.status is True
        assert args.analysis_type is None

    @patch("sys.argv", ["analyze", "--list"])
    @patch("mfa.cli.analyze.create_config_provider")
    @patch("mfa.cli.analyze.AnalysisOrchestrator")
    def test_main_list_analyses(self, mock_orchestrator_class, mock_create_config):
        """Test main function with list flag."""
        mock_config_provider = Mock()
        mock_create_config.return_value = mock_config_provider

        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_orchestrator.list_available_analyses.return_value = ["fund-holdings", "portfolio"]

        with patch("builtins.print") as mock_print:
            main()

            # Should have called list_available_analyses
            mock_orchestrator.list_available_analyses.assert_called_once()

            # Should have printed the analysis types
            mock_print.assert_any_call("📋 Available analysis types:")
            mock_print.assert_any_call("  • fund-holdings")
            mock_print.assert_any_call("  • portfolio")

    @patch("sys.argv", ["analyze", "--status"])
    @patch("mfa.cli.analyze.create_config_provider")
    @patch("mfa.cli.analyze.AnalysisOrchestrator")
    def test_main_show_status(self, mock_orchestrator_class, mock_create_config):
        """Test main function with status flag."""
        mock_config_provider = Mock()
        mock_create_config.return_value = mock_config_provider

        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_orchestrator.get_analysis_status.return_value = {
            "holdings": {"enabled": True, "type": "fund-holdings", "strategy": "categories"}
        }

        with patch("builtins.print"):
            main()

            # Should have called get_analysis_status
            mock_orchestrator.get_analysis_status.assert_called_once()

    @patch("sys.argv", ["analyze", "holdings"])
    @patch("mfa.cli.analyze.create_config_provider")
    @patch("mfa.cli.analyze.AnalysisOrchestrator")
    def test_main_run_specific_analysis(self, mock_orchestrator_class, mock_create_config):
        """Test main function running specific analysis."""
        mock_config_provider = Mock()
        mock_create_config.return_value = mock_config_provider

        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator

        main()

        # Should have called run_analysis with specific type
        mock_orchestrator.run_analysis.assert_called_once_with("holdings", None, False)

    @patch("sys.argv", ["analyze", "--date", "20240903"])
    @patch("mfa.cli.analyze.create_config_provider")
    def test_main_missing_analysis_type(self, mock_create_config):
        """Test main function with missing analysis_type."""
        mock_config_provider = Mock()
        mock_create_config.return_value = mock_config_provider

        # Should exit with error when analysis_type is missing
        with pytest.raises(SystemExit):
            main()

    @patch("sys.argv", ["analyze", "holdings"])
    @patch("mfa.cli.analyze.create_config_provider")
    @patch("mfa.cli.analyze.AnalysisOrchestrator")
    def test_main_handles_orchestration_errors(self, mock_orchestrator_class, mock_create_config):
        """Test main function handles orchestration errors gracefully."""
        mock_config_provider = Mock()
        mock_create_config.return_value = mock_config_provider

        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_orchestrator.run_analysis.side_effect = OrchestrationError("Test error")

        # Should not crash, should let exception propagate
        with pytest.raises(OrchestrationError):
            main()

    @patch("sys.argv", ["analyze", "holdings"])
    @patch("mfa.cli.analyze.create_config_provider")
    def test_main_config_creation_failure(self, mock_create_config):
        """Test main function handles config creation failures."""
        mock_create_config.side_effect = Exception("Config creation failed")

        with pytest.raises(SystemExit):  # sys.exit() called on error
            main()

    @patch("sys.argv", ["analyze", "holdings"])
    @patch("mfa.cli.analyze.create_config_provider")
    @patch("mfa.cli.analyze.AnalysisOrchestrator")
    def test_main_orchestrator_creation_failure(self, mock_orchestrator_class, mock_create_config):
        """Test main function handles orchestrator creation failures."""
        mock_config_provider = Mock()
        mock_create_config.return_value = mock_config_provider

        mock_orchestrator_class.side_effect = Exception("Orchestrator creation failed")

        with pytest.raises(SystemExit):  # sys.exit() called on error
            main()

    @patch("sys.argv", ["analyze"])
    @patch("mfa.cli.analyze.create_config_provider")
    @patch("mfa.cli.analyze.AnalysisOrchestrator")
    def test_main_no_analysis_type_no_flags(self, mock_orchestrator_class, mock_create_config):
        """Test main function when no analysis_type and no informational flags are provided."""
        mock_config_provider = Mock()
        mock_create_config.return_value = mock_config_provider

        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator

        # Should exit when no analysis_type is provided and no informational flags
        with pytest.raises(SystemExit):
            main()
