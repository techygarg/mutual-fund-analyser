"""Unit tests for custom exception handling."""

from mfa.core.exceptions import (
    AnalysisError,
    BrowserError,
    ConfigurationError,
    ConfigValidationError,
    DataProcessingError,
    FactoryError,
    FileNotFoundError,
    FilePermissionError,
    MFAError,
    NetworkError,
    OrchestrationError,
    ParsingError,
    PathGenerationError,
    RequirementError,
    ScrapingError,
    StorageError,
    ValidationError,
    create_analysis_error,
    create_config_error,
    create_scraping_error,
    create_storage_error,
)


class TestBaseException:
    """Test base MFA exception functionality."""

    def test_mfa_error_creation(self):
        """Test MFAError creation with message."""
        error = MFAError("Test error message")

        assert str(error) == "Test error message"
        assert error.context == {}

    def test_mfa_error_with_context(self):
        """Test MFAError creation with context."""
        context = {"analysis_type": "holdings", "file_path": "/test/path"}
        error = MFAError("Test error", context)

        assert error.context == context
        assert str(error) == "Test error [analysis_type=holdings, file_path=/test/path]"

    def test_mfa_error_empty_context(self):
        """Test MFAError with empty context."""
        error = MFAError("Test error", {})

        assert str(error) == "Test error"

    def test_mfa_error_none_context(self):
        """Test MFAError with None context."""
        error = MFAError("Test error", None)

        assert error.context == {}
        assert str(error) == "Test error"


class TestSpecificExceptions:
    """Test specific exception types."""

    def test_configuration_error(self):
        """Test ConfigurationError inheritance."""
        error = ConfigurationError("Config error")

        assert isinstance(error, MFAError)
        assert isinstance(error, ConfigurationError)
        assert str(error) == "Config error"

    def test_scraping_error(self):
        """Test ScrapingError inheritance."""
        error = ScrapingError("Scraping failed")

        assert isinstance(error, MFAError)
        assert isinstance(error, ScrapingError)

    def test_analysis_error(self):
        """Test AnalysisError inheritance."""
        error = AnalysisError("Analysis failed")

        assert isinstance(error, MFAError)
        assert isinstance(error, AnalysisError)

    def test_storage_error(self):
        """Test StorageError inheritance."""
        error = StorageError("Storage failed")

        assert isinstance(error, MFAError)
        assert isinstance(error, StorageError)

    def test_orchestration_error(self):
        """Test OrchestrationError inheritance."""
        error = OrchestrationError("Orchestration failed")

        assert isinstance(error, MFAError)
        assert isinstance(error, OrchestrationError)

    def test_validation_error(self):
        """Test ValidationError inheritance."""
        error = ValidationError("Validation failed")

        assert isinstance(error, MFAError)
        assert isinstance(error, ValidationError)


class TestNestedExceptions:
    """Test nested exception hierarchy."""

    def test_network_error_inheritance(self):
        """Test NetworkError inherits from ScrapingError."""
        error = NetworkError("Network failed")

        assert isinstance(error, ScrapingError)
        assert isinstance(error, MFAError)

    def test_parsing_error_inheritance(self):
        """Test ParsingError inherits from ScrapingError."""
        error = ParsingError("Parsing failed")

        assert isinstance(error, ScrapingError)
        assert isinstance(error, MFAError)

    def test_browser_error_inheritance(self):
        """Test BrowserError inherits from ScrapingError."""
        error = BrowserError("Browser failed")

        assert isinstance(error, ScrapingError)
        assert isinstance(error, MFAError)

    def test_file_not_found_error_inheritance(self):
        """Test FileNotFoundError inherits from StorageError."""
        error = FileNotFoundError("File not found")

        assert isinstance(error, StorageError)
        assert isinstance(error, MFAError)

    def test_file_permission_error_inheritance(self):
        """Test FilePermissionError inherits from StorageError."""
        error = FilePermissionError("Permission denied")

        assert isinstance(error, StorageError)
        assert isinstance(error, MFAError)

    def test_path_generation_error_inheritance(self):
        """Test PathGenerationError inherits from StorageError."""
        error = PathGenerationError("Path generation failed")

        assert isinstance(error, StorageError)
        assert isinstance(error, MFAError)

    def test_config_validation_error_inheritance(self):
        """Test ConfigValidationError inherits from ConfigurationError."""
        error = ConfigValidationError("Config validation failed")

        assert isinstance(error, ConfigurationError)
        assert isinstance(error, MFAError)

    def test_data_processing_error_inheritance(self):
        """Test DataProcessingError inherits from AnalysisError."""
        error = DataProcessingError("Data processing failed")

        assert isinstance(error, AnalysisError)
        assert isinstance(error, MFAError)

    def test_factory_error_inheritance(self):
        """Test FactoryError inherits from OrchestrationError."""
        error = FactoryError("Factory failed")

        assert isinstance(error, OrchestrationError)
        assert isinstance(error, MFAError)

    def test_requirement_error_inheritance(self):
        """Test RequirementError inherits from OrchestrationError."""
        error = RequirementError("Requirements not met")

        assert isinstance(error, OrchestrationError)
        assert isinstance(error, MFAError)


