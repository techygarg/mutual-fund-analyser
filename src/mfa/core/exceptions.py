"""
Custom exception hierarchy for the Mutual Fund Analyzer (MFA) system.

This module defines specific exceptions for different types of errors that can
occur within the MFA application, enabling better error handling and debugging.
"""

from __future__ import annotations

from typing import Any


class MFAError(Exception):
    """
    Base exception for all MFA-related errors.

    This is the root exception for all custom errors in the MFA system,
    allowing for consistent error handling and logging.
    """

    def __init__(self, message: str, context: dict[str, Any] | None = None):
        """
        Initialize MFA error with message and optional context.

        Args:
            message: Error description
            context: Additional context information (e.g., analysis_type, file_path, etc.)
        """
        super().__init__(message)
        self.context = context or {}

    def __str__(self) -> str:
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{super().__str__()} [{context_str}]"
        return super().__str__()


class ConfigurationError(MFAError):
    """Raised when there's an issue with configuration loading or validation."""

    pass


class ScrapingError(MFAError):
    """Raised when there's an error during web scraping operations."""

    pass


class AnalysisError(MFAError):
    """Raised when there's an error during analysis processing."""

    pass


class StorageError(MFAError):
    """Raised when there's an error with file storage operations."""

    pass


class OrchestrationError(MFAError):
    """Raised when there's an error in the analysis orchestration process."""

    pass


class ValidationError(MFAError):
    """Raised when input validation fails."""

    pass


class NetworkError(ScrapingError):
    """Raised when network-related errors occur during scraping."""

    pass


class ParsingError(ScrapingError):
    """Raised when data parsing fails during scraping."""

    pass


class BrowserError(ScrapingError):
    """Raised when browser automation fails."""

    pass


class FileNotFoundError(StorageError):
    """Raised when required files are not found."""

    pass


class FilePermissionError(StorageError):
    """Raised when file permissions prevent operations."""

    pass


class PathGenerationError(StorageError):
    """Raised when path generation fails."""

    pass


class ConfigValidationError(ConfigurationError):
    """Raised when configuration validation fails."""

    pass


class DataProcessingError(AnalysisError):
    """Raised when data processing fails during analysis."""

    pass


class FactoryError(OrchestrationError):
    """Raised when factory creation fails."""

    pass


class RequirementError(OrchestrationError):
    """Raised when data requirements cannot be satisfied."""

    pass


# Convenience functions for creating specific errors


def create_config_error(message: str, config_path: str | None = None) -> ConfigurationError:
    """Create a configuration error with context."""
    context = {"config_path": config_path} if config_path else None
    return ConfigurationError(message, context)


def create_scraping_error(
    message: str, url: str | None = None, fund_name: str | None = None
) -> ScrapingError:
    """Create a scraping error with context."""
    context = {}
    if url:
        context["url"] = url
    if fund_name:
        context["fund_name"] = fund_name
    return ScrapingError(message, context)


def create_storage_error(
    message: str, file_path: str | None = None, operation: str | None = None
) -> StorageError:
    """Create a storage error with context."""
    context = {}
    if file_path:
        context["file_path"] = file_path
    if operation:
        context["operation"] = operation
    return StorageError(message, context)


def create_analysis_error(
    message: str, analysis_type: str | None = None, category: str | None = None
) -> AnalysisError:
    """Create an analysis error with context."""
    context = {}
    if analysis_type:
        context["analysis_type"] = analysis_type
    if category:
        context["category"] = category
    return AnalysisError(message, context)
