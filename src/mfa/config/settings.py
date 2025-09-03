from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from mfa.core.exceptions import ConfigurationError, create_config_error

from .models import AnalysisConfig, MFAConfig


class ConfigProvider:
    """
    Configuration provider with type-safe model support.

    Now uses dependency injection instead of singleton pattern for better testability
    and flexibility.
    """

    def __init__(self, config_path: Path | None = None):
        """
        Initialize configuration provider.

        Args:
            config_path: Optional path to config file. If None, uses default location.
        """
        self.config_path = config_path or (Path.cwd() / "config" / "config.yaml")
        self._raw_config: dict[str, Any] | None = None
        self._typed_config: MFAConfig | None = None

        # Load configuration immediately
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file with environment variable resolution."""
        env_path = Path.cwd() / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        if not self.config_path.exists():
            raise create_config_error(
                f"Configuration file not found: {self.config_path}", str(self.config_path)
            )

        with open(self.config_path, encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}

        self._raw_config = self._resolve_env_vars(raw)

        # Create typed configuration model
        self._typed_config = MFAConfig(**self._raw_config)

    def _resolve_env_vars(self, obj: Any) -> Any:
        """Recursively resolve environment variables in configuration."""
        if isinstance(obj, dict):
            return {k: self._resolve_env_vars(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._resolve_env_vars(v) for v in obj]
        if isinstance(obj, str):
            pattern = r"\$\{([^}]+)\}"
            for var in re.findall(pattern, obj):
                val = os.getenv(var)
                if val is not None:
                    obj = obj.replace(f"${{{var}}}", val)
            return obj
        return obj

    def get_config(self) -> MFAConfig:
        """Get the complete typed configuration model."""
        if self._typed_config is None:
            raise ConfigurationError("Configuration not loaded - call load_config() first")
        return self._typed_config

    def get_analysis_config(self, analysis_name: str) -> AnalysisConfig | None:
        """Get configuration for a specific analysis."""
        return self.get_config().get_analysis(analysis_name)

    def get_enabled_analyses(self) -> dict[str, AnalysisConfig]:
        """Get all enabled analysis configurations."""
        return self.get_config().get_enabled_analyses()


# Factory function for backwards compatibility during transition
def create_config_provider(config_path: Path | None = None) -> ConfigProvider:
    """
    Factory function to create a ConfigProvider instance.

    This provides a clean interface for dependency injection while maintaining
    backwards compatibility during the transition.
    """
    return ConfigProvider(config_path)


# For backwards compatibility during transition - will be removed
_default_provider: ConfigProvider | None = None


def get_default_config_provider() -> ConfigProvider:
    """Get default config provider (temporary compatibility function)."""
    global _default_provider
    if _default_provider is None:
        _default_provider = ConfigProvider()
    return _default_provider
