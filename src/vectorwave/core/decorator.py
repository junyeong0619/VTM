import inspect
import time
import traceback
from datetime import datetime, timezone
from functools import wraps
from weaviate.util import generate_uuid5

from ..batch.batch import get_batch_manager
from ..models.db_config import get_weaviate_settings

def vectorize(search_description: str,
              sequence_narrative: str):
    """
    VectorWave Decorator

    (1) 함수 정의(정적 데이터)를 스크립트 로드 시 1회 수집합니다.
    (2) 함수 실행(동적 데이터)을 함수 호출 시 매번 기록합니다.
    """

    def decorator(func):

        # --- 1. 정적 데이터 수집 (스크립트 로드 시 1회 실행) ---
        func_uuid = None
        try:
            module_name = func.__module__
            function_name = func.__name__

            func_identifier = f"{module_name}.{function_name}"
            func_uuid = generate_uuid5(func_identifier)

            # db.py의 create_vectorwave_schema 기본 속성과 일치
            static_properties = {
                "function_name": function_name,
                "module_name": module_name,
                "docstring": inspect.getdoc(func) or "",
                "source_code": inspect.getsource(func),
                "search_description": search_description,
                "sequence_narrative": sequence_narrative
            }

            batch = get_batch_manager()
            settings = get_weaviate_settings()

            batch.add_object(
                collection=settings.COLLECTION_NAME,
                properties=static_properties,
                uuid=func_uuid
            )

        except Exception as e:
            print(f"Error in @vectorize setup for {func.__name__}: {e}") # print 유지
        # --- -------------------------------------------- ---


        @wraps(func)
        def wrapper(*args, **kwargs):

            # --- 2. 동적 데이터 로깅 (함수 호출 시 매번 실행) ---
            if not func_uuid:
                print(f"Warning: Skipping execution log for {func.__name__}: func_uuid not set.") # print 유지
                return func(*args, **kwargs)

            start_time = time.perf_counter()
            timestamp_utc = datetime.now(timezone.utc).isoformat()
            status = "SUCCESS"
            error_msg = None
            result = None

            try:
                result = func(*args, **kwargs)
            except Exception as e:
                status = "ERROR"
                error_msg = traceback.format_exc()
                print(f"Error during execution of {func.__name__}: {e}") # print 유지
                raise e
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000

                try:
                    settings = get_weaviate_settings()
                    global_values = settings.global_custom_values or {}

                    # db.py의 create_execution_schema 기본 속성과 일치
                    execution_props = {
                        "function_uuid": func_uuid,
                        "timestamp_utc": timestamp_utc,
                        "duration_ms": duration_ms,
                        "status": status,
                        "error_message": error_msg,
                    }

                    # 전역 커스텀 값(run_id 등) 병합
                    execution_props.update(global_values)

                    batch = get_batch_manager()
                    batch.add_object(
                        collection=settings.EXECUTION_COLLECTION_NAME,
                        properties=execution_props
                    )
                except Exception as e:
                    print(f"Error: Failed to log execution for {func.__name__}: {e}") # print 유지

            return result

        return wrapper
    return decorator