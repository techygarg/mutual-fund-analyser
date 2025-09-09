"""
Shared pipeline execution utilities for integration tests.

Simple, focused utilities for running analysis pipelines.
"""

from typing import Dict, Any
from mfa.orchestration.analysis_orchestrator import AnalysisOrchestrator


def run_analysis_pipeline(analysis_type: str, config_provider) -> None:
    """
    Run a complete analysis pipeline.

    Args:
        analysis_type: Type of analysis to run (e.g., 'holdings', 'portfolio')
        config_provider: Configuration provider instance
    """
    print(f"\n🚀 Running {analysis_type} analysis pipeline...")

    orchestrator = AnalysisOrchestrator(config_provider)
    orchestrator.run_analysis(analysis_type)

    print(f"✅ {analysis_type} analysis completed successfully")


def verify_config_loaded(analysis_type: str, config_provider) -> Dict[str, Any]:
    """
    Verify that configuration is loaded correctly for the analysis.

    Args:
        analysis_type: Type of analysis
        config_provider: Configuration provider instance

    Returns:
        Analysis configuration data
    """
    config = config_provider.get_config()
    analysis_config = config.get_analysis(analysis_type)

    if not analysis_config:
        raise ValueError(f"Analysis configuration not found: {analysis_type}")

    print(f"🔧 Configuration loaded for {analysis_type} analysis")
    return analysis_config
