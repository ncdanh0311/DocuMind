import logging
from typing import List
import httpx
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.url = f"{settings.AI_SERVICE_URL}/embed"
        logger.info(f"Initialized EmbeddingService client calling {self.url}")

    def embed_text(self, texts: List[str], is_query: bool = False) -> List[List[float]]:
        """
        Gửi yêu cầu sinh vector embedding tới AI service qua HTTP.
        """
        if not texts:
            return []

        try:
            # Tăng timeout vì sinh embedding có thể tốn thời gian với danh sách dài
            response = httpx.post(
                self.url,
                json={"texts": texts, "is_query": is_query},
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            return data["embeddings"]
        except Exception as e:
            logger.error(f"Lỗi khi kết nối với AI service tại {self.url}: {e}")
            raise RuntimeError(f"AI Service Embedding Error: {e}")

# Singleton instance
embedding_service = EmbeddingService()
