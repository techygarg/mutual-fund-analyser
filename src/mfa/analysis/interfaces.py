"""
Core interfaces for the analysis framework.

This module defines the contracts that all analyzers and scraping coordinators
must implement, enabling a clean factory pattern architecture.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ScrapingStrategy(Enum):
    """Supported scraping strategies."""
    CATEGORIES = "categories"
    TARGETED_FUNDS = "targeted_funds"


@dataclass
class DataRequirement:
    """Defines what data an analyzer needs to be scraped."""
    strategy: ScrapingStrategy
    urls: List[str]
    metadata: Dict[str, Any]


@dataclass
class AnalysisResult:
    """Result of running an analysis."""
    analysis_type: str
    date: str
    output_paths: List[Path]
    summary: Dict[str, Any]


class IAnalyzer(ABC):
    """Interface that all analyzers must implement."""
    
    @abstractmethod
    def get_data_requirements(self) -> DataRequirement:
        """Define what data this analyzer needs to be scraped."""
        pass
    
    @abstractmethod
    def analyze(self, scraped_data: Dict[str, Any], date: str) -> AnalysisResult:
        """Perform the analysis on scraped data."""
        pass
    
    @property
    @abstractmethod
    def analysis_type(self) -> str:
        """Type identifier for this analyzer."""
        pass


class IScrapingCoordinator(ABC):
    """Interface for scraping coordinators."""
    
    @abstractmethod
    def scrape_for_requirement(self, requirement: DataRequirement) -> Dict[str, Any]:
        """Scrape data based on the given requirement."""
        pass


class IDataStore(ABC):
    """Interface for data storage operations."""
    
    @abstractmethod
    def save_analysis_result(self, result: AnalysisResult) -> None:
        """Save analysis result to storage."""
        pass
    
    @abstractmethod
    def load_scraped_data(self, requirement: DataRequirement, date: str) -> Optional[Dict[str, Any]]:
        """Load existing scraped data if available."""
        pass
