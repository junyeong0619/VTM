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
    IS_VECTORIZE_COLLECTION_NAME: bool = True

    # Configure to read from a .env file (optional)

    CUSTOM_PROPERTIES_FILE_PATH: str = ".weaviate_properties"
    custom_properties: Optional[Dict[str, Dict[str, Any]]] = None
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# @lru_cache ensures this function creates the Settings object only once (Singleton pattern)
# and reuses the cached object on subsequent calls.
@lru_cache
def get_weaviate_settings() -> WeaviateSettings:
    """
    Factory function that returns the settings object.
    """
    settings = WeaviateSettings()

    file_path = settings.CUSTOM_PROPERTIES_FILE_PATH

    if file_path and os.path.exists(file_path):
        print(f"Loading custom properties from '{file_path}'...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                settings.custom_properties = json.load(f)

        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse JSON from '{file_path}'. File might be malformed. {e}")
            settings.custom_properties = None
        except Exception as e:
            print(f"Warning: Could not read file '{file_path}': {e}")
            settings.custom_properties = None

    elif file_path:
        print(f"Note: Custom properties file not found at '{file_path}'. Skipping.")


    return settings