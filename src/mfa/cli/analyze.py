from __future__ import annotations

import argparse

# Import analyzers and coordinators to ensure they get registered
import mfa.analysis.analyzers.holdings  # noqa: F401 - Registers holdings analyzer
import mfa.analysis.analyzers.portfolio  # noqa: F401 - Registers portfolio analyzer
import mfa.analysis.scraping.category_coordinator  # noqa: F401 - Registers category coordinator
import mfa.analysis.scraping.targeted_coordinator  # noqa: F401 - Registers targeted coordinator
from mfa.config.settings import create_config_provider
from mfa.logging.logger import setup_logging
from mfa.orchestration.analysis_orchestrator import AnalysisOrchestrator


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mutual Fund Analyzer - Extract and analyze fund holdings", prog="mfa-analyze"
    )
    parser.add_argument(
        "analysis_type",
        nargs="?",
        help="Analysis type to run (e.g., 'holdings'). Required unless using --list or --status.",
    )
    parser.add_argument(
        "--category", "-c", help="Fund category to analyze (largeCap, midCap, smallCap)"
    )
    parser.add_argument(
        "--date", "-d", help="Date for analysis (YYYYMMDD format). Defaults to today."
    )
    parser.add_argument(
        "--list", "-l", action="store_true", help="List available analysis types and exit"
    )
    parser.add_argument(
        "--status", "-s", action="store_true", help="Show current analysis configuration and exit"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--analysis-only",
        "--no-scrape",
        action="store_true",
        help="Skip scraping and run analysis on existing data only",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    # Setup logging based on verbosity
    if args.verbose:
        setup_logging("DEBUG")
    else:
        setup_logging()

    try:
        # Create configuration provider using dependency injection
        config_provider = create_config_provider()

        # Ensure directories exist
        config = config_provider.get_config()
        config.ensure_directories()

        # Create orchestrator with injected config provider
        orchestrator = AnalysisOrchestrator(config_provider)
    except Exception as e:
        print(f"\n❌ Failed to initialize Mutual Fund Analyzer: {e}")
        print("💡 Check your configuration and try again.")
        import sys

        sys.exit(1)

    # Handle informational commands
    if args.list:
        print("📋 Available analysis types:")
        analyses = orchestrator.list_available_analyses()
        for name in analyses:
            print(f"  • {name}")
        print(
            f"\n💡 Run 'mfa-analyze {analyses[0] if analyses else 'analysis-type'}' to start analysis"
        )
        return

    if args.status:
        print("📊 Analysis Configuration Status:")
        try:
            status = orchestrator.get_analysis_status()
            for name, info in status.items():
                enabled_icon = "✅" if info["enabled"] else "❌"
                print(f"  {enabled_icon} {name} ({info['type']}) - {info['strategy']} strategy")
        except Exception as e:
            print(f"  ❌ Could not retrieve status: {e}")
        return

    # Validate analysis_type is provided for actual analysis
    if not args.analysis_type:
        print("❌ Error: analysis_type is required when not using --list or --status")
        print("💡 Use 'mfa-analyze --help' for usage information")
        import sys

        sys.exit(1)

    # Main analysis execution
    try:
        print("🚀 Starting Mutual Fund Analysis...")
        if args.category:
            print(f"📂 Category: {args.category}")
        if args.date:
            print(f"📅 Date: {args.date}")
        print(f"🔍 Analysis: {args.analysis_type}")

        if args.analysis_only:
            print("🔄 Analysis-only mode: skipping scraping")

        orchestrator.run_analysis(args.analysis_type, args.date, args.analysis_only)

        print("\n🎉 Analysis completed successfully!")
        print("📊 View results at: http://localhost:8787 (run 'make dashboard')")

    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        print("💡 Check the troubleshooting guide for common solutions.")
        raise


if __name__ == "__main__":
    main()
