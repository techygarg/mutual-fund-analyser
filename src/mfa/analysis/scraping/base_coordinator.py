"""
Base scraping coordinator with direct config access.

This module provides shared scraping functionality that can be reused
across different scraping strategies with simplified interfaces.
"""

from __future__ import annotations

import time
from typing import Any

from mfa.config.settings import ConfigProvider
from mfa.logging.logger import logger
from mfa.scraping.zerodha_coin import ZerodhaCoinScraper
from mfa.storage.path_generator import PathGenerator


class BaseScrapingCoordinator:
    """Base class for scraping coordinators with dependency injection."""

    def __init__(self, config_provider: ConfigProvider):
        """
        Initialize base coordinator with injected config provider.

        Args:
            config_provider: Configuration provider instance
        """
        self.config_provider = config_provider
        self.path_generator = PathGenerator(config_provider)
        self._scraper: ZerodhaCoinScraper | None = None

    def _get_scraper(self) -> ZerodhaCoinScraper:
        """Get or create a scraper instance."""
        if self._scraper is None:
            settings = self._get_scraping_settings()
            self._scraper = ZerodhaCoinScraper(
                headless=settings["headless"], nav_timeout_ms=settings["timeout_seconds"] * 1000
            )
        return self._scraper

    def _get_scraping_settings(self) -> dict[str, Any]:
        """Get scraping settings from config."""
        config = self.config_provider.get_config()
        scraping_config = config.scraping
        return {
            "headless": scraping_config.headless,
            "timeout_seconds": scraping_config.timeout_seconds,
            "delay_seconds": scraping_config.delay_between_requests,
            "save_extracted_json": scraping_config.save_extracted_json,
        }

    def _scrape_urls_with_delay(
        self,
        urls: list[str],
        max_holdings: int,
        category: str,
        storage_config: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Scrape a list of URLs with proper delays between requests.

        Simplified interface - storage_config contains all needed info.
        """
        scraper = self._get_scraper()
        results = []
        settings = self._get_scraping_settings()

        for i, url in enumerate(urls):
            try:
                logger.info(f"Scraping {i + 1}/{len(urls)}: {url}")

                result = scraper.scrape(
                    url=url, max_holdings=max_holdings, storage_config=storage_config
                )
                results.append(result)

                # Add delay between requests (except for the last one)
                if i < len(urls) - 1 and settings["delay_seconds"] > 0:
                    logger.debug(f"Waiting {settings['delay_seconds']}s before next request...")
                    time.sleep(settings["delay_seconds"])

            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
                # Continue with other URLs even if one fails
                continue

        return results

    def _log_scraping_start(self, strategy: str, total_urls: int) -> None:
        """Log the start of scraping process."""
        logger.info(f"🕷️  Starting {strategy} scraping for {total_urls} URLs")

    def _log_scraping_complete(self, strategy: str, successful: int, total: int) -> None:
        """Log the completion of scraping process."""
        logger.info(f"✅ {strategy} scraping completed: {successful}/{total} URLs successful")
