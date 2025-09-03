"""
Factory classes for creating analyzers and scraping coordinators.

This module implements the factory pattern to create appropriate instances
with direct config access, enabling easy extension with new analysis types.
"""
from __future__ import annotations

from typing import List, Type

from .interfaces import IAnalyzer, IScrapingCoordinator


class AnalyzerFactory:
    """Factory for creating analyzer instances with direct config access."""
    
    _analyzers: dict[str, Type[IAnalyzer]] = {}
    
    @classmethod
    def create_analyzer(cls, analysis_type: str, config_provider: ConfigProvider) -> IAnalyzer:
        """
        Create an analyzer instance for the given type with dependency injection.

        Args:
            analysis_type: Type of analyzer to create
            config_provider: Configuration provider instance

        Returns:
            Initialized analyzer instance
        """
        if analysis_type not in cls._analyzers:
            raise ValueError(f"Unknown analysis type: {analysis_type}")

        analyzer_class = cls._analyzers[analysis_type]
        return analyzer_class(config_provider)
    
    @classmethod
    def register_analyzer(cls, analysis_type: str, analyzer_class: Type[IAnalyzer]) -> None:
        """Register a new analyzer type."""
        cls._analyzers[analysis_type] = analyzer_class
    
    @classmethod
    def get_available_types(cls) -> List[str]:
        """Get list of available analyzer types."""
        return list(cls._analyzers.keys())


class ScrapingCoordinatorFactory:
    """Factory for creating scraping coordinator instances."""
    
    _coordinators: dict[str, Type[IScrapingCoordinator]] = {}
    
    @classmethod
    def create_coordinator(cls, strategy: str, config_provider: ConfigProvider) -> IScrapingCoordinator:
        """
        Create a scraping coordinator for the given strategy with dependency injection.

        Args:
            strategy: Scraping strategy to use
            config_provider: Configuration provider instance

        Returns:
            Initialized coordinator instance
        """
        if strategy not in cls._coordinators:
            raise ValueError(f"Unknown scraping strategy: {strategy}")

        coordinator_class = cls._coordinators[strategy]
        return coordinator_class(config_provider)
    
    @classmethod
    def register_coordinator(cls, strategy: str, coordinator_class: Type[IScrapingCoordinator]) -> None:
        """Register a new scraping coordinator."""
        cls._coordinators[strategy] = coordinator_class
    
    @classmethod
    def get_available_strategies(cls) -> List[str]:
        """Get list of available scraping strategies."""
        return list(cls._coordinators.keys())


def register_analyzer(analysis_type: str):
    """Decorator to register an analyzer class."""
    def decorator(analyzer_class: Type[IAnalyzer]) -> Type[IAnalyzer]:
        AnalyzerFactory.register_analyzer(analysis_type, analyzer_class)
        return analyzer_class
    return decorator


def register_coordinator(strategy: str):
    """Decorator to register a scraping coordinator class."""
    def decorator(coordinator_class: Type[IScrapingCoordinator]) -> Type[IScrapingCoordinator]:
        ScrapingCoordinatorFactory.register_coordinator(strategy, coordinator_class)
        return coordinator_class
    return decorator