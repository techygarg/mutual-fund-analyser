"""
Targeted fund scraping coordinator with direct config access.

This coordinator handles scraping specific fund URLs,
which is used by portfolio analysis.
"""

from __future__ import annotations

from typing import Any

from mfa.config.settings import ConfigProvider

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

    def scrape_for_requirement(self, requirement: DataRequirement) -> dict[str, Any]:
        """
        Scrape specific fund URLs and save to files.

        Returns file paths for analysis instead of in-memory data.
        Uses configurable scraper type (API or Playwright).
        """
        urls = requirement.urls
        analysis_id = requirement.metadata.get("analysis_id", "default")

        # Read config directly for this analysis
        config = self.config_provider.get_config()
        analysis_config = config.get_analysis(analysis_id)

        if not analysis_config:
            raise ValueError(f"Analysis config not found: {analysis_id}")

        max_holdings = analysis_config.params.max_holdings or 50

        # Get scraper type from analysis config
        scraper_type = getattr(analysis_config.data_requirements, "scraper_type", "api")

        self._log_scraping_start(f"targeted ({scraper_type})", len(urls))

        try:
            # Build storage config
            storage_config = self._build_storage_config_for_targeted(analysis_config, analysis_id)

            # Scrape and save to files using configured scraper type
            results = self._scrape_urls_with_delay(urls, max_holdings, scraper_type, storage_config)

            # Generate file paths that were created
            file_paths = self._generate_expected_file_paths(urls, storage_config)

            scraped_data = {
                "strategy": "targeted_funds",
                "data": {"targeted": results},
                "file_paths": {"targeted": file_paths},
            }

        finally:
            # Ensure session cleanup
            self.close_session()

        self._log_scraping_complete("targeted", len(results), len(urls))
        return scraped_data

    def _build_storage_config_for_targeted(
        self, analysis_config: Any, analysis_id: str
    ) -> dict[str, Any]:
        """Build storage configuration for targeted scraping."""
        config = self.config_provider.get_config()

        # Use analysis_id directly, but map portfolio to portfolio folder
        analysis_type_value = "portfolio" if analysis_id == "portfolio" else analysis_id

        storage_config = {
            "should_save": True,
            "base_dir": config.paths.output_dir,
            # For portfolio analysis we do not want a nested category folder
            # so keep category empty to make path: {output_dir}/{date}/{analysis_type}
            "category": "",
            "filename_prefix": "coin_",
            "type": analysis_type_value,  # PathGenerator expects "type"
        }

        return storage_config

    def _generate_expected_file_paths(
        self, urls: list[str], storage_config: dict[str, Any]
    ) -> list[str]:
        """Generate the expected file paths where scraped data was saved."""
        from datetime import datetime

        file_paths: list[str] = []
        date_str = datetime.now().strftime("%Y%m%d")

        # Create analysis config for path generation
        analysis_config = {
            "type": storage_config.get("type", "default"),
            "path_template": storage_config.get("path_template"),
        }

        for url in urls:
            file_path = self.path_generator.generate_scraped_data_path(
                url=url,
                category=storage_config.get("category", ""),
                analysis_config=analysis_config,
                date_str=date_str,
            )
            file_paths.append(str(file_path))

        return file_paths
