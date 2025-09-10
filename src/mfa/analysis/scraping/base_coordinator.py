"""
Base scraping coordinator with configurable scraper types.

This module provides shared scraping functionality that can be reused
across different scraping strategies with any scraper type (API or Playwright).
"""

from __future__ import annotations

import time
from typing import Any

from mfa.config.settings import ConfigProvider
from mfa.logging.logger import logger
from mfa.scraping.scraper_factory import IScraper, ScraperFactory
from mfa.storage.path_generator import PathGenerator


class BaseScrapingCoordinator:
    """Base class for scraping coordinators with configurable scraper types."""

    def __init__(self, config_provider: ConfigProvider):
        """
        Initialize base coordinator with injected config provider.

        Args:
            config_provider: Configuration provider instance
        """
        self.config_provider = config_provider
        self.path_generator = PathGenerator(config_provider)
        self._scraper: IScraper | None = None

    def _get_scraper(self, scraper_type: str | None = None) -> IScraper:
        """
        Get scraper instance based on type.

        Args:
            scraper_type: Type of scraper to create ("api" or "playwright").
                         If None, uses default from config.

        Returns:
            Scraper instance implementing IScraper interface
        """
        if self._scraper is None:
            # Determine scraper type
            if scraper_type is None:
                config = self.config_provider.get_config()
                scraper_type = getattr(config.scraping, "default_scraper", "api")

            logger.debug(f"🔧 Creating {scraper_type} scraper")
            self._scraper = ScraperFactory.create_scraper(scraper_type, self.config_provider)

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
        scraper_type: str,
        storage_config: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Scrape a list of URLs with proper delays between requests.

        Args:
            urls: List of URLs to scrape
            max_holdings: Maximum holdings per fund
            scraper_type: Type of scraper to use ("api" or "playwright")
            storage_config: Optional storage configuration

        Returns:
            List of scraped fund data
        """
        scraper = self._get_scraper(scraper_type)
        results = []

        config = self.config_provider.get_config()
        delay_seconds = config.scraping.delay_between_requests

        for i, url in enumerate(urls):
            try:
                logger.info(f"Scraping {i + 1}/{len(urls)} with {scraper_type}: {url}")

                result = scraper.scrape(
                    url=url, max_holdings=max_holdings, storage_config=storage_config
                )
                results.append(result)

                # Add delay between requests (except for the last one)
                if i < len(urls) - 1 and delay_seconds > 0:
                    logger.debug(f"Waiting {delay_seconds}s before next request...")
                    time.sleep(delay_seconds)

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

    def close_session(self) -> None:
        """Close scraper and clean up resources."""
        if self._scraper is not None:
            logger.debug("🔒 Closing scraper session")
            self._scraper.close()
            self._scraper = None

    def __enter__(self) -> BaseScrapingCoordinator:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - ensures session cleanup."""
        self.close_session()
