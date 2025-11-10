from unittest.mock import MagicMock

import pytest
from vectorwave.batch.batch import get_batch_manager
from vectorwave.exception.exceptions import WeaviateConnectionError
from vectorwave.models.db_config import WeaviateSettings


@pytest.fixture
def mock_deps(monkeypatch):
    """
    Fixture to mock dependencies for batch.py (db, config, atexit)
    """
    # Mock WeaviateClient
    mock_client = MagicMock()
    mock_client.batch = MagicMock()
    mock_client.batch.configure = MagicMock()
    mock_client.batch.add_object = MagicMock()
    mock_client.batch.flush = MagicMock()

    mock_collection_data = MagicMock()
    mock_collection = MagicMock()
    mock_collection.data = mock_collection_data
    mock_client.collections.get = MagicMock(return_value=mock_collection)

    # Mock get_weaviate_client
    mock_get_client = MagicMock(return_value=mock_client)
    monkeypatch.setattr("vectorwave.batch.batch.get_weaviate_client", mock_get_client)

    # Mock get_weaviate_settings
    mock_settings = WeaviateSettings()
    mock_get_settings = MagicMock(return_value=mock_settings)
    monkeypatch.setattr("vectorwave.batch.batch.get_weaviate_settings", mock_get_settings)

    # Mock atexit.register
    mock_atexit_register = MagicMock()
    monkeypatch.setattr("atexit.register", mock_atexit_register)

    # Clear lru_cache
    get_batch_manager.cache_clear()

    return {
        "get_client": mock_get_client,
        "get_settings": mock_get_settings,
        "client": mock_client,
        "settings": mock_settings,
        "atexit": mock_atexit_register
    }

def test_get_batch_manager_is_singleton(mock_deps):
    """
    Case 1: Test if get_batch_manager() always returns the same instance (singleton)
    """
    manager1 = get_batch_manager()
    manager2 = get_batch_manager()
    assert manager1 is manager2

def test_batch_manager_initialization(mock_deps):
    """
    Case 2: Test if BatchManager correctly calls dependencies (configure, atexit) upon initialization
    """
    manager = get_batch_manager()

    mock_deps["get_settings"].assert_called_once()
    mock_deps["get_client"].assert_called_once_with(mock_deps["settings"])

    assert manager._initialized is True

def test_batch_manager_init_failure(monkeypatch):
    """
    Case 3: Test if _initialized remains False when DB connection (get_weaviate_client) fails
    """
    # Mock get_weaviate_client to raise an exception
    mock_get_client_fail = MagicMock(side_effect=WeaviateConnectionError("Test connection error"))
    monkeypatch.setattr("vectorwave.batch.batch.get_weaviate_client", mock_get_client_fail)

    get_batch_manager.cache_clear()
    manager = get_batch_manager()

    # The _initialized flag should be False if initialization fails
    assert manager._initialized is False

def test_add_object_calls_client_batch(mock_deps):
    """
    Case 4: Test if add_object() correctly calls client.batch.add_object
    """
    manager = get_batch_manager()
    props = {"key": "value"}

    manager.add_object(collection="TestCollection", properties=props, uuid="test-uuid")

    mock_deps["client"].collections.get.assert_called_once_with("TestCollection")

    mock_deps["client"].collections.get.return_value.data.insert.assert_called_once_with(
        properties=props,
        uuid="test-uuid",
        vector=None
)
