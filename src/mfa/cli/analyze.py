from __future__ import annotations

import argparse

from mfa.analysis.analyzer import FundAnalyzer
from mfa.config.settings import ConfigProvider
from mfa.logging.logger import setup_logging


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze fund holdings JSONs")
    parser.add_argument("--date", help="YYYYMMDD date folder under outputs/extracted_json")
    parser.add_argument("--category", help="Category to analyze (e.g., largeCap)")
    return parser.parse_args()


def main() -> None:
    config = ConfigProvider.get_instance()
    config.ensure_directories()
    setup_logging("outputs")

    args = _parse_args()

    analyzer = FundAnalyzer()
    try:
        result = analyzer.analyze(
            date=args.date,
            category=args.category
        )
        print(f"\n🎉 Analysis completed successfully!")
        print(f"📊 Analyzed {result.categories_analyzed}/{result.total_categories} categories")
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()