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
from .aggregator import PortfolioAggregator
from .data_processor import PortfolioDataProcessor
from .output_builder import PortfolioOutputBuilder


@register_analyzer("portfolio-composition")
class PortfolioAnalyzer(BaseAnalyzer):
    """Analyzer for portfolio composition across funds by units and NAV."""

    def __init__(self, config_provider: ConfigProvider):
        super().__init__(config_provider, "portfolio-composition")
        self.path_generator = PathGenerator(config_provider)
        self.data_processor = PortfolioDataProcessor(config_provider)
        self.aggregator = PortfolioAggregator(config_provider)
        self.output_builder = PortfolioOutputBuilder(config_provider)

    def get_data_requirements(self) -> DataRequirement:
        """Define data requirements by reading config directly."""
        config = self.config_provider.get_config()
        portfolio_config = config.get_analysis("portfolio")
        if portfolio_config is None:
            raise ConfigurationError(
                "Portfolio analysis configuration not found",
                {"analysis": "portfolio"},
            )

        funds = portfolio_config.data_requirements.funds or []
        urls = [f["url"] for f in funds if isinstance(f, dict) and f.get("url")]

        return DataRequirement(
            strategy=ScrapingStrategy.API_SCRAPING,
            urls=urls,
            metadata={
                "analysis_id": "portfolio",
            },
        )

    def analyze(self, data_source: dict[str, Any], date: str) -> AnalysisResult:
        """Perform portfolio analysis by reading from saved files."""
        self._validate_data_source(data_source)
        logger.info("🔍 Starting portfolio analysis (file-based)")

        # Read config for funds & parameters
        config = self.config_provider.get_config()
        portfolio_config = config.get_analysis("portfolio")
        assert portfolio_config is not None

        funds_cfg = portfolio_config.data_requirements.funds or []
        params = portfolio_config.params

        # Build url -> units map
        url_to_units = self.data_processor.map_url_to_units(funds_cfg)

        # Load JSONs
        targeted_files = data_source.get("file_paths", {}).get("targeted", [])
        fund_documents: list[dict[str, Any]] = []
        for file_path in targeted_files:
            try:
                fund_documents.append(JsonStore.load(Path(file_path)))
            except Exception as e:
                logger.warning(f"Failed to load {file_path}: {e}")

        if not fund_documents:
            raise ConfigurationError("No portfolio fund data files found", {"date": date})

        # Process and aggregate
        processed_funds = self.data_processor.process_fund_jsons(fund_documents, url_to_units)
        aggregation = self.aggregator.aggregate_portfolio(processed_funds, params)
        output = self.output_builder.build_output(aggregation, processed_funds, params)

        output_path = self._save_portfolio_result(output, date)

        summary = {
            "funds": len(processed_funds),
            "unique_companies": len(output.get("company_allocations", [])),
            "total_investment": output.get("portfolio_summary", {}).get("total_value", 0.0),
        }

        return self._create_result([output_path], summary, date)

    def _save_portfolio_result(self, data: dict[str, Any], date: str) -> Path:
        analysis_config = {
            "type": self.analysis_type,
        }
        output_path = self.path_generator.generate_analysis_output_path(
            category="portfolio", analysis_config=analysis_config, date_str=date
        )
        JsonStore.save_with_path(data=data, file_path=output_path)
        logger.debug(f"💾 Saved portfolio analysis to: {output_path}")
        return output_path
