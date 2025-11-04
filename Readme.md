


# VectorWave: Seamless Auto-Vectorization Framework

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## 🌟 Overview

**VectorWave** is an innovative framework that uses a **decorator** to automatically save and manage the output of Python functions/methods in a **Vector Database (Vector DB)**. Developers can convert function outputs into intelligent vector data with a single line of code (`@vectorize`), without worrying about the complex processes of data collection, embedding generation, or storage in a Vector DB.

## ✨ Features

* **`@vectorize` Decorator:**
  1.  **Static Data Collection:** Saves the function's source code, docstring, and metadata to the `VectorWaveFunctions` collection once when the script is loaded.
  2.  **Dynamic Data Logging:** Records the execution time, success/failure status, error logs, and 'dynamic tags' to the `VectorWaveExecutions` collection every time the function is called.
* **Concise Search Interface:** (Coming soon) Provides meaningful search capabilities (Similarity Search) for the stored vector data, facilitating the construction of RAG (Retrieval-Augmented Generation) systems.

## ⚙️ Configuration

VectorWave automatically reads Weaviate database connection information from **environment variables** or a `.env` file.

Create a `.env` file in the root directory of your project (e.g., where `main.py` is located) and set the required values.

### .env File Example

```ini
# .env
# --- Basic Weaviate Connection Settings ---
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_GRPC_PORT=50051

# --- Vectorizer Settings (if using OpenAI) ---
# An OpenAI API key is required if using modules like text2vec-openai.
# OPENAI_API_KEY=sk-your-key-here

# --- [Advanced] Custom Property Settings ---
# 1. The path to the JSON file defining custom properties to add to the schema.
CUSTOM_PROPERTIES_FILE_PATH=.weaviate_properties

# 2. Environment variables to be used for 'Global Dynamic Tagging'.
#    ("run_id" must be defined in the .weaviate_properties file)
RUN_ID=test-run-001
EXPERIMENT_ID=exp-abc
````

-----

### Custom Properties and Dynamic Execution Tagging

VectorWave can store user-defined metadata in both static definitions (`VectorWaveFunctions`) and dynamic logs (`VectorWaveExecutions`). This works in two steps.

#### Step 1: Define Custom Schema (The "Allow-List")

Create a JSON file at the path specified by `CUSTOM_PROPERTIES_FILE_PATH` (default: `.weaviate_properties`).

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

* Defining these will add `run_id`, `experiment_id`, `team`, and `priority` properties to *both* collections.

#### Step 2: Dynamic Execution Tagging (Adding Values)

When a function executes, VectorWave adds tags to the `VectorWaveExecutions` log. It does this in two ways, which are then merged:

**1. Global Tags (from Environment Variables)**
VectorWave searches for environment variables whose names match the **uppercase** keys from Step 1 (e.g., `RUN_ID`, `EXPERIMENT_ID`). If found, their values are loaded as `global_custom_values` and added to *all* execution logs. This is ideal for run-wide metadata.

**2. Function-Specific Tags (from Decorator)**
You can pass tags directly to the `@vectorize` decorator as keyword arguments (`**execution_tags`). This is ideal for function-specific metadata.

```python
# --- .env file ---
# RUN_ID=global-run-abc
# TEAM=default-team

@vectorize(
    search_description="Process a payment",
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

1.  **Validation (Most Important):** A tag (either global or specific) will **only** be saved to Weaviate if its key (e.g., `run_id`, `team`, `priority`) was first defined in your `.weaviate_properties` file (Step 1). Tags not defined in the schema will be **ignored**, and a warning will be printed on startup.

2.  **Priority (Override):** If a tag key is defined in both places (e.g., a global `RUN_ID` in `.env` and a specific `run_id="override-run-xyz"` on the decorator), the **function-specific tag from the decorator will always win**.

**Resulting Logs:**

* `process_payment()` log will have: `{"run_id": "global-run-abc", "team": "billing", "priority": 1}`
* `other_function()` log will have: `{"run_id": "override-run-xyz", "team": "default-team"}`

-----

## 🤝 Contributing

All forms of contribution are welcome, including bug reports, feature requests, and code contributions. For details, please refer to [CONTRIBUTING.md](httpsS://www.google.com/search?q=CONTRIBUTING.md).

## 📜 License

This project is distributed under the MIT License. See the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

