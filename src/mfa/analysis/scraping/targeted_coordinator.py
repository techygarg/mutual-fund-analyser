"""
Targeted funds scraping coordinator.

This coordinator handles scraping specific fund URLs,
which will be used by portfolio analysis.
"""
from __future__ import annotations

from typing import Any, Dict

from ..factories import register_coordinator
from ..interfaces import DataRequirement, IScrapingCoordinator
from .base_coordinator import BaseScrapingCoordinator


@register_coordinator("targeted_funds")
class TargetedScrapingCoordinator(BaseScrapingCoordinator, IScrapingCoordinator):
    """Scraping coordinator for targeted fund collection."""
    
    def scrape_for_requirement(self, requirement: DataRequirement) -> Dict[str, Any]:
        """Scrape specific fund URLs."""
        urls = requirement.urls
        
        # Get scraping parameters from requirement metadata
        max_holdings = requirement.metadata.get("max_holdings", 10)
        output_path_template = requirement.metadata.get("output_path_template", None)
        
        self._log_scraping_start("targeted funds", len(urls))
        
        results = self._scrape_urls_with_delay(urls, max_holdings=max_holdings, output_path_template=output_path_template)
        
        scraped_data = {
            "strategy": "targeted_funds", 
            "data": {}
        }
        
        # Map results back to URLs for easy lookup
        for url, result in zip(urls, results):
            scraped_data["data"][url] = result
        
        self._log_scraping_complete("targeted funds", len(results), len(urls))
        return scraped_data
