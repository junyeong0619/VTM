import logging
import inspect
import time
import traceback
from functools import wraps
from contextvars import ContextVar
from typing import Optional, List, Dict, Any, Callable
from uuid import uuid4
from datetime import datetime, timezone

from ..batch.batch import get_batch_manager
from ..models.db_config import get_weaviate_settings, WeaviateSettings

# Create module-level logger
logger = logging.getLogger(__name__)

class TraceCollector:
    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self.settings: WeaviateSettings = get_weaviate_settings()
        self.batch = get_batch_manager()


current_tracer_var: ContextVar[Optional[TraceCollector]] = ContextVar('current_tracer', default=None)


def trace_root() -> Callable:
    """
    Decorator factory for the workflow's entry point function.
    Creates and sets the TraceCollector in ContextVar.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_tracer_var.get() is not None:
                return func(*args, **kwargs)

            trace_id = kwargs.pop('trace_id', str(uuid4()))
            tracer = TraceCollector(trace_id=trace_id)
            token = current_tracer_var.set(tracer)

            try:
                # ⭐️ Key: Here, func is the wrapper of @trace_span.
                return func(*args, **kwargs)
            finally:
                current_tracer_var.reset(token)

        return wrapper

    return decorator


def trace_span(
        _func: Optional[Callable] = None,
        *,
        attributes_to_capture: Optional[List[str]] = None
) -> Callable:
    """
    Decorator to capture function execution as a 'span'.
    Can be used as @trace_span or @trace_span(attributes_to_capture=[...]).
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = current_tracer_var.get()
            if not tracer:
                return func(*args, **kwargs)

            start_time = time.perf_counter()
            status = "SUCCESS"
            error_msg = None
            error_code = None
            result = None

            captured_attributes = {}
            if attributes_to_capture:
                try:
                    # Directly checks the kwargs dictionary.
                    for attr_name in attributes_to_capture:
                        if attr_name in kwargs:
                            value = kwargs[attr_name]
                            if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                                value = str(value)
                            captured_attributes[attr_name] = value
                except Exception as e:
                    logger.warning("Failed to capture attributes for '%s': %s", func.__name__, e)

            try:
                result = func(*args, **kwargs)
            except Exception as e:
                status = "ERROR"
                error_msg = traceback.format_exc()

                try:
                    if hasattr(e, 'error_code'):
                        error_code = str(e.error_code)

                    elif tracer.settings.failure_mapping:
                        exception_class_name = type(e).__name__
                        if exception_class_name in tracer.settings.failure_mapping:
                            error_code = tracer.settings.failure_mapping[exception_class_name]

                    if not error_code:
                        error_code = type(e).__name__
                except Exception as e_code:
                    logger.warning(f"Failed to determine error_code: {e_code}")
                    error_code = "UNKNOWN_ERROR_CODE_FAILURE"
                raise e
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000

                span_properties = {
                    "trace_id": tracer.trace_id,
                    "span_id": str(uuid4()),
                    "function_name": func.__name__,
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "duration_ms": duration_ms,
                    "status": status,
                    "error_message": error_msg,
                    "error_code": error_code,
                }

                # 1. Apply global tags first.
                if tracer.settings.global_custom_values:
                    span_properties.update(tracer.settings.global_custom_values)

                # 2. Apply captured attributes second (overriding global values if necessary).
                # (If 'run_id' was captured, this value (e.g., override-run-xyz) overrides the global value.)
                span_properties.update(captured_attributes)

                try:
                    tracer.batch.add_object(
                        collection=tracer.settings.EXECUTION_COLLECTION_NAME,
                        properties=span_properties
                    )
                except Exception as e:
                    logger.error("Failed to log span for '%s' (trace_id: %s): %s", func.__name__, tracer.trace_id, e)

            return result

        return wrapper

    if _func is None:
        return decorator
    else:
        return decorator(_func)