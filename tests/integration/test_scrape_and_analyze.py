"""
Integration test for scraping and analysis pipeline.

This test runs the full scrape -> analyze pipeline with minimal test data.
"""

import json
import shutil
from collections.abc import Generator
from pathlib import Path

import pytest
import yaml

from mfa.config.settings import create_config_provider


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
        """No longer needed with dependency injection pattern."""
        # ConfigProvider is no longer a singleton, so no reset needed
        yield

    def test_scrape_and_analyze_pipeline(self, test_workspace: tuple[Path, dict], reset_config):
        """Test the complete scrape -> analyze pipeline."""
        workspace_path, config_data = test_workspace

        # Change to test workspace directory so config provider reads from there
        import os

        original_cwd = Path.cwd()
        os.chdir(workspace_path)

        try:
            # Create config provider with dependency injection pattern
            config_provider = create_config_provider(workspace_path / "config" / "config.yaml")
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

            orchestrator = AnalysisOrchestrator(config_provider)
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

                # Check required analysis fields (updated for new structure)
                required_fields = ["category", "summary", "funds", "companies"]

                for field in required_fields:
                    assert field in analysis_data, f"Analysis should contain '{field}' field"

                # Check summary fields
                summary = analysis_data["summary"]
                assert "total_funds" in summary, "Summary should contain total_funds"
                assert "total_companies" in summary, "Summary should contain total_companies"
                assert "companies_in_results" in summary, (
                    "Summary should contain companies_in_results"
                )

                # Basic validation of analysis values
                assert summary["total_funds"] >= 1, "Should have analyzed at least 1 fund"
                assert summary["total_companies"] >= 0, "Should have counted companies"
                assert len(analysis_data["companies"]) >= 0, "Should have companies list"

                # Validate structure of companies
                companies = analysis_data["companies"]
                assert isinstance(companies, list), "companies should be a list"

                if companies:  # If we have company data
                    company = companies[0]
                    # Check for correct field names in our new output structure
                    company_fields = [
                        "name",
                        "fund_count",
                        "total_weight",
                        "average_weight",
                        "sample_funds",
                    ]
                    for field in company_fields:
                        assert field in company, f"Company data should contain '{field}' field"

            print("✅ Analysis completed and validated")
            print(f"📁 Test workspace: {workspace_path}")
            print(f"📊 Generated analysis for {len(analysis_files)} categories")

        finally:
            # Restore original working directory
            os.chdir(original_cwd)
