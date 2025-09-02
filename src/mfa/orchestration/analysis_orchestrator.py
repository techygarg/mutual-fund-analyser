"""
Analysis orchestrator with factory pattern.

This orchestrator coordinates the entire analysis process using the factory
pattern to create appropriate analyzers and scraping coordinators.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from mfa.analysis.factories import AnalyzerFactory, ScrapingCoordinatorFactory
from mfa.config.settings import ConfigProvider
from mfa.config.models import AnalysisConfig
from mfa.logging.logger import logger


class AnalysisOrchestrator:
    """Orchestrates analysis processes using factory pattern."""
    
    def __init__(self):
        self.config = ConfigProvider.get_instance()
        
        # Import analyzers and coordinators to register them
        self._import_components()
    
    def _import_components(self):
        """Import all components to ensure they are registered."""
        # Import analyzers
        from mfa.analysis.analyzers.holdings_analyzer import HoldingsAnalyzer
        
        # Import scraping coordinators  
        from mfa.analysis.scraping.category_coordinator import CategoryScrapingCoordinator
        from mfa.analysis.scraping.targeted_coordinator import TargetedScrapingCoordinator
    
    def run_analysis(self, analysis_type: Optional[str] = None, date: Optional[str] = None) -> None:
        """Run analysis by type or all enabled analyses."""
        # New type-safe way - access through typed model
        config = self.config.get_config()
        
        if not config.analyses:
            logger.error("❌ No analyses configured")
            return
        
        if analysis_type:
            if analysis_type not in config.analyses:
                available = list(config.analyses.keys())
                logger.error(f"❌ Analysis type '{analysis_type}' not found. Available: {available}")
                return
            target_analyses = {analysis_type: config.analyses[analysis_type]}
        else:
            # Use typed method instead of manual filtering
            target_analyses = config.get_enabled_analyses()
        
        if not target_analyses:
            logger.warning("⚠️  No analyses to run (none enabled)")
            return
        
        logger.info(f"🚀 Starting analysis orchestration")
        logger.info(f"📋 Analyses to run: {list(target_analyses.keys())}")
        
        for analysis_id, analysis_config in target_analyses.items():
            self._run_single_analysis(analysis_id, analysis_config, date)
    
    def _run_single_analysis(self, analysis_id: str, analysis_config: AnalysisConfig, date: Optional[str]) -> None:
        """Run a single analysis end-to-end using factory pattern."""
        try:
            logger.info(f"\n📊 Starting analysis: {analysis_id}")
            
            # 1. Create analyzer using factory
            # Convert typed model back to dict for factory (temporary compatibility)
            analyzer = AnalyzerFactory.create_analyzer(
                analysis_config.type, 
                analysis_config.model_dump()
            )
            
            # 2. Get data requirements
            requirements = analyzer.get_data_requirements()
            logger.info(f"📋 Data requirements: {requirements.strategy.value} strategy, "
                       f"{len(requirements.urls)} URLs")
            
            # 3. Get or scrape data
            scraped_data = self._get_scraped_data(requirements, date)
            
            # 4. Run analysis
            result = analyzer.analyze(scraped_data, date or self._get_current_date())
            
            logger.info(f"✅ Analysis '{analysis_id}' completed successfully")
            logger.info(f"   📁 Output files: {len(result.output_paths)}")
            logger.info(f"   📈 Summary: {result.summary}")
            
        except Exception as e:
            logger.error(f"❌ Analysis '{analysis_id}' failed: {e}")
            logger.debug("Full traceback:", exc_info=True)
            raise
    
    def _get_scraped_data(self, requirements, date: Optional[str]) -> Dict[str, Any]:
        """Get scraped data - scrape if needed."""
        # For now, always scrape fresh data
        # Future enhancement: Add caching logic here to check if data already exists
        return self._scrape_data(requirements)
    
    def _scrape_data(self, requirements) -> Dict[str, Any]:
        """Scrape data using appropriate coordinator."""
        try:
            coordinator = ScrapingCoordinatorFactory.create_coordinator(
                requirements.strategy.value
            )
            
            return coordinator.scrape_for_requirement(requirements)
            
        except Exception as e:
            logger.error(f"❌ Scraping failed: {e}")
            raise
    
    def _get_current_date(self) -> str:
        """Get current date in YYYYMMDD format."""
        return datetime.now().strftime("%Y%m%d")
    
    def list_available_analyses(self) -> List[str]:
        """Get list of available analysis types."""
        config = self.config.get_config()
        return list(config.analyses.keys())
    
    def get_analysis_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all configured analyses."""
        config = self.config.get_config()
        status = {}
        
        for name, analysis_config in config.analyses.items():
            status[name] = {
                "type": analysis_config.type,
                "enabled": analysis_config.enabled,
                "strategy": analysis_config.data_requirements.scraping_strategy
            }
        
        return status
