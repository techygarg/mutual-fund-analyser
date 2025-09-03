"""
Analysis orchestrator with simplified direct config access.

This module orchestrates the analysis workflow with a clean separation
between scraping (save to files) and analysis (read from files) phases.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from mfa.analysis.factories import AnalyzerFactory, ScrapingCoordinatorFactory
from mfa.config.models import AnalysisConfig
from mfa.config.settings import ConfigProvider
from mfa.core.exceptions import OrchestrationError, AnalysisError, create_analysis_error
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
    
    def run_analysis(self, analysis_type: Optional[str] = None, date: Optional[str] = None) -> None:
        """
        Run analysis with simplified orchestration.
        
        Components read their own config directly, eliminating parameter passing.
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
                raise OrchestrationError(f"Analysis '{analysis_type}' not found or not enabled", {"analysis_type": analysis_type})
        else:
            # Run all enabled analyses
            analyses_to_run = enabled_analyses
        
        if not analyses_to_run:
            logger.warning("No analyses to run")
            return
        
        logger.info(f"📋 Analyses to run: {list(analyses_to_run.keys())}")
        
        # Run each analysis
        for analysis_id, analysis_config in analyses_to_run.items():
            self._run_single_analysis(analysis_id, analysis_config, date)
    
    def _run_single_analysis(self, analysis_id: str, analysis_config: AnalysisConfig, date: Optional[str]) -> None:
        """
        Run a single analysis with simplified workflow.
        
        1. Create analyzer (reads own config)
        2. Get requirements (analyzer reads config)  
        3. Scrape and save to files
        4. Analyze from files
        """
        try:
            logger.info(f"\n📊 Starting analysis: {analysis_id}")
            
            # 1. Create analyzer with injected config provider
            analyzer = AnalyzerFactory.create_analyzer(analysis_config.type, self.config_provider)
            
            # 2. Get data requirements (analyzer reads config directly)
            requirements = analyzer.get_data_requirements()
            logger.info(f"📋 Data requirements: {requirements.strategy.value} strategy, "
                       f"{len(requirements.urls)} URLs")
            
            # 3. Scrape and save to files (returns file paths)
            scraped_data_info = self._scrape_and_save_data(requirements, date)
            
            # 4. Analyze from files (not in-memory data)
            result = analyzer.analyze(scraped_data_info, date or self._get_current_date())
            
            logger.info(f"✅ Analysis '{analysis_id}' completed successfully")
            logger.info(f"   📁 Output files: {len(result.output_paths)}")
            logger.info(f"   📈 Summary: {result.summary}")
            
        except Exception as e:
            logger.error(f"❌ Analysis '{analysis_id}' failed: {e}")
            logger.debug("Full traceback:", exc_info=True)
            if isinstance(e, (OrchestrationError, AnalysisError)):
                raise  # Re-raise our custom exceptions
            else:
                # Wrap unexpected exceptions
                raise OrchestrationError(f"Unexpected error during analysis '{analysis_id}': {e}", {"analysis_type": analysis_id}) from e
    
    def _scrape_and_save_data(self, requirements, date: Optional[str]) -> Dict[str, Any]:
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
    
    def get_analysis_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all configured analyses."""
        config = self.config_provider.get_config()
        status = {}
        
        for name, analysis_config in config.analyses.items():
            status[name] = {
                "enabled": analysis_config.enabled,
                "type": analysis_config.type,
                "strategy": analysis_config.data_requirements.scraping_strategy
            }
        
        return status