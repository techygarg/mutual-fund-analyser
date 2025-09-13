"""
Holdings analyzer with direct config access and file-based analysis.

This module implements holdings analysis by reading from saved JSON files
instead of processing in-memory data, providing better separation between
scraping and analysis phases.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mfa.config.settings import ConfigProvider
from mfa.core.exceptions import ConfigurationError
from mfa.logging.logger import logger
from mfa.storage.json_store import JsonStore
from mfa.storage.path_generator import PathGenerator

from ...factories import register_analyzer
from ...interfaces import AnalysisResult, BaseAnalyzer, DataRequirement, ScrapingStrategy
from ..utils.analyzer_utils import AnalyzerUtils
from .aggregator import HoldingsAggregator
from .data_processor import HoldingsDataProcessor
from .output_builder import HoldingsOutputBuilder


@register_analyzer("holdings")
class HoldingsAnalyzer(BaseAnalyzer):
    """
    Analyzer for fund holdings patterns and overlaps with dependency injection.

    This analyzer accepts a ConfigProvider through dependency injection for better
    testability and processes data from saved JSON files.
    """

    def __init__(self, config_provider: ConfigProvider):
        """
        Initialize holdings analyzer with injected config provider.

        Args:
            config_provider: Configuration provider instance
        """
        super().__init__(config_provider, "holdings")  # Call parent constructor
        # self.config_provider is already set by parent
        self.path_generator = PathGenerator(config_provider)

        # Initialize components with dependency injection
        self.data_processor = HoldingsDataProcessor(config_provider)
        self.aggregator = HoldingsAggregator(config_provider)
        self.output_builder = HoldingsOutputBuilder(config_provider)

    def get_data_requirements(self) -> DataRequirement:
        """Define data requirements by reading config directly."""
        config = self.config_provider.get_config()
        holdings_config = config.get_analysis("holdings")  # Typed access
        if holdings_config is None:
            raise ConfigurationError(
                "Holdings analysis configuration not found",
                {"analysis": "holdings"},
            )

        # Extract categories from typed config
        categories = holdings_config.data_requirements.categories

        # Flatten, sanitize and deduplicate URLs from all categories
        all_urls: list[str] = []
        if categories:
            for category_urls in categories.values():
                if not category_urls:
                    continue
                all_urls.extend(category_urls)

        # Sanitize and deduplicate
        urls = sorted({u.strip() for u in all_urls if isinstance(u, str) and u.strip()})

        # Get scraping strategy from config
        strategy_str = holdings_config.data_requirements.scraping_strategy
        strategy = ScrapingStrategy(strategy_str)

        return DataRequirement(
            strategy=strategy,
            urls=urls,
            metadata={
                "categories": categories,
                "analysis_id": "holdings",  # For coordinators to identify which analysis
            },
        )

    def analyze(self, data_source: dict[str, Any], date: str) -> AnalysisResult:
        """
        Perform holdings analysis by reading from saved files.

        Args:
            data_source: Contains file paths and metadata, not actual data
            date: Analysis date

        Returns:
            AnalysisResult with analysis outputs and summary
        """
        # Initialize analysis
        self._validate_data_source(data_source)
        logger.info("🔍 Starting holdings analysis (file-based)")

        # Load and validate data
        loaded_data = self._load_and_validate_data(data_source)

        # Process each category
        output_paths, summary = self._process_all_categories(loaded_data, date)

        # Complete analysis
        self._log_completion_summary(summary)
        return self._create_result(output_paths, summary, date)

    def _load_and_validate_data(
        self, data_source: dict[str, Any]
    ) -> dict[str, list[dict[str, Any]]]:
        """Load and validate data from source."""
        loaded_data = AnalyzerUtils.load_files_from_data_source(data_source)
        AnalyzerUtils.validate_loaded_data(loaded_data, "holdings")
        return loaded_data

    def _process_all_categories(
        self, loaded_data: dict[str, list[dict[str, Any]]], date: str
    ) -> tuple[list[Path], dict[str, Any]]:
        """Process all categories and return output paths and summary."""
        output_paths = []
        summary = self._initialize_summary(loaded_data)

        for category, fund_data_list in loaded_data.items():
            if self._should_skip_category(category, fund_data_list):
                continue

            # Process single category
            category_results = self._process_single_category(category, fund_data_list, date)

            # Update tracking
            output_paths.append(category_results["output_path"])
            self._update_summary(summary, category_results)

            self._log_category_completion(category, category_results)

        return output_paths, summary

    def _initialize_summary(self, loaded_data: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        """Initialize analysis summary structure."""
        return {
            "total_categories": len(loaded_data),
            "categories_processed": 0,
            "total_funds": 0,
            "total_companies": 0,
        }

    def _should_skip_category(self, category: str, fund_data_list: list[dict[str, Any]]) -> bool:
        """Check if category should be skipped due to no data."""
        if not fund_data_list:
            logger.warning(f"No valid data files found for category {category}")
            return True
        return False

    def _process_single_category(
        self, category: str, fund_data_list: list[dict[str, Any]], date: str
    ) -> dict[str, Any]:
        """Process a single category and return results."""
        logger.info(f"📊 Analyzing category: {category}")

        # Process using components with dependency injection
        processed_funds = self.data_processor.process_fund_jsons(fund_data_list)
        aggregated_data = self.aggregator.aggregate_holdings(processed_funds)
        category_output = self.output_builder.build_category_output(category, aggregated_data)

        # Save analysis result
        output_path = self._save_category_result(category, category_output, date)

        return {
            "output_path": output_path,
            "processed_funds": processed_funds,
            "category_output": category_output,
        }

    def _update_summary(self, summary: dict[str, Any], category_results: dict[str, Any]) -> None:
        """Update summary with category results."""
        summary["categories_processed"] += 1
        summary["total_funds"] += len(category_results["processed_funds"])
        summary["total_companies"] += category_results["category_output"].get("unique_companies", 0)

    def _log_category_completion(self, category: str, category_results: dict[str, Any]) -> None:
        """Log completion of category processing."""
        fund_count = len(category_results["processed_funds"])
        company_count = category_results["category_output"].get("unique_companies", 0)
        logger.info(f"   ✅ {category}: {fund_count} funds, {company_count} companies")

    def _log_completion_summary(self, summary: dict[str, Any]) -> None:
        """Log final completion summary."""
        logger.info(
            f"🎉 Holdings analysis completed: "
            f"{summary['categories_processed']}/{summary['total_categories']} categories"
        )

    def _save_category_result(
        self, category: str, category_output: dict[str, Any], date: str
    ) -> Path:
        """Save category analysis result to file using PathGenerator."""
        # Create analysis config for path generation
        analysis_config = {
            "type": self.analysis_type,
            # Could add analysis_output_template here in future
        }

        # Generate path using PathGenerator
        output_path = self.path_generator.generate_analysis_output_path(
            category=category, analysis_config=analysis_config, date_str=date
        )

        # Save using JsonStore
        JsonStore.save_with_path(data=category_output, file_path=output_path)

        logger.debug(f"💾 Saved {category} analysis to: {output_path}")
        return output_path
