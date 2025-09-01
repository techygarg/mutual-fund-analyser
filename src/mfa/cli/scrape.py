from __future__ import annotations

from pathlib import Path

import orjson

from mfa.config.settings import ConfigProvider
from mfa.logging.logger import logger, setup_logging
from mfa.scraping.zerodha_coin import ZerodhaCoinScraper
from mfa.utils.paths import ensure_parent


def _load_urls(urls_file: Path) -> list[str]:
    with open(urls_file, encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]


def _get_scraper():
    config = ConfigProvider.get_instance()
    headless = str(config.get("scraping.playwright.headless", "true")).lower() == "true"
    return ZerodhaCoinScraper(headless=headless)


def _save_raw_json(doc: dict, filename: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    ensure_parent(path)
    with open(path, "wb") as fh:
        fh.write(orjson.dumps(doc, option=orjson.OPT_INDENT_2))
    return path


def main() -> None:
    config = ConfigProvider.get_instance()
    config.ensure_directories()
    setup_logging("outputs")

    urls_path = Path(str(config.get("paths.urls_file")))
    output_dir = Path(str(config.get("paths.output_dir")))
    urls = _load_urls(urls_path)

    logger.info("Loaded {} URLs from {}", len(urls), urls_path)
    scraper = _get_scraper()
    for url in urls:
        if "coin.zerodha.com/mf/fund/" in url:
            doc = scraper.scrape(url)
            safe_name = url.rstrip("/").split("/")[-2]
            out_path = _save_raw_json(doc, f"coin_{safe_name}.json", output_dir)
            logger.info("Saved {}", out_path)
        else:
            logger.warning("Skipping unsupported URL: {}", url)


if __name__ == "__main__":
    main()
