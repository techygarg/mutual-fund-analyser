"""
API-based scraping coordinator for mutual fund data.

This module provides coordination for API-based scraping, following the same
interface as other scraping coordinators but using HTTP APIs instead of browser automation.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from mfa.analysis.interfaces import DataRequirement, IScrapingCoordinator
from mfa.analysis.scraping.base_coordinator import BaseScrapingCoordinator
from mfa.config.settings import ConfigProvider
from mfa.scraping.zerodha_api import ZerodhaAPIFundScraper


class APIScrapingCoordinator(BaseScrapingCoordinator, IScrapingCoordinator):
    """
    Coordinator for API-based scraping of mutual fund data.

    Handles fund data extraction using HTTP APIs, providing faster and more
    reliable data collection compared to browser automation approaches.
    """

    def __init__(self, config_provider: ConfigProvider) -> None:
        """
        Initialize API scraping coordinator.

        Args:
            config_provider: Configuration provider instance
        """
        super().__init__(config_provider)
        self._api_scraper: ZerodhaAPIFundScraper | None = None

    def scrape_for_requirement(self, requirement: DataRequirement) -> dict[str, Any]:
        """
        Scrape fund data using APIs based on requirements.
        
        Supports both flat URL lists (portfolio) and categorized URLs (holdings).

        Args:
            requirement: Data requirement specification

        Returns:
            Dictionary with scraped data information and file paths

        Raises:
            ValueError: If analysis configuration is not found
        """
        analysis_id = requirement.metadata.get("analysis_id", "default")
        categories = requirement.metadata.get("categories", {})

        # Read configuration for this analysis
        config = self.config_provider.get_config()
        analysis_config = config.get_analysis(analysis_id)

        if not analysis_config:
            raise ValueError(f"Analysis config not found: {analysis_id}")

        # Extract scraping parameters
        max_holdings = getattr(analysis_config.params, "max_holdings", 50)
        delay_between_requests = config.scraping.delay_between_requests

        logger.debug(
            f"🔧 API scraping config: max_holdings={max_holdings}, delay={delay_between_requests}s"
        )

        # Initialize API scraper
        self._api_scraper = ZerodhaAPIFundScraper(delay_between_requests=delay_between_requests)

        try:
            # Handle categorized URLs (holdings analysis)
            if categories:
                return self._scrape_categorized_urls(categories, analysis_config, max_holdings)
            # Handle flat URL list (portfolio analysis)
            else:
                return self._scrape_flat_urls(requirement.urls, analysis_config, max_holdings)

        finally:
            # Ensure scraper cleanup
            self.close_session()

    def _build_storage_config_for_api(self, analysis_config: Any) -> dict[str, Any]:
        """Build storage configuration for API scraping."""
        config = self.config_provider.get_config()

        # Derive analysis folder name
        analysis_type_value = (
            "portfolio"
            if getattr(analysis_config, "type", "") == "portfolio-composition"
            else analysis_config.type.split("-")[-1]
        )

        storage_config = {
            "should_save": True,
            "base_dir": config.paths.output_dir,
            "category": analysis_type_value,  # portfolio, holdings, etc.
            "date": None,  # Will be auto-generated
            "url_path_template": "api_{fund_id}_{fund_name}",
        }

        logger.debug(f"📁 Storage config: {storage_config}")
        return storage_config

    def _scrape_urls_with_api(
        self, urls: list[str], max_holdings: int, storage_config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Scrape multiple URLs using API with delay between requests.

        Args:
            urls: List of fund URLs to scrape
            max_holdings: Maximum holdings per fund
            storage_config: Storage configuration

        Returns:
            List of scraping results
        """
        results = []

        for i, url in enumerate(urls, 1):
            try:
                logger.info(f"Scraping {i}/{len(urls)}: {url}")

                # Scrape this URL
                if self._api_scraper is None:
                    raise RuntimeError("API scraper not initialized")

                document = self._api_scraper.scrape(
                    url=url, max_holdings=max_holdings, storage_config=storage_config
                )

                # Build result metadata
                result = {
                    "url": url,
                    "status": "success",
                    "holdings_count": len(document.data.top_holdings),
                    "fund_name": document.data.fund_info.fund_name,
                    "extraction_timestamp": document.extraction_timestamp.isoformat(),
                }

                results.append(result)
                logger.debug(
                    f"✅ Successfully scraped {result['holdings_count']} holdings from {url}"
                )

            except Exception as e:
                logger.error(f"❌ Failed to scrape {url}: {e}")
                # Add failed result
                results.append(
                    {
                        "url": url,
                        "status": "failed",
                        "error": str(e),
                    }
                )

            # Add delay before next request (except for last URL)
            if i < len(urls):
                delay = self.config_provider.get_config().scraping.delay_between_requests
                if delay > 0:
                    logger.debug(f"Waiting {delay:.1f}s before next request...")
                    import time

                    time.sleep(delay)

        return results

    def _generate_expected_file_paths(
        self, urls: list[str], storage_config: dict[str, Any]
    ) -> list[str]:
        """
        Generate expected file paths for scraped data.

        Args:
            urls: URLs that were scraped
            storage_config: Storage configuration

        Returns:
            List of expected file paths
        """
        from mfa.storage.path_generator import PathGenerator

        path_generator = PathGenerator(self.config_provider)
        file_paths = []

        for url in urls:
            try:
                # Generate the path that would be used for this URL
                expected_path = path_generator.generate_scraped_data_path(
                    url=url,
                    category=storage_config.get("category", ""),
                    analysis_config=storage_config,
                )
                file_paths.append(str(expected_path))
            except Exception as e:
                logger.warning(f"⚠️ Could not generate path for {url}: {e}")

        return file_paths

    def _scrape_categorized_urls(
        self, categories: dict[str, list[str]], analysis_config: Any, max_holdings: int
    ) -> dict[str, Any]:
        """
        Handle category-based scraping for holdings analysis.
        
        Args:
            categories: Dictionary mapping category names to URL lists
            analysis_config: Analysis configuration
            max_holdings: Maximum holdings per fund
            
        Returns:
            Dictionary with categorized file paths and scraping results
        """
        logger.info(f"🗂️ Starting categorized API scraping for {len(categories)} categories")
        
        all_results = []
        category_files = {}
        total_urls = sum(len(urls) for urls in categories.values())
        
        self._log_scraping_start("categorized API", total_urls)
        
        for category, urls in categories.items():
            logger.info(f"📊 Scraping category '{category}' with {len(urls)} funds")
            
            # Build storage config for this category
            storage_config = self._build_storage_config_for_category(analysis_config, category)
            
            # Scrape all URLs in this category
            category_results = self._scrape_urls_with_api(urls, max_holdings, storage_config)
            
            # Generate file paths for this category
            category_file_paths = self._generate_expected_file_paths(urls, storage_config)
            
            category_files[category] = category_file_paths
            all_results.extend(category_results)
            
            logger.info(f"   ✅ {category}: scraped {len(category_results)} funds")

        successful_results = [r for r in all_results if r.get("status") == "success"]
        self._log_scraping_complete("categorized API", len(successful_results), len(all_results))
        
        return {
            "strategy": "api_scraping",
            "data": {"api": all_results},
            "file_paths": category_files,  # Categorized paths for holdings analysis
        }

    def _scrape_flat_urls(
        self, urls: list[str], analysis_config: Any, max_holdings: int
    ) -> dict[str, Any]:
        """
        Handle flat URL list scraping for portfolio analysis.
        
        Args:
            urls: List of URLs to scrape
            analysis_config: Analysis configuration
            max_holdings: Maximum holdings per fund
            
        Returns:
            Dictionary with flat file paths and scraping results
        """
        logger.info(f"📋 Starting flat API scraping for {len(urls)} funds")
        
        self._log_scraping_start("flat API", len(urls))
        
        # Build storage configuration
        storage_config = self._build_storage_config_for_api(analysis_config)
        
        # Scrape all URLs
        results = self._scrape_urls_with_api(urls, max_holdings, storage_config)
        
        # Generate file paths
        file_paths = self._generate_expected_file_paths(urls, storage_config)
        
        successful_results = [r for r in results if r.get("status") == "success"]
        self._log_scraping_complete("flat API", len(successful_results), len(results))
        
        return {
            "strategy": "api_scraping", 
            "data": {"api": results},
            "file_paths": {"targeted": file_paths},  # Flat paths for portfolio analysis
        }

    def _build_storage_config_for_category(self, analysis_config: Any, category: str) -> dict[str, Any]:
        """Build storage configuration for a specific category."""
        config = self.config_provider.get_config()

        # Extract analysis type from config instead of hardcoding
        analysis_type = getattr(analysis_config, "type", "default")
        
        storage_config = {
            "should_save": True,
            "base_dir": config.paths.output_dir,
            "category": category,  # Use the specific category (largeCap, midCap, etc.)
            "date": None,  # Will be auto-generated
            "url_path_template": "api_{fund_id}_{fund_name}",
            "analysis_type": analysis_type,  # Use actual analysis type from config
            "type": analysis_type,  # Also set 'type' for compatibility with PathGenerator
        }

        logger.debug(f"📁 Category storage config for '{category}': {storage_config}")
        return storage_config

    def close_session(self) -> None:
        """Close API scraper and clean up resources."""
        if self._api_scraper:
            # Note: ZerodhaAPIFundScraper might not have a close() method
            # but we'll implement it for consistency
            if hasattr(self._api_scraper, 'close'):
                self._api_scraper.close()
            self._api_scraper = None
            logger.debug("🔒 Closed API scraper session")


# Register the coordinator with factory (if needed)
# This will be handled in the factory update step
