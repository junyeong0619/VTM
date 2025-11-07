import pytest
from unittest.mock import patch, MagicMock
import inspect
from weaviate.util import generate_uuid5

from vectorwave.core.decorator import vectorize
from vectorwave.models.db_config import WeaviateSettings

from vectorwave.batch.batch import get_batch_manager as real_get_batch_manager
from vectorwave.database.db import get_cached_client as real_get_cached_client
from vectorwave.models.db_config import get_weaviate_settings as real_get_settings


@pytest.fixture
def mock_decorator_deps(monkeypatch):
    """
    Mocks dependencies for decorator.py (get_batch_manager, get_weaviate_settings)
    """
    # 1. Mock BatchManager
    mock_batch_manager = MagicMock()
    mock_batch_manager.add_object = MagicMock()
    mock_get_batch_manager = MagicMock(return_value=mock_batch_manager)

    # 2. Mock Settings
    mock_custom_props = {
        "run_id": {"data_type": "TEXT"},
        "team": {"data_type": "TEXT"},
        "priority": {"data_type": "INT"}
    }
    mock_settings = WeaviateSettings(
        COLLECTION_NAME="TestFunctions",
        EXECUTION_COLLECTION_NAME="TestExecutions",
        custom_properties=mock_custom_props,
        global_custom_values={"run_id": "test-run-abc"}
    )
    mock_get_settings = MagicMock(return_value=mock_settings)

    mock_client = MagicMock()
    mock_get_client = MagicMock(return_value=mock_client)


    # --- decorator.py ---
    monkeypatch.setattr("vectorwave.core.decorator.get_batch_manager", mock_get_batch_manager)
    monkeypatch.setattr("vectorwave.core.decorator.get_weaviate_settings", mock_get_settings)

    # --- tracer.py ---
    monkeypatch.setattr("vectorwave.monitoring.tracer.get_batch_manager", mock_get_batch_manager)
    monkeypatch.setattr("vectorwave.monitoring.tracer.get_weaviate_settings", mock_get_settings)

    # --- batch.py (tracer가 get_batch_manager()를 호출할 때 사용) ---
    # WeaviateBatchManager.__init__이 실패하지 않도록 패치
    monkeypatch.setattr("vectorwave.batch.batch.get_weaviate_client", mock_get_client)
    monkeypatch.setattr("vectorwave.batch.batch.get_weaviate_settings", mock_get_settings)

    # 5. Clear caches to ensure mocks are used
    real_get_batch_manager.cache_clear()
    real_get_cached_client.cache_clear()
    real_get_settings.cache_clear()

    return {
        "get_batch": mock_get_batch_manager,
        "get_settings": mock_get_settings,
        "batch": mock_batch_manager,
        "settings": mock_settings
    }


@pytest.fixture
def mock_decorator_deps_no_props(monkeypatch):
    """
    Fixture variant where settings.custom_properties is None
    """
    # 1. Mock BatchManager
    mock_batch_manager = MagicMock()
    mock_batch_manager.add_object = MagicMock()
    mock_get_batch_manager = MagicMock(return_value=mock_batch_manager)

    # 2. Mock Settings (custom_properties=None)
    mock_settings = WeaviateSettings(
        COLLECTION_NAME="TestFunctions",
        EXECUTION_COLLECTION_NAME="TestExecutions",
        custom_properties=None,  # <-- No properties loaded
        global_custom_values=None  # <-- No globals
    )
    mock_get_settings = MagicMock(return_value=mock_settings)

    mock_client = MagicMock()
    mock_get_client = MagicMock(return_value=mock_client)

    monkeypatch.setattr("vectorwave.core.decorator.get_batch_manager", mock_get_batch_manager)
    monkeypatch.setattr("vectorwave.core.decorator.get_weaviate_settings", mock_get_settings)
    monkeypatch.setattr("vectorwave.monitoring.tracer.get_batch_manager", mock_get_batch_manager)
    monkeypatch.setattr("vectorwave.monitoring.tracer.get_weaviate_settings", mock_get_settings)
    monkeypatch.setattr("vectorwave.batch.batch.get_weaviate_client", mock_get_client)
    monkeypatch.setattr("vectorwave.batch.batch.get_weaviate_settings", mock_get_settings)

    # 5. Clear caches
    real_get_batch_manager.cache_clear()
    real_get_cached_client.cache_clear()
    real_get_settings.cache_clear()

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


