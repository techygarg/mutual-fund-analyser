"""
Analysis orchestrator with simplified direct config access.

This module orchestrates the analysis workflow with a clean separation
between scraping (save to files) and analysis (read from files) phases.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

# Import analyzers and coordinators to ensure they get registered
import mfa.analysis.analyzers.holdings  # noqa: F401 - Registers holdings analyzer
import mfa.analysis.analyzers.portfolio  # noqa: F401 - Registers portfolio analyzer
import mfa.analysis.scraping.category_coordinator  # noqa: F401 - Registers category coordinator
import mfa.analysis.scraping.targeted_coordinator  # noqa: F401 - Registers targeted coordinator
from mfa.analysis.factories import AnalyzerFactory, ScrapingCoordinatorFactory
from mfa.analysis.interfaces import DataRequirement
from mfa.config.models import AnalysisConfig
from mfa.config.settings import ConfigProvider
from mfa.core.exceptions import AnalysisError, OrchestrationError
from mfa.logging.logger import logger


class AnalysisOrchestrator:
    """
    Orchestrates analysis workflows with dependency-injected configuration.

    Uses dependency injection for better testability and flexibility.
    """

    def __init__(self, config_provider: ConfigProvider):
        """
        Initialize orchestrator with injected configuration provider.

        Args:
            config_provider: Configuration provider instance
        """
        self.config_provider = config_provider

    def run_analysis(
        self, analysis_type: str | None = None, date: str | None = None, analysis_only: bool = False
    ) -> None:
        """
        Run analysis with simplified orchestration.

        Components read their own config directly, eliminating parameter passing.

        Args:
            analysis_type: Specific analysis to run, or None for all enabled
            date: Date for analysis, or None for today
            analysis_only: If True, skip scraping and use existing data only
        """
        logger.info("🚀 Starting analysis orchestration")

        # Get enabled analyses from config
        config = self.config_provider.get_config()
        enabled_analyses = config.get_enabled_analyses()

        if analysis_type:
            # Run specific analysis
            if analysis_type in enabled_analyses:
                analyses_to_run = {analysis_type: enabled_analyses[analysis_type]}
            else:
                raise OrchestrationError(
                    f"Analysis '{analysis_type}' not found or not enabled",
                    {"analysis_type": analysis_type},
                )
        else:
            # Run all enabled analyses
            analyses_to_run = enabled_analyses

        if not analyses_to_run:
            logger.warning("No analyses to run")
            return

        logger.info(f"📋 Analyses to run: {list(analyses_to_run.keys())}")

        # Run each analysis
        for analysis_id, analysis_config in analyses_to_run.items():
            self._run_single_analysis(analysis_id, analysis_config, date, analysis_only)

    def _run_single_analysis(
        self,
        analysis_id: str,
        analysis_config: AnalysisConfig,
        date: str | None,
        analysis_only: bool = False,
    ) -> None:
        """
        Run a single analysis with simplified workflow.

        1. Create analyzer (reads own config)
        2. Get requirements (analyzer reads config)
        3. Scrape and save to files (unless analysis_only=True)
        4. Analyze from files
        """
        try:
            logger.info(f"\n📊 Starting analysis: {analysis_id}")

            # 1. Create analyzer with injected config provider
            analyzer = AnalyzerFactory.create_analyzer(analysis_config.type, self.config_provider)

            # 2. Get data requirements (analyzer reads config directly)
            requirements = analyzer.get_data_requirements()
            logger.info(
                f"📋 Data requirements: {requirements.strategy.value} strategy, "
                f"{len(requirements.urls)} URLs"
            )

            # 3. Scrape and save to files (unless analysis_only=True)
            if analysis_only:
                logger.info("🔄 Analysis-only mode: skipping scraping, using existing data")
                # Discover existing data files
                scraped_data_info = self._discover_existing_data_files(requirements, date)
            else:
                scraped_data_info = self._scrape_and_save_data(requirements, date)

            # 4. Analyze from files (not in-memory data)
            result = analyzer.analyze(scraped_data_info, date or self._get_current_date())

            logger.info(f"✅ Analysis '{analysis_id}' completed successfully")
            logger.info(f"   📁 Output files: {len(result.output_paths)}")
            logger.info(f"   📈 Summary: {result.summary}")

        except Exception as e:
            logger.error(f"❌ Analysis '{analysis_id}' failed: {e}")
            logger.debug("Full traceback:", exc_info=True)
            if isinstance(e, OrchestrationError | AnalysisError):
                raise  # Re-raise our custom exceptions
            else:
                # Wrap unexpected exceptions
                raise OrchestrationError(
                    f"Unexpected error during analysis '{analysis_id}': {e}",
                    {"analysis_type": analysis_id},
                ) from e

    def _scrape_and_save_data(
        self, requirements: DataRequirement, date: str | None
    ) -> dict[str, Any]:
        """
        Scrape data and save to files.

        Returns file paths and metadata instead of in-memory data.
        """
        try:
            coordinator = ScrapingCoordinatorFactory.create_coordinator(
                requirements.strategy.value, self.config_provider
            )

            # Coordinator saves files and returns file path info + metadata
            return coordinator.scrape_for_requirement(requirements)

        except Exception as e:
            logger.error(f"❌ Scraping failed: {e}")
            if isinstance(e, OrchestrationError):
                raise  # Re-raise our custom exceptions
            else:
                # Wrap unexpected exceptions
                raise OrchestrationError(f"Unexpected error during scraping: {e}") from e

    def _get_current_date(self) -> str:
        """Get current date string."""
        return datetime.now().strftime("%Y%m%d")

    def list_available_analyses(self) -> list[str]:
        """List all available analysis types."""
        return AnalyzerFactory.get_available_types()

    def get_analysis_status(self) -> dict[str, dict[str, Any]]:
        """Get status of all configured analyses."""
        config = self.config_provider.get_config()
        status = {}

        for name, analysis_config in config.analyses.items():
            status[name] = {
                "enabled": analysis_config.enabled,
                "type": analysis_config.type,
                "strategy": analysis_config.data_requirements.scraping_strategy,
            }

        return status

    def _discover_existing_data_files(
        self, requirements: DataRequirement, date: str | None
    ) -> dict[str, Any]:
        """
        Discover existing scraped data files for analysis-only mode.

        Args:
            requirements: Data requirements from analyzer
            date: Optional date string for file discovery

        Returns:
            Dict with strategy and file_paths for analysis
        """
        from pathlib import Path

        config = self.config_provider.get_config()
        date_str = date or self._get_current_date()

        scraped_data_info: dict[str, Any] = {
            "strategy": requirements.strategy.value,
            "data": {},
            "file_paths": dict[str, list[str]](),
        }

        # Determine analysis folder from metadata (e.g., 'holdings', 'portfolio')
        analysis_folder = requirements.metadata.get("analysis_id", "holdings")

        if requirements.strategy.value == "categories":
            # Discover files organized by categories
            categories = requirements.metadata.get("categories", {})

            for category, _urls in categories.items():
                category_files = []
                base_dir = Path(config.paths.output_dir) / date_str / analysis_folder / category

                if base_dir.exists():
                    # Find all JSON files in this category directory
                    json_files = list(base_dir.glob("*.json"))
                    category_files = [str(f) for f in json_files]
                    logger.debug(f"📁 Found {len(category_files)} files for category '{category}'")
                else:
                    logger.warning(
                        f"📁 No data directory found for category '{category}': {base_dir}"
                    )

                scraped_data_info["file_paths"][category] = category_files

        elif requirements.strategy.value == "targeted_funds":
            # Discover files for targeted strategy under analysis folder
            base_dir = Path(config.paths.output_dir) / date_str / analysis_folder

            if base_dir.exists():
                json_files = list(base_dir.glob("*.json"))
                scraped_data_info["file_paths"]["targeted"] = [str(f) for f in json_files]
                logger.debug(f"📁 Found {len(json_files)} targeted files in '{base_dir}'")
            else:
                logger.warning(f"📁 No data directory found for targeted strategy: {base_dir}")
                scraped_data_info["file_paths"]["targeted"] = []

        file_paths_dict = scraped_data_info["file_paths"]
        total_files = sum(
            len(files) for files in file_paths_dict.values() if isinstance(files, list)
        )
        logger.info(f"📁 Discovered {total_files} existing data files for analysis")

        return scraped_data_info
