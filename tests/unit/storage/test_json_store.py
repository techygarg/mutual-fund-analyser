"""Unit tests for JsonStore - demonstrating clean code testability."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from mfa.storage.json_store import JsonStorageError, JsonStore


class TestJsonStore:
    """Test cases for JsonStore class."""

    def test_save_and_load_roundtrip(self):
        """Test saving and loading data maintains integrity."""
        test_data = {"test": "value", "number": 42}

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"

            # Save data
            JsonStore.save(test_data, file_path)
            assert file_path.exists()

            # Load data
            loaded_data = JsonStore.load(file_path)
            assert loaded_data == test_data

    def test_save_creates_parent_directories(self):
        """Test that save creates parent directories."""
        test_data = {"test": "value"}

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nested" / "deep" / "test.json"

            JsonStore.save(test_data, file_path)
            assert file_path.exists()
            assert file_path.parent.exists()

    def test_load_nonexistent_file_raises_error(self):
        """Test loading non-existent file raises appropriate error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nonexistent.json"

            with pytest.raises(JsonStorageError, match="Failed to load JSON file"):
                JsonStore.load(file_path)

    def test_exists_returns_true_for_valid_file(self):
        """Test exists returns True for valid JSON file."""
        test_data = {"test": "value"}

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            JsonStore.save(test_data, file_path)

            assert JsonStore.exists(file_path) is True

    def test_exists_returns_false_for_nonexistent_file(self):
        """Test exists returns False for non-existent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nonexistent.json"

            assert JsonStore.exists(file_path) is False

    def test_get_file_size_kb(self):
        """Test file size calculation."""
        test_data = {"test": "value" * 100}  # Make it bigger

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            JsonStore.save(test_data, file_path)

            size_kb = JsonStore.get_file_size_kb(file_path)
            assert size_kb > 0
            assert isinstance(size_kb, float)

    def test_validate_json_structure_valid_data(self):
        """Test validation passes for valid data."""
        test_data = {"required_key": "value", "other_key": "value"}
        required_keys = ["required_key"]

        # Should not raise any exception
        JsonStore.validate_json_structure(test_data, required_keys)

    def test_validate_json_structure_missing_keys(self):
        """Test validation fails for missing required keys."""
        test_data = {"other_key": "value"}
        required_keys = ["required_key", "another_required"]

        with pytest.raises(JsonStorageError, match="Missing required keys"):
            JsonStore.validate_json_structure(test_data, required_keys)

    @patch("mfa.storage.json_store.orjson.dumps")
    def test_save_handles_serialization_error(self, mock_dumps):
        """Test save handles serialization errors gracefully."""
        mock_dumps.side_effect = ValueError("Serialization error")
        test_data = {"test": "value"}

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"

            with pytest.raises(JsonStorageError, match="Failed to save JSON file"):
                JsonStore.save(test_data, file_path)