def test_vectorize_dynamic_data_with_execution_tags(mock_decorator_deps):
    """
    Case 4: Test if execution logs correctly merge global tags (run_id) and
    function-specific tags (team, priority) provided via **kwargs.
    """
    mock_batch = mock_decorator_deps["batch"]
    mock_settings = mock_decorator_deps["settings"]

    # 1. Arrange: Define a function with function-specific execution tags
    @vectorize(
        search_description="Test with specific tags",
        sequence_narrative="Tags should be merged",
        team="backend",  # <-- Function-specific tag
        priority=1  # <-- Function-specific tag
    )
    def my_tagged_function():
        return "Tagged success"

    # 2. Act: Execute the decorated function
    result = my_tagged_function()

    # 3. Assert: Basic execution
    assert result == "Tagged success"
    # (1 static call + 1 dynamic call)
    assert mock_batch.add_object.call_count == 2

    # 4. Assert: Check the properties of the dynamic log (the last call)
    args, kwargs = mock_batch.add_object.call_args

    assert kwargs["collection"] == mock_settings.EXECUTION_COLLECTION_NAME
    assert kwargs["properties"]["status"] == "SUCCESS"

    # 4a. Verify Global Tag (from fixture)
    assert kwargs["properties"]["run_id"] == "test-run-abc"

    # 4b. Verify Function-Specific Tags (from @vectorize)
    assert kwargs["properties"]["team"] == "backend"
    assert kwargs["properties"]["priority"] == 1


def test_vectorize_execution_tags_override_global_tags(mock_decorator_deps):
    """
    Case 5: Test if a function-specific tag (e.g., 'run_id')
    correctly overrides a global tag with the same name.
    """
    mock_batch = mock_decorator_deps["batch"]

    # 1. Arrange: Define function where 'run_id' will override the global value
    # The fixture provides a global "run_id": "test-run-abc"
    @vectorize(
        search_description="Test override",
        sequence_narrative="Next",
        run_id="override-run-xyz"  # <-- This should WIN against "test-run-abc"
    )
    def my_override_function():
        pass

    # 2. Act
    my_override_function()

    # 3. Assert
    args, kwargs = mock_batch.add_object.call_args

    # Verify that the function-specific 'run_id' overrode the global one
    assert kwargs["properties"]["run_id"] == "override-run-xyz"


def test_vectorize_filters_invalid_execution_tags(mock_decorator_deps):
    """
    Case 6: Test that the decorator filters out execution tags that are
    NOT in settings.custom_properties and only logs the valid tags.
    (This test intentionally does not check the warning output mechanism)
    """
    mock_batch = mock_decorator_deps["batch"]
    mock_settings = mock_decorator_deps["settings"]

    # 1. Arrange: Define function with valid tags ('team', 'priority')
    # and one invalid tag ('unknown_tag')
    # (Fixture defines 'run_id', 'team', 'priority' as custom_properties)
    @vectorize(
        search_description="Test tag filtering",
        sequence_narrative="Next",
        team="data-science",  # <-- Valid
        priority=2,  # <-- Valid
        unknown_tag="should-be-ignored"  # <-- INVALID
    )
    def my_mixed_tags_function():
        pass

    # 2. Act
    my_mixed_tags_function()  # Run the wrapper

    # 3. Assert: Check final execution log properties
    # (We check the *last* call, which is the dynamic log)
    args, kwargs = mock_batch.add_object.call_args
    props = kwargs["properties"]

    assert kwargs["collection"] == mock_settings.EXECUTION_COLLECTION_NAME

    # 3a. Valid global tag should exist
    assert props["run_id"] == "test-run-abc"

    # 3b. Valid function-specific tags should exist
    assert props["team"] == "data-science"
    assert props["priority"] == 2

    # 3c. Invalid tag should NOT exist
    assert "unknown_tag" not in props


def test_vectorize_handles_tags_when_no_props_file(mock_decorator_deps_no_props):
    """
    Case 7: Test that if settings.custom_properties is None,
    ALL execution_tags are ignored.
    (This test intentionally does not check the warning output mechanism)
    """
    mock_batch = mock_decorator_deps_no_props["batch"]
    mock_settings = mock_decorator_deps_no_props["settings"]

    # 1. Arrange
    @vectorize(
        search_description="Test no props",
        sequence_narrative="Next",
        team="should-be-ignored"  # <-- Invalid (because no file)
    )
    def my_no_props_function():
        pass

    # 2. Act
    my_no_props_function()  # Run wrapper

    # 3. Assert: Check final execution log properties
    args, kwargs = mock_batch.add_object.call_args
    props = kwargs["properties"]

    assert kwargs["collection"] == mock_settings.EXECUTION_COLLECTION_NAME

    # 3a. Basic properties should still exist
    assert props["status"] == "SUCCESS"

    # 3b. The tag should NOT exist
    assert "team" not in props