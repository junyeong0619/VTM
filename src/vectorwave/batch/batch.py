import weaviate
import atexit
import logging
from functools import lru_cache
from ..models.db_config import get_weaviate_settings, WeaviateSettings
from ..database.db import get_weaviate_client
from ..exception.exceptions import WeaviateConnectionError



class WeaviateBatchManager:
    """
    A singleton class that manages Weaviate batch imports.
    """

    def __init__(self):
        self._initialized = False
        print("Initializing WeaviateBatchManager...") # print 유지
        self.client: weaviate.WeaviateClient = None

        try:
            # (get_weaviate_settings is reused as it is handled by lru_cache)            self.settings:
            self.settings: WeaviateSettings = get_weaviate_settings()
            self.client: weaviate.WeaviateClient = get_weaviate_client(self.settings)

            if not self.client:
                raise WeaviateConnectionError("Client is None, cannot configure batch.")

            self.client.batch.configure(
                batch_size=20,
                dynamic=True,
                timeout_retries=3,
            )

            # Register atexit: Automatically calls self.flush() on script exit
            atexit.register(self.flush)
            self._initialized = True
            print("WeaviateBatchManager initialized and 'atexit' flush registered.") # print 유지

        except Exception as e:
            # Prevents VectorWave from stopping the main app upon DB connection failure
            print(f"Failed to initialize WeaviateBatchManager: {e}. Batching will be disabled.") # print 유지

    def add_object(self, collection: str, properties: dict, uuid: str = None):
        """
        Adds an object to the Weaviate batch queue.
        """
        if not self._initialized or not self.client:
            print("Warning: Batch manager not initialized. Skipping add_object.") # print 유지
            return

        try:
            self.client.batch.add_object(
                collection=collection,
                properties=properties,
                uuid=uuid
            )

        except Exception as e:
            print(f"Error: Failed to add object to batch (Collection: {collection}): {e}") # print 유지

    def flush(self):
        """
        Forcibly sends all remaining objects in the batch queue to Weaviate.
        (Automatically called on script exit by 'atexit')
        """
        if not self._initialized or not self.client:
            return

        if len(self.client.batch) > 0:
            print(f"Flushing Weaviate batch ({len(self.client.batch)} items)...") # print 유지
            try:
                result = self.client.batch.flush()

                errors = []
                for res in result:
                    if "errors" in res.get("result", {}):
                        errors.append(res["result"]["errors"])

                if errors:
                    print(f"Error: Errors occurred during batch flush: {errors}") # print 유지
                else:
                    print("Batch flush complete.")
            except Exception as e:
                print(f"Error: Exception during final batch flush: {e}") # print 유지
        else:
            print("Weaviate batch queue is empty. No flush needed.") # print 유지


@lru_cache(None)
def get_batch_manager() -> WeaviateBatchManager:
    return WeaviateBatchManager()