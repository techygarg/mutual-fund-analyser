"""Unit tests for factory patterns with dependency injection."""

from unittest.mock import Mock

import pytest

from mfa.analysis.analyzers.holdings import HoldingsAnalyzer
from mfa.analysis.factories import AnalyzerFactory, ScrapingCoordinatorFactory
from mfa.analysis.scraping.category_coordinator import CategoryScrapingCoordinator
from mfa.config.settings import ConfigProvider


class TestAnalyzerFactory:
    """Test AnalyzerFactory with dependency injection."""

    def test_create_analyzer_returns_correct_type(self, mock_config_provider: ConfigProvider):
        """Test create_analyzer returns analyzer of correct type."""
        analyzer = AnalyzerFactory.create_analyzer("holdings", mock_config_provider)

        assert isinstance(analyzer, HoldingsAnalyzer)
        assert analyzer.config_provider is mock_config_provider

    def test_create_analyzer_unknown_type_raises_error(self, mock_config_provider: ConfigProvider):
        """Test create_analyzer raises error for unknown analyzer type."""
        with pytest.raises(ValueError, match="Unknown analysis type"):
            AnalyzerFactory.create_analyzer("unknown-type", mock_config_provider)

    def test_get_available_types_returns_registered_analyzers(self):
        """Test get_available_types returns all registered analyzer types."""
        available_types = AnalyzerFactory.get_available_types()

        assert isinstance(available_types, list)
        assert "holdings" in available_types

    def test_analyzer_factory_maintains_registration(self):
        """Test analyzer factory maintains registration across calls."""
        # This test ensures the registration decorator works correctly
        AnalyzerFactory.get_available_types()

        # This test doesn't need actual functionality testing
        # Just verify the registration exists
        available_types = AnalyzerFactory.get_available_types()
        assert "holdings" in available_types


class TestScrapingCoordinatorFactory:
    """Test ScrapingCoordinatorFactory with dependency injection."""

    def test_create_coordinator_returns_correct_type(self, mock_config_provider: ConfigProvider):
        """Test create_coordinator returns coordinator of correct type."""
        coordinator = ScrapingCoordinatorFactory.create_coordinator(
            "categories", mock_config_provider
        )

        assert isinstance(coordinator, CategoryScrapingCoordinator)
        assert coordinator.config_provider is mock_config_provider

    def test_create_coordinator_unknown_strategy_raises_error(
        self, mock_config_provider: ConfigProvider
    ):
        """Test create_coordinator raises error for unknown strategy."""
        with pytest.raises(ValueError, match="Unknown scraping strategy"):
            ScrapingCoordinatorFactory.create_coordinator("unknown-strategy", mock_config_provider)

    def test_coordinator_factory_passes_config_to_components(
        self, mock_config_provider: ConfigProvider
    ):
        """Test coordinator factory passes config provider to created components."""
        coordinator = ScrapingCoordinatorFactory.create_coordinator(
            "categories", mock_config_provider
        )

        # Verify the coordinator received the config provider
        assert coordinator.config_provider is mock_config_provider

        # Verify base coordinator components also received config
        assert coordinator.path_generator.config_provider is mock_config_provider


class TestFactoryIntegration:
    """Integration tests for factory patterns working together."""

    def test_factories_create_components_with_same_config(
        self, mock_config_provider: ConfigProvider
    ):
        """Test both factories create components using the same config provider."""
        analyzer = AnalyzerFactory.create_analyzer("holdings", mock_config_provider)
        coordinator = ScrapingCoordinatorFactory.create_coordinator(
            "categories", mock_config_provider
        )

        # Both should use the same config provider
        assert analyzer.config_provider is mock_config_provider
        assert coordinator.config_provider is mock_config_provider

    def test_factory_created_components_are_functional(self, mock_config_provider: ConfigProvider):
        """Test factory-created components are functional and properly initialized."""
        analyzer = AnalyzerFactory.create_analyzer("holdings", mock_config_provider)
        coordinator = ScrapingCoordinatorFactory.create_coordinator(
            "categories", mock_config_provider
        )

        # Test analyzer can get data requirements
        requirements = analyzer.get_data_requirements()
        assert requirements is not None
        assert hasattr(requirements, "strategy")
        assert hasattr(requirements, "urls")

        # Test coordinator has required attributes
        assert hasattr(coordinator, "config_provider")
        assert hasattr(coordinator, "path_generator")

    def test_factory_error_handling(self, mock_config_provider: ConfigProvider):
        """Test factories handle errors appropriately."""
        # Test with invalid analyzer type
        with pytest.raises(ValueError):
            AnalyzerFactory.create_analyzer("invalid-analyzer", mock_config_provider)

        # Test with invalid coordinator strategy
        with pytest.raises(ValueError):
            ScrapingCoordinatorFactory.create_coordinator("invalid-strategy", mock_config_provider)


class TestFactoryRegistration:
    """Test factory registration and discovery."""

    def test_analyzer_registration_decorator(self):
        """Test that registration decorator works correctly."""
        # The @register_analyzer decorator should have registered the HoldingsAnalyzer
        available_types = AnalyzerFactory.get_available_types()

        assert "holdings" in available_types
        assert len(available_types) >= 1

    def test_coordinator_registration_decorator(self):
        """Test that coordinator registration decorator works correctly."""
        # This test doesn't need actual functionality testing
        # Just verify the registration exists
        available_strategies = ScrapingCoordinatorFactory.get_available_strategies()
        assert "categories" in available_strategies
