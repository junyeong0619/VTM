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
    decorator.py의 의존성 (get_batch_manager, get_weaviate_settings)을 모킹
    """
    # get_batch_manager 모킹
    mock_batch_manager = MagicMock()
    mock_batch_manager.add_object = MagicMock()
    mock_get_batch_manager = MagicMock(return_value=mock_batch_manager)

    # get_weaviate_settings 모킹
    mock_settings = WeaviateSettings(
        COLLECTION_NAME="TestFunctions",
        EXECUTION_COLLECTION_NAME="TestExecutions",
        global_custom_values={"run_id": "test-run-abc"}
    )
    mock_get_settings = MagicMock(return_value=mock_settings)

    # patch.dict는 decorator.py 내부의 임포트에 적용
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
    Case 1: 데코레이터가 로드될 때 (정적) 'VectorWaveFunctions'에 데이터를 1회 추가하는지 테스트
    """
    mock_batch = mock_decorator_deps["batch"]
    mock_settings = mock_decorator_deps["settings"]

    # --- 데코레이터 정의 ---
    @vectorize(
        search_description="Test search desc",
        sequence_narrative="Test sequence narr"
    )
    def my_test_function_static():
        """My test docstring"""
        pass
    # --- ----------------- ---

    # 1. Assert: get_batch_manager와 get_weaviate_settings가 로드 시점에 호출됨
    mock_decorator_deps["get_batch"].assert_called_once()
    # (get_weaviate_settings는 batch 초기화 때 이미 1번 호출되었을 수 있으므로 call_count 대신 확인)
    assert mock_decorator_deps["get_settings"].called

    # 2. Assert: batch.add_object가 1회 호출됨
    mock_batch.add_object.assert_called_once()

    # 3. Assert: 호출 인자가 'VectorWaveFunctions' 컬렉션에 대한 것인지 확인
    args, kwargs = mock_batch.add_object.call_args

    assert kwargs["collection"] == mock_settings.COLLECTION_NAME
    assert kwargs["properties"]["function_name"] == "my_test_function_static"
    assert kwargs["properties"]["docstring"] == "My test docstring"
    assert "def my_test_function_static" in kwargs["properties"]["source_code"]
    assert kwargs["properties"]["search_description"] == "Test search desc"
    assert kwargs["properties"]["sequence_narrative"] == "Test sequence narr"

def test_vectorize_dynamic_data_logging_success(mock_decorator_deps):
    """
    Case 2: 데코레이트된 함수가 '성공' 실행 시 (동적) 'VectorWaveExecutions'에 로그를 추가하는지 테스트
    """
    mock_batch = mock_decorator_deps["batch"]
    mock_settings = mock_decorator_deps["settings"]

    @vectorize(search_description="Test", sequence_narrative="Test")
    def my_test_function_dynamic():
        return "Success"

    # --- 함수 실행 ---
    result = my_test_function_dynamic()
    # --- ----------- ---

    # 1. Assert: 함수 결과가 정상 반환
    assert result == "Success"

    # 2. Assert: add_object가 총 2번 호출됨 (정적 1회 + 동적 1회)
    assert mock_batch.add_object.call_count == 2

    # 3. Assert: 마지막 호출(동적 로그)의 인자 확인
    args, kwargs = mock_batch.add_object.call_args

    assert kwargs["collection"] == mock_settings.EXECUTION_COLLECTION_NAME
    assert kwargs["properties"]["status"] == "SUCCESS"
    assert kwargs["properties"]["error_message"] is None
    assert kwargs["properties"]["duration_ms"] > 0
    # global_custom_values (run_id)가 병합되었는지 확인
    assert kwargs["properties"]["run_id"] == "test-run-abc"

def test_vectorize_dynamic_data_logging_failure(mock_decorator_deps):
    """
    Case 3: 데코레이트된 함수가 '실패' 실행 시 'status=ERROR' 로그를 추가하는지 테스트
    """
    mock_batch = mock_decorator_deps["batch"]
    mock_settings = mock_decorator_deps["settings"]

    @vectorize(search_description="FailTest", sequence_narrative="FailTest")
    def my_failing_function():
        raise ValueError("This is a test error")

    # --- 함수 실행 (예외 발생 확인) ---
    with pytest.raises(ValueError, match="This is a test error"):
        my_failing_function()
    # --- ------------------------- ---

    # 1. Assert: add_object가 총 2번 호출됨 (정적 1회 + 동적 1회)
    assert mock_batch.add_object.call_count == 2

    # 2. Assert: 마지막 호출(동적 로그)의 인자 확인
    args, kwargs = mock_batch.add_object.call_args

    assert kwargs["collection"] == mock_settings.EXECUTION_COLLECTION_NAME
    assert kwargs["properties"]["status"] == "ERROR"
    assert "ValueError: This is a test error" in kwargs["properties"]["error_message"]
    assert "Traceback (most recent call last):" in kwargs["properties"]["error_message"] # [수정된 코드]
    assert kwargs["properties"]["run_id"] == "test-run-abc"