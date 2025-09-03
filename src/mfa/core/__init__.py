"""
MFA Core Module

Contains fundamental components used throughout the application:
- Custom exception hierarchy (exceptions.py)
- Pydantic data models (schemas.py)
"""

from .exceptions import (
    MFAError,
    ConfigurationError,
    ScrapingError,
    AnalysisError,
    StorageError,
    OrchestrationError,
    ValidationError,
    NetworkError,
    ParsingError,
    BrowserError,
    FileNotFoundError,
    FilePermissionError,
    PathGenerationError,
    ConfigValidationError,
    DataProcessingError,
    FactoryError,
    RequirementError,
    create_config_error,
    create_scraping_error,
    create_storage_error,
    create_analysis_error,
)

__all__ = [
    # Base exceptions
    "MFAError",
    "ConfigurationError",
    "ScrapingError",
    "AnalysisError",
    "StorageError",
    "OrchestrationError",
    "ValidationError",

    # Specific exceptions
    "NetworkError",
    "ParsingError",
    "BrowserError",
    "FileNotFoundError",
    "FilePermissionError",
    "PathGenerationError",
    "ConfigValidationError",
    "DataProcessingError",
    "FactoryError",
    "RequirementError",

    # Factory functions
    "create_config_error",
    "create_scraping_error",
    "create_storage_error",
    "create_analysis_error",
]
