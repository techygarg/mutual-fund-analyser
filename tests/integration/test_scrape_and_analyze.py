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

            # Verify analysis content structure (dashboard-compatible format)
            with open(analysis_files[0]) as f:
                analysis_data = json.load(f)

                # Check required TOP-LEVEL fields for dashboard compatibility
                required_top_level_fields = [
                    "total_files", "total_funds", "funds", "unique_companies",
                    "top_by_fund_count", "top_by_total_weight", "common_in_all_funds"
                ]

                for field in required_top_level_fields:
                    assert field in analysis_data, f"Analysis must contain '{field}' field for dashboard compatibility"

                # Validate that we DON'T have the old broken structure
                broken_fields = ["category", "summary", "companies"]
                for field in broken_fields:
                    assert field not in analysis_data, f"Analysis should NOT contain old '{field}' field structure"

                # Validate critical dashboard field values
                assert analysis_data["total_files"] >= 1, "Should have total_files >= 1"
                assert analysis_data["total_funds"] >= 1, "Should have total_funds >= 1"
                assert analysis_data["unique_companies"] >= 0, "Should have unique_companies count"
                
                # Validate arrays exist and are lists
                assert isinstance(analysis_data["top_by_fund_count"], list), "top_by_fund_count should be a list"
                assert isinstance(analysis_data["top_by_total_weight"], list), "top_by_total_weight should be a list"
                assert isinstance(analysis_data["common_in_all_funds"], list), "common_in_all_funds should be a list"
                assert isinstance(analysis_data["funds"], list), "funds should be a list"

                # Validate fund structure
                if analysis_data["funds"]:
                    fund = analysis_data["funds"][0]
                    fund_fields = ["name", "aum"]
                    for field in fund_fields:
                        assert field in fund, f"Fund data should contain '{field}' field"

                # Validate company structure in each array
                for array_name in ["top_by_fund_count", "top_by_total_weight", "common_in_all_funds"]:
                    companies_array = analysis_data[array_name]
                    if companies_array:  # If we have company data
                        company = companies_array[0]
                        # Check for EXACT field names dashboard expects
                        company_fields = [
                            "name", "company", "fund_count", "total_weight", "avg_weight", "sample_funds"
                        ]
                        for field in company_fields:
                            assert field in company, f"Company in {array_name} should contain '{field}' field"
                        
                        # Validate that 'name' and 'company' have the same value
                        assert company["name"] == company["company"], f"Company 'name' and 'company' fields should have the same value"
                        
                        # Validate we DON'T have the wrong field name
                        assert "average_weight" not in company, f"Company in {array_name} should use 'avg_weight', not 'average_weight'"

                # Validate sorting logic
                top_by_fund_count = analysis_data["top_by_fund_count"]
                if len(top_by_fund_count) >= 2:
                    # Should be sorted by fund_count descending, then total_weight descending
                    for i in range(len(top_by_fund_count) - 1):
                        current = top_by_fund_count[i]
                        next_item = top_by_fund_count[i + 1]
                        assert (
                            current["fund_count"] > next_item["fund_count"] or
                            (current["fund_count"] == next_item["fund_count"] and 
                             current["total_weight"] >= next_item["total_weight"])
                        ), "top_by_fund_count should be sorted by fund_count desc, then total_weight desc"

                top_by_total_weight = analysis_data["top_by_total_weight"]
                if len(top_by_total_weight) >= 2:
                    # Should be sorted by total_weight descending
                    for i in range(len(top_by_total_weight) - 1):
                        current = top_by_total_weight[i]
                        next_item = top_by_total_weight[i + 1]
                        assert current["total_weight"] >= next_item["total_weight"], (
                            "top_by_total_weight should be sorted by total_weight desc"
                        )

                # Validate common_in_all_funds logic
                total_funds = analysis_data["total_funds"]
                common_companies = analysis_data["common_in_all_funds"]
                for company in common_companies:
                    assert company["fund_count"] == total_funds, (
                        f"Companies in common_in_all_funds should appear in ALL {total_funds} funds, "
                        f"but {company['name']} appears in {company['fund_count']} funds"
                    )

            print("✅ Analysis completed and validated")
            print(f"📁 Test workspace: {workspace_path}")
            print(f"📊 Generated analysis for {len(analysis_files)} categories")

        finally:
            # Restore original working directory
            os.chdir(original_cwd)
