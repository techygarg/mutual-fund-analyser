"""Unit tests for configuration system with dependency injection."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from mfa.config.settings import ConfigProvider, create_config_provider
from mfa.config.models import MFAConfig, AnalysisConfig, DataRequirementsConfig, AnalysisParamsConfig
from mfa.core.exceptions import ConfigurationError


class TestConfigProvider:
    """Test ConfigProvider with dependency injection pattern."""

    @pytest.fixture
    def sample_config_data(self) -> dict:
        """Sample configuration data for testing."""
        return {
            "paths": {
                "output_dir": "outputs/extracted_json",
                "analysis_dir": "outputs/analysis"
            },
            "scraping": {
                "headless": True,
                "timeout_seconds": 30,
                "delay_between_requests": 1.0,
                "save_extracted_json": True
            },
            "output": {
                "filename_prefix": "coin_",
                "include_date_in_folder": True
            },
            "analyses": {
                "holdings": {
                    "enabled": True,
                    "type": "fund-holdings",
                    "data_requirements": {
                        "scraping_strategy": "categories",
                        "categories": {
                            "largeCap": ["https://example.com/large-cap"],
                            "midCap": ["https://example.com/mid-cap"]
                        }
                    },
                    "params": {
                        "max_holdings": 10,
                        "max_companies_in_results": 100,
                        "max_sample_funds_per_company": 5,
                        "exclude_from_analysis": ["CASH", "TREPS"]
                    }
                }
            }
        }

    def test_create_config_provider_creates_instance(self):
        """Test create_config_provider factory function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"

            # Create a minimal config
            config_data = {
                "paths": {"output_dir": "outputs", "analysis_dir": "analysis"},
                            "scraping": {"headless": False, "timeout_seconds": 10, "delay_between_requests": 0.5, "save_extracted_json": True},
            "output": {"filename_prefix": "coin_", "include_date_in_folder": True},
            "analyses": {}
            }

            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)

            provider = create_config_provider(config_path)

            assert isinstance(provider, ConfigProvider)
            assert provider.get_config().paths.output_dir == "outputs"

    def test_config_provider_loads_valid_config(self, sample_config_data: dict):
        """Test ConfigProvider loads and validates configuration correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"

            with open(config_path, 'w') as f:
                yaml.dump(sample_config_data, f)

            provider = ConfigProvider(config_path)
            config = provider.get_config()

            # Verify paths
            assert config.paths.output_dir == "outputs/extracted_json"
            assert config.paths.analysis_dir == "outputs/analysis"

            # Verify scraping config
            assert config.scraping.headless is True
            assert config.scraping.timeout_seconds == 30
            assert config.scraping.save_extracted_json is True

            # Verify analyses
            assert "holdings" in config.analyses
            holdings_config = config.analyses["holdings"]
            assert holdings_config.enabled is True
            assert holdings_config.type == "fund-holdings"
            assert holdings_config.params.max_holdings == 10

    def test_config_provider_handles_missing_file(self):
        """Test ConfigProvider handles missing configuration file."""
        nonexistent_path = Path("/nonexistent/config.yaml")

        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            ConfigProvider(nonexistent_path)

    def test_config_provider_validates_required_sections(self, sample_config_data: dict):
        """Test ConfigProvider validates required configuration sections."""
        # Remove required paths section
        incomplete_config = sample_config_data.copy()
        del incomplete_config["paths"]

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"

            with open(config_path, 'w') as f:
                yaml.dump(incomplete_config, f)

            # Should fail during Pydantic validation
            with pytest.raises(Exception):  # Pydantic validation error
                ConfigProvider(config_path)

    def test_get_enabled_analyses_filters_correctly(self, sample_config_data: dict):
        """Test get_enabled_analyses filters only enabled analyses."""
        # Add a disabled analysis
        sample_config_data["analyses"]["disabled_analysis"] = {
            "enabled": False,
            "type": "disabled-type",
            "data_requirements": {"scraping_strategy": "categories", "categories": {}},
            "params": {"max_holdings": 5}
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"

            with open(config_path, 'w') as f:
                yaml.dump(sample_config_data, f)

            provider = ConfigProvider(config_path)
            enabled_analyses = provider.get_enabled_analyses()

            # Should only include holdings (enabled), not disabled_analysis
            assert len(enabled_analyses) == 1
            assert "holdings" in enabled_analyses
            assert "disabled_analysis" not in enabled_analyses

    def test_get_analysis_config_returns_correct_config(self, sample_config_data: dict):
        """Test get_analysis_config returns specific analysis configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"

            with open(config_path, 'w') as f:
                yaml.dump(sample_config_data, f)

            provider = ConfigProvider(config_path)

            holdings_config = provider.get_analysis_config("holdings")
            assert holdings_config is not None
            assert holdings_config.enabled is True
            assert holdings_config.type == "fund-holdings"

            # Test non-existent analysis
            nonexistent_config = provider.get_analysis_config("nonexistent")
            assert nonexistent_config is None

    def test_config_provider_handles_environment_variables(self):
        """Test ConfigProvider resolves environment variables in config."""
        config_data = {
            "paths": {
                "output_dir": "${TEST_OUTPUT_DIR}",
                "analysis_dir": "outputs/analysis"
            },
            "scraping": {
                "headless": False,
                "timeout_seconds": 30,
                "delay_between_requests": 1.0,
                "save_extracted_json": True
            },
            "output": {
                "filename_prefix": "coin_",
                "include_date_in_folder": True
            },
            "analyses": {}
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"

            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)

            with patch.dict("os.environ", {"TEST_OUTPUT_DIR": "/custom/output/path"}):
                provider = ConfigProvider(config_path)
                config = provider.get_config()

                assert config.paths.output_dir == "/custom/output/path"

    def test_config_provider_handles_missing_env_vars(self):
        """Test ConfigProvider handles missing environment variables gracefully."""
        config_data = {
            "paths": {
                "output_dir": "${MISSING_VAR}",
                "analysis_dir": "outputs/analysis"
            },
            "scraping": {
                "headless": False,
                "timeout_seconds": 30,
                "delay_between_requests": 1.0,
                "save_extracted_json": True
            },
            "output": {
                "filename_prefix": "coin_",
                "include_date_in_folder": True
            },
            "analyses": {}
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"

            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)

            provider = ConfigProvider(config_path)
            config = provider.get_config()

            # Should keep the unresolved variable
            assert config.paths.output_dir == "${MISSING_VAR}"
