from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv

from .models import MFAConfig, AnalysisConfig


class ConfigProvider:
    """
    Configuration provider with type-safe model support.
    
    Provides structured, typed access to configuration through Pydantic models.
    """
    _instance: ConfigProvider | None = None
    _raw_config: dict[str, Any] | None = None
    _typed_config: MFAConfig | None = None

    def __new__(cls) -> ConfigProvider:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._raw_config is None:
            self._load_config()

    @classmethod
    def get_instance(cls) -> ConfigProvider:
        return cls()

    def _load_config(self) -> None:
        """Load configuration from YAML file with environment variable resolution."""
        env_path = Path.cwd() / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        config_path = Path.cwd() / "config" / "config.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, encoding="utf-8") as fh:
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

    # Removed legacy string-based access methods - use get_config() instead

    # New type-safe access methods
    def get_config(self) -> MFAConfig:
        """Get the complete typed configuration model."""
        if self._typed_config is None:
            raise RuntimeError("Configuration not loaded")
        return self._typed_config
    
    def get_analysis_config(self, analysis_name: str) -> Optional[AnalysisConfig]:
        """Get configuration for a specific analysis."""
        return self.get_config().get_analysis(analysis_name)
    
    def get_enabled_analyses(self) -> dict[str, AnalysisConfig]:
        """Get all enabled analysis configurations."""
        return self.get_config().get_enabled_analyses()


# Create singleton instance
config = ConfigProvider.get_instance()
