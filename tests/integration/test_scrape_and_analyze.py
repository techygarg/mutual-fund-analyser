"""
Integration test for scraping and analysis pipeline.

This test runs the full scrape -> analyze pipeline with minimal test data.
"""

import json
import shutil
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from mfa.cli import analyze, orchestrate
from mfa.config.settings import ConfigProvider


class TestScrapeAndAnalyze:
    """Integration test for the scrape and analyze pipeline."""

    @pytest.fixture
    def test_workspace(self) -> Generator[tuple[Path, dict], None, None]:
        """Create an isolated test workspace with test config."""
        # Create test workspace in the integration test directory
        test_integration_dir = Path(__file__).parent
        test_workspace = test_integration_dir / "test_workspace"

        # Clean up any existing test workspace
        if test_workspace.exists():
            shutil.rmtree(test_workspace)

        # Create test workspace structure
        test_workspace.mkdir()
        (test_workspace / "config").mkdir()
        (test_workspace / "outputs").mkdir()
        (test_workspace / "outputs" / "extracted_json").mkdir()
        (test_workspace / "outputs" / "analysis").mkdir()

        # Read test config and update paths to use test workspace
        test_config_path = Path(__file__).parent / "test_config.yaml"
        with open(test_config_path) as f:
            config_data = yaml.safe_load(f)

        # Update paths to use the test workspace
        config_data["paths"]["output_dir"] = str(test_workspace / "outputs" / "extracted_json")
        config_data["paths"]["analysis_dir"] = str(test_workspace / "outputs" / "analysis")

        # Write config to test workspace
        config_file_path = test_workspace / "config" / "config.yaml"
        with open(config_file_path, "w") as f:
            yaml.dump(config_data, f)

        try:
            yield test_workspace, config_data
        finally:
            # Clean up test workspace after test
            if test_workspace.exists():
                shutil.rmtree(test_workspace)

    @pytest.fixture
    def reset_config(self):
        """Reset the config singleton between tests."""
        # Clear the singleton instance
        ConfigProvider._instance = None
        ConfigProvider._config = None
        yield
        # Clear again after test
        ConfigProvider._instance = None
        ConfigProvider._config = None

    def test_scrape_and_analyze_pipeline(self, test_workspace: tuple[Path, dict], reset_config):
        """Test the complete scrape -> analyze pipeline."""
        workspace_path, config_data = test_workspace

        # Change to test workspace directory so config provider reads from there
        import os

        original_cwd = Path.cwd()
        os.chdir(workspace_path)

        try:
            # Force reset config provider AFTER changing directory
            ConfigProvider._instance = None
            ConfigProvider._raw_config = None
            ConfigProvider._typed_config = None

            # Get fresh config instance that will read from test workspace
            config_provider = ConfigProvider.get_instance()
            config = config_provider.get_config()

            # Verify test config is loaded correctly
            holdings_config = config.get_analysis("holdings")
            categories = holdings_config.data_requirements.categories if holdings_config else {}
            print(f"📁 Test workspace: {workspace_path}")
            print(
                f"🔧 Using test config with {len(categories.get('largeCap', []))} largeCap and {len(categories.get('midCap', []))} midCap funds"
            )

            # Step 1: Run scraping and analysis - using new analysis orchestrator
            print("\n🚀 Running analysis orchestrator...")
            from mfa.orchestration.analysis_orchestrator import AnalysisOrchestrator
            orchestrator = AnalysisOrchestrator()
            orchestrator.run_analysis("holdings")

            print("✅ Analysis orchestrator completed successfully")

            # Step 2: Verify analysis outputs (analysis runs automatically with orchestrator)
            print("\n📊 Verifying analysis outputs...")
            # Verify analysis outputs
            analysis_dir = Path(config.paths.analysis_dir)
            assert analysis_dir.exists(), "Analysis directory should be created"

            # Should have date-based subdirectory with analysis files
            analysis_date_dirs = [d for d in analysis_dir.iterdir() if d.is_dir()]
            assert len(analysis_date_dirs) >= 1, "Should create analysis date directories"

            analysis_date_dir = analysis_date_dirs[0]

            # Check for analysis JSON files for all categories
            analysis_files = list(analysis_date_dir.glob("*.json"))
            assert len(analysis_files) >= 1, "Should create analysis files"

            print(f"✅ Generated analysis for {len(analysis_files)} categories")

            # Verify analysis content structure (using first analysis file)
            with open(analysis_files[0]) as f:
                analysis_data = json.load(f)

                # Check required analysis fields
                required_fields = [
                    "total_files",
                    "total_funds",
                    "unique_companies",
                    "top_by_fund_count",
                    "top_by_total_weight",
                ]

                for field in required_fields:
                    assert field in analysis_data, f"Analysis should contain '{field}' field"

                # Basic validation of analysis values
                assert analysis_data["total_files"] >= 1, "Should have processed at least 1 file"
                assert analysis_data["total_funds"] >= 1, "Should have analyzed at least 1 fund"
                assert analysis_data["unique_companies"] >= 0, "Should have counted companies"

                # Validate structure of top companies
                top_by_fund_count = analysis_data["top_by_fund_count"]
                assert isinstance(top_by_fund_count, list), "top_by_fund_count should be a list"

                if top_by_fund_count:  # If we have company data
                    company = top_by_fund_count[0]
                    # Check for correct field names in our new output structure
                    company_fields = ["company", "fund_count", "total_weight", "avg_weight"]
                    for field in company_fields:
                        assert field in company, f"Company data should contain '{field}' field"

            print("✅ Analysis completed and validated")
            print(f"📁 Test workspace: {workspace_path}")
            print(f"📊 Generated analysis for {len(analysis_files)} categories")

        finally:
            # Restore original working directory
            os.chdir(original_cwd)
