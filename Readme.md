
# VectorWave: Seamless Auto-Vectorization Framework

[](https://www.google.com/search?q=LICENSE)

## 🌟 Overview

**VectorWave** is an innovative framework that uses a **decorator** to automatically save and manage the output of Python functions/methods in a **Vector Database (Vector DB)**. Developers can convert function outputs into intelligent vector data with a single line of code (`@vectorize`), without worrying about the complex processes of data collection, embedding generation, or storage in a Vector DB.

---

## ✨ Features

* **`@vectorize` Decorator:**
  1.  **Static Data Collection:** Saves the function's source code, docstring, and metadata to the `VectorWaveFunctions` collection once when the script is loaded.
  2.  **Dynamic Data Logging:** Records the execution time, success/failure status, error logs, and 'dynamic tags' to the `VectorWaveExecutions` collection every time the function is called.
* **Distributed Tracing:** By combining the `@vectorize` and `@trace_span` decorators, you can analyze the execution of complex multi-step workflows, grouped under a single **`trace_id`**.
* **Search Interface:** Provides `search_functions` (for vector search) and `search_executions` (for log filtering) to facilitate the construction of RAG and monitoring systems.

---

## 🚀 Usage

VectorWave consists of 'storing' via decorators and 'searching' via functions, and now includes **execution flow tracing**.

### 1. (Required) Initialize the Database and Configuration

```python
import time
from vectorwave import (
    vectorize, 
    initialize_database, 
    search_functions, 
    search_executions
)
# [ADDITION] Import trace_span separately for distributed tracing.
from vectorwave.monitoring.tracer import trace_span 

# This only needs to be called once when the script starts.
try:
    client = initialize_database()
    print("VectorWave DB initialized successfully.")
except Exception as e:
    print(f"DB initialization failed: {e}")
    exit()
````

### 2\. [Store] Use `@vectorize` with Distributed Tracing

The `@vectorize` acts as the **Root** for tracing, and `@trace_span` is used on internal functions to group the execution flow under a single `trace_id`.

```python
# --- Child Span Function: Captures arguments ---
@trace_span(attributes_to_capture=['user_id', 'amount'])
def step_1_validate_payment(user_id: str, amount: int):
    """(Span) Payment validation. Records user_id and amount in the log."""
    print(f"  [SPAN 1] Validating payment for {user_id}...")
    time.sleep(0.1)
    return True

@trace_span(attributes_to_capture=['user_id', 'receipt_id'])
def step_2_send_receipt(user_id: str, receipt_id: str):
    """(Span) Sends the receipt."""
    print(f"  [SPAN 2] Sending receipt {receipt_id}...")
    time.sleep(0.2)


# --- Root Function (@trace_root role) ---
@vectorize(
    search_description="Charges a user in the payment system.",
    sequence_narrative="Returns a receipt ID upon successful payment.",
    team="billing",  # <-- Custom Tag (recorded in all execution logs)
    priority=1       # <-- Custom Tag (execution priority)
)
def process_payment(user_id: str, amount: int):
    """(Root Span) Executes the user payment workflow."""
    print(f"  [ROOT EXEC] process_payment: Starting workflow for {user_id}...")
    
    # When calling child functions, the same trace_id is automatically inherited via ContextVar.
    step_1_validate_payment(user_id=user_id, amount=amount) 
    
    receipt_id = f"receipt_{user_id}_{amount}"
    step_2_send_receipt(user_id=user_id, receipt_id=receipt_id)

    print(f"  [ROOT DONE] process_payment")
    return {"status": "success", "receipt_id": receipt_id}

# --- Execute the Function ---
print("Now calling 'process_payment'...")
# This single call records 3 execution logs (spans) in the DB,
# all grouped under one 'trace_id'.
process_payment("user_789", 5000)
```

### 3\. [Search ①] Function Definition Search (for RAG)

```python
# Search for functions related to 'payment' using natural language (vector search).
print("\n--- Searching for 'payment' functions ---")
payment_funcs = search_functions(
    query="user payment processing",
    limit=3
)
for func in payment_funcs:
    print(f"  - Function: {func['properties']['function_name']}")
    print(f"  - Description: {func['properties']['search_description']}")
    print(f"  - Similarity (Distance): {func['metadata'].distance:.4f}")
```

### 4\. [Search ②] Execution Log Search (Monitoring and Tracing)

The `search_executions` function can now search for all related execution logs (spans) based on the `trace_id`.

```python
# 1. Find the Trace ID of a specific workflow (process_payment).
latest_payment_span = search_executions(
    limit=1, 
    filters={"function_name": "process_payment"},
    sort_by="timestamp_utc",
    sort_ascending=False
)
trace_id = latest_payment_span[0]["trace_id"] 

# 2. Search all spans belonging to that Trace ID, sorted chronologically.
print(f"\n--- Full Trace for ID ({trace_id[:8]}...) ---")
trace_spans = search_executions(
    limit=10,
    filters={"trace_id": trace_id},
    sort_by="timestamp_utc",
    sort_ascending=True # Ascending sort for workflow flow analysis
)

for i, span in enumerate(trace_spans):
    print(f"  - [Span {i+1}] {span['function_name']} ({span['duration_ms']:.2f}ms)")
    # Captured arguments (user_id, amount, etc.) are displayed for the child spans.
    
# Example Output:
# - [Span 1] step_1_validate_payment (100.81ms)
# - [Span 2] step_2_send_receipt (202.06ms)
# - [Span 3] process_payment (333.18ms)
```
-----

## ⚙️ Configuration

VectorWave automatically reads Weaviate database connection info and **vectorization strategy** from **environment variables** or a `.env` file.

Create a `.env` file in your project's root directory (e.g., where `test_ex/example.py` is located) and set the required values.

### Vectorizer Strategy (VECTORIZER)

You can select the text vectorization method via the `VECTORIZER` environment variable in your `test_ex/.env` file.

| `VECTORIZER` Setting | Description | Required Additional Settings |
| :--- | :--- | :--- |
| **`huggingface`** | (Default Recommended) Uses the `sentence-transformers` library to vectorize on your local CPU. No API key is needed, making it great for immediate testing. | `HF_MODEL_NAME` (e.g., "sentence-transformers/all-MiniLM-L6-v2") |
| **`openai_client`** | (High-Performance) Uses the OpenAI Python client to vectorize with modern models like `text-embedding-3-small`. | `OPENAI_API_KEY` (A valid OpenAI API key) |
| **`weaviate_module`** | (Docker Delegate) Delegates the vectorization task to the Weaviate container's built-in module (e.g., `text2vec-openai`). | `WEAVIATE_VECTORIZER_MODULE`, `OPENAI_API_KEY` |
| **`none`** | Disables vectorization. Data will be stored without vectors. | None |

-----

### .env File Examples

Configure your `.env` file according to the strategy you want to use.

#### Example 1: Using `huggingface` (Local, No API Key)

Uses a `sentence-transformers` model on your local machine. Ideal for testing without API keys.

```ini
# .env (Using HuggingFace)
# --- Basic Weaviate Connection ---
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_GRPC_PORT=50051

# --- [Strategy 1] HuggingFace Config ---
VECTORIZER="huggingface"
HF_MODEL_NAME="sentence-transformers/all-MiniLM-L6-v2"

# (OPENAI_API_KEY is not required for this mode)
OPENAI_API_KEY=sk-...

# --- [Advanced] Custom Properties ---
CUSTOM_PROPERTIES_FILE_PATH=.weaviate_properties
RUN_ID=test-run-001
```

#### Example 2: Using `openai_client` (Python Client, High-Performance)

Directly calls the OpenAI API via the `openai` Python library.

```ini
# .env (Using OpenAI Python Client)
# --- Basic Weaviate Connection ---
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_GRPC_PORT=50051

# --- [Strategy 2] OpenAI Client Config ---
VECTORIZER="openai_client"

# [Required] You must enter a valid OpenAI API key.
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# (HF_MODEL_NAME is not used in this mode)
HF_MODEL_NAME=...

# --- [Advanced] Custom Properties ---
CUSTOM_PROPERTIES_FILE_PATH=.weaviate_properties
RUN_ID=test-run-001
```

#### Example 3: Using `weaviate_module` (Docker Delegate)

Delegates vectorization to the Weaviate Docker container instead of Python. (See `vw_docker.yml` config).

```ini
# .env (Delegating to Weaviate Module)
# --- Basic Weaviate Connection ---
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_GRPC_PORT=50051

# --- [Strategy 3] Weaviate Module Config ---
VECTORIZER="weaviate_module"
WEAVIATE_VECTORIZER_MODULE=text2vec-openai
WEAVIATE_GENERATIVE_MODULE=generative-openai

# [Required] The Weaviate container will read this API key.
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# --- [Advanced] Custom Properties ---
CUSTOM_PROPERTIES_FILE_PATH=.weaviate_properties
RUN_ID=test-run-001
```

-----

### Custom Properties and Dynamic Execution Tagging

VectorWave can store user-defined metadata in addition to static data (function definitions) and dynamic data (execution logs). This works in two steps.

#### Step 1: Define Custom Schema (Tag "Allow-list")

Create a JSON file at the path specified by `CUSTOM_PROPERTIES_FILE_PATH` in your `.env` file (default: `.weaviate_properties`).

This file instructs VectorWave to add **new properties (columns)** to the Weaviate collections. This file acts as an **"allow-list"** for all custom tags.

**`.weaviate_properties` Example:**

```json
{
  "run_id": {
    "data_type": "TEXT",
    "description": "The ID of the specific test run"
  },
  "experiment_id": {
    "data_type": "TEXT",
    "description": "Identifier for the experiment"
  },
  "team": {
    "data_type": "TEXT",
    "description": "The team responsible for this function"
  },
  "priority": {
    "data_type": "INT",
    "description": "Execution priority level"
  }
}
```

* This definition will add `run_id`, `experiment_id`, `team`, and `priority` properties to both the `VectorWaveFunctions` and `VectorWaveExecutions` collections.

#### Step 2: Dynamic Execution Tagging (Adding Values)

When a function is executed, VectorWave adds tags to the `VectorWaveExecutions` log. These tags are collected and merged from two sources.

**1. Global Tags (Environment Variables)**
VectorWave looks for environment variables matching the **UPPERCASE name** of the keys defined in Step 1 (e.g., `RUN_ID`, `EXPERIMENT_ID`). Found values are loaded as `global_custom_values` and added to *all* execution logs. Ideal for run-wide metadata.

**2. Function-Specific Tags (Decorator)**
You can pass tags as keyword arguments (`**execution_tags`) directly to the `@vectorize` decorator. Ideal for function-specific metadata.

```python
# --- .env file ---
# RUN_ID=global-run-abc
# TEAM=default-team

@vectorize(
    search_description="Process payment",
    sequence_narrative="...",
    team="billing",  # <-- Function-specific tag
    priority=1       # <-- Function-specific tag
)
def process_payment():
    pass

@vectorize(
    search_description="Another function",
    sequence_narrative="...",
    run_id="override-run-xyz" # <-- Overrides the global tag
)
def other_function():
    pass
```

**Tag Merging and Validation Rules**

1.  **Validation (Important):** Tags (global or function-specific) will **only** be saved to Weaviate if their key (e.g., `run_id`, `team`, `priority`) was first defined in the `.weaviate_properties` file (Step 1). Tags not defined in the schema are **ignored**, and a warning is printed at script startup.

2.  **Priority (Override):** If a tag key is defined in both places (e.g., global `RUN_ID` in `.env` and `run_id="override-xyz"` in the decorator), the **function-specific tag from the decorator always wins**.

**Resulting Logs:**

* `process_payment()` execution log: `{"run_id": "global-run-abc", "team": "billing", "priority": 1}`
* `other_function()` execution log: `{"run_id": "override-run-xyz", "team": "default-team"}`

-----

## 🤝 Contributing

All forms of contribution are welcome, including bug reports, feature requests, and code contributions. For details, please refer to [CONTRIBUTING.md](https://www.google.com/search?q=httpsS://www.google.com/search%3Fq%3DCONTRIBUTING.md).

## 📜 License

This project is distributed under the MIT License. See the [LICENSE](https://www.google.com/search?q=httpsS://www.google.com/search%3Fq%3DLICENSE) file for details.

