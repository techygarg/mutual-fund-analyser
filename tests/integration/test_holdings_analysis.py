"""
Integration test for holdings analysis.

Tests the complete holdings analysis pipeline using the shared framework.
"""

import pytest
from pathlib import Path

from tests.integration.fixtures.workspace import AnalysisWorkspace
from tests.integration.fixtures.pipeline import run_analysis_pipeline, verify_config_loaded
from tests.integration.validators.holdings import (
    validate_holdings_directory_structure,
    validate_holdings_output_files,
    validate_holdings_analysis_content,
    validate_holdings_extracted_data,
)


class TestHoldingsAnalysis:
    """Integration test for holdings analysis pipeline."""

    @pytest.fixture
    def test_workspace(self):
        """Create test workspace for holdings analysis."""
        base_dir = Path(__file__).parent
        workspace = AnalysisWorkspace("holdings", base_dir)

        # Setup with holdings-specific config
        base_config = base_dir / "test_config.yaml"

        workspace.setup(base_config)

        try:
            yield workspace
        finally:
            workspace.cleanup()

    def test_holdings_analysis_pipeline(self, test_workspace: AnalysisWorkspace):
        """Test the complete holdings analysis pipeline."""
        # Verify configuration
        analysis_config = verify_config_loaded("holdings", test_workspace.config_provider)
        self._verify_holdings_config(analysis_config)

        # Run the pipeline
        run_analysis_pipeline("holdings", test_workspace.config_provider)

        # Validate extracted data
        extracted_dir = test_workspace.get_extracted_dir()
        validate_holdings_extracted_data(extracted_dir)

        # Validate analysis outputs
        analysis_dir = test_workspace.get_analysis_dir()
        holdings_dir = validate_holdings_directory_structure(analysis_dir)
        analysis_files = validate_holdings_output_files(holdings_dir)
        validated_data = validate_holdings_analysis_content(analysis_files)

        # Verify results
        self._verify_holdings_results(validated_data)

        print("✅ Holdings analysis integration test completed successfully")

    def _verify_holdings_config(self, analysis_config) -> None:
        """Verify holdings configuration is correct."""
        # Check data requirements
        assert hasattr(analysis_config, "data_requirements"), (
            "Holdings config should have data_requirements"
        )
        assert hasattr(analysis_config.data_requirements, "categories"), (
            "Holdings should have categories"
        )

        categories = analysis_config.data_requirements.categories
        assert len(categories) >= 2, "Holdings should have at least 2 categories for testing"

        print(f"🔧 Holdings config verified: {len(categories)} categories")

    def _verify_holdings_results(self, validated_data) -> None:
        """Verify holdings analysis results."""
        assert len(validated_data) >= 1, "Should have at least 1 holdings analysis result"

        # Verify each category result
        for data in validated_data:
            assert data["total_funds"] >= 1, "Each category should have funds"
            assert data["unique_companies"] >= 0, "Each category should have companies"

        print(f"🎯 Holdings results verified: {len(validated_data)} categories processed")
