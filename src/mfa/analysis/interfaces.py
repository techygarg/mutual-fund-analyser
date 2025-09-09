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
from typing import Any

from mfa.config.settings import ConfigProvider


class ScrapingStrategy(Enum):
    """Supported scraping strategies."""

    CATEGORIES = "categories"
    TARGETED_FUNDS = "targeted_funds"
    API_SCRAPING = "api_scraping"


@dataclass
class DataRequirement:
    """Defines what data an analyzer needs to be scraped."""

    strategy: ScrapingStrategy
    urls: list[str]
    metadata: dict[str, Any]


@dataclass
class AnalysisResult:
    """Result of running an analysis."""

    analysis_type: str
    date: str
    output_paths: list[Path]
    summary: dict[str, Any]


class IAnalyzer(ABC):
    """Interface that all analyzers must implement."""

    @abstractmethod
    def get_data_requirements(self) -> DataRequirement:
        """Define what data this analyzer needs to be scraped."""
        pass

    @abstractmethod
    def analyze(self, data_source: dict[str, Any], date: str) -> AnalysisResult:
        """
        Perform the analysis on the provided data source.

        The data_source can contain either:
        - Direct scraped data (in-memory)
        - File path information for file-based analysis
        - Metadata about where to find the data

        Args:
            data_source: Data source containing scraped information or file references
            date: Analysis date for output file naming

        Returns:
            AnalysisResult with analysis outputs and summary
        """
        pass

    @property
    @abstractmethod
    def analysis_type(self) -> str:
        """Type identifier for this analyzer."""
        pass


class BaseAnalyzer(IAnalyzer):
    """
    Base implementation of IAnalyzer providing common functionality.

    This class provides default implementations for common analyzer functionality,
    allowing concrete analyzers to focus on their specific analysis logic.
    """

    def __init__(self, config_provider: ConfigProvider, analysis_type: str):
        """
        Initialize base analyzer.

        Args:
            config_provider: Configuration provider instance
            analysis_type: String identifier for this analyzer type
        """
        self.config_provider = config_provider
        self._analysis_type = analysis_type

    @property
    def analysis_type(self) -> str:
        """Type identifier for this analyzer."""
        return self._analysis_type

    def _validate_data_source(self, data_source: dict[str, Any]) -> None:
        """
        Validate that the data source contains required information.

        Args:
            data_source: Data source to validate

        Raises:
            ValueError: If data source is invalid
        """
        if not isinstance(data_source, dict):
            raise ValueError("data_source must be a dictionary")

        if not data_source:
            raise ValueError("data_source cannot be empty")

    def _create_result(
        self, output_paths: list, summary: dict[str, Any], date: str
    ) -> AnalysisResult:
        """
        Create an AnalysisResult with consistent structure.

        Args:
            output_paths: List of paths to generated output files
            summary: Summary dictionary with analysis metrics
            date: Analysis date

        Returns:
            Properly structured AnalysisResult
        """
        from pathlib import Path

        return AnalysisResult(
            analysis_type=self.analysis_type,
            date=date,
            output_paths=[Path(path) for path in output_paths],
            summary=summary,
        )


class IScrapingCoordinator(ABC):
    """Interface for scraping coordinators."""

    @abstractmethod
    def scrape_for_requirement(self, requirement: DataRequirement) -> dict[str, Any]:
        """Scrape data based on the given requirement."""
        pass


class IDataStore(ABC):
    """Interface for data storage operations."""

    @abstractmethod
    def save_analysis_result(self, result: AnalysisResult) -> None:
        """Save analysis result to storage."""
        pass

    @abstractmethod
    def load_scraped_data(self, requirement: DataRequirement, date: str) -> dict[str, Any] | None:
        """Load existing scraped data if available."""
        pass
