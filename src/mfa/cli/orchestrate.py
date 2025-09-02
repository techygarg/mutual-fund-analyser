from __future__ import annotations

import argparse

from mfa.config.settings import ConfigProvider
from mfa.logging.logger import setup_logging
from mfa.orchestration.analysis_orchestrator import AnalysisOrchestrator


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run analysis orchestration")
    parser.add_argument(
        "--analysis",
        "-a",
        help="Analysis type to run (e.g., 'holdings'). If omitted, runs all enabled analyses.",
    )
    parser.add_argument("--date", help="Date (YYYYMMDD) for analysis")
    return parser.parse_args()


def main() -> None:
    config_provider = ConfigProvider.get_instance()
    config = config_provider.get_config()
    config.ensure_directories()
    setup_logging("outputs")

    args = _parse_args()
    analysis_type = (args.analysis or "").strip() if args else None

    orchestrator = AnalysisOrchestrator()
    try:
        orchestrator.run_analysis(analysis_type, args.date)
        print("\n🎉 Analysis orchestration completed successfully!")
    except Exception as e:
        print(f"\n❌ Analysis orchestration failed: {e}")
        raise


if __name__ == "__main__":
    main()
