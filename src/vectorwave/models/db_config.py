from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Dict, Optional, Any
import json
import os


class WeaviateSettings(BaseSettings):
    """
    Manages Weaviate database connection settings.

    Reads values from environment variables or a .env file.
    (e.g., WEAVIATE_HOST=10.0.0.1)
    """
    # If environment variables are not set, these default values will be used.
    WEAVIATE_HOST: str = "localhost"
    WEAVIATE_PORT: int = 8080
    WEAVIATE_GRPC_PORT: int = 50051
    COLLECTION_NAME: str = "VectorWaveFunctions"
    EXECUTION_COLLECTION_NAME: str = "VectorWaveExecutions"
    IS_VECTORIZE_COLLECTION_NAME: bool = True

    # Configure to read from a .env file (optional)

    VECTORIZER_CONFIG: str = "text2vec-openai"
    GENERATIVE_CONFIG: str = "generative-openai"

    CUSTOM_PROPERTIES_FILE_PATH: str = ".weaviate_properties"
    custom_properties: Optional[Dict[str, Dict[str, Any]]] = None
    global_custom_values: Optional[Dict[str, Any]] = None
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",extra='ignore')


# @lru_cache ensures this function creates the Settings object only once (Singleton pattern)
# and reuses the cached object on subsequent calls.
@lru_cache()
def get_weaviate_settings() -> WeaviateSettings:
    """
    Factory function that returns the settings object.
    """
    settings = WeaviateSettings()

    file_path = settings.CUSTOM_PROPERTIES_FILE_PATH

    if file_path and os.path.exists(file_path):
        print(f"Loading custom properties schema from '{file_path}'...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

                if isinstance(loaded_data, dict):
                    settings.custom_properties = loaded_data
                else:
                    print(
                        f"Warning: Content in '{file_path}' is not a valid dictionary (JSON root). "
                        f"Custom properties will not be loaded."
                    )
                    settings.custom_properties = None

        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse JSON from '{file_path}'. File might be malformed. {e}")
            settings.custom_properties = None
        except Exception as e:
            print(f"Warning: Could not read file '{file_path}': {e}")
            settings.custom_properties = None

    elif file_path:
        print(f"Note: Custom properties file not found at '{file_path}'. Skipping schema.")

    if settings.custom_properties:
        settings.global_custom_values = {}
        print(f"Loading global custom values from environment variables...")

        for prop_name in settings.custom_properties.keys():
            env_var_name = prop_name.upper()
            value = os.environ.get(env_var_name)

            if value:
                settings.global_custom_values[prop_name] = value
                print(f"Loaded global value for '{prop_name}' from env var '{env_var_name}'.")

    return settings
