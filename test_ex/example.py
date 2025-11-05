import sys
import os
import time

# 1. Find the directory path where 'example.py' is located.
current_script_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Calculate the 'src' directory path.
project_root = os.path.dirname(current_script_dir)
src_path = os.path.join(project_root, 'src')

# 3. Add the 'src' path so Python can find the 'vectorwave' module.
sys.path.insert(0, src_path)

# 4. [Important] Change the current working directory to where 'example.py' is,
#    so it can read .env and .weaviate_properties files.
#    (Because db_config.py looks for ".env" in the current path)
os.chdir(current_script_dir)

from vectorwave import vectorize, initialize_database

client = None

try:
    print("Attempting to initialize VectorWave database...")
    # initialize_database internally calls get_weaviate_settings and
    # get_weaviate_client, then creates the schema.
    client = initialize_database() # Assign Weaviate client to the client variable

    if client:
        print("Database connection and schema initialization successful.")
    else:
        # 3. Raise an exception instead of exiting.
        #    - If an exception occurs, it immediately moves to the except or finally block.
        raise ConnectionError("Database initialization failed. Check your settings.")

    # --- 3. Function Definitions using @vectorize decorator ---
    # These functions are saved as static data in the 'VectorWaveFunctions'
    # collection at definition time (script load).

    @vectorize(
        search_description="Process user payment and return a receipt.",
        sequence_narrative="After payment is complete, a receipt is sent via email.",
        team="billing",  # Custom tag defined in .weaviate_properties
        priority=1
    )
    def process_payment(user_id: str, amount: int):
        """
        Main function to process user payment.
        This Docstring is saved to Weaviate.
        """
        print(f"  [EXEC] process_payment: Processing payment of {amount} for user {user_id}...")
        # (Actual payment logic)
        time.sleep(0.5)
        print(f"  [DONE] process_payment")
        return {"status": "success", "receipt_id": "receipt_12345"}

    @vectorize(
        search_description="Generate a report for data analysis.",
        sequence_narrative="After the report is generated, an admin is notified.",
        team="data-science" # Custom tag
    )
    def generate_report():
        """Generates a data analysis report."""
        print(f"  [EXEC] generate_report: Generating report...")
        time.sleep(1.0)
        # (Actual report generation logic)
        print(f"  [DONE] generate_report")
        return {"report_url": "/reports/analytics.pdf"}

    print("="*30)
    print("Function definitions complete (static data collected).")
    print("="*30)


    # --- 4. Function Execution ---
    # When a function is called, dynamic logs (execution time, status, tags, etc.)
    # are recorded in the 'VectorWaveExecutions' collection.

    print("Now calling functions (dynamic logging starts)...")

    # This try-except block only handles exceptions during 'function execution'.
    # Even if the main logic fails, the script will not be interrupted,
    # allowing the resource cleanup in 'finally' to run.
    try:
        process_payment(user_id="user_A", amount=10000)
        generate_report()

        print("\nFunction calls completed successfully.")

    except Exception as e:
        print(f"\nError during function execution: {e}")

except Exception as e:
    # Handles exceptions that occurred during DB initialization (ConnectionError)
    # or function definition (@vectorize).
    print(f"\n[Fatal Error] Script execution halted: {e}")
    if "Initialization failed" in str(e):
        print("Check if Weaviate server is running and .env file is correct.")

finally:
    # 4. (Important) 'finally' block

    print("="*30)
    print("Script will be terminating soon.")
    print("On program exit, the batch manager registered with atexit")
    print("will flush all remaining data to Weaviate.")

    # [MODIFIED]
    # The batch_manager.flush() registered with 'atexit'
    # needs to use the open client, so we do not call
    # client.close() here.
    #
    # if client:
    #     print("Closing Weaviate client connection before script exit.")
    #     client.close() # <-- This part is commented out or deleted.

    if not client:
        print("Client was not successfully initialized.")
