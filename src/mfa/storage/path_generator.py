"""
Path generator service for creating structured file paths.

This service handles all path generation logic, extracting it from JSONStore
to maintain single responsibility principle. It supports both smart defaults
and custom path templates for different analysis types.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from mfa.config.settings import ConfigProvider
from mfa.core.exceptions import PathGenerationError


class PathGenerator:
    """
    Service for generating structured file paths with template support.

    This service handles path generation logic separately from file I/O operations,
    enabling better separation of concerns and testability.
    """

    def __init__(self, config_provider: ConfigProvider):
        """
        Initialize path generator with configuration provider.

        Args:
            config_provider: Configuration provider instance
        """
        self.config_provider = config_provider

    def generate_scraped_data_path(
        self,
        url: str,
        category: str = "",
        analysis_config: dict | None = None,
        date_str: str | None = None,
    ) -> Path:
        """
        Generate path for scraped data files.

        Args:
            url: Source URL for data
            category: Fund category (e.g., "largeCap", "midCap")
            analysis_config: Analysis configuration with optional path_template
            date_str: Optional date string (defaults to today)

        Returns:
            Complete path for the scraped data file
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")

        # Get config for base paths
        config = self.config_provider.get_config()
        base_dir = config.paths.output_dir

        # Use custom template if provided, otherwise smart defaults
        if analysis_config and analysis_config.get("path_template"):
            directory_path = self._resolve_path_template(
                analysis_config["path_template"],
                base_dir,
                date_str,
                analysis_config.get("type", "").split("-")[-1],  # Extract analysis type
                category,
            )
        else:
            # Smart defaults based on analysis type and category
            analysis_type = (
                analysis_config.get("type", "").split("-")[-1] if analysis_config else "default"
            )
            directory_path = self._generate_smart_default_path(
                base_dir, date_str, analysis_type, category
            )

        # Generate filename from URL
        filename = self._generate_filename_from_url(url)

        return Path(directory_path) / filename

    def generate_analysis_output_path(
        self, category: str, analysis_config: dict | None = None, date_str: str | None = None
    ) -> Path:
        """
        Generate path for analysis output files.

        Args:
            category: Analysis category (e.g., "largeCap", "midCap")
            analysis_config: Analysis configuration with optional output_template
            date_str: Optional date string (defaults to today)

        Returns:
            Complete path for the analysis output file
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")

        # Get config for base paths
        config = self.config_provider.get_config()
        base_dir = config.paths.analysis_dir

        # Use custom template if provided, otherwise smart defaults
        if analysis_config and analysis_config.get("analysis_output_template"):
            directory_path = self._resolve_path_template(
                analysis_config["analysis_output_template"],
                base_dir,
                date_str,
                analysis_config.get("type", "").split("-")[-1],
                category,
            )
        else:
            # Smart defaults for analysis outputs - should be flat under analysis_type
            analysis_type = analysis_config.get("type", "unknown") if analysis_config else "unknown"
            # For analysis outputs, we want: base_dir/date/analysis_type/ (no category subdirectory)
            directory_path = f"{base_dir}/{date_str}/{analysis_type}"

        return Path(directory_path) / f"{category}.json"

    def _resolve_path_template(
        self, template: str, base_dir: str, date_str: str, analysis_type: str, category: str
    ) -> str:
        """
        Resolve a path template with variable substitution.

        Args:
            template: Path template with variables (e.g., "{base_dir}/{date}/{analysis_type}")
            base_dir: Base output directory
            date_str: Date string (YYYYMMDD format)
            analysis_type: Type of analysis
            category: Fund category (may be empty for non-categorized analyses)

        Returns:
            str: Resolved directory path

        Raises:
            PathGenerationError: If template contains unknown variables
        """
        # Available template variables
        template_vars = {
            "base_dir": base_dir,
            "output_dir": base_dir,  # Alias for backwards compatibility
            "analysis_dir": base_dir,  # For analysis output paths
            "date": date_str,
            "analysis_type": analysis_type,
            "category": category if category else "",
        }

        try:
            resolved_path = template.format(**template_vars)
            # Clean up path separators and remove trailing slashes
            resolved_path = re.sub(r"/+", "/", resolved_path)
            return resolved_path.rstrip("/")
        except KeyError as e:
            raise PathGenerationError(
                f"Unknown template variable in path template '{template}': {e}"
            ) from e

    def _generate_smart_default_path(
        self, base_dir: str, date_str: str, analysis_type: str, category: str
    ) -> str:
        """
        Generate smart default path based on analysis type and category.

        Args:
            base_dir: Base directory
            date_str: Date string
            analysis_type: Type of analysis
            category: Fund category

        Returns:
            Smart default directory path
        """
        if category and category != "default":
            # Categorized analysis (e.g., holdings): base_dir/date/analysis_type/category/
            return f"{base_dir}/{date_str}/{analysis_type}/{category}"
        else:
            # Non-categorized analysis (e.g., portfolio): base_dir/date/analysis_type/
            return f"{base_dir}/{date_str}/{analysis_type}"

    def _generate_filename_from_url(self, url: str) -> str:
        """
        Generate filename from URL.

        Args:
            url: Source URL

        Returns:
            Safe filename for the scraped data
        """
        # Extract the last part of URL which contains the fund identifier
        url_parts = url.strip("/").split("/")

        if len(url_parts) >= 2:
            # Get the fund code and name parts
            fund_code = url_parts[-2] if len(url_parts) >= 2 else ""
            fund_name = url_parts[-1] if len(url_parts) >= 1 else ""

            # Combine them with underscore
            if fund_code and fund_name:
                fund_identifier = f"{fund_code}_{fund_name}"
            else:
                fund_identifier = fund_name or fund_code
        else:
            # Fallback: sanitize the entire URL
            fund_identifier = re.sub(
                r"[^a-zA-Z0-9_-]", "_", url.split("/")[-1] if "/" in url else url
            )

        # Get filename prefix from config
        config = self.config_provider.get_config()
        prefix = config.output.filename_prefix

        return f"{prefix}{fund_identifier}.json"


# Factory function for creating PathGenerator instances
def create_path_generator(config_provider: ConfigProvider) -> PathGenerator:
    """
    Factory function to create a PathGenerator instance.

    Args:
        config_provider: Configuration provider instance

    Returns:
        Initialized PathGenerator
    """
    return PathGenerator(config_provider)
