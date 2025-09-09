"""
Factory classes for creating analyzers and scraping coordinators.

This module implements the factory pattern to create appropriate instances
with direct config access, enabling easy extension with new analysis types.
"""

from __future__ import annotations

from collections.abc import Callable

from mfa.config.settings import ConfigProvider

from .interfaces import IAnalyzer, IScrapingCoordinator


class AnalyzerFactory:
    """Factory for creating analyzer instances with direct config access."""

    _analyzers: dict[str, type[IAnalyzer]] = {}

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
        return analyzer_class(config_provider)  # type: ignore

    @classmethod
    def register_analyzer(cls, analysis_type: str, analyzer_class: type[IAnalyzer]) -> None:
        """Register a new analyzer type."""
        cls._analyzers[analysis_type] = analyzer_class

    @classmethod
    def get_available_types(cls) -> list[str]:
        """Get list of available analyzer types."""
        return list(cls._analyzers.keys())


class ScrapingCoordinatorFactory:
    """Factory for creating scraping coordinator instances."""

    _coordinators: dict[str, type[IScrapingCoordinator]] = {}

    @classmethod
    def create_coordinator(
        cls, strategy: str, config_provider: ConfigProvider
    ) -> IScrapingCoordinator:
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
        return coordinator_class(config_provider)  # type: ignore

    @classmethod
    def register_coordinator(
        cls, strategy: str, coordinator_class: type[IScrapingCoordinator]
    ) -> None:
        """Register a new scraping coordinator."""
        cls._coordinators[strategy] = coordinator_class

    @classmethod
    def get_available_strategies(cls) -> list[str]:
        """Get list of available scraping strategies."""
        return list(cls._coordinators.keys())


def register_analyzer(analysis_type: str) -> Callable[[type[IAnalyzer]], type[IAnalyzer]]:
    """Decorator to register an analyzer class."""

    def decorator(analyzer_class: type[IAnalyzer]) -> type[IAnalyzer]:
        AnalyzerFactory.register_analyzer(analysis_type, analyzer_class)
        return analyzer_class

    return decorator


def register_coordinator(
    strategy: str,
) -> Callable[[type[IScrapingCoordinator]], type[IScrapingCoordinator]]:
    """Decorator to register a scraping coordinator class."""

    def decorator(coordinator_class: type[IScrapingCoordinator]) -> type[IScrapingCoordinator]:
        ScrapingCoordinatorFactory.register_coordinator(strategy, coordinator_class)
        return coordinator_class

    return decorator


# Import and register coordinators to ensure they're available
def _register_default_coordinators() -> None:
    """Register default scraping coordinators."""
    # Import here to avoid circular imports
    from mfa.analysis.scraping.api_coordinator import APIScrapingCoordinator
    from mfa.analysis.scraping.category_coordinator import CategoryScrapingCoordinator
    from mfa.analysis.scraping.targeted_coordinator import TargetedScrapingCoordinator

    # Register coordinators
    ScrapingCoordinatorFactory.register_coordinator("categories", CategoryScrapingCoordinator)
    ScrapingCoordinatorFactory.register_coordinator("targeted_funds", TargetedScrapingCoordinator)
    ScrapingCoordinatorFactory.register_coordinator("api_scraping", APIScrapingCoordinator)


# Auto-register coordinators when module is imported
_register_default_coordinators()
