from ai.runtime.models import runtime

class EmbeddingService:
    def embed_text(self, texts, is_query=False, expected_version=None):
        if not texts: return []
        if len(texts) > 16: raise ValueError("ERR_EMBEDDING_BATCH")
        with runtime.lock:
            manifest, tokenizer, model, device = runtime.load("embedding")
            import torch
            import torch.nn.functional as F
            if expected_version and manifest.version != expected_version: raise ValueError("ERR_MODEL_VERSION_CHANGED")
            prefix = "query: " if is_query else "passage: "
            values = [prefix + text for text in texts]
            if any(len(tokenizer.encode(text)) > manifest.max_input_tokens for text in values): raise ValueError("ERR_TOKEN_BUDGET")
            inputs = tokenizer(values, padding=True, truncation=False, return_tensors="pt").to(device)
            with torch.inference_mode():
                outputs = model(**inputs).last_hidden_state
                mask = inputs.attention_mask.unsqueeze(-1).bool()
                pooled = outputs.masked_fill(~mask, 0).sum(1) / mask.sum(1).clamp(min=1)
                vectors = F.normalize(pooled, p=2, dim=1)
            if vectors.shape[1] != 384: raise ValueError("ERR_EMBEDDING_SHAPE")
            return vectors.cpu().tolist()

embedding_service = EmbeddingService()
