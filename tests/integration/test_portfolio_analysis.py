"""
Integration test for portfolio analysis.

Tests the complete portfolio analysis pipeline using the shared framework.
"""

import pytest
from pathlib import Path

from tests.integration.fixtures.workspace import AnalysisWorkspace
from tests.integration.fixtures.pipeline import run_analysis_pipeline, verify_config_loaded
from tests.integration.validators.portfolio import (
    validate_portfolio_directory_structure,
    validate_portfolio_output_files, 
    validate_portfolio_analysis_content,
    validate_portfolio_extracted_data
)


class TestPortfolioAnalysis:
    """Integration test for portfolio analysis pipeline."""
    
    @pytest.fixture
    def test_workspace(self):
        """Create test workspace for portfolio analysis."""
        base_dir = Path(__file__).parent
        workspace = AnalysisWorkspace("portfolio", base_dir)
        
        # Setup with portfolio-specific config
        base_config = base_dir / "test_config.yaml"
        
        workspace.setup(base_config)
        
        try:
            yield workspace
        finally:
            workspace.cleanup()
    
    def test_portfolio_analysis_pipeline(self, test_workspace: AnalysisWorkspace):
        """Test the complete portfolio analysis pipeline."""
        # Verify configuration
        analysis_config = verify_config_loaded("portfolio", test_workspace.config_provider)
        self._verify_portfolio_config(analysis_config)
        
        # Run the pipeline
        run_analysis_pipeline("portfolio", test_workspace.config_provider)
        
        # Validate extracted data
        extracted_dir = test_workspace.get_extracted_dir()
        validate_portfolio_extracted_data(extracted_dir)
        
        # Validate analysis outputs
        analysis_dir = test_workspace.get_analysis_dir()
        portfolio_dir = validate_portfolio_directory_structure(analysis_dir)
        analysis_files = validate_portfolio_output_files(portfolio_dir)
        validated_data = validate_portfolio_analysis_content(analysis_files)
        
        # Verify results
        self._verify_portfolio_results(validated_data)
        
        print("✅ Portfolio analysis integration test completed successfully")
    
    def _verify_portfolio_config(self, analysis_config) -> None:
        """Verify portfolio configuration is correct."""
        # Check data requirements
        assert hasattr(analysis_config, 'data_requirements'), "Portfolio config should have data_requirements"
        assert hasattr(analysis_config.data_requirements, 'funds'), "Portfolio should have funds"
        
        funds = analysis_config.data_requirements.funds
        assert len(funds) >= 1, "Portfolio should have at least 1 fund for testing"
        
        # Check each fund has required fields
        for fund in funds:
            assert "url" in fund, "Each fund should have a URL"
            assert "units" in fund, "Each fund should have units"
        
        print(f"�� Portfolio config verified: {len(funds)} funds")
    
    def _verify_portfolio_results(self, validated_data) -> None:
        """Verify portfolio analysis results."""
        assert len(validated_data) >= 1, "Should have at least 1 portfolio analysis result"
        
        # Verify each portfolio result
        for data in validated_data:
            portfolio_summary = data["portfolio_summary"]
            assert portfolio_summary["fund_count"] >= 1, "Portfolio should have funds"
            assert portfolio_summary["unique_companies"] >= 0, "Portfolio should have companies"
            assert portfolio_summary["total_value"] >= 0, "Portfolio should have valid total value"
            
            # Verify structure completeness
            assert len(data["funds"]) == portfolio_summary["fund_count"], "Funds array should match fund_count"
            assert len(data["company_allocations"]) == portfolio_summary["unique_companies"], "Companies should match unique_companies"
            
        print(f"🎯 Portfolio results verified: {len(validated_data)} portfolio processed")
