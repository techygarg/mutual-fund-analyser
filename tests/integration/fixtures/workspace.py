"""
Shared workspace management for integration tests.

Simple, focused utilities for test workspace setup.
"""

import shutil
from pathlib import Path
from typing import Dict, Any
import yaml

from mfa.config.settings import create_config_provider


class AnalysisWorkspace:
    """Manages an isolated test workspace for integration tests."""

    def __init__(self, name: str, base_dir: Path):
        self.name = name
        self.workspace_path = base_dir / f"test_workspace_{name}"
        self.config_provider = None
        self._original_cwd = None

    def setup(self, base_config_path: Path, config_overrides: Dict[str, Any] = None) -> None:
        """Setup workspace with configuration."""
        self._create_directories()
        self._setup_config(base_config_path, config_overrides or {})
        self._change_to_workspace()

    def cleanup(self) -> None:
        """Clean up workspace and restore environment."""
        self._restore_directory()
        self._remove_workspace()

    def get_analysis_dir(self) -> Path:
        """Get the analysis output directory."""
        config = self.config_provider.get_config()
        return Path(config.paths.analysis_dir)

    def get_extracted_dir(self) -> Path:
        """Get the extracted data directory."""
        config = self.config_provider.get_config()
        return Path(config.paths.output_dir)

    def _create_directories(self) -> None:
        """Create workspace directory structure."""
        if self.workspace_path.exists():
            shutil.rmtree(self.workspace_path)

        self.workspace_path.mkdir()
        (self.workspace_path / "config").mkdir()
        (self.workspace_path / "outputs").mkdir()
        (self.workspace_path / "outputs" / "extracted_json").mkdir()
        (self.workspace_path / "outputs" / "analysis").mkdir()

    def _setup_config(self, base_config_path: Path, overrides: Dict[str, Any]) -> None:
        """Setup test configuration."""
        # Load base config
        with open(base_config_path) as f:
            config_data = yaml.safe_load(f)

        # Update paths
        config_data["paths"]["output_dir"] = str(self.workspace_path / "outputs" / "extracted_json")
        config_data["paths"]["analysis_dir"] = str(self.workspace_path / "outputs" / "analysis")

        # Apply overrides
        self._deep_update(config_data, overrides)

        # Write config
        config_file_path = self.workspace_path / "config" / "config.yaml"
        with open(config_file_path, "w") as f:
            yaml.dump(config_data, f)

        # Create config provider
        self.config_provider = create_config_provider(config_file_path)

    def _change_to_workspace(self) -> None:
        """Change to workspace directory."""
        import os

        self._original_cwd = Path.cwd()
        os.chdir(self.workspace_path)

    def _restore_directory(self) -> None:
        """Restore original working directory."""
        if self._original_cwd:
            import os

            os.chdir(self._original_cwd)

    def _remove_workspace(self) -> None:
        """Remove workspace directory."""
        if self.workspace_path.exists():
            shutil.rmtree(self.workspace_path)

    def _deep_update(self, base_dict: Dict, update_dict: Dict) -> None:
        """Deep update dictionary."""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
