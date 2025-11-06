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