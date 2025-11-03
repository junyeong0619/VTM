
# VectorWave: Seamless Auto-Vectorization Framework

[](LICENSE)

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

# 2. Environment variables to be used for 'dynamic tagging'.
#    ("run_id" must be defined in the .weaviate_properties file)
RUN_ID=test-run-001
EXPERIMENT_ID=exp-abc
```

-----

### Custom Properties and Dynamic Execution Tagging

In addition to static data (function definitions) and dynamic data (execution logs), VectorWave can store user-defined metadata. This works in two steps using a combination of the `.weaviate_properties` file and `.env` environment variables.

#### Step 1: Define Custom Schema (`.weaviate_properties` file)

Create a JSON file at the path specified by `CUSTOM_PROPERTIES_FILE_PATH` in your `.env` file (default: `.weaviate_properties`).

This file instructs VectorWave to add **new properties (columns)** to the Weaviate collections.

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
  }
}
```

* Defining it this way will add `run_id` (TEXT) and `experiment_id` (TEXT) properties to both the `VectorWaveFunctions` and `VectorWaveExecutions` collections.

#### Step 2: Dynamic Tagging (Environment Variables)

VectorWave takes the keys defined in the `.weaviate_properties` file (e.g., `run_id`), **capitalizes them** (e.g., `RUN_ID`), and looks for a matching **environment variable**.

If `RUN_ID=test-run-001` is set in your `.env` file, VectorWave loads this `test-run-001` value into `global_custom_values`.

These "global values" are automatically added like 'tags' to the **dynamic log data (`VectorWaveExecutions`)** that is collected **every time** a `@vectorize`-decorated function is executed.

**Result:**
If you run a script with `RUN_ID=test-run-001` set, all execution logs saved to the `VectorWaveExecutions` collection will include the property `{"run_id": "test-run-001"}`. This enables powerful analysis later, such as "filtering all execution logs for a specific `run_id`."

*(Note: These values are tagged only on the function 'execution logs' (`VectorWaveExecutions`), not on the function 'definitions' (`VectorWaveFunctions`).)*

-----

## 🤝 Contributing

All forms of contribution are welcome, including bug reports, feature requests, and code contributions. For details, please refer to [CONTRIBUTING.md](httpsS://www.google.com/search?q=CONTRIBUTING.md).

## 📜 License

This project is distributed under the MIT License. See the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.