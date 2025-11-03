import pytest
from unittest.mock import patch, MagicMock, call
import atexit

# 테스트 대상
from vectorwave.batch.batch import get_batch_manager, WeaviateBatchManager
from vectorwave.models.db_config import WeaviateSettings
from vectorwave.exception.exceptions import WeaviateConnectionError

@pytest.fixture
def mock_deps(monkeypatch):
    """
    batch.py의 의존성 (db, config, atexit)을 모킹하는 Fixture
    """
    # WeaviateClient 모킹
    mock_client = MagicMock()
    mock_client.batch = MagicMock()
    mock_client.batch.configure = MagicMock()
    mock_client.batch.add_object = MagicMock()
    mock_client.batch.flush = MagicMock()

    # get_weaviate_client 모킹
    mock_get_client = MagicMock(return_value=mock_client)
    monkeypatch.setattr("vectorwave.batch.batch.get_weaviate_client", mock_get_client)

    # get_weaviate_settings 모킹
    mock_settings = WeaviateSettings()
    mock_get_settings = MagicMock(return_value=mock_settings)
    monkeypatch.setattr("vectorwave.batch.batch.get_weaviate_settings", mock_get_settings)

    # atexit.register 모킹
    mock_atexit_register = MagicMock()
    monkeypatch.setattr("atexit.register", mock_atexit_register)

    # lru_cache 클리어
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
    Case 1: get_batch_manager()가 항상 동일한 인스턴스를 반환하는지 (싱글톤) 테스트
    """
    manager1 = get_batch_manager()
    manager2 = get_batch_manager()
    assert manager1 is manager2

def test_batch_manager_initialization(mock_deps):
    """
    Case 2: BatchManager가 초기화될 때 의존성(configure, atexit)을 올바르게 호출하는지 테스트
    """
    manager = get_batch_manager()

    mock_deps["get_settings"].assert_called_once()
    mock_deps["get_client"].assert_called_once_with(mock_deps["settings"])

    # client.batch.configure가 올바른 인자(dynamic=True)로 호출되었는지 확인
    mock_deps["client"].batch.configure.assert_called_once_with(
        batch_size=20,
        dynamic=True,
        timeout_retries=3
    )

    # atexit.register가 manager.flush 함수와 함께 호출되었는지 확인
    mock_deps["atexit"].assert_called_once_with(manager.flush)
    assert manager._initialized is True

def test_batch_manager_init_failure(monkeypatch):
    """
    Case 3: DB 연결(get_weaviate_client) 실패 시, _initialized가 False로 유지되는지 테스트
    """
    # get_weaviate_client가 예외를 발생시키도록 모킹
    mock_get_client_fail = MagicMock(side_effect=WeaviateConnectionError("Test connection error"))
    monkeypatch.setattr("vectorwave.batch.batch.get_weaviate_client", mock_get_client_fail)

    get_batch_manager.cache_clear()
    manager = get_batch_manager()

    # 초기화 실패 시 _initialized 플래그는 False여야 함
    assert manager._initialized is False

def test_add_object_calls_client_batch(mock_deps):
    """
    Case 4: add_object()가 client.batch.add_object를 올바르게 호출하는지 테스트
    """
    manager = get_batch_manager()
    props = {"key": "value"}

    manager.add_object(collection="TestCollection", properties=props, uuid="test-uuid")

    mock_deps["client"].batch.add_object.assert_called_once_with(
        collection="TestCollection",
        properties=props,
        uuid="test-uuid"
    )

def test_flush_calls_client_flush_when_items_exist(mock_deps):
    """
    Case 5: 큐에 아이템이 있을 때(len > 0), flush()가 client.batch.flush를 호출하는지 테스트
    """
    # 큐에 아이템이 있다고 가정 (len(batch)가 1을 반환하도록 설정)
    mock_deps["client"].batch.__len__.return_value = 1

    manager = get_batch_manager()
    manager.flush()

    mock_deps["client"].batch.flush.assert_called_once()

def test_flush_skips_when_empty(mock_deps):
    """
    Case 6: 큐가 비어있을 때(len == 0), flush()가 client.batch.flush를 호출하지 않는지 테스트
    """
    # 큐가 비어있다고 가정 (len(batch)가 0을 반환)
    mock_deps["client"].batch.__len__.return_value = 0

    manager = get_batch_manager()
    manager.flush()

    mock_deps["client"].batch.flush.assert_not_called()