class TestExceptionFactories:
    """Test exception factory functions."""

    def test_create_config_error(self):
        """Test create_config_error factory function."""
        error = create_config_error("Config failed", "/path/to/config.yaml")

        assert isinstance(error, ConfigurationError)
        assert str(error) == "Config failed [config_path=/path/to/config.yaml]"
        assert error.context["config_path"] == "/path/to/config.yaml"

    def test_create_config_error_no_path(self):
        """Test create_config_error without path."""
        error = create_config_error("Config failed")

        assert isinstance(error, ConfigurationError)
        assert str(error) == "Config failed"
        assert error.context == {}

    def test_create_scraping_error(self):
        """Test create_scraping_error factory function."""
        error = create_scraping_error(
            "Scraping failed", url="https://example.com", fund_name="Test Fund"
        )

        assert isinstance(error, ScrapingError)
        expected_msg = "Scraping failed [url=https://example.com, fund_name=Test Fund]"
        assert str(error) == expected_msg

    def test_create_scraping_error_minimal(self):
        """Test create_scraping_error with minimal parameters."""
        error = create_scraping_error("Scraping failed")

        assert isinstance(error, ScrapingError)
        assert str(error) == "Scraping failed"
        assert error.context == {}

    def test_create_storage_error(self):
        """Test create_storage_error factory function."""
        error = create_storage_error(
            "Storage failed", file_path="/test/file.json", operation="save"
        )

        assert isinstance(error, StorageError)
        expected_msg = "Storage failed [file_path=/test/file.json, operation=save]"
        assert str(error) == expected_msg

    def test_create_storage_error_minimal(self):
        """Test create_storage_error with minimal parameters."""
        error = create_storage_error("Storage failed")

        assert isinstance(error, StorageError)
        assert str(error) == "Storage failed"
        assert error.context == {}

    def test_create_analysis_error(self):
        """Test create_analysis_error factory function."""
        error = create_analysis_error(
            "Analysis failed", analysis_type="holdings", category="largeCap"
        )

        assert isinstance(error, AnalysisError)
        expected_msg = "Analysis failed [analysis_type=holdings, category=largeCap]"
        assert str(error) == expected_msg

    def test_create_analysis_error_minimal(self):
        """Test create_analysis_error with minimal parameters."""
        error = create_analysis_error("Analysis failed")

        assert isinstance(error, AnalysisError)
        assert str(error) == "Analysis failed"
        assert error.context == {}


class TestExceptionContextHandling:
    """Test exception context handling."""

    def test_exception_context_preservation(self):
        """Test that exception context is properly preserved."""
        original_context = {"test": "value", "number": 42}
        error = MFAError("Test error", original_context)

        assert error.context is original_context
        assert error.context["test"] == "value"
        assert error.context["number"] == 42

    def test_exception_context_modification(self):
        """Test that exception context can be modified after creation."""
        error = MFAError("Test error")
        error.context["new_key"] = "new_value"

        assert error.context["new_key"] == "new_value"
        assert str(error) == "Test error [new_key=new_value]"

    def test_exception_context_multiple_keys(self):
        """Test exception with multiple context keys."""
        context = {
            "analysis_type": "holdings",
            "category": "largeCap",
            "file_count": 5,
            "error_code": "VALIDATION_FAILED",
        }
        error = MFAError("Processing failed", context)

        context_str = ", ".join(
            [
                "analysis_type=holdings",
                "category=largeCap",
                "file_count=5",
                "error_code=VALIDATION_FAILED",
            ]
        )
        expected_msg = f"Processing failed [{context_str}]"
        assert str(error) == expected_msg

    def test_exception_context_special_characters(self):
        """Test exception context with special characters."""
        context = {
            "path": "/usr/local/bin/python",
            "url": "https://example.com/test?param=value",
            "message": "Error: something went wrong!",
        }
        error = MFAError("Operation failed", context)

        # Should handle special characters properly
        error_str = str(error)
        assert "path=/usr/local/bin/python" in error_str
        assert "url=https://example.com/test?param=value" in error_str
        assert "message=Error: something went wrong!" in error_str
