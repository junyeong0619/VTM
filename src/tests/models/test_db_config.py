import pytest
import json
from unittest.mock import patch, mock_open
from json import JSONDecodeError

# Function to test
from vectorwave.models.db_config import get_weaviate_settings

# --- Mock Data ---

# Mock content for a successfully loaded .weaviate_properties file
MOCK_JSON_DATA = """
{
  "run_id": {
    "data_type": "TEXT",
    "description": "Test run ID"
  },
  "experiment_id": {
    "data_type": "INT",
    "description": "Identifier for the experiment"
  }
}
"""

# Mock content for a malformed .weaviate_properties file (invalid JSON)
MOCK_INVALID_JSON = """
{
  "run_id": {
    "data_type": "TEXT"
  } 
""" # Missing closing '}'

# --- Test Cases ---

@patch('os.path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open, read_data=MOCK_JSON_DATA)
def test_get_settings_loads_custom_props_success(mock_open_file, mock_exists):
    """
    Case 1: .weaviate_properties file exists and JSON is valid
    - settings.custom_properties should be loaded correctly as a dictionary
    """
    # Arrange
    # Clear the @lru_cache to bypass caching for this test
    get_weaviate_settings.cache_clear()

    # Act
    settings = get_weaviate_settings()

    # Assert
    # Verify that the default path (.weaviate_properties) was checked
    mock_exists.assert_called_with(".weaviate_properties")
    # Verify the file was opened in 'r' mode
    mock_open_file.assert_called_with(".weaviate_properties", 'r', encoding='utf-8')

    assert settings.custom_properties is not None
    assert "run_id" in settings.custom_properties
    assert settings.custom_properties["run_id"]["data_type"] == "TEXT"
    assert settings.custom_properties["run_id"]["description"] == "Test run ID"
    assert "experiment_id" in settings.custom_properties


@patch('os.path.exists', return_value=False)
def test_get_settings_file_not_found(mock_exists, capsys):
    """
    Case 2: .weaviate_properties file does not exist
    - settings.custom_properties should be None
    - A 'file not found' note should be printed
    """
    # Arrange
    get_weaviate_settings.cache_clear()

    # Act
    settings = get_weaviate_settings()

    # Assert
    mock_exists.assert_called_with(".weaviate_properties")
    assert settings.custom_properties is None

    # Check if 'file not found' note was printed
    captured = capsys.readouterr()
    assert "file not found" in captured.out


@patch('os.path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open, read_data=MOCK_INVALID_JSON)
@patch('json.load', side_effect=JSONDecodeError("Mock JSON Decode Error", "", 0))
def test_get_settings_invalid_json(mock_json_load, mock_open_file, mock_exists, capsys):
    """
    Case 3: File exists but JSON format is invalid
    - settings.custom_properties should be None
    - A 'Could not parse JSON' warning should be printed
    """
    # Arrange
    get_weaviate_settings.cache_clear()

    # Act
    settings = get_weaviate_settings()

    # Assert
    mock_exists.assert_called_once()
    mock_open_file.assert_called_once()
    mock_json_load.assert_called_once() # json.load was called but failed (due to side_effect)
    assert settings.custom_properties is None # Should be None due to parsing failure

    # Check if 'Could not parse JSON' warning was printed
    captured = capsys.readouterr()
    assert "Could not parse JSON" in captured.out