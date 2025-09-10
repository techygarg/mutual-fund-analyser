"""
Scraper factory for creating different types of scrapers.

This module provides a clean factory pattern for creating API-based or
Playwright-based scrapers with explicit configuration.
"""

from __future__ import annotations

from typing import Any, Protocol

from mfa.config.settings import ConfigProvider
from mfa.logging.logger import logger
from mfa.scraping.core.playwright_scraper import PlaywrightSession
from mfa.scraping.zerodha_api import ZerodhaAPIFundScraper
from mfa.scraping.zerodha_coin import ZerodhaCoinScraper


class IScraper(Protocol):
    """Interface that all scrapers must implement."""

    def scrape(
        self, url: str, max_holdings: int = 50, storage_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Scrape fund data from URL.

        Args:
            url: Fund URL to scrape
            max_holdings: Maximum holdings to extract
            storage_config: Optional storage configuration

        Returns:
            Scraped fund data as dictionary
        """
        ...

    def close(self) -> None:
        """Close scraper and clean up resources."""
        ...


class APIScraperAdapter:
    """Adapter to make ZerodhaAPIFundScraper compatible with IScraper interface."""

    def __init__(self, scraper: ZerodhaAPIFundScraper):
        self._scraper = scraper

    def scrape(
        self, url: str, max_holdings: int = 50, storage_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Scrape using API scraper and convert result to dict."""
        result = self._scraper.scrape(url, max_holdings, storage_config)
        # Convert ExtractedFundDocument to dict if needed
        if hasattr(result, 'model_dump'):
            return result.model_dump(mode="json")
        # This should not happen, but handle it gracefully
        return dict(result) if result else {}

    def close(self) -> None:
        """Close API scraper."""
        if hasattr(self._scraper, 'close'):
            self._scraper.close()


class PlaywrightScraperAdapter:
    """Adapter to make ZerodhaCoinScraper compatible with IScraper interface."""

    def __init__(self, scraper: ZerodhaCoinScraper):
        self._scraper = scraper

    def scrape(
        self, url: str, max_holdings: int = 50, storage_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Scrape using Playwright scraper."""
        return self._scraper.scrape(url, max_holdings, storage_config)

    def close(self) -> None:
        """Close Playwright scraper."""
        if hasattr(self._scraper, 'session') and hasattr(self._scraper.session, 'close'):
            self._scraper.session.close()


class ScraperFactory:
    """Factory for creating scraper instances based on type."""

    @staticmethod
    def create_scraper(scraper_type: str, config_provider: ConfigProvider) -> IScraper:
        """
        Create scraper based on type.

        Args:
            scraper_type: Type of scraper ("api" or "playwright")
            config_provider: Configuration provider instance

        Returns:
            Scraper instance implementing IScraper

        Raises:
            ValueError: If scraper_type is unknown
        """
        config = config_provider.get_config()

        if scraper_type == "api":
            logger.debug(f"🏭 Creating API scraper with {config.scraping.delay_between_requests}s delay")
            api_scraper = ZerodhaAPIFundScraper(delay_between_requests=config.scraping.delay_between_requests)
            return APIScraperAdapter(api_scraper)

        elif scraper_type == "playwright":
            logger.debug(
                f"🏭 Creating Playwright scraper (headless={config.scraping.headless}, "
                f"timeout={config.scraping.timeout_seconds}s)"
            )
            settings = config.scraping
            session = PlaywrightSession(
                headless=settings.headless, nav_timeout_ms=settings.timeout_seconds * 1000
            )
            session.open()
            playwright_scraper = ZerodhaCoinScraper(session=session)
            return PlaywrightScraperAdapter(playwright_scraper)

        else:
            raise ValueError(f"Unknown scraper type: {scraper_type}. Supported types: 'api', 'playwright'")

    @staticmethod
    def get_available_types() -> list[str]:
        """Get list of available scraper types."""
        return ["api", "playwright"]


