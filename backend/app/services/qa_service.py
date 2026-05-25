import logging
import httpx
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class QAService:
    def __init__(self):
        self.url = f"{settings.AI_SERVICE_URL}/qa"
        logger.info(f"Initialized QAService client calling {self.url}")

    def answer_question(self, context: str, question: str) -> str:
        """
        Gửi yêu cầu giải đáp câu hỏi (QA) tới AI service qua HTTP.
        """
        if not context or not question:
            return "ERR_INVALID_INPUT"

        try:
            response = httpx.post(
                self.url,
                json={"context": context, "question": question},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return data["answer"]
        except Exception as e:
            logger.error(f"Lỗi khi kết nối với AI service tại {self.url}: {e}")
            raise RuntimeError(f"AI Service QA Error: {e}")

# Singleton instance
qa_service = QAService()
