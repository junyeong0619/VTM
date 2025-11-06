import weaviate
import weaviate.classes as wvc
from typing import Dict, Any, Optional, List

from weaviate.collections.classes.filters import _Filters

from ..models.db_config import get_weaviate_settings, WeaviateSettings
from .db import get_cached_client
from ..exception.exceptions import WeaviateConnectionError


def _build_weaviate_filters(filters: Optional[Dict[str, Any]]) -> _Filters | None:
    if not filters:
        return None
    filter_list = [
        wvc.query.Filter.by_property(key).equal(value)
        for key, value in filters.items()
    ]
    if not filter_list:
        return None
    return wvc.query.Filter.all_of(filter_list)


def search_functions(query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Searches function definitions from the [VectorWaveFunctions] collection using natural language (nearText).
    """
    try:
        settings: WeaviateSettings = get_weaviate_settings()
        client: weaviate.WeaviateClient = get_cached_client()

        collection = client.collections.get(settings.COLLECTION_NAME)
        weaviate_filter = _build_weaviate_filters(filters)

        response = collection.query.near_text(
            query=query,
            limit=limit,
            filters=weaviate_filter,
            return_metadata=wvc.query.MetadataQuery(distance=True)
        )

        #todo expand custom range needed
        results = [
            {
                "properties": obj.properties,
                "metadata": obj.metadata,  # This contains the distance
                "uuid": obj.uuid          # Add uuid separately here
            }
            for obj in response.objects
        ]
        return results

    except Exception as e:
        print(f"Error during Weaviate search: {e}")
        raise WeaviateConnectionError(f"Failed to execute 'search_functions': {e}")


def search_executions(
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = "timestamp_utc",
        sort_ascending: bool = False
) -> List[Dict[str, Any]]:
    """
    Searches execution logs from the [VectorWaveExecutions] collection using filtering and sorting.
    """
    try:
        settings: WeaviateSettings = get_weaviate_settings()
        client: weaviate.WeaviateClient = get_cached_client()

        collection = client.collections.get(settings.EXECUTION_COLLECTION_NAME)
        weaviate_filter = _build_weaviate_filters(filters)
        weaviate_sort = None

        if sort_by:
            weaviate_sort = wvc.query.Sort.by_property(
                name=sort_by,
                ascending=sort_ascending
            )

        response = collection.query.fetch_objects(
            limit=limit,
            filters=weaviate_filter,
            sort=weaviate_sort
        )

        return [obj.properties for obj in response.objects]

    except Exception as e:
        raise WeaviateConnectionError(f"Failed to execute 'search_executions': {e}")