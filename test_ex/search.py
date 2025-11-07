import sys
import os
import json
import time

# --- 1. Path setup (same as example.py) ---
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_script_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)
os.chdir(current_script_dir)

# --- 2. Import VectorWave search functions ---
try:
    from vectorwave import initialize_database, search_functions, search_executions
    # [MODIFIED] Import get_cached_client to close it at the end
    from vectorwave.database.db import get_cached_client
except ImportError as e:
    print(f"Failed to import VectorWave module: {e}")
    print("Check if sys.path is set correctly.")
    exit()

def run_tests():
    print("="*40)
    print("Starting VectorWave Search Test...")
    print("="*40)

    # --- Scenario 1: Natural Language Function Search (search_functions) ---
    print("\n[Scenario 1: Natural Language Function Search]")
    print("  (Query: 'payment processing function')")

    try:
        funcs = search_functions(
            query="payment processing function",
            limit=3
        )

        if not funcs:
            print("  -> No results. (Check if example.py was run first)")
        else:
            for i, func in enumerate(funcs):
                # [No change] distance is inside the metadata object
                distance = func['metadata'].distance or 0.0
                print(f"  --- Result {i+1} (Distance: {distance:.4f}) ---")
                print(f"  Name: {func['properties']['function_name']}")
                print(f"  Description: {func['properties']['search_description']}")
                # [CORE MODIFICATION] Access uuid from the top level, outside metadata
                print(f"  UUID: {func['uuid']}")

    except Exception as e:
        print(f"  [Error] Error during search_functions execution: {e}")


    # --- Scenario 2: Search for Top 5 Slowest Execution Logs (search_executions) ---
    print("\n[Scenario 2: Top 5 Slowest Execution Logs]")

    try:
        slow_logs = search_executions(
            limit=5,
            sort_by="duration_ms",
            sort_ascending=False
        )

        if not slow_logs:
            print("  -> No results.")
        else:
            for i, log in enumerate(slow_logs):
                print(f"  --- Rank {i+1} ---")
                print(f"  UUID: {log['function_uuid']}")
                print(f"  Status: {log['status']}")
                print(f"  Time: {log['duration_ms']:.2f} ms")
                print(f"  Team:   {log.get('team', 'N...A')}")

    except Exception as e:
        print(f"  [Error] Error during search_executions (slow logs): {e}")


    # --- Scenario 3: Search for Error Logs from 'billing' team (Filter) ---
    print("\n[Scenario 3: Search for 'billing' team's Error Logs]")

    try:
        error_logs = search_executions(
            limit=5,
            filters={
                "team": "billing",
                "status": "ERROR"
            },
            sort_by="timestamp_utc",
            sort_ascending=False
        )

        if not error_logs:
            print("  -> No error logs found for 'billing' team.")
        else:
            print(f"  -> Found {len(error_logs)} error logs:")
            for log in error_logs:
                print(f"  - {log['timestamp_utc']} / {log['error_message'][:50]}...")

    except Exception as e:
        print(f"  [Error] Error during search_executions (error filter): {e}")

    print("\n" + "="*40)
    print("Search test complete.")
    print("="*40)
    print("\n[Scenario 4: Trace Grouping with a Single Trace ID]")

    trace_id_to_find = None

    # 4a. Retrieve the trace_id from the latest 'process_payment' log
    try:
        print("  (1/2) Retrieving the latest trace_id for 'process_payment'...")
        latest_root_span = search_executions(
            limit=1,
            filters={"function_name": "process_payment"},
            sort_by="timestamp_utc",
            sort_ascending=False
        )

        if latest_root_span and latest_root_span[0].get("trace_id"):
            trace_id_to_find = latest_root_span[0]["trace_id"]
            print(f"  -> Target Trace ID: {trace_id_to_find}")
        else:
            print("  -> Error: Could not find 'process_payment' log or trace_id.")
            print("     Please ensure 'example.py' has been executed first.")

    except Exception as e:
        print(f"  [Error] Error while retrieving trace_id: {e}")

    # 4b. Search all spans associated with the found trace_id
    if trace_id_to_find:
        try:
            print(f"  (2/2) Searching all spans for Trace ID ({trace_id_to_find[:8]}...)...")

            trace_spans = search_executions(
                limit=10,
                filters={"trace_id": trace_id_to_find},
                sort_by="timestamp_utc",
                sort_ascending=True # Sort by time ascending
            )

            print(f"\n  --- 🚀 Single Workflow: {trace_id_to_find} ---")
            total_duration = 0

            for i, span in enumerate(trace_spans):
                func_name = span.get('function_name', 'N/A')
                duration = span.get('duration_ms', 0)
                total_duration += duration

                print(f"    [Span {i+1}] {func_name} ({duration:.2f} ms)")

                # Print captured arguments (only non-None values)
                args = {k: v for k, v in span.items() if k in ['user_id', 'amount', 'receipt_id'] and v is not None}
                if args:
                    print(f"      -> Args: {args}")

            print("  --------------------------------------------------")
            print(f"  -> Total {len(trace_spans)} spans found, Total duration: {total_duration:.2f} ms")

            if len(trace_spans) == 3:
                print("  -> [SUCCESS] Root span (1) and child spans (2) were successfully grouped.")

        except Exception as e:
            print(f"  [Error] Error during span search: {e}")


if __name__ == "__main__":
    print("Checking DB connection...")
    # [MODIFIED] initialize_database() internally calls get_cached_client()
    # to cache the client.
    client = initialize_database()

    if client:
        print("DB connection successful. Running search tests.")
        # [MODIFIED] Do not close the client here.
        run_tests()

        # [MODIFIED] After all tests are finished, close the cached singleton client.
        print("All tests complete. Closing singleton client connection.")
        # Get the cached client via get_cached_client() and close it.
        get_cached_client().close()
    else:
        print("DB connection failed. Check if Weaviate Docker is running and .env file is correct.")