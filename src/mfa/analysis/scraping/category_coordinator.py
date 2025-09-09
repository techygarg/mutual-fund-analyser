"""
Category-based scraping coordinator with direct config access.

This coordinator handles scraping funds organized by categories,
saves data to files, and provides file paths for analysis.
"""

from __future__ import annotations

from typing import Any

from mfa.config.settings import ConfigProvider
from mfa.logging.logger import logger

from ..factories import register_coordinator
from ..interfaces import DataRequirement, IScrapingCoordinator
from .base_coordinator import BaseScrapingCoordinator


@register_coordinator("categories")
class CategoryScrapingCoordinator(BaseScrapingCoordinator, IScrapingCoordinator):
    """Scraping coordinator for category-based fund collection with file-based output."""

    def __init__(self, config_provider: ConfigProvider):
        """
        Initialize category coordinator with injected config provider.

        Args:
            config_provider: Configuration provider instance
        """
        super().__init__(config_provider)

    def scrape_for_requirement(self, requirement: DataRequirement) -> dict[str, Any]:
        """
        Scrape funds organized by categories and save to files.

        Returns file paths for analysis instead of in-memory data.
        Uses shared Playwright session for efficiency.
        """
        categories = requirement.metadata["categories"]
        analysis_id = requirement.metadata.get("analysis_id", "default")

        # Read config directly for this analysis
        config = self.config_provider.get_config()
        analysis_config = config.analyses.get(analysis_id)  # Dictionary access

        if not analysis_config:
            raise ValueError(f"Analysis config not found: {analysis_id}")

        max_holdings = analysis_config.params.max_holdings or 10

        # Calculate total URLs for logging
        total_urls = sum(len(urls) for urls in categories.values())
        self._log_scraping_start("category-based", total_urls)

        scraped_data: dict[str, Any] = {
            "strategy": "categories",
            "data": {},
            "file_paths": {},  # Track where files are saved for analysis
        }

        successful_scrapes = 0

        try:
            # Use shared session for all categories
            for category, urls in categories.items():
                logger.info(f"📂 Scraping category: {category} ({len(urls)} funds)")

                # Scrape and save to files using shared session
                category_results, file_paths = self._scrape_and_save_category(
                    urls, category, max_holdings, analysis_config, analysis_id
                )

                # Store both in-memory data (for compatibility) and file paths
                scraped_data["data"][category] = category_results
                scraped_data["file_paths"][category] = file_paths

                successful_scrapes += len(category_results)
                logger.info(
                    f"   ✅ Category '{category}': {len(category_results)}/{len(urls)} funds scraped"
                )
                logger.info(f"   📁 Saved to {len(file_paths)} files")

        finally:
            # Ensure session cleanup
            self.close_session()

        self._log_scraping_complete("category-based", successful_scrapes, total_urls)
        return scraped_data

    def _scrape_and_save_category(
        self,
        urls: list[str],
        category: str,
        max_holdings: int,
        analysis_config: Any,
        analysis_id: str,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """
        Scrape URLs for a category and save to files.

        Returns:
            tuple: (scraped_data_list, file_paths_list)
        """
        # Build storage config for this category
        storage_config = self._build_storage_config_for_category(
            category, analysis_config, analysis_id
        )

        # Scrape with file saving enabled
        category_results = self._scrape_urls_with_delay(
            urls, max_holdings, category, storage_config
        )

        # Generate file paths that were created
        file_paths = self._generate_expected_file_paths(urls, category, storage_config)

        return category_results, file_paths

    def _build_storage_config_for_category(
        self, category: str, analysis_config: Any, analysis_id: str
    ) -> dict[str, Any]:
        """Build storage configuration for a specific category."""
        config = self.config_provider.get_config()

        storage_config = {
            "should_save": True,  # Always save for file-based analysis
            "base_dir": config.paths.output_dir,
            "category": category,
            "filename_prefix": "coin_",
            "analysis_type": analysis_id,  # Use analysis_id directly
        }

        # Add custom path template if specified
        if hasattr(analysis_config, "path_template") and analysis_config.path_template:
            storage_config["path_template"] = analysis_config.path_template

        return storage_config

    def _generate_expected_file_paths(
        self, urls: list[str], category: str, storage_config: dict[str, Any]
    ) -> list[str]:
        """Generate the expected file paths where scraped data was saved."""
        from datetime import datetime

        file_paths = []
        date_str = datetime.now().strftime("%Y%m%d")

        # Create analysis config for path generation
        analysis_config = {
            "type": storage_config.get("analysis_type", "default"),
            "path_template": storage_config.get("path_template"),
        }

        for url in urls:
            # Use PathGenerator to generate consistent paths
            file_path = self.path_generator.generate_scraped_data_path(
                url=url, category=category, analysis_config=analysis_config, date_str=date_str
            )

            file_paths.append(str(file_path))

        return file_paths
