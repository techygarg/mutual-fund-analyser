"""
Integration test for scraping and analysis pipeline.

This test runs the full scrape -> analyze pipeline with minimal test data.
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest
import yaml

from mfa.config.settings import ConfigProvider
from mfa.cli import orchestrate, analyze


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
        with open(config_file_path, 'w') as f:
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
            ConfigProvider._config = None
            
            # Get fresh config instance that will read from test workspace
            config = ConfigProvider.get_instance()
            
            # Verify test config is loaded correctly
            funds = config.get("funds", {})
            print(f"📁 Test workspace: {workspace_path}")
            
            # Step 1: Run scraping - process all categories configured in test config
            print("\n🕷️ Running scraping...")
            # Mock command line arguments for orchestrate (no category = run all configured)
            with patch('sys.argv', ['orchestrate.py']):
                orchestrate.main()
            
            # Verify scraping outputs
            output_dir = Path(config.get("paths.output_dir"))
            assert output_dir.exists(), "Output directory should be created after scraping"
            
            # Should have date-based subdirectories
            date_dirs = [d for d in output_dir.iterdir() if d.is_dir()]
            assert len(date_dirs) >= 1, "Should create at least one date directory"
            
            # Check for category directories and JSON files
            date_dir = date_dirs[0]  # Use the first (likely only) date directory
            
            # Should have directories for all configured categories
            category_dirs = [d for d in date_dir.iterdir() if d.is_dir()]
            assert len(category_dirs) >= 1, "Should create category directories"
            
            # Check for JSON files in all scraped categories
            total_files = 0
            for category_dir in category_dirs:
                json_files = list(category_dir.glob("*.json"))
                assert len(json_files) >= 1, f"Should create JSON files for {category_dir.name} funds"
                total_files += len(json_files)
                print(f"✅ Scraped {len(json_files)} {category_dir.name} funds successfully")
            
            print(f"✅ Total scraped files: {total_files}")
            
            # Verify JSON structure of scraped data (using first file found)
            first_json_file = next(category_dirs[0].glob("*.json"))
            with open(first_json_file) as f:
                scraped_data = json.load(f)
                assert "data" in scraped_data, "Scraped JSON should contain 'data' key"
                
                data = scraped_data["data"]
                assert "fund_info" in data, "Should contain fund_info"
                assert "top_holdings" in data, "Should contain top_holdings"
                
                # Basic validation of fund info
                fund_info = data["fund_info"]
                assert "fund_name" in fund_info, "Fund info should contain fund_name"
                
                # Basic validation of holdings
                holdings = data["top_holdings"]
                assert isinstance(holdings, list), "Holdings should be a list"
                if holdings:  # If we have holdings data
                    holding = holdings[0]
                    assert "company_name" in holding, "Holdings should contain company_name"
                    assert "allocation_percentage" in holding, "Holdings should contain allocation_percentage"
            
            print("✅ Scraping completed and validated")
            
            # Step 2: Run analysis - process all categories that were scraped
            print("\n📊 Running analysis...")
            # Mock command line arguments for analyze (no category = run all scraped)
            with patch('sys.argv', ['analyze.py']):
                analyze.main()
            
            # Verify analysis outputs
            analysis_dir = Path(config.get("paths.analysis_dir"))
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
                    "top_by_total_weight"
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
                    # Fix: Use 'name' instead of 'company_name' based on the error we saw
                    company_fields = ["name", "fund_count", "total_weight", "avg_weight"]
                    for field in company_fields:
                        assert field in company, f"Company data should contain '{field}' field"
            
            print("✅ Analysis completed and validated")
            print(f"📁 Test workspace: {workspace_path}")
            print(f"📄 Scraped {total_files} fund files")
            print(f"📊 Generated analysis for {len(analysis_files)} categories")
            
        finally:
            # Restore original working directory
            os.chdir(original_cwd)