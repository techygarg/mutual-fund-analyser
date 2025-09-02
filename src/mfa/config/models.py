"""
Configuration models representing the YAML structure.

This module defines plain Pydantic models that represent our YAML configuration
structure, providing type safety and IDE support without complex validation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class PathsConfig(BaseModel):
    """Directory paths configuration."""
    
    output_dir: str
    analysis_dir: str


class ScrapingConfig(BaseModel):
    """Global scraping configuration."""
    
    headless: bool
    timeout_seconds: int
    delay_between_requests: float
    save_extracted_json: bool


class OutputConfig(BaseModel):
    """Output formatting configuration."""
    
    filename_prefix: str
    include_date_in_folder: bool


class DataRequirementsConfig(BaseModel):
    """Data requirements for an analysis."""
    
    scraping_strategy: str
    categories: Optional[Dict[str, List[str]]] = None
    funds: Optional[List[Dict[str, Any]]] = None


class AnalysisParamsConfig(BaseModel):
    """Parameters for analysis configuration."""
    
    # Common parameters
    max_holdings: Optional[int] = None
    exclude_from_analysis: Optional[List[str]] = None
    
    # Holdings analysis specific
    max_companies_in_results: Optional[int] = None
    max_sample_funds_per_company: Optional[int] = None
    
    # Portfolio analysis specific (future)
    target_investment: Optional[float] = None
    chart_top_n: Optional[int] = None


class AnalysisConfig(BaseModel):
    """Configuration for a single analysis."""
    
    enabled: bool
    type: str
    data_requirements: DataRequirementsConfig
    params: AnalysisParamsConfig
    
    # Optional path templates for custom directory structures
    path_template: Optional[str] = None
    analysis_output_template: Optional[str] = None


class MFAConfig(BaseModel):
    """Main configuration model for the MFA application."""
    
    paths: PathsConfig
    scraping: ScrapingConfig
    output: OutputConfig
    analyses: Dict[str, AnalysisConfig]
    
    def get_enabled_analyses(self) -> Dict[str, AnalysisConfig]:
        """Get only the enabled analyses."""
        return {name: config for name, config in self.analyses.items() if config.enabled}
    
    def get_analysis(self, name: str) -> Optional[AnalysisConfig]:
        """Get a specific analysis configuration by name."""
        return self.analyses.get(name)
    
    def ensure_directories(self) -> None:
        """Ensure all configured directories exist."""
        Path(self.paths.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.paths.analysis_dir).mkdir(parents=True, exist_ok=True)
