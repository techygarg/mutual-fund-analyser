"""
JSON Schema-based validation for MFA test data.

Clean, declarative validation using JSON Schema instead of manual field-by-field checks.
"""

import json
from pathlib import Path
from typing import Any, Dict

import jsonschema
from jsonschema import Draft202012Validator


class SchemaValidator:
    """JSON Schema validator for test data validation."""

    def __init__(self, schemas_dir: Path | None = None):
        """
        Initialize schema validator.

        Args:
            schemas_dir: Directory containing schema files. Defaults to tests/schemas/
        """
        if schemas_dir is None:
            schemas_dir = Path(__file__).parent.parent / "schemas"

        self.schemas_dir = schemas_dir
        self._schema_cache: Dict[str, Dict[str, Any]] = {}

    def validate_file(self, json_file: Path, schema_path: str) -> Dict[str, Any]:
        """
        Validate a JSON file against a schema.

        Args:
            json_file: Path to JSON file to validate
            schema_path: Relative path to schema file (e.g., "holdings/analysis_output.json")

        Returns:
            Parsed and validated JSON data

        Raises:
            jsonschema.ValidationError: If validation fails
            FileNotFoundError: If schema or data file not found
        """
        # Load and parse data
        with open(json_file) as f:
            data = json.load(f)

        # Validate against schema
        self.validate_data(data, schema_path)

        return data

    def validate_data(self, data: Dict[str, Any], schema_path: str) -> None:
        """
        Validate data dictionary against schema.

        Args:
            data: Data to validate
            schema_path: Relative path to schema file

        Raises:
            jsonschema.ValidationError: If validation fails
        """
        schema = self._load_schema(schema_path)
        validator = Draft202012Validator(schema)
        validator.validate(data)  # Raises ValidationError if invalid

    def _load_schema(self, schema_path: str) -> Dict[str, Any]:
        """Load schema from file with caching."""
        if schema_path not in self._schema_cache:
            schema_file = self.schemas_dir / schema_path
            if not schema_file.exists():
                raise FileNotFoundError(f"Schema file not found: {schema_file}")

            with open(schema_file) as f:
                self._schema_cache[schema_path] = json.load(f)

        return self._schema_cache[schema_path]


# Global validator instance
_validator = SchemaValidator()


def validate_holdings_analysis_file(json_file: Path) -> Dict[str, Any]:
    """
    Validate holdings analysis output file.

    Args:
        json_file: Path to analysis JSON file

    Returns:
        Validated analysis data

    Raises:
        jsonschema.ValidationError: If validation fails
    """
    return _validator.validate_file(json_file, "holdings/analysis_output.json")


def validate_holdings_extracted_file(json_file: Path) -> Dict[str, Any]:
    """
    Validate holdings extracted data file.

    Args:
        json_file: Path to extracted JSON file

    Returns:
        Validated extracted data

    Raises:
        jsonschema.ValidationError: If validation fails
    """
    return _validator.validate_file(json_file, "holdings/extracted_data.json")


def validate_holdings_analysis_data(data: Dict[str, Any]) -> None:
    """
    Validate holdings analysis data dictionary.

    Args:
        data: Analysis data to validate

    Raises:
        jsonschema.ValidationError: If validation fails
    """
    _validator.validate_data(data, "holdings/analysis_output.json")


def validate_holdings_extracted_data(data: Dict[str, Any]) -> None:
    """
    Validate holdings extracted data dictionary.

    Args:
        data: Extracted data to validate

    Raises:
        jsonschema.ValidationError: If validation fails
    """
    _validator.validate_data(data, "holdings/extracted_data.json")
