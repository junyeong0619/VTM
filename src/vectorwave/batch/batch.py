import weaviate
import atexit
import logging
from functools import lru_cache
from ..models.db_config import get_weaviate_settings, WeaviateSettings
from ..database.db import get_weaviate_client
from ..exception.exceptions import WeaviateConnectionError

# logging 대신 print 사용 요청에 따라 logging 비활성화 (필요시 logging.getLogger 사용)
# logger = logging.getLogger(__name__)

class WeaviateBatchManager:
    """
    Weaviate 배치 임포트를 관리하는 싱글톤 클래스입니다.
    """

    def __init__(self):
        self._initialized = False
        print("Initializing WeaviateBatchManager...") # print 유지
        self.client: weaviate.WeaviateClient = None

        try:
            # (get_weaviate_settings가 lru_cache 처리되어 있으므로 재사용됨)
            self.settings: WeaviateSettings = get_weaviate_settings()
            self.client: weaviate.WeaviateClient = get_weaviate_client(self.settings)

            if not self.client:
                raise WeaviateConnectionError("Client is None, cannot configure batch.")

            self.client.batch.configure(
                batch_size=20,
                dynamic=True,
                timeout_retries=3,
            )

            # atexit 등록: 스크립트 종료 시 self.flush() 자동 호출
            atexit.register(self.flush)

            self._initialized = True
            print("WeaviateBatchManager initialized and 'atexit' flush registered.") # print 유지

        except Exception as e:
            # DB 연결 실패 시 VectorWave가 메인 앱을 중단시키지 않도록 함
            print(f"Failed to initialize WeaviateBatchManager: {e}. Batching will be disabled.") # print 유지

    def add_object(self, collection: str, properties: dict, uuid: str = None):
        """
        Weaviate 배치 큐에 객체를 추가합니다.
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
            # (디버그 로그는 너무 많으므로 주석 처리)
            # print(f"Added object to batch for collection '{collection}'.")
        except Exception as e:
            print(f"Error: Failed to add object to batch (Collection: {collection}): {e}") # print 유지

    def flush(self):
        """
        배치 큐에 남아있는 모든 객체를 강제로 Weaviate에 전송합니다.
        ('atexit'에 의해 스크립트 종료 시 자동으로 호출됨)
        """
        if not self._initialized or not self.client:
            return

        if len(self.client.batch) > 0:
            print(f"Flushing Weaviate batch ({len(self.client.batch)} items)...") # print 유지
            try:
                result = self.client.batch.flush()

                # 에러 리포트 확인
                errors = []
                for res in result:
                    if "errors" in res.get("result", {}):
                        errors.append(res["result"]["errors"])

                if errors:
                    print(f"Error: Errors occurred during batch flush: {errors}") # print 유지
                else:
                    print("Batch flush complete.") # print 유지
            except Exception as e:
                print(f"Error: Exception during final batch flush: {e}") # print 유지
        else:
            print("Weaviate batch queue is empty. No flush needed.") # print 유지


@lru_cache(None)
def get_batch_manager() -> WeaviateBatchManager:
    """
    WeaviateBatchManager의 싱글톤 인스턴스를 반환합니다.
    """
    return WeaviateBatchManager()