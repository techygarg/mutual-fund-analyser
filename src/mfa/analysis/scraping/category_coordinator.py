"""
Category-based scraping coordinator.

This coordinator handles scraping funds organized by categories,
which is used by the holdings analysis.
"""
from __future__ import annotations

from typing import Any, Dict

from mfa.logging.logger import logger

from ..factories import register_coordinator
from ..interfaces import DataRequirement, IScrapingCoordinator
from .base_coordinator import BaseScrapingCoordinator


@register_coordinator("categories")
class CategoryScrapingCoordinator(BaseScrapingCoordinator, IScrapingCoordinator):
    """Scraping coordinator for category-based fund collection."""
    
    def scrape_for_requirement(self, requirement: DataRequirement) -> Dict[str, Any]:
        """Scrape funds organized by categories with hybrid template support."""
        categories = requirement.metadata["categories"]
        
        # Get scraping parameters from requirement metadata
        max_holdings = requirement.metadata.get("max_holdings", 10)
        analysis_config = requirement.metadata.get("analysis_config", {})
        
        # Calculate total URLs for logging
        total_urls = sum(len(urls) for urls in categories.values())
        self._log_scraping_start("category-based", total_urls)
        
        scraped_data = {
            "strategy": "categories",
            "data": {}
        }
        
        successful_scrapes = 0
        
        for category, urls in categories.items():
            logger.info(f"📂 Scraping category: {category} ({len(urls)} funds)")
            
            category_results = self._scrape_urls_with_delay(
                urls, 
                max_holdings=max_holdings, 
                category=category, 
                analysis_config=analysis_config
            )
            scraped_data["data"][category] = category_results
            
            successful_scrapes += len(category_results)
            logger.info(f"   ✅ Category '{category}': {len(category_results)}/{len(urls)} funds scraped")
        
        self._log_scraping_complete("category-based", successful_scrapes, total_urls)
        return scraped_data
    

