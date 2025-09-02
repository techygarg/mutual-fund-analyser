from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import orjson

from mfa.logging.logger import logger


class JsonStorageError(Exception):
    """Custom exception for JSON storage operations."""

    pass


class JsonStore:
    """
    Provides reliable JSON file storage operations.

    Handles file I/O with proper error handling, logging, and validation
    for JSON data persistence across the application.
    """

    @staticmethod
    def save(data: dict[str, Any], file_path: Path) -> None:
        """
        Save data to JSON file with error handling.

        Args:
            data: Dictionary data to save
            file_path: Path where to save the file

        Raises:
            JsonStorageError: When save operation fails
        """
        try:
            JsonStore._ensure_parent_directory(file_path)
            JsonStore._write_json_file(data, file_path)
            logger.debug("💾 Saved JSON data to: {}", file_path)
        except Exception as e:
            error_msg = f"Failed to save JSON file to {file_path}: {e}"
            logger.error("❌ {}", error_msg)
            raise JsonStorageError(error_msg) from e

    @staticmethod
    def save_with_template(
        data: dict[str, Any], 
        base_dir: str, 
        category: str, 
        url: str, 
        filename_prefix: str = "coin_",
        date_str: Optional[str] = None,
        path_template: Optional[str] = None,
        analysis_type: str = "default"
    ) -> Path:
        """
        Save data using a hybrid template-based path generation approach.
        
        This method supports both smart defaults and custom path templates,
        handling all path generation logic centrally in JSONStore.

        Args:
            data: Dictionary data to save
            base_dir: Base output directory (e.g., "outputs/extracted_json") - used as fallback
            category: Fund category (e.g., "largeCap", "midCap") 
            url: Source URL for fund data (used for filename generation)
            filename_prefix: Prefix for the generated filename
            date_str: Optional date string (defaults to today in YYYYMMDD format)
            path_template: Optional custom path template (e.g., "{base_dir}/{date}/{analysis_type}/{category}")
            analysis_type: Type of analysis (e.g., "holdings", "portfolio")

        Returns:
            Path: The actual path where the file was saved

        Raises:
            JsonStorageError: When save operation fails
        """
        try:
            # Generate date string if not provided
            if date_str is None:
                date_str = datetime.now().strftime("%Y%m%d")
            
            # Extract fund identifier from URL
            fund_identifier = JsonStore._extract_fund_identifier_from_url(url)
            filename = f"{filename_prefix}{fund_identifier}.json"
            
            # Build directory path using template or smart defaults
            if path_template:
                # Use custom template
                directory_path = JsonStore._resolve_path_template(
                    path_template, base_dir, date_str, analysis_type, category
                )
            else:
                # Use smart defaults based on whether category is meaningful
                if category and category != "default":
                    directory_path = f"{base_dir}/{date_str}/{analysis_type}/{category}"
                else:
                    directory_path = f"{base_dir}/{date_str}/{analysis_type}"
            
            # Build complete file path
            file_path = Path(directory_path) / filename
            
            # Use the standard save method
            JsonStore.save(data, file_path)
            
            return file_path
            
        except Exception as e:
            error_msg = f"Failed to save JSON with template for URL {url}: {e}"
            logger.error("❌ {}", error_msg)
            raise JsonStorageError(error_msg) from e

    @staticmethod
    def load(file_path: Path) -> dict[str, Any]:
        """
        Load data from JSON file with error handling.

        Args:
            file_path: Path to the JSON file to load

        Returns:
            Dictionary containing the loaded JSON data

        Raises:
            JsonStorageError: When load operation fails
        """
        try:
            JsonStore._validate_file_exists(file_path)
            data = JsonStore._read_json_file(file_path)
            logger.debug("📖 Loaded JSON data from: {}", file_path)
            return data
        except Exception as e:
            error_msg = f"Failed to load JSON file from {file_path}: {e}"
            logger.error("❌ {}", error_msg)
            raise JsonStorageError(error_msg) from e

    @staticmethod
    def exists(file_path: Path) -> bool:
        """
        Check if JSON file exists and is readable.

        Args:
            file_path: Path to check

        Returns:
            True if file exists and is a readable file, False otherwise
        """
        return file_path.exists() and file_path.is_file() and JsonStore._is_readable(file_path)

    @staticmethod
    def get_file_size_kb(file_path: Path) -> float:
        """
        Get file size in kilobytes.

        Args:
            file_path: Path to the file

        Returns:
            File size in KB

        Raises:
            JsonStorageError: When file doesn't exist
        """
        if not JsonStore.exists(file_path):
            raise JsonStorageError(f"File does not exist: {file_path}")

        return file_path.stat().st_size / 1024

    @staticmethod
    def validate_json_structure(data: dict[str, Any], required_keys: list[str]) -> None:
        """
        Validate that JSON data contains required keys.

        Args:
            data: JSON data to validate
            required_keys: List of required top-level keys

        Raises:
            JsonStorageError: When validation fails
        """
        if not isinstance(data, dict):
            raise JsonStorageError("JSON data must be a dictionary")

        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            raise JsonStorageError(f"Missing required keys: {missing_keys}")

    @staticmethod
    def _ensure_parent_directory(file_path: Path) -> None:
        """Ensure parent directory exists."""
        file_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _write_json_file(data: dict[str, Any], file_path: Path) -> None:
        """Write data to JSON file."""
        with open(file_path, "wb") as file_handle:
            file_handle.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))

    @staticmethod
    def _validate_file_exists(file_path: Path) -> None:
        """Validate that file exists and is readable."""
        if not file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        if not file_path.is_file():
            raise FileNotFoundError(f"Path is not a file: {file_path}")

        if not JsonStore._is_readable(file_path):
            raise PermissionError(f"Cannot read file: {file_path}")

    @staticmethod
    def _read_json_file(file_path: Path) -> dict[str, Any]:
        """Read and parse JSON file."""
        with open(file_path, "rb") as file_handle:
            data = orjson.loads(file_handle.read())
            if not isinstance(data, dict):
                raise ValueError(f"Expected JSON object, got {type(data)}")
            return data

    @staticmethod
    def _is_readable(file_path: Path) -> bool:
        """Check if file is readable."""
        try:
            with open(file_path, "rb"):
                return True
        except (PermissionError, OSError):
            return False

    @staticmethod
    def _resolve_path_template(
        template: str, 
        base_dir: str, 
        date_str: str, 
        analysis_type: str, 
        category: str
    ) -> str:
        """
        Resolve a path template with variable substitution.
        
        This centralizes template parsing logic, supporting the hybrid approach
        where analyses can define custom path structures.
        
        Args:
            template: Path template with variables (e.g., "{base_dir}/{date}/{analysis_type}")
            base_dir: Base output directory
            date_str: Date string (YYYYMMDD format)
            analysis_type: Type of analysis
            category: Fund category (may be empty for non-categorized analyses)
            
        Returns:
            str: Resolved directory path
        """
        # Simple variable substitution using string format
        template_vars = {
            "base_dir": base_dir,
            "output_dir": base_dir,  # Alias for backwards compatibility
            "date": date_str,
            "analysis_type": analysis_type,
            "category": category if category else "",
        }
        
        try:
            resolved_path = template.format(**template_vars)
            # Clean up any double slashes or empty category segments
            resolved_path = re.sub(r'/+', '/', resolved_path)  # Multiple slashes -> single slash
            resolved_path = re.sub(r'//', '/', resolved_path)   # Double slashes -> single slash
            return resolved_path.rstrip('/')  # Remove trailing slash
        except KeyError as e:
            raise JsonStorageError(f"Unknown template variable in path template '{template}': {e}")

    @staticmethod
    def _extract_fund_identifier_from_url(url: str) -> str:
        """
        Extract fund identifier from URL for filename generation.
        
        This centralizes the logic for converting URLs to safe, consistent filenames,
        making it reusable across the application.
        
        Args:
            url: Fund URL (e.g., https://coin.zerodha.com/mf/fund/INF204K01XI3/nippon-india-large-cap-fund-direct-growth)
            
        Returns:
            str: Fund identifier (e.g., INF204K01XI3_nippon-india-large-cap-fund-direct-growth)
        """
        # Extract the last part of URL which contains the fund identifier
        # Example: https://coin.zerodha.com/mf/fund/INF204K01XI3/nippon-india-large-cap-fund-direct-growth
        # Should return: INF204K01XI3_nippon-india-large-cap-fund-direct-growth
        url_parts = url.strip('/').split('/')
        
        if len(url_parts) >= 2:
            # Get the fund code and name parts
            fund_code = url_parts[-2] if len(url_parts) >= 2 else ""
            fund_name = url_parts[-1] if len(url_parts) >= 1 else ""
            
            # Combine them with underscore
            if fund_code and fund_name:
                return f"{fund_code}_{fund_name}"
            else:
                return fund_name or fund_code
        else:
            # Fallback: sanitize the entire URL
            sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', url.split('/')[-1] if '/' in url else url)
            return sanitized
