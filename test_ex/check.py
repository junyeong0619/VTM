import sys
import os
import json

# Import weaviate.classes
try:
    import weaviate.classes as wvc
except ImportError:
    print("weaviate-client library is not installed or the version might be low.")
    print("Please run: pip install -U weaviate-client")
    wvc = None

# --- 1. Path setup (same as example.py) ---
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_script_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)
os.chdir(current_script_dir)

# --- 2. Client Connection ---
client = None
try:
    # Use the same function as example.py to get the client
    from vectorwave import initialize_database

    print("Connecting to client via DB initialization function...")
    # This function skips schema creation if it exists and returns the client object.
    client = initialize_database()
    print("Successfully connected to Weaviate client (Port 8080)\n")

except ImportError:
    print(f"Client connection failed: 'vectorwave' module not found.")
    print("Please check if sys.path is set correctly.")
    exit()
except Exception as e:
    print(f"Client connection failed: {e}")
    print("Please check if the Weaviate server (test_ex-weaviate-1) is running.")
    exit()

if client:
    try:
        # --- 3. Query 'VectorWaveFunctions' Collection ---
        print("="*30)
        print("✅ [VectorWaveFunctions] (Registered Functions)")
        print("="*30)

        functions_col = client.collections.get("VectorWaveFunctions")
        response = functions_col.query.fetch_objects(limit=100)

        if not response.objects:
            print(" -> No data found.")
        else:
            print(f" -> Found {len(response.objects)} functions in total")
            for obj in response.objects:
                # [MODIFIED] Convert datetime objects to strings for printing
                print(json.dumps(obj.properties, indent=2, ensure_ascii=False, default=str))
                print("-" * 20)

        # --- 4. Query 'VectorWaveExecutions' Collection ---
        print("\n" + "="*30)
        print("✅ [VectorWaveExecutions] (Function Execution Logs)")
        print("="*30)

        executions_col = client.collections.get("VectorWaveExecutions")

        # Create Sort object for sorting
        sort_order = None
        if wvc:
            try:
                config = executions_col.config.get()
                has_timestamp_prop = False
                if config.properties:
                    has_timestamp_prop = any(prop.name == "timestamp_utc" for prop in config.properties)

                if has_timestamp_prop:
                    sort_order = wvc.query.Sort.by_property("timestamp_utc", ascending=False)
                else:
                    print(" (Warning: Skipping sort. 'timestamp_utc' property not found.)")

            except Exception as e:
                print(f" (Warning: Error during property check, skipping sort: {e})")

        # Fetch the latest 100 execution logs
        response = executions_col.query.fetch_objects(
            limit=100,
            sort=sort_order
        )

        if not response.objects:
            print(" -> No data found.")
        else:
            print(f" -> Found {len(response.objects)} logs in total")
            for obj in response.objects:
                # [MODIFIED] Convert datetime objects to strings for printing
                print(json.dumps(obj.properties, indent=2, ensure_ascii=False, default=str))
                print("-" * 20)

    except Exception as e:
        print(f"Error during data query: {e}")
    finally:
        # --- 5. Close Client ---
        print("\nData query complete. Closing connection.")
        client.close()
