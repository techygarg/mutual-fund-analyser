from __future__ import annotations

import argparse

from mfa.config.settings import ConfigProvider
from mfa.logging.logger import setup_logging
from mfa.orchestration.orchestrator import Orchestrator


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape funds by category from config")
    parser.add_argument(
        "--category",
        "-c",
        help="Category key under 'funds' to process (e.g., largeCap). If omitted, process all.",
    )
    return parser.parse_args()


def main() -> None:
    config = ConfigProvider.get_instance()
    config.ensure_directories()
    setup_logging("outputs")

    args = _parse_args()
    category_arg = (args.category or "").strip() if args else ""

    orchestrator = Orchestrator()
    try:
        result = orchestrator.run(category=category_arg if category_arg else None)
        print(f"\n🎉 Orchestration completed successfully!")
        print(f"📊 Processed {result.processed_count}/{result.total_funds} funds")
    except Exception as e:
        print(f"\n❌ Orchestration failed: {e}")
        raise


if __name__ == "__main__":
    main()