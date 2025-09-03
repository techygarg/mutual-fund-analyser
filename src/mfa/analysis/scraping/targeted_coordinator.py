"""
Targeted fund scraping coordinator with direct config access.

This coordinator handles scraping specific fund URLs,
which is used by portfolio analysis.
"""
from __future__ import annotations

from typing import Any, Dict

from mfa.config.settings import ConfigProvider
from mfa.logging.logger import logger

from ..factories import register_coordinator
from ..interfaces import DataRequirement, IScrapingCoordinator
from .base_coordinator import BaseScrapingCoordinator


@register_coordinator("targeted_funds")
class TargetedScrapingCoordinator(BaseScrapingCoordinator, IScrapingCoordinator):
    """Scraping coordinator for targeted fund collection with file-based output."""

    def __init__(self, config_provider: ConfigProvider):
        """
        Initialize targeted coordinator with injected config provider.

        Args:
            config_provider: Configuration provider instance
        """
        super().__init__(config_provider)
    
    def scrape_for_requirement(self, requirement: DataRequirement) -> Dict[str, Any]:
        """
        Scrape specific fund URLs and save to files.
        
        Returns file paths for analysis instead of in-memory data.
        """
        urls = requirement.urls
        analysis_id = requirement.metadata.get("analysis_id", "default")
        
        # Read config directly for this analysis
        config = self.config_provider.get_config()
        analysis_config = getattr(config.analyses, analysis_id, None)
        
        if not analysis_config:
            raise ValueError(f"Analysis config not found: {analysis_id}")
        
        max_holdings = analysis_config.params.max_holdings
        
        self._log_scraping_start("targeted", len(urls))
        
        # Build storage config
        storage_config = self._build_storage_config_for_targeted(analysis_config)
        
        # Scrape and save to files
        results = self._scrape_urls_with_delay(urls, max_holdings, "targeted", storage_config)
        
        # Generate file paths that were created
        file_paths = self._generate_expected_file_paths(urls, storage_config)
        
        scraped_data = {
            "strategy": "targeted_funds",
            "data": {"targeted": results},
            "file_paths": {"targeted": file_paths}
        }
        
        self._log_scraping_complete("targeted", len(results), len(urls))
        return scraped_data
    
    def _build_storage_config_for_targeted(self, analysis_config: Any) -> Dict[str, Any]:
        """Build storage configuration for targeted scraping."""
        config = self.config_provider.get_config()
        
        storage_config = {
            "should_save": True,
            "base_dir": config.paths.output_dir,
            "category": "targeted",  # No specific category for targeted scraping
            "filename_prefix": config.output.filename_prefix,
            "analysis_type": analysis_config.type.split("-")[-1]
        }
        
        # Add custom path template if specified
        if hasattr(analysis_config, 'path_template') and analysis_config.path_template:
            storage_config["path_template"] = analysis_config.path_template
        
        return storage_config
    
    def _generate_expected_file_paths(self, urls, storage_config: Dict[str, Any]) -> list[str]:
        """Generate the expected file paths where scraped data was saved."""
        from datetime import datetime
        from mfa.storage.json_store import JsonStore
        
        file_paths = []
        date_str = datetime.now().strftime("%Y%m%d")
        
        for url in urls:
            # Use the same logic as JsonStore to predict file paths
            fund_identifier = JsonStore._extract_fund_identifier_from_url(url)
            filename = f"{storage_config['filename_prefix']}{fund_identifier}.json"
            
            # Build directory path (same logic as JsonStore)
            if storage_config.get("path_template"):
                directory_path = JsonStore._resolve_path_template(
                    storage_config["path_template"],
                    storage_config["base_dir"],
                    date_str,
                    storage_config["analysis_type"],
                    storage_config["category"]
                )
            else:
                # Use smart defaults
                directory_path = f"{storage_config['base_dir']}/{date_str}/{storage_config['analysis_type']}"
            
            file_path = f"{directory_path}/{filename}"
            file_paths.append(file_path)
        
        return file_paths