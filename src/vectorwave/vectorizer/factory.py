# [NEW] File: src/vectorwave/vectorizer/factory.py
from functools import lru_cache
from typing import Optional

from ..models.db_config import get_weaviate_settings, WeaviateSettings
from .base import BaseVectorizer
from .huggingface_vectorizer import HuggingFaceVectorizer
from .openai_vectorizer import OpenAIVectorizer

@lru_cache()
def get_vectorizer() -> Optional[BaseVectorizer]:
    """
    Reads the configuration file (.env) and returns an appropriate Python Vectorizer instance.
    - "weaviate_module" or "none": Returns None as Weaviate handles processing.
    - "huggingface", "openai_client": Returns the actual instance as Python handles processing.
    """
    settings: WeaviateSettings = get_weaviate_settings()
    vectorizer_name = settings.VECTORIZER.lower()

    print(f"[VectorWave] Initializing vectorizer based on setting: '{vectorizer_name}'")

    if vectorizer_name == "huggingface":
        try:
            return HuggingFaceVectorizer(model_name=settings.HF_MODEL_NAME)
        except Exception as e:
            print(f"Error: Failed to initialize HuggingFaceVectorizer: {e}")
            return None

    elif vectorizer_name == "openai_client":
        if not settings.OPENAI_API_KEY:
            print("Warning: VECTORIZER='openai_client' but OPENAI_API_KEY is not set. Vectorizer disabled.")
            return None
        try:
            return OpenAIVectorizer(api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            print(f"Error: Failed to initialize OpenAIVectorizer: {e}")
            return None

    elif vectorizer_name == "weaviate_module":
        print("[VectorWave] Using Weaviate's internal module for vectorization.")
        return None

    elif vectorizer_name == "none":
        print("[VectorWave] Vectorization is disabled ('none').")
        return None

    else:
        print(f"Warning: Unknown VECTORIZER setting: '{vectorizer_name}'. Disabling vectorizer.")
        return None