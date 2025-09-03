from __future__ import annotations

import argparse

from mfa.config.settings import ConfigProvider, create_config_provider
from mfa.logging.logger import setup_logging
from mfa.orchestration.analysis_orchestrator import AnalysisOrchestrator

# Import analyzers and coordinators to ensure they get registered
from mfa.analysis.analyzers.holdings import HoldingsAnalyzer
from mfa.analysis.scraping.category_coordinator import CategoryScrapingCoordinator
from mfa.analysis.scraping.targeted_coordinator import TargetedScrapingCoordinator


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MFA analysis")
    parser.add_argument("analysis_type", nargs="?", 
                       help="Analysis type to run (e.g., 'holdings'). If not specified, runs all enabled analyses.")
    parser.add_argument("--date", help="Date (YYYYMMDD) for analysis")
    parser.add_argument("--list", action="store_true", help="List available analysis types")
    parser.add_argument("--status", action="store_true", help="Show analysis status")
    return parser.parse_args()


def main() -> None:
    setup_logging()

    args = _parse_args()

    try:
        # Create configuration provider using dependency injection
        config_provider = create_config_provider()

        # Ensure directories exist
        config = config_provider.get_config()
        config.ensure_directories()

        # Create orchestrator with injected config provider
        orchestrator = AnalysisOrchestrator(config_provider)
    except Exception as e:
        print(f"\n❌ Failed to initialize application: {e}")
        import sys
        sys.exit(1)

    if args.list:
        analyses = orchestrator.list_available_analyses()
        print("Available analyses:")
        for name in analyses:
            print(f"  - {name}")
        return
    
    if args.status:
        status = orchestrator.get_analysis_status()
        print("Analysis status:")
        for name, info in status.items():
            enabled_str = "enabled" if info["enabled"] else "disabled"
            print(f"  {name} ({info['type']}) - {enabled_str} - {info['strategy']} strategy")
        return

    try:
        orchestrator.run_analysis(args.analysis_type, args.date)
        print("\n🎉 Analysis orchestration completed successfully!")
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()