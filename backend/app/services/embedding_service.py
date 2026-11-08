"""Compatibility client with the same bounded batches as the worker."""
from backend.app.services.ai_client import ai_client

class EmbeddingService:
    def embed_text(self, texts, is_query=False):
        vectors = []
        for start in range(0, len(texts), 16):
            vectors.extend(ai_client.embed(texts[start:start + 16], is_query))
        return vectors

embedding_service = EmbeddingService()
