"""
Base scraping coordinator with common functionality.

This module provides shared scraping functionality that can be reused
across different scraping strategies.
"""
from __future__ import annotations

import time
from abc import ABC
from typing import Any, Dict, List

from mfa.config.settings import ConfigProvider
from mfa.logging.logger import logger
from mfa.scraping.zerodha_coin import ZerodhaCoinScraper


class BaseScrapingCoordinator(ABC):
    """Base class for scraping coordinators with common functionality."""
    
    def __init__(self):
        self.config = ConfigProvider.get_instance()
        self._scraper = None
    
    def _get_scraper(self) -> ZerodhaCoinScraper:
        """Get or create a scraper instance."""
        if self._scraper is None:
            settings = self._get_scraping_settings()
            self._scraper = ZerodhaCoinScraper(
                headless=settings["headless"],
                nav_timeout_ms=settings["timeout_seconds"] * 1000
            )
        return self._scraper
    
    def _get_scraping_settings(self) -> Dict[str, Any]:
        """Get scraping settings from config."""
        # New type-safe way - no more string keys!
        scraping_config = self.config.get_config().scraping
        return {
            "headless": scraping_config.headless,
            "timeout_seconds": scraping_config.timeout_seconds,
            "delay_seconds": scraping_config.delay_between_requests,
            "save_extracted_json": scraping_config.save_extracted_json,
        }
    
    def _scrape_urls_with_delay(self, urls: List[str], max_holdings: int = 10, category: str = "", analysis_config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Scrape a list of URLs with proper delays between requests.
        
        This method now uses storage_config approach with hybrid template support,
        delegating all path generation to JSONStore.
        """
        scraper = self._get_scraper()
        results = []
        settings = self._get_scraping_settings()
        
        # Build storage configuration once with template support
        storage_config = self._build_storage_config(category, analysis_config) if settings["save_extracted_json"] else None
        
        for i, url in enumerate(urls):
            try:
                logger.info(f"Scraping {i+1}/{len(urls)}: {url}")
                
                result = scraper.scrape(
                    url=url, 
                    max_holdings=max_holdings, 
                    storage_config=storage_config
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
    
    def _build_storage_config(self, category: str, analysis_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Build storage configuration for scraped data with hybrid template support.
        
        This supports both smart defaults and custom path templates,
        delegating all path logic to JSONStore.
        """
        config = self.config.get_config()
        
        storage_config = {
            "should_save": True,
            "base_dir": config.paths.output_dir,
            "category": category,
            "filename_prefix": config.output.filename_prefix,
            "analysis_type": "default"  # Will be overridden by specific coordinators
        }
        
        # Add template if analysis has custom path configuration
        if analysis_config:
            if analysis_config.get("path_template"):
                storage_config["path_template"] = analysis_config["path_template"]
            
            # Extract analysis type from config
            if analysis_config.get("type"):
                # Convert "fund-holdings" -> "holdings", "portfolio-composition" -> "portfolio"
                analysis_type = analysis_config["type"].split("-")[-1]
                storage_config["analysis_type"] = analysis_type
        
        return storage_config
    
    def _log_scraping_start(self, strategy: str, total_urls: int) -> None:
        """Log the start of scraping process."""
        logger.info(f"🕷️  Starting {strategy} scraping for {total_urls} URLs")
    
    def _log_scraping_complete(self, strategy: str, successful: int, total: int) -> None:
        """Log the completion of scraping process."""
        logger.info(f"✅ {strategy} scraping completed: {successful}/{total} URLs successful")
    

