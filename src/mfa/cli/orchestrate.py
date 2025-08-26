from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import orjson

from mfa.config.settings import config
from mfa.logging.logger import logger, setup_logging
from mfa.scraping.zerodha_coin import ZerodhaCoinScraper
from mfa.scraping.core.playwright_scraper import PlaywrightSession


def _today_str() -> str:
    return datetime.utcnow().strftime("%Y%m%d")


def _category_dir(root: Path, category: str) -> Path:
    d = root / _today_str() / category
    d.mkdir(parents=True, exist_ok=True)
    return d


def _safe_name_from_url(url: str) -> str:
    parts = url.rstrip("/").split("/")
    tail = parts[-2:] if len(parts) >= 2 else parts
    return "_".join(tail)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape funds by category from config")
    parser.add_argument(
        "--category",
        "-c",
        help="Category key under 'funds' to process (e.g., largeCap). If omitted, process all.",
    )
    return parser.parse_args()


def main() -> None:
    config.ensure_directories()
    setup_logging("outputs")

    output_root = Path(str(config.get("paths.output_dir") or "outputs/extracted_json"))
    funds: Dict[str, List[str]] = config.get("funds", {}) or {}
    if not funds:
        logger.warning("No funds configured under 'funds' in config.yaml")
        return

    args = _parse_args()
    category_arg = (args.category or "").strip() if args else ""

    selected: Dict[str, List[str]]
    if category_arg:
        if category_arg not in funds:
            logger.error(
                "Unknown category '{}'. Available: {}",
                category_arg,
                ", ".join(sorted(funds.keys())),
            )
            return
        selected = {category_arg: funds[category_arg]}
    else:
        selected = funds

    logger.info("Starting orchestrator for categories: {}", ", ".join(sorted(selected.keys())))
    for category, urls in selected.items():
        target_dir = _category_dir(output_root, category)
        logger.info("Category '{}' -> {} URLs -> {}", category, len(urls), target_dir)
        scraper = ZerodhaCoinScraper(session=PlaywrightSession(headless=True, nav_timeout_ms=3000))
        try:
            for url in urls:
                try:
                    logger.info("Processing URL: {}", url)
                    result = scraper.scrape(url)
                    fname = f"coin_{_safe_name_from_url(url)}.json"
                    out = target_dir / fname
                    with open(out, "wb") as fh:
                        fh.write(orjson.dumps(result, option=orjson.OPT_INDENT_2))
                    logger.info("Saved {}", out)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Failed to process {}: {}", url, exc)
        finally:
            pass


if __name__ == "__main__":
    main()


