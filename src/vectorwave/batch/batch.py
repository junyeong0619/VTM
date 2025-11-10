import weaviate
import atexit
import logging
from functools import lru_cache
from typing import Optional, List
from ..models.db_config import get_weaviate_settings, WeaviateSettings
from ..database.db import get_weaviate_client
from ..exception.exceptions import WeaviateConnectionError

# Create module-level logger
logger = logging.getLogger(__name__)

class WeaviateBatchManager:
    """
    A singleton class that manages Weaviate batch imports.
    """

    def __init__(self):
        self._initialized = False
        logger.debug("Initializing WeaviateBatchManager")
        self.client: weaviate.WeaviateClient = None

        try:
            # (get_weaviate_settings is reused as it is handled by lru_cache)
            self.settings: WeaviateSettings = get_weaviate_settings()
            self.client: weaviate.WeaviateClient = get_weaviate_client(self.settings)

            if not self.client:
                raise WeaviateConnectionError("Client is None, cannot configure batch.")

            # self.client.batch.configure(
            #     batch_size=20,
            #     dynamic=True,
            #     timeout_retries=3,
            # )

            # Register atexit: Automatically calls self.flush() on script exit
            # atexit.register(self.flush)
            self._initialized = True
            logger.info("WeaviateBatchManager initialized successfully")

        except Exception as e:
            # Prevents VectorWave from stopping the main app upon DB connection failure
            logger.error("Failed to initialize WeaviateBatchManager: %s", e)

    def add_object(self, collection: str, properties: dict, uuid: str = None, vector: Optional[List[float]] = None):
        """
        Adds an object to the Weaviate batch queue.
        """
        if not self._initialized or not self.client:
            logger.warning("Batch manager not initialized, skipping add_object")
            return

        try:
            self.client.collections.get(collection).data.insert(
                properties=properties,
                uuid=uuid,
                vector=vector
            )

        except Exception as e:
            logger.error("Failed to add object to batch (collection '%s'): %s", collection, e)



@lru_cache(None)
def get_batch_manager() -> WeaviateBatchManager:
    return WeaviateBatchManager()