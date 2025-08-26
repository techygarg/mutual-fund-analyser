from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv


class ConfigProvider:
    _instance: "ConfigProvider | None" = None
    _config: Dict[str, Any] | None = None

    def __new__(cls) -> "ConfigProvider":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._config is None:
            self._load_config()

    @classmethod
    def get_instance(cls) -> "ConfigProvider":
        return cls()

    def _load_config(self) -> None:
        env_path = Path.cwd() / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        config_path = Path.cwd() / "config" / "config.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}

        self._config = self._resolve_env_vars(raw)

    def _resolve_env_vars(self, obj: Any) -> Any:
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

    def get(self, key_path: str, default: Any | None = None) -> Any:
        value: Any = self._config
        for key in key_path.split("."):
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def ensure_directories(self) -> None:
        paths = self.get("paths", {}) or {}
        for key in ("output_dir", "analysis_dir"):
            p = Path(paths.get(key, ""))
            if p:
                p.mkdir(parents=True, exist_ok=True)


config = ConfigProvider.get_instance()


