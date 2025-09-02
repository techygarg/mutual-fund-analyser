"""
Holdings analyzer implementation.

This analyzer processes fund holdings data to find patterns, overlaps,
and common investments across different fund categories.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from mfa.logging.logger import logger
from mfa.storage.json_store import JsonStore

from ..factories import register_analyzer
from ..interfaces import AnalysisResult, DataRequirement, IAnalyzer, ScrapingStrategy
from .holdings.aggregator import HoldingsAggregator
from .holdings.data_processor import HoldingsDataProcessor
from .holdings.output_builder import HoldingsOutputBuilder


@register_analyzer("fund-holdings")
class HoldingsAnalyzer(IAnalyzer):
    """Analyzer for fund holdings patterns and overlaps."""
    
    analysis_type = "fund-holdings"
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Extract typed params from config dict (factory compatibility)
        params_dict = config.get("params", {})
        
        # Initialize components with typed params
        self.data_processor = HoldingsDataProcessor(params_dict)
        self.aggregator = HoldingsAggregator(params_dict)
        self.output_builder = HoldingsOutputBuilder(params_dict)
    
    def get_data_requirements(self) -> DataRequirement:
        """Define data requirements for holdings analysis."""
        # Extract from dict config (factory compatibility)
        data_req = self.config.get("data_requirements", {})
        categories = data_req.get("categories", {})
        params = self.config.get("params", {})
        max_holdings = params.get("max_holdings", 10)
        
        # Flatten all URLs from all categories
        all_urls = []
        for category_urls in categories.values():
            all_urls.extend(category_urls)
        
        return DataRequirement(
            strategy=ScrapingStrategy.CATEGORIES,
            urls=all_urls,
            metadata={
                "categories": categories,
                "max_holdings": max_holdings,
                "analysis_config": self.config  # Pass the full config for template support
            }
        )
    
    def analyze(self, scraped_data: Dict[str, Any], date: str) -> AnalysisResult:
        """Perform holdings analysis on scraped data."""
        logger.info("🔍 Starting holdings analysis")
        
        categories_data = scraped_data["data"]
        output_paths = []
        summary = {
            "total_categories": len(categories_data),
            "categories_processed": 0,
            "total_funds": 0,
            "total_companies": 0
        }
        
        for category, fund_jsons in categories_data.items():
            try:
                logger.info(f"📊 Analyzing category: {category}")
                category_result = self._analyze_single_category(category, fund_jsons, date)
                output_paths.append(category_result["output_path"])
                
                summary["categories_processed"] += 1
                summary["total_funds"] += category_result["fund_count"]
                summary["total_companies"] += category_result["company_count"]
                
                logger.info(f"   ✅ {category}: {category_result['fund_count']} funds, "
                          f"{category_result['company_count']} companies")
                
            except Exception as e:
                logger.error(f"❌ Failed to analyze category {category}: {e}")
                continue
        
        logger.info(f"🎉 Holdings analysis completed: {summary['categories_processed']}"
                   f"/{summary['total_categories']} categories")
        
        return AnalysisResult(
            analysis_type=self.analysis_type,
            date=date,
            output_paths=output_paths,
            summary=summary
        )
    
    def _analyze_single_category(self, category: str, fund_jsons: List[Dict], date: str) -> Dict[str, Any]:
        """Analyze holdings for a single category."""
        # Process raw fund data
        processed_funds = self.data_processor.process_fund_jsons(fund_jsons)
        
        if not processed_funds:
            logger.warning(f"No valid funds found in category: {category}")
            return {
                "output_path": Path(),
                "fund_count": 0,
                "company_count": 0
            }
        
        # Aggregate holdings data
        aggregated_data = self.aggregator.aggregate_holdings(processed_funds)
        
        # Build output structure
        output_data = self.output_builder.build_category_output(
            category, aggregated_data, processed_funds
        )
        
        # Save output
        output_path = self._save_category_result(category, output_data, date)
        
        return {
            "output_path": output_path,
            "fund_count": len(processed_funds),
            "company_count": len(aggregated_data.companies)
        }
    
    def _save_category_result(self, category: str, output_data: Dict, date: str) -> Path:
        """Save category analysis result to file."""
        output_dir = Path("outputs/analysis") / date
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / f"{category}.json"
        JsonStore.save(output_data, output_path)
        
        logger.debug(f"💾 Saved {category} analysis to: {output_path}")
        return output_path
