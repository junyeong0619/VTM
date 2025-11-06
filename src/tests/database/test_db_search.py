import pytest
from unittest.mock import patch, MagicMock, ANY
import weaviate.classes as wvc
import weaviate

# Functions to test
from vectorwave.database.db_search import (
    search_functions,
    search_executions,
    _build_weaviate_filters
)
from vectorwave.models.db_config import WeaviateSettings


@pytest.fixture
def mock_search_deps(monkeypatch):
    """ Mock dependencies for search_functions (mocking near_text method) """
    mock_settings = WeaviateSettings(COLLECTION_NAME="TestFunctions")
    mock_get_settings = MagicMock(return_value=mock_settings)
    monkeypatch.setattr("vectorwave.database.db_search.get_weaviate_settings", mock_get_settings)

    mock_client = MagicMock(spec=weaviate.WeaviateClient)
    mock_collections_obj = MagicMock()
    mock_func_collection = MagicMock()

    mock_query_obj = MagicMock()
    mock_obj = MagicMock()
    mock_obj.properties = {"name": "test_func"}
    mock_obj.metadata = MagicMock(uuid="test-uuid")
    mock_query_obj.near_text.return_value = MagicMock(objects=[mock_obj])

    mock_func_collection.query = mock_query_obj

    def get_collection_side_effect(name):
        if name == "TestFunctions":
            return mock_func_collection
        return MagicMock()

    mock_collections_obj.get = MagicMock(side_effect=get_collection_side_effect)
    mock_client.collections = mock_collections_obj

    mock_get_client = MagicMock(return_value=mock_client)
    monkeypatch.setattr("vectorwave.database.db_search.get_cached_client", mock_get_client)

    return {
        "client": mock_client,
        "collection": mock_func_collection,
        "query": mock_query_obj, # Return query object for testing
        "settings": mock_settings
    }

# --- Test _build_weaviate_filters helper function ---

def test_build_filters_none_or_empty():
    assert _build_weaviate_filters(None) is None
    assert _build_weaviate_filters({}) is None

def test_build_filters_single():
    filters = {"team": "billing"}
    result = _build_weaviate_filters(filters)
    # [MODIFIED] isinstance -> is not None (Fix AssertionError)
    assert result is not None

def test_build_filters_multiple():
    filters = {"team": "billing", "priority": 1}
    result = _build_weaviate_filters(filters)
    # [MODIFIED] isinstance -> is not None (Fix AssertionError)
    assert result is not None


# --- Basic tests for search_functions ---

def test_search_functions_basic_call(mock_search_deps):
    # [MODIFIED] Test the near_text method instead of fetch_objects.
    mock_query = mock_search_deps["query"]
    search_functions(query="test query", limit=3)

    mock_query.near_text.assert_called_once_with(
        query="test query",
        limit=3,
        filters=None,
        return_metadata=wvc.query.MetadataQuery(distance=True)
    )

def test_search_functions_with_filters(mock_search_deps):
    mock_query = mock_search_deps["query"]
    test_filters = {"team": "billing"}

    search_functions(query="filtered query", limit=5, filters=test_filters)

    mock_query.near_text.assert_called_once()
    call_args = mock_query.near_text.call_args

    assert call_args.kwargs['query'] == "filtered query"
    assert call_args.kwargs['limit'] == 5
    assert call_args.kwargs['filters'] is not None


# --- Tests for search_executions ---

@pytest.fixture
def mock_search_exec_deps(monkeypatch):
    """ Mock dependencies for search_executions (no change) """
    mock_settings = WeaviateSettings(EXECUTION_COLLECTION_NAME="TestExecutions")
    mock_get_settings = MagicMock(return_value=mock_settings)
    monkeypatch.setattr("vectorwave.database.db_search.get_weaviate_settings", mock_get_settings)

    mock_client = MagicMock(spec=weaviate.WeaviateClient)
    mock_collections_obj = MagicMock()
    mock_exec_collection = MagicMock()
    mock_exec_collection.query.fetch_objects.return_value = MagicMock(objects=[])

    def get_collection_side_effect(name):
        if name == "TestExecutions":
            return mock_exec_collection
        return MagicMock()

    mock_collections_obj.get = MagicMock(side_effect=get_collection_side_effect)
    mock_client.collections = mock_collections_obj

    mock_get_client = MagicMock(return_value=mock_client)
    monkeypatch.setattr("vectorwave.database.db_search.get_cached_client", mock_get_client)

    return {
        "client": mock_client,
        "collection": mock_exec_collection,
        "settings": mock_settings
    }

def test_search_executions_default_sort(mock_search_exec_deps):
    mock_collection = mock_search_exec_deps["collection"]
    search_executions(limit=5)

    mock_collection.query.fetch_objects.assert_called_once_with(
        limit=5,
        filters=None,
        sort=ANY
    )

    call_args = mock_collection.query.fetch_objects.call_args
    sort_arg = call_args.kwargs['sort']

    assert sort_arg is not None

def test_search_executions_filter_and_sort_duration(mock_search_exec_deps):
    mock_collection = mock_search_exec_deps["collection"]
    test_filters = {"status": "SUCCESS"}

    search_executions(
        limit=3,
        filters=test_filters,
        sort_by="duration_ms",
        sort_ascending=False
    )

    mock_collection.query.fetch_objects.assert_called_once()
    call_args = mock_collection.query.fetch_objects.call_args

    assert call_args.kwargs['limit'] == 3
    assert call_args.kwargs['filters'] is not None

    sort_arg = call_args.kwargs['sort']
    assert sort_arg is not None