"""Bounded HTTP contract shared by API and workers; no model loads at import."""
import httpx
from fastapi import HTTPException
from backend.app.core.config import settings
from backend.app.services.features import require_ai

class AIClient:
    def request(self, path: str, payload: dict | None = None) -> dict:
        require_ai()
        try:
            url = settings.AI_SERVICE_URL.rstrip("/") + path
            response = httpx.get(url, timeout=15) if payload is None else httpx.post(url, json=payload, timeout=settings.AI_TIMEOUT_SECONDS)
            if response.status_code in (422, 503):
                detail = response.json().get("detail")
                code = detail if isinstance(detail, str) and detail.startswith("ERR_") else "ERR_AI_SERVICE_ERROR"
                raise HTTPException(response.status_code, code)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict): raise ValueError("Invalid response")
            return data
        except httpx.TimeoutException:
            raise HTTPException(504, "ERR_AI_TIMEOUT") from None
        except httpx.RequestError:
            raise HTTPException(503, "ERR_AI_SERVICE_UNAVAILABLE") from None
        except (httpx.HTTPStatusError, ValueError, TypeError):
            raise HTTPException(502, "ERR_AI_SERVICE_ERROR") from None

    def capability(self, model: str) -> dict:
        matches = [item for item in self.request("/capabilities")["models"] if item["id"] == model]
        if not matches or not matches[0]["ready"]: raise HTTPException(503, "ERR_MODEL_UNAVAILABLE")
        return matches[0]

    def split(self, text: str, model: str, overlap: int = 0) -> list[dict]:
        return self.request("/split", {"text": text, "model": model, "overlap": overlap})["spans"]

    def embed(self, texts: list[str], is_query: bool = False, expected_version: str | None = None) -> list[list[float]]:
        return self.request("/embed", {"texts": texts, "is_query": is_query, "expected_version": expected_version})["embeddings"]

ai_client = AIClient()
