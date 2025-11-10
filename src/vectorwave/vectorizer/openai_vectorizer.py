from .base import BaseVectorizer
from typing import List

try:
    from openai import OpenAI
except ImportError:
    # Warning: The 'openai' library is not installed.
    print("Warning: The 'openai' library is not installed.")
    # To use OpenAIVectorizer, run 'pip install openai'.
    print("To use OpenAIVectorizer, run 'pip install openai'.")
    OpenAI = None


class OpenAIVectorizer(BaseVectorizer):

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        if OpenAI is None:
            # Could not find the 'openai' library.
            raise ImportError("Could not find the 'openai' library.")
        if not api_key:
            raise ValueError("OpenAI API key is required for OpenAIVectorizer.")

        self.client = OpenAI(api_key=api_key)
        self.model = model
        print(f"[VectorWave] OpenAIVectorizer initialized with model '{self.model}'.")

    def embed(self, text: str) -> List[float]:
        text = text.replace("\n", " ")
        response = self.client.embeddings.create(input=[text], model=self.model)
        return response.data[0].embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        texts = [t.replace("\n", " ") for t in texts]
        response = self.client.embeddings.create(input=texts, model=self.model)
        return [d.embedding for d in response.data]