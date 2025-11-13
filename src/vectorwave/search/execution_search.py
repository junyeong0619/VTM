import sys
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any

# --- Path Setup ---
# Assumes this file is in src/vectorwave/search/
# Adds the top-level 'src' folder to sys.path to import other modules
current_dir = os.path.dirname(os.path.abspath(__file__))
src_root = os.path.dirname(os.path.dirname(current_dir))  # src/
sys.path.insert(0, src_root)

try:
    # Import the low-level DB search function
    #
    from vectorwave.database.db_search import search_executions
    from vectorwave import initialize_database
    from vectorwave.database.db import get_cached_client
except ImportError as e:
    # Use logger for the error, but print is necessary if logger fails
    print(f"Failed to import VectorWave module: {e}")
    logging.error(f"Failed to import VectorWave module: {e}", exc_info=True)
    sys.exit(1)

# Set up a module-level logger
logger = logging.getLogger(__name__)


def find_executions(
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "timestamp_utc",
        sort_ascending: bool = False,
        limit: int = 10
) -> List[Dict[str, Any]]:
    """
    A general wrapper function for searching the VectorWaveExecutions collection.

    Args:
        filters: A dictionary of Weaviate filters (e.g., {"status": "ERROR"})
        sort_by: The property to sort by (e.g., "duration_ms")
        sort_ascending: Whether to sort in ascending order
        limit: The maximum number of results to return

    Returns:
        A list of retrieved log objects (dictionaries)
    """
    logger.info(f"Querying executions. Filters: {filters}, SortBy: {sort_by}, Limit: {limit}")
    try:
        #
        return search_executions(
            limit=limit,
            filters=filters,
            sort_by=sort_by,
            sort_ascending=sort_ascending
        )
    except Exception as e:
        logger.error(f"An error occurred while searching execution logs: {e}", exc_info=True)
        return []


def find_recent_errors(
        minutes_ago: int = 5,
        limit: int = 20,
        error_codes: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Searches for error logs from the last N minutes. (For Alerter)
    Performs manual filtering in Python as db_search.py may not support range queries.
    """
    logger.info(f"--- Searching for error logs from the last {minutes_ago} minutes ---")

    # 1. Fetch the 100 most recent logs filtered by 'status' only.
    filters = {"status": "ERROR"}

    all_errors = find_executions(
        filters=filters,
        sort_by="timestamp_utc",
        sort_ascending=False,
        limit=100  # Fetch a larger batch for filtering
    )

    # 2. Manually filter by time and error codes in Python
    time_limit = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    result = []

    for log in all_errors:
        try:
            log_time = datetime.fromisoformat(log["timestamp_utc"])

            # Skip logs that are older than the time limit
            if log_time <= time_limit:
                continue

            # If error_codes are specified, skip logs that don't match
            if error_codes and log.get("error_code") not in error_codes:
                continue

            # Add logs that pass all filters
            result.append(log)
            if len(result) >= limit:
                break

        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse log timestamp (log_time='{log.get('timestamp_utc')}'): {e}")

    logger.info(f"-> Found {len(result)} matching errors.")
    return result


def find_slowest_executions(
        limit: int = 5,
        min_duration_ms: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Searches for the slowest execution logs. (For performance monitoring)
    """
    logger.info(f"\n--- Searching for Top {limit} Slowest Executions ---")

    # [Note] db_search.py currently only supports equality filters.
    # A more advanced implementation would pass a range filter.
    filters = {}
    if min_duration_ms > 0:
        # This filter will only work if db_search.py is updated
        # filters["duration_ms__gte"] = min_duration_ms
        logger.warning(f"min_duration_ms filter is not yet supported in db_search.py, ignoring.")

    return find_executions(
        filters=filters,
        sort_by="duration_ms",
        sort_ascending=False,
        limit=limit
    )


def find_by_trace_id(trace_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Searches for all spans/logs belonging to a specific trace_id, sorted by time.
    """
    logger.info(f"\n--- Searching for Trace ID '{trace_id}' ---")
    filters = {"trace_id": trace_id}

    return find_executions(
        filters=filters,
        sort_by="timestamp_utc",
        sort_ascending=True,  # Sort chronologically
        limit=limit
    )