"""
Holdings analyzer with direct config access and file-based analysis.

This module implements holdings analysis by reading from saved JSON files
instead of processing in-memory data, providing better separation between
scraping and analysis phases.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from mfa.config.settings import ConfigProvider
from mfa.logging.logger import logger
from mfa.storage.json_store import JsonStore

from ..factories import register_analyzer
from ..interfaces import AnalysisResult, DataRequirement, IAnalyzer, ScrapingStrategy
from .holdings.aggregator import HoldingsAggregator
from .holdings.data_processor import HoldingsDataProcessor
from .holdings.output_builder import HoldingsOutputBuilder


@register_analyzer("fund-holdings")
class HoldingsAnalyzer(IAnalyzer):
    """
    Analyzer for fund holdings patterns and overlaps with direct config access.
    
    This analyzer reads configuration directly from ConfigProvider and processes
    data from saved JSON files rather than in-memory data structures.
    """
    
    analysis_type = "fund-holdings"
    
    def __init__(self):
        """Initialize with direct config access."""
        self.config_provider = ConfigProvider.get_instance()
        
        # Initialize components (they'll get params per call)
        self.data_processor = HoldingsDataProcessor()
        self.aggregator = HoldingsAggregator()
        self.output_builder = HoldingsOutputBuilder()
    
    def get_data_requirements(self) -> DataRequirement:
        """Define data requirements by reading config directly."""
        config = self.config_provider.get_config()
        holdings_config = config.analyses["holdings"]  # Dictionary access
        
        # Extract categories from typed config
        categories = holdings_config.data_requirements.categories
        
        # Flatten all URLs from all categories
        all_urls = []
        for category_urls in categories.values():
            all_urls.extend(category_urls)
        
        return DataRequirement(
            strategy=ScrapingStrategy.CATEGORIES,
            urls=all_urls,
            metadata={
                "categories": categories,
                "analysis_id": "holdings"  # For coordinators to identify which analysis
            }
        )
    
    def analyze(self, scraped_data_info: Dict[str, Any], date: str) -> AnalysisResult:
        """
        Perform holdings analysis by reading from saved files.
        
        Args:
            scraped_data_info: Contains file paths and metadata, not actual data
            date: Analysis date
        
        Returns:
            AnalysisResult with analysis outputs and summary
        """
        logger.info("🔍 Starting holdings analysis (file-based)")
        
        config = self.config_provider.get_config()
        holdings_config = config.analyses["holdings"]  # Dictionary access
        
        file_paths = scraped_data_info.get("file_paths", {})
        
        output_paths = []
        summary = {
            "total_categories": len(file_paths),
            "categories_processed": 0,
            "total_funds": 0,
            "total_companies": 0
        }
        
        for category in file_paths.keys():
            logger.info(f"📊 Analyzing category: {category}")
            
            # Read JSON files from disk instead of using in-memory data
            category_file_paths = file_paths[category]
            fund_data_list = []
            
            for file_path in category_file_paths:
                try:
                    fund_data = JsonStore.load(Path(file_path))
                    fund_data_list.append(fund_data)
                except Exception as e:
                    logger.warning(f"Failed to load {file_path}: {e}")
                    continue
            
            if not fund_data_list:
                logger.warning(f"No valid data files found for category {category}")
                continue
            
            # Process using existing components (pass config params)
            processed_funds = self.data_processor.process_fund_jsons(
                fund_data_list, holdings_config.params
            )
            aggregated_data = self.aggregator.aggregate_holdings(
                processed_funds, holdings_config.params
            )
            category_output = self.output_builder.build_category_output(
                category, aggregated_data, holdings_config.params
            )
            
            # Save analysis result
            output_path = self._save_category_result(category, category_output, date)
            output_paths.append(output_path)
            
            # Update summary
            summary["categories_processed"] += 1
            summary["total_funds"] += len(processed_funds)
            summary["total_companies"] += len(category_output.get("companies", []))
            
            logger.info(f"   ✅ {category}: {len(processed_funds)} funds, {len(category_output.get('companies', []))} companies")
        
        logger.info(f"🎉 Holdings analysis completed: {summary['categories_processed']}/{summary['total_categories']} categories")
        
        return AnalysisResult(
            analysis_type=self.analysis_type,
            date=date,
            output_paths=output_paths,
            summary=summary
        )
    
    def _save_category_result(self, category: str, category_output: Dict[str, Any], date: str) -> Path:
        """Save category analysis result to file."""
        config = self.config_provider.get_config()
        
        # Use analysis output directory
        output_dir = Path(config.paths.analysis_dir) / date
        output_file = output_dir / f"{category}.json"
        
        # Save using JsonStore
        JsonStore.save(category_output, output_file)
        
        logger.debug(f"💾 Saved {category} analysis to: {output_file}")
        return output_file