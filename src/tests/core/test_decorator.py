import pytest
from unittest.mock import patch, MagicMock
import inspect
from weaviate.util import generate_uuid5

# 테스트 대상
from vectorwave.core.decorator import vectorize
from vectorwave.models.db_config import WeaviateSettings

@pytest.fixture
def mock_decorator_deps(monkeypatch):
    """
    Mocks dependencies for decorator.py (get_batch_manager, get_weaviate_settings)
    """
    # Mock get_batch_manager
    mock_batch_manager = MagicMock()
    mock_batch_manager.add_object = MagicMock()
    mock_get_batch_manager = MagicMock(return_value=mock_batch_manager)

    # Mock get_weaviate_settings
    mock_settings = WeaviateSettings(
        COLLECTION_NAME="TestFunctions",
        EXECUTION_COLLECTION_NAME="TestExecutions",
        global_custom_values={"run_id": "test-run-abc"}
    )
    mock_get_settings = MagicMock(return_value=mock_settings)

    # patch.dict applies to imports inside decorator.py
    monkeypatch.setattr("vectorwave.core.decorator.get_batch_manager", mock_get_batch_manager)
    monkeypatch.setattr("vectorwave.core.decorator.get_weaviate_settings", mock_get_settings)

    return {
        "get_batch": mock_get_batch_manager,
        "get_settings": mock_get_settings,
        "batch": mock_batch_manager,
        "settings": mock_settings
    }

def test_vectorize_static_data_collection(mock_decorator_deps):
    """
    Case 1: Test if data is added once to 'VectorWaveFunctions' (static) when the decorator is loaded
    """
    mock_batch = mock_decorator_deps["batch"]
    mock_settings = mock_decorator_deps["settings"]

    @vectorize(
        search_description="Test search desc",
        sequence_narrative="Test sequence narr"
    )
    def my_test_function_static():
        """My test docstring"""
        pass
    # --- ----------------- ---

    # 1. Assert: get_batch_manager and get_weaviate_settings are called at load time
    mock_decorator_deps["get_batch"].assert_called_once()
    # (get_weaviate_settings might have already been called once during batch initialization,
    # so check 'called' instead of 'call_count')
    assert mock_decorator_deps["get_settings"].called

    # 2. Assert: batch.add_object is called once
    mock_batch.add_object.assert_called_once()

    # 3. Assert: Check if the call arguments are for the 'VectorWaveFunctions' collection
    args, kwargs = mock_batch.add_object.call_args

    assert kwargs["collection"] == mock_settings.COLLECTION_NAME
    assert kwargs["properties"]["function_name"] == "my_test_function_static"
    assert kwargs["properties"]["docstring"] == "My test docstring"
    assert "def my_test_function_static" in kwargs["properties"]["source_code"]
    assert kwargs["properties"]["search_description"] == "Test search desc"
    assert kwargs["properties"]["sequence_narrative"] == "Test sequence narr"

def test_vectorize_dynamic_data_logging_success(mock_decorator_deps):
    """
    Case 2: Test if the decorated function adds a log to 'VectorWaveExecutions' (dynamic) on 'successful' execution
    """
    mock_batch = mock_decorator_deps["batch"]
    mock_settings = mock_decorator_deps["settings"]

    @vectorize(search_description="Test", sequence_narrative="Test")
    def my_test_function_dynamic():
        return "Success"

    result = my_test_function_dynamic()

    # 1. Assert: Function returns the result normally
    assert result == "Success"

    # 2. Assert: add_object is called 2 times in total (1 static + 1 dynamic)
    assert mock_batch.add_object.call_count == 2

    # 3. Assert: Check arguments of the last call (dynamic log)
    args, kwargs = mock_batch.add_object.call_args

    assert kwargs["collection"] == mock_settings.EXECUTION_COLLECTION_NAME
    assert kwargs["properties"]["status"] == "SUCCESS"
    assert kwargs["properties"]["error_message"] is None
    assert kwargs["properties"]["duration_ms"] > 0
    # Check if global_custom_values (run_id) were merged
    assert kwargs["properties"]["run_id"] == "test-run-abc"

def test_vectorize_dynamic_data_logging_failure(mock_decorator_deps):
    """
    Case 3: Test if the decorated function adds a 'status=ERROR' log on 'failed' execution
    """
    mock_batch = mock_decorator_deps["batch"]
    mock_settings = mock_decorator_deps["settings"]

    @vectorize(search_description="FailTest", sequence_narrative="FailTest")
    def my_failing_function():
        raise ValueError("This is a test error")

    with pytest.raises(ValueError, match="This is a test error"):
        my_failing_function()

    # 1. Assert: add_object is called 2 times in total (1 static + 1 dynamic)
    assert mock_batch.add_object.call_count == 2

    # 2. Assert: Check arguments of the last call (dynamic log)
    args, kwargs = mock_batch.add_object.call_args

    assert kwargs["collection"] == mock_settings.EXECUTION_COLLECTION_NAME
    assert kwargs["properties"]["status"] == "ERROR"
    assert "ValueError: This is a test error" in kwargs["properties"]["error_message"]
    assert "Traceback (most recent call last):" in kwargs["properties"]["error_message"]
    assert kwargs["properties"]["run_id"] == "test-run-abc"