"""Compatibility client using the same passage/offset contract as notebook QA."""
from backend.app.services.ai_client import ai_client

class QAService:
    def answer_question(self, context, question, model_type="phobert_qa"):
        return ai_client.request("/qa", {"question": question, "model_type": model_type,
            "passages": [{"chunk_id": "standalone", "content": context}]})["answer"]

qa_service = QAService()
