from __future__ import annotations

from pathlib import Path
from typing import Any

import orjson

from mfa.core.exceptions import create_storage_error
from mfa.logging.logger import logger


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
            StorageError: When save operation fails
        """
        try:
            JsonStore._ensure_parent_directory(file_path)
            JsonStore._write_json_file(data, file_path)
            logger.debug("💾 Saved JSON data to: {}", file_path)
        except Exception as e:
            error_msg = f"Failed to save JSON file to {file_path}: {e}"
            logger.error("❌ {}", error_msg)
            raise create_storage_error(error_msg, str(file_path), "save") from e

    @staticmethod
    def save_with_path(data: dict[str, Any], file_path: Path) -> None:
        """
        Save data to a specific file path.

        This method focuses solely on file I/O operations, with path generation
        handled by the PathGenerator service.

        Args:
            data: Dictionary data to save
            file_path: Complete path where to save the file

        Raises:
            StorageError: When save operation fails
        """
        try:
            JsonStore.save(data, file_path)
        except Exception as e:
            error_msg = f"Failed to save JSON to {file_path}: {e}"
            logger.error("❌ {}", error_msg)
            raise create_storage_error(error_msg, str(file_path), "save") from e

    @staticmethod
    def load(file_path: Path) -> dict[str, Any]:
        """
        Load data from JSON file with error handling.

        Args:
            file_path: Path to the JSON file to load

        Returns:
            Dictionary containing the loaded JSON data

        Raises:
            StorageError: When load operation fails
        """
        try:
            JsonStore._validate_file_exists(file_path)
            data = JsonStore._read_json_file(file_path)
            logger.debug("📖 Loaded JSON data from: {}", file_path)
            return data
        except Exception as e:
            error_msg = f"Failed to load JSON file from {file_path}: {e}"
            logger.error("❌ {}", error_msg)
            raise create_storage_error(error_msg, str(file_path), "save") from e

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
            StorageError: When file doesn't exist
        """
        if not JsonStore.exists(file_path):
            raise create_storage_error(
                f"File does not exist: {file_path}", str(file_path), "exists"
            )

        return file_path.stat().st_size / 1024

    @staticmethod
    def validate_json_structure(data: dict[str, Any], required_keys: list[str]) -> None:
        """
        Validate that JSON data contains required keys.

        Args:
            data: JSON data to validate
            required_keys: List of required top-level keys

        Raises:
            StorageError: When validation fails
        """
        if not isinstance(data, dict):
            raise create_storage_error("JSON data must be a dictionary", operation="validate")

        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            raise create_storage_error(
                f"Missing required keys: {missing_keys}", operation="validate"
            )

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
