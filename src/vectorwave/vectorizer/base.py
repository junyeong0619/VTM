from abc import ABC, abstractmethod
from typing import List

class BaseVectorizer(ABC):

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        pass