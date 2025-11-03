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

    (1) Collects function definitions (static data) once on script load.
    (2) Records function execution (dynamic data) every time the function is called.
    """

    def decorator(func):

        # --- 1. Static Data Collection (Runs once on script load) ---
        func_uuid = None
        try:
            module_name = func.__module__
            function_name = func.__name__

            func_identifier = f"{module_name}.{function_name}"
            func_uuid = generate_uuid5(func_identifier)

            # Matches the base properties in db.py's create_vectorwave_schema
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

            # --- 2. Dynamic Data Logging (Runs every time the function is called) ---
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

                    # Matches the base properties in db.py's create_execution_schema
                    execution_props = {
                        "function_uuid": func_uuid,
                        "timestamp_utc": timestamp_utc,
                        "duration_ms": duration_ms,
                        "status": status,
                        "error_message": error_msg,
                    }

                    # Merge global custom values (e.g., run_id)
